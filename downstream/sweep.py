"""Cut nine 21-layer windows from a 101-layer render, run the ink_9um checkpoint on each in both depth orders,
and score every one against the published labels: AUC over the held-out validation mask, and the share of
labelled ink and labelled background called ink. The valid mask is the centre window's for every position,
so all nine are measured on the same pixels. This is the script that produced depth/ctl_curve.json, with
one change: SWEEP_BATCH and SWEEP_WORKERS may lower the batch size and worker count (defaults 8 and 2,
about 5 GB). At batch 2 the challenge's aligned input re-scored at 0.9123 against 0.912 at batch 8.

usage: sweep_depth.py <render.zarr> <labels.npz> <work_dir> <ckpt.pth> <villa_src_dir> [starts=0,10,20,30,40,50,60,70,80]
Writes <work_dir>/cuts/<name>/surface-volume.zarr, <work_dir>/preds/, <work_dir>/sweep_results.json and prints a table.
"""
import glob, json, os, shutil, subprocess, sys, time
import numpy as np, zarr, tifffile
from numcodecs import Blosc

render, labels_npz, work, ckpt, villa_src = sys.argv[1:6]
starts = [int(s) for s in (sys.argv[6] if len(sys.argv) > 6 else "0,10,20,30,40,50,60,70,80").split(",")]
DEPTH = 21
T0 = time.time()


def log(m):
    print(f"[{time.time() - T0:7.1f}s] {m}", flush=True)


def open_render(path):
    node = zarr.open(path, mode="r")
    arr = node if hasattr(node, "shape") else node[sorted(node.array_keys(), key=lambda k: (len(k), k))[0]]
    axis = [i for i, s in enumerate(arr.shape) if s == 101]
    if len(axis) != 1:
        raise SystemExit(f"render {path}: cannot find the 101-slice axis in shape {arr.shape}")
    return arr, axis[0]


def read_slab(arr, axis, z0, z1):
    idx = [slice(None)] * 3
    idx[axis] = slice(z0, z1)
    a = np.asarray(arr[tuple(idx)])
    return np.ascontiguousarray(np.moveaxis(a, axis, 0)).astype(np.uint8)


def write_v2(path, data, attrs, clevel=5):
    shutil.rmtree(path, ignore_errors=True)
    g = zarr.open_group(path, mode="w", zarr_format=2)
    g.attrs.update(attrs)
    comp = Blosc(cname="zstd", clevel=clevel, shuffle=Blosc.BITSHUFFLE)
    a = g.create_array("0", shape=data.shape, chunks=(data.shape[0], 128, 128), dtype="uint8", compressors=comp,
                       fill_value=0, chunk_key_encoding={"name": "v2", "separator": "/"})
    a[:] = data
    back = zarr.open(path, mode="r")["0"]
    if back.shape != data.shape or not np.array_equal(np.asarray(back[:, :64, :64]), data[:, :64, :64]):
        raise SystemExit(f"read-back mismatch for {path}")


