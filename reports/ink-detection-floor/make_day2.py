"""Generate floor_day2.py from the published day-1 job (floor_kernel.py v5) by exact-match replacements, as
floor_day3.py was generated: the jobs, the plants, the shams, the transplants, the scoring and the gates are day 1's,
byte for byte. Only the model changes: PREREG section 3, day 2, "hecate 9.6 um (hecate_9.6um.pth, run with the model
card's own hecate.py) is added on day 2 under the same rules, on its own jobs: each finished 28-layer volume
resampled from 9.362 to 9.6 um in all three directions, then hecate.py reads its central 16 planes, forward and with
--reverse; masks carried to that grid by nearest neighbour."

  python3 make_day2.py        (writes floor_day2.py beside this file and prints how many lines changed)
"""
import difflib, os

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = open(f"{HERE}/floor_kernel.py").read()
REPS = [
# 1. what this job is
('''"""Ink detection floor, day 1 on Kaggle (pre-registration: PREREG.md, beside this file). Does planted ink read like real ink?
''', '''"""Ink detection floor, day 2 on Kaggle: the day-1 jobs read by hecate 9.6 um (PREREG.md section 3, day 2). Generated from
floor_kernel.py (day 1, v5) by make_day2.py; everything below the model is day 1's. The day-1 description follows.

Ink detection floor, day 1 on Kaggle (pre-registration: PREREG.md, beside this file). Does planted ink read like real ink?
'''),
('SCRIPT_VERSION = "floor_kernel v5 (24 Sep 2026): ',
 'SCRIPT_VERSION = "floor_day2 v2 (25 Sep 2026): the day-1 jobs read by hecate 9.6 um (review 7: fp32, exact 9.6 um grid, inputs pinned), generated from floor_kernel v5 (24 Sep 2026): '),
# 2. the model: hecate 9.6 um at a pinned revision, the checkpoint and its own script checked by sha256
('''CKPTS = {"seed42_step010000": "hybrid_3d2d-seed42/step-010000.pth", "seed43_step060000": "hybrid_3d2d-seed43/step-060000.pth"}
HF_REV = "7109667e2607db1b90c37c8b09cb876ea7fe7bb1"              # PREREG section 3: the revision and the files' sha256
CKPT_SHA256 = {"seed42_step010000": "5d0896899092f312299c988de5861a5b6d3669112ee2a4976e2ecf44d4fe3664",
               "seed43_step060000": "bf229faf754da3f1fc3026a3f9a9649341aeb3feb7bc89099cad31c55525d270"}
''', '''CKPTS = {"hecate_9.6um": "hecate_9.6um.pth"}
HF_REPO, HF_REV = "scrollprize/hecate", "9cb86e500e944b11a06a7020403cde5dffb5bcb2"   # day 2: the revision and the sha256s
CKPT_SHA256 = {"hecate_9.6um": "809f4f10f7cb7afa19b4bee0f7d2ab31edd7e11b664f9f210cc9c17f22fcfe5d"}
HECATE_PY_SHA256 = "c232c18a1a86cfb91257a00db13288202bb8ae33732ba26f7291a9b8adb8da59"
AFF = 9.6 / 9.362                   # output voxel i sits at input i * 9.6 / 9.362: exactly 9.6 um apart (review 7)
GRID = (27, 998, 998)               # every output voxel inside the 28 x 1024 x 1024 input: 26 * AFF <= 27, 997 * AFF <= 1023
INPUT_SHA256 = {"windows.json": "c3e90e83effc8f4adc61b44bb1b8bbda0425605031fa24d7401d300baa9e0828",
                "masks.npz": "f87c5cf97f01fb545fb20171c51afe2ca90f1fc7dd3d493086ca93068249189c"}   # day 1's inputs
'''),
# 3. each job: the whole finished 28-layer volume, resampled (linear) to 9.6 um, for hecate.py
('''def write_job(name, vol28):
    path = f"{jobs_dir}/{name}/surface-volume.zarr"
    data = np.ascontiguousarray(vol28[LAYERS[0]:LAYERS[1]])
    g = zarr.open_group(path, mode="w", zarr_format=2)
    g.attrs.update({"floor": name, "layers": list(LAYERS), "voxel_um": 9.362})
    a = g.create_array("0", shape=data.shape, chunks=(data.shape[0], 128, 128), dtype="uint8",
                       compressors=Blosc(cname="zstd", clevel=5, shuffle=Blosc.BITSHUFFLE), fill_value=0,
                       chunk_key_encoding={"name": "v2", "separator": "/"})
    a[:] = data
    back = zarr.open(path, mode="r")["0"]
    if back.shape != data.shape or not np.array_equal(np.asarray(back[:, :64, :64]), data[:, :64, :64]):
        raise SystemExit(f"read-back mismatch for {name}")
''', '''def write_job(name, vol28):
    os.makedirs(f"{jobs_dir}/{name}", exist_ok=True)
    v = ndimage.affine_transform(np.asarray(vol28, np.float32), [AFF] * 3, output_shape=GRID, order=1, mode="nearest")
    np.save(f"{jobs_dir}/{name}/hecate_in.npy", np.clip(np.rint(v), 0, 255).astype(np.uint8))
'''),
# 4. inference: the model card's own hecate.py (load_model, predict), both directions, on every GPU
('''setup_villa(srcdir)
ck_paths = {}
''', '''hpy = f"{TMP}/hecate.py"
for attempt in range(5):
    if os.path.isfile(hpy) and sha256(hpy) == HECATE_PY_SHA256:
        break
    try:
        urllib.request.urlretrieve(f"https://huggingface.co/{HF_REPO}/resolve/{HF_REV}/hecate.py", hpy)
    except Exception as e:                      # noqa: BLE001
        RESULTS["errors"][f"download_hecate_py_{attempt}"] = repr(e)
        time.sleep(10 * (attempt + 1))
if not (os.path.isfile(hpy) and sha256(hpy) == HECATE_PY_SHA256):
    RESULTS["status"] = "failed: hecate.py missing or not the pre-registered file"
    save()
    raise SystemExit(RESULTS["status"])
RESULTS["hecate"] = {"repo": HF_REPO, "revision": HF_REV, "hecate_py_sha256": HECATE_PY_SHA256, "step": AFF, "grid": GRID,
                     "resample": "scipy.ndimage.affine_transform, voxel i at input i * 9.6 / 9.362, linear, grid 27 x 998 x 998; "
                                 "masks the same map, nearest neighbour",
                     "reads": "hecate.predict: the central 16 planes, forward and reversed; fp32 (the card's default), batch 32"}
ck_paths = {}
'''),
('''RESULTS["inputs"] = {"windows": wins[0], "prereg": W.get("prereg"), "seed": W.get("seed"), "catalog_etag": W.get("catalog_etag"),
                     "sha256": {"windows.json": sha256(wins[0]),
                                "masks.npz": sha256(glob.glob(f"{ROOT}/**/masks.npz", recursive=True)[0])}}
''', '''RESULTS["inputs"] = {"windows": wins[0], "prereg": W.get("prereg"), "seed": W.get("seed"), "catalog_etag": W.get("catalog_etag"),
                     "sha256": {"windows.json": sha256(wins[0]),
                                "masks.npz": sha256(glob.glob(f"{ROOT}/**/masks.npz", recursive=True)[0])}}
if RESULTS["inputs"]["sha256"] != INPUT_SHA256:                   # day 2 reads day 1's exact inputs (review 7)
    RESULTS["status"] = f"failed: inputs are not day 1's: {RESULTS['inputs']['sha256']}"
    save()
    raise SystemExit(RESULTS["status"])
'''),
('''            urllib.request.urlretrieve(f"https://huggingface.co/scrollprize/ink_9um/resolve/{HF_REV}/{rel}", dst)''',
 '''            urllib.request.urlretrieve(f"https://huggingface.co/{HF_REPO}/resolve/{HF_REV}/{rel}", dst)'''),
('''def infer_all(ck, tag):
    order = sorted(os.listdir(jobs_dir))
    groups = max(1, ngpu)
    procs = []
    for g in range(groups):
        gdir = f"{TMP}/g{g}_{tag}"
        shutil.rmtree(gdir, ignore_errors=True)
        os.makedirs(gdir, exist_ok=True)
        for j in order[g::groups]:
            os.symlink(os.path.abspath(f"{jobs_dir}/{j}"), f"{gdir}/{j}")
        env = dict(os.environ, PYTHONUNBUFFERED="1", TQDM_MININTERVAL="60")
        env["PYTHONPATH"] = srcdir + (":" + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
        if ngpu:
            env["CUDA_VISIBLE_DEVICES"] = str(g)
            env.setdefault("OMP_NUM_THREADS", "2")
        cmd = [sys.executable, "-u", "-m", "vesuvius.ink_detection.inference.infer", "--folder", gdir,
               "--checkpoint-path", ck, "--layer-start", "0", "--layer-end", str(LAYERS[1] - LAYERS[0]),
               "--direction", "both", "--overlap", "0.5", "--blend-mode", "hann", "--batch-size", "8",
               "--num-workers", "2", "--no-compile"] + (["--gpus", "0"] if ngpu else [])
''', '''RUNNER = """import os, sys
import numpy as np, torch
sys.path.insert(0, os.path.dirname(sys.argv[1]))
import hecate                                     # the model card's own script, checked by sha256 above
dev = "cuda" if torch.cuda.is_available() else "cpu"
model = hecate.load_model(sys.argv[2], dev)
for job in sys.argv[3:]:
    vol = np.load(os.path.join(job, "hecate_in.npy"), mmap_mode="r")
    for d, rev in (("forward", False), ("reverse", True)):   # --reverse: the full depth reversed first
        out = np.zeros(vol.shape[1:], np.uint8)
        hecate.predict(model, vol, out, reverse=rev, batch_size=32, precision="fp32")   # the card's default; native on T4
        np.save(os.path.join(job, "hecate_" + d + ".npy"), out)
    print("done", os.path.basename(job), flush=True)
"""
open(f"{TMP}/hecate_runner.py", "w").write(RUNNER)


def infer_all(ck, tag):
    order = sorted(os.listdir(jobs_dir))
    groups = max(1, ngpu)
    procs = []
    for g in range(groups):
        env = dict(os.environ, PYTHONUNBUFFERED="1")
        if ngpu:
            env["CUDA_VISIBLE_DEVICES"] = str(g)
            env.setdefault("OMP_NUM_THREADS", "2")
        cmd = [sys.executable, "-u", f"{TMP}/hecate_runner.py", hpy, ck] + [f"{jobs_dir}/{j}" for j in order[g::groups]]
'''),
# 5. scoring: day 1's AUC on hecate's 2D map, the masks carried to its grid by nearest neighbour
('''        for d in ("forward", "reverse"):
            hits = sorted(glob.glob(f"{jobs_dir}/{name}/preds/*_{d}_*.tif"))
            if not hits:
                continue
            p = tifffile.imread(hits[-1]).astype(np.float32) / 255.0
''', '''        pos = ndimage.affine_transform(pos.astype(np.uint8), [AFF] * 2, output_shape=GRID[1:], order=0,
                                       mode="nearest").astype(bool)                    # nearest neighbour
        neg = ndimage.affine_transform(neg.astype(np.uint8), [AFF] * 2, output_shape=GRID[1:], order=0,
                                       mode="nearest").astype(bool)
        oy, ox, core = int(round(oy / AFF)), int(round(ox / AFF)), int(round(CORE / AFF))
        maps[f"{name}__pos"] = pos[oy:oy + core, ox:ox + core].astype(np.uint8)      # the core's masks, on this grid
        maps[f"{name}__neg"] = neg[oy:oy + core, ox:ox + core].astype(np.uint8)
        for d in ("forward", "reverse"):
            hits = [f"{jobs_dir}/{name}/hecate_{d}.npy"] if os.path.isfile(f"{jobs_dir}/{name}/hecate_{d}.npy") else []
            if not hits:
                continue
            p = np.load(hits[-1]).astype(np.float32) / 255.0
'''),
('''            maps[f"{name}__{d}"] = np.rint(p[oy:oy + CORE, ox:ox + CORE] * 255).astype(np.uint8)   # the raw map, kept
''', '''            maps[f"{name}__{d}"] = np.rint(p[oy:oy + core, ox:ox + core] * 255).astype(np.uint8)   # the raw map, kept
'''),
('''        shutil.rmtree(f"{jobs_dir}/{name}/preds", ignore_errors=True)   # the next checkpoint writes fresh maps
''', '''        for d in ("forward", "reverse"):                                 # the next checkpoint writes fresh maps
            if os.path.isfile(f"{jobs_dir}/{name}/hecate_{d}.npy"):
                os.remove(f"{jobs_dir}/{name}/hecate_{d}.npy")
'''),
]
out = SRC
for old, new in REPS:
    if out.count(old) != 1:
        raise SystemExit(f"no single match for: {old[:80]!r}")
    out = out.replace(old, new)
open(f"{HERE}/floor_day2.py", "w").write(out)
changed = [l for l in difflib.unified_diff(SRC.splitlines(), out.splitlines(), lineterm="", n=0)
           if l[:1] in "+-" and not l.startswith(("+++", "---"))]
print(f"floor_day2.py: {len(changed)} changed lines against floor_kernel.py")