def auc(s, y):
    from scipy.stats import rankdata
    y = y.astype(bool)
    n1 = int(y.sum())
    n0 = y.size - n1
    if n1 == 0 or n0 == 0:
        return None
    r = rankdata(s)
    return float((r[y].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


# ---------------------------------------------------------------- cut
arr, axis = open_render(render)
log(f"render {arr.shape} depth axis {axis}; windows {starts} x {DEPTH}")
centre = read_slab(arr, axis, 40, 61)
valid = centre.max(axis=0) > 0                      # the same mask every earlier run used, for all nine positions
log(f"valid mask from the centre window: {valid.mean():.3f} of {valid.size} px")
jobs = f"{work}/cuts"
os.makedirs(jobs, exist_ok=True)
names = []
for s in starts:
    if s + DEPTH > arr.shape[axis]:
        log(f"!!! SKIP start {s}: past the end of the render")
        continue
    name = f"ctl_d{s:02d}"
    slab = centre if s == 40 else read_slab(arr, axis, s, s + DEPTH)
    write_v2(f"{jobs}/{name}/surface-volume.zarr",
             slab, {"plan_d": "depth sweep window", "layers": [s, s + DEPTH], "source_render": render, "voxel_um": 9.362})
    names.append(name)
    log(f"cut {name} layers [{s},{s + DEPTH}) mean on valid {slab[DEPTH // 2][valid].mean():.1f}")
np.save(f"{work}/valid.npy", valid)

# ---------------------------------------------------------------- infer
env = dict(os.environ)
env["PYTHONPATH"] = villa_src + (":" + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
env["PYTHONUNBUFFERED"] = "1"
env["TQDM_MININTERVAL"] = "30"
cmd = [sys.executable, "-u", "-m", "vesuvius.ink_detection.inference.infer", "--folder", jobs, "--checkpoint-path", ckpt,
       "--layer-start", "0", "--layer-end", str(DEPTH), "--direction", "both", "--overlap", "0.5", "--blend-mode", "hann",
       "--batch-size", os.environ.get("SWEEP_BATCH", "8"), "--num-workers", os.environ.get("SWEEP_WORKERS", "2"),
       "--no-compile"]
log("infer: " + " ".join(cmd))
logf = open(f"{work}/infer.log", "w")
rc = subprocess.run(cmd, env=env, stdout=logf, stderr=subprocess.STDOUT).returncode
logf.close()
txt = open(f"{work}/infer.log", errors="replace").read()
loaded = [l for l in txt.splitlines() if "missing_keys" in l]
log(f"infer exit {rc}; {loaded[-1][:160] if loaded else 'no weight-load line'}")
if rc != 0:
    log("!!! inference failed; see infer.log")
    raise SystemExit(2)

# ---------------------------------------------------------------- score
L = np.load(labels_npz)
lab = {k: L[k] for k in ("V", "I", "S", "valid")}
vv = lab["V"] & lab["valid"]
ss = lab["S"] & lab["valid"] & ~lab["V"]
rows = []
for name in names:
    s = int(name[5:])
    row = {"name": name, "start": s, "layers": [s, s + DEPTH]}
    for d in ("forward", "reverse"):
        hits = sorted(glob.glob(f"{jobs}/{name}/preds/*_{d}_*.tif"))
        if not hits:
            log(f"!!! {name} {d}: no prediction map")
            continue
        p = tifffile.imread(hits[-1]).astype(np.float32) / 255.0
        if p.shape != valid.shape:
            log(f"!!! {name} {d}: map {p.shape} vs valid {valid.shape}")
            continue
        row[f"auc_{d}"] = auc(p[vv], lab["I"][vv])
        row[f"auc_trained_{d}"] = auc(p[ss], lab["I"][ss])
        row[f"share_{d}"] = float((p[valid] > 0.5).mean())
        row[f"share_on_ink_{d}"] = float((p[vv & lab["I"]] > 0.5).mean())
        row[f"share_on_bg_{d}"] = float((p[vv & ~lab["I"]] > 0.5).mean())
    rows.append(row)
    log(f"{name}: " + json.dumps({k: (round(v, 4) if isinstance(v, float) else v) for k, v in row.items()}))
json.dump({"render": render, "ckpt": ckpt, "starts": starts, "depth": DEPTH, "n_val_px": int(vv.sum()), "rows": rows},
          open(f"{work}/sweep_results.json", "w"), indent=1)

print("\n| layers | AUC fwd | AUC rev | ink share fwd | on labelled ink fwd | on labelled background fwd |")
print("|---|---|---|---|---|---|")
for r in rows:
    f = lambda k, nd=3: ("n/a" if r.get(k) is None else f"{r[k]:.{nd}f}")
    print(f"| [{r['start']},{r['start'] + DEPTH}) | {f('auc_forward')} | {f('auc_reverse')} | "
          f"{f('share_forward')} | {f('share_on_ink_forward')} | {f('share_on_bg_forward')} |")
log("SWEEP_DONE")
