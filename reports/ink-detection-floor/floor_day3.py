"""Ink detection floor, day 3 on Kaggle (PREREG.md, amendment 1): the floor on PHerc0846B's surfaces.

Built from the day-1 kernel (floor_kernel.py v5) by replacing only the day-3 parts: the inputs, the target and sham
jobs, the whole-surface jobs and the readout. Planting, scoring, inference and environment handling are day 1's,
byte for byte.

Inputs: the day-1 dataset (windows.json, masks.npz, villa_vesuvius_src.tar), day-1's own results.json (for the
reference control), day3/windows_day3.json (prep_day3.py) and the seven PHerc0846B renders (villa's vc_render_tifxyz,
31 planes; planes [1, 29) are the 28-layer volume, surface at layer 14).

Jobs: the six day-1 references again (the control); for each day-3 target, clean, the swap plant at three strengths
and two shams at each, one of PHerc0846B papyrus and one of PHerc0139 papyrus (surface to surface, no depth shift); and each whole surface, for the models' own output.
env: FL_INPUT FL_WORK FL_TMP FL_PIP FL_STRENGTHS FL_SELFTEST_ONLY FL_LIMIT_TARGETS FL_NO_INFER
"""
import glob, json, os, re, shutil, ssl, subprocess, sys, tarfile, time
from concurrent.futures import ThreadPoolExecutor

SCRIPT_VERSION = "floor_day3 v2 (24 Sep 2026): the floor on PHerc0846B (PREREG amendment 1), built from floor_kernel v5; review 4: PHerc0139 shams, inputs pinned, profiles checked"
T0 = time.time()
ROOT = os.environ.get("FL_INPUT", "/kaggle/input")
WORK = os.environ.get("FL_WORK", "/kaggle/working")
OUT = f"{WORK}/out"
TMP = os.environ.get("FL_TMP") or "/kaggle/tmp/floor"
try:
    os.makedirs(TMP, exist_ok=True)
except OSError:
    TMP = f"{WORK}/tmp"
PIP = os.environ.get("FL_PIP", "1") == "1"
PLANTS = ["swap"]                                   # carried forward from day 1 (PREREG amendment 1)
STRENGTHS = [float(s) for s in os.environ.get("FL_STRENGTHS", "0.25,0.5,1").split(",")]
SELFTEST_ONLY = os.environ.get("FL_SELFTEST_ONLY", "0") == "1"
LIMIT_TARGETS = int(os.environ.get("FL_LIMIT_TARGETS", "0"))
NO_INFER = os.environ.get("FL_NO_INFER", "0") == "1"      # local test: build the jobs, stop before the GPU stage
HTTP = "https://vesuvius-challenge-open-data.s3.us-east-1.amazonaws.com/"
CKPTS = {"seed42_step010000": "hybrid_3d2d-seed42/step-010000.pth", "seed43_step060000": "hybrid_3d2d-seed43/step-060000.pth"}
HF_REV = "7109667e2607db1b90c37c8b09cb876ea7fe7bb1"              # PREREG section 3: the revision and the files' sha256
CKPT_SHA256 = {"seed42_step010000": "5d0896899092f312299c988de5861a5b6d3669112ee2a4976e2ecf44d4fe3664",
               "seed43_step060000": "bf229faf754da3f1fc3026a3f9a9649341aeb3feb7bc89099cad31c55525d270"}
LAYERS = (4, 25)                    # plane 14 is the middle of the model's 21-layer window
SIGMA, DILATE, FEATHER, CORE = 48.0, 3, 2.0, 512
RESULTS = {"script_version": SCRIPT_VERSION, "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "plants": PLANTS, "strengths": STRENGTHS, "layers": LAYERS, "sigma": SIGMA, "feather_px": FEATHER,
           "status": "running", "errors": {}, "jobs": {}}
os.makedirs(OUT, exist_ok=True)


def log(m):
    print(f"[floor {time.strftime('%H:%M:%S')} + {(time.time() - T0) / 60:5.1f} min] {m}", flush=True)


def save():
    json.dump(RESULTS, open(f"{OUT}/results.json", "w"), indent=1)


def pip_install(pkg):
    if PIP:
        log(f"pip install --no-deps {pkg}")
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "--no-deps", pkg], check=False)


# ---------------------------------------------------------------- 1. environment, before anything expensive
PIP_NAMES = {"zarr": "zarr<4", "numcodecs": "numcodecs<0.17", "PIL": "pillow", "cv2": "opencv-python-headless",
             "skimage": "scikit-image", "yaml": "pyyaml", "sklearn": "scikit-learn", "nrrd": "pynrrd",
             "huggingface_hub": "huggingface-hub", "dynamic_network_architectures": "dynamic-network-architectures"}


def ensure(mod, tries=8):
    for _ in range(tries):
        try:
            __import__(mod)
            return None
        except ModuleNotFoundError as e:
            name = getattr(e, "name", None) or str(e).split("'")[1]
            pip_install(PIP_NAMES.get(name, name))
        except Exception as e:                       # noqa: BLE001
            return f"{mod}: {e!r}"
    try:
        __import__(mod)
        return None
    except Exception as e:                           # noqa: BLE001
        return f"{mod}: {e!r}"


import importlib.util                               # noqa: E402
for _mod, _pkg in (("numcodecs", "numcodecs<0.17"), ("zarr", "zarr<4"), ("imagecodecs", "imagecodecs"),
                   ("tifffile", "tifffile")):
    if importlib.util.find_spec(_mod) is None:
        pip_install(_pkg)
missing = [m for m in (ensure(x) for x in ("numpy", "numcodecs", "zarr", "imagecodecs", "tifffile",
                                          "scipy.ndimage", "scipy.stats", "PIL.Image", "torch")) if m]
if missing:
    RESULTS["status"] = "failed: imports"
    RESULTS["errors"]["imports"] = missing
    save()
    raise SystemExit("imports: " + "; ".join(missing))
import numpy as np, zarr, tifffile                  # noqa: E402
from numcodecs import Blosc                          # noqa: E402
from scipy import ndimage, stats                     # noqa: E402
from PIL import Image                                # noqa: E402
log("imports ok: " + SCRIPT_VERSION)


# ---------------------------------------------------------------- 2. the science, as small pure functions
def background(v, weight):
    """Per-layer normalised Gaussian smoothing of v (Z, H, W) with 2-D weights (H, W) in [0, 1]."""
    w = weight.astype(np.float32)
    den = ndimage.gaussian_filter(w, SIGMA)
    out = np.empty(v.shape, np.float32)
    for z in range(v.shape[0]):
        out[z] = ndimage.gaussian_filter(v[z].astype(np.float32) * w, SIGMA) / np.maximum(den, 1e-6)
    return out


def rstd(x):
    x = np.asarray(x, np.float32).ravel()
    return float(1.4826 * np.median(np.abs(x - np.median(x)))) if x.size else float("nan")


def shift_z(e, d):
    if d == 0:
        return e
    out = np.zeros_like(e)
    if d > 0:
        out[d:] = e[:-d]
    else:
        out[:d] = e[-d:]
    return out


def auc(score, pos, neg):
    """Pixel AUC by ranks: P(score of a random positive > score of a random negative), ties counted half."""
    sp, sn = score[pos].ravel(), score[neg].ravel()
    if sp.size == 0 or sn.size == 0:
        return float("nan")
    r = stats.rankdata(np.concatenate([sp, sn]))
    return float((r[:sp.size].sum() - sp.size * (sp.size + 1) / 2) / (sp.size * sn.size))


def soft(mask):
    """The ink mask with its edges softened by FEATHER px (real ink edges are not knife-sharp at 9 um)."""
    return np.clip(ndimage.gaussian_filter(mask.astype(np.float32), FEATHER), 0, 1)


def plant(target, resid_d, s, k, y0, x0, msoft, mode, t_resid):
    """R = V - B (residual texture). additive: target + m*s*k*R_donor. swap: target + m*((sqrt(1 - s^2) - 1)*R_target
    + s*k*R_donor): the donor's residual goes in at amplitude s and the target's own residual is scaled so that the
    two, being unrelated, keep the texture level (s = 1 replaces it; s = 0 leaves the target untouched).
    Returns the uint8 volume and the share of changed voxels, in the layers the model reads, clipped at 0 or 255."""
    out = target.astype(np.float32).copy()
    h, w = msoft.shape
    if mode == "swap":
        add = msoft[None] * ((np.sqrt(max(0.0, 1.0 - s * s)) - 1.0) * t_resid + s * k * resid_d)
    else:
        add = s * k * resid_d * msoft[None]
    out[:, y0:y0 + h, x0:x0 + w] += add
    core = out[LAYERS[0]:LAYERS[1], y0:y0 + h, x0:x0 + w]              # the layers the model reads
    touched = np.abs(add[LAYERS[0]:LAYERS[1]]) >= 0.5
    clipped = float(((core < -0.5) | (core > 255.5))[touched].mean()) if touched.any() else 0.0
    return np.clip(np.rint(out), 0, 255).astype(np.uint8), clipped


def selftest():
    """Code, not science: the planter touches only the mask; the scorer gives 1, 0.5 and 0 where it must."""
    rng = np.random.default_rng(0)
    v = rng.integers(60, 120, size=(28, 256, 256)).astype(np.uint8)
    m = np.zeros((96, 96), bool)
    m[20:40, 10:80] = True
    m[50:70, 30:50] = True
    e = np.full((28, 96, 96), 30.0, np.float32)
    changed = np.zeros((256, 256), bool)
    changed[80:176, 80:176] = m
    ok_plant = True
    for mode in ("additive", "swap"):
        p, _ = plant(v, e, 1.0, 1.0, 80, 80, m.astype(np.float32), mode, np.zeros((28, 96, 96), np.float32))
        diff = (p.astype(int) != v.astype(int)).any(axis=0)
        ok_plant = ok_plant and bool(diff[~changed].sum() == 0 and diff[changed].mean() > 0.9)
    pos = changed
    neg = np.zeros_like(pos)
    neg[80:176, 80:176] = ~m
    perfect = pos.astype(np.float32) * 0.8 + rng.random(pos.shape) * 0.1
    noise = rng.random(pos.shape).astype(np.float32)
    a1, a5, a0 = auc(perfect, pos, neg), auc(noise, pos, neg), auc(1 - perfect, pos, neg)
    ok_auc = a1 > 0.99 and 0.45 < a5 < 0.55 and a0 < 0.01
    bg = background(np.full((3, 64, 64), 100, np.uint8), np.ones((64, 64), bool))
    ok_bg = bool(np.allclose(bg, 100, atol=1e-3))
    sh = shift_z(np.arange(28, dtype=np.float32)[:, None, None] * np.ones((28, 2, 2), np.float32), 3)
    ok_shift = bool(sh[3, 0, 0] == 0 and sh[27, 0, 0] == 24 and sh[:3].sum() == 0)
    # the swap keeps the texture level at every strength (two unrelated textures of equal spread); a transplant
    # (swap, s = 1, mask of ones) leaves exactly the target's background plus the donor's residual
    rt = rng.normal(0, 20, size=(28, 96, 96)).astype(np.float32)
    rd = rng.normal(0, 20, size=(28, 96, 96)).astype(np.float32)
    base = np.full((28, 256, 256), 128, np.uint8)
    base[:, 80:176, 80:176] = np.clip(np.rint(128 + rt), 0, 255).astype(np.uint8)
    ones = np.ones((96, 96), np.float32)
    lvl = []
    for s_ in (0.25, 0.5, 1.0):
        p, _ = plant(base, rd, s_, 1.0, 80, 80, ones, "swap", base[:, 80:176, 80:176].astype(np.float32) - 128)
        lvl.append(round(float(p[:, 80:176, 80:176].astype(np.float32).std() / base[:, 80:176, 80:176].astype(np.float32).std()), 3))
    ok_level = all(0.95 < x < 1.05 for x in lvl)
    p, clip0 = plant(base, rd, 1.0, 1.0, 80, 80, ones, "swap", base[:, 80:176, 80:176].astype(np.float32) - 128)
    ok_transplant = bool(np.abs(p[:, 80:176, 80:176].astype(np.float32) - np.clip(np.rint(128 + rd), 0, 255)).max() <= 1.0)
    _, clip_big = plant(base, rd * 20, 1.0, 1.0, 80, 80, ones, "additive", rt)
    ok_clip = clip0 < 0.01 and clip_big > 0.3
    RESULTS["selftest"] = {"plant_only_under_mask": ok_plant, "auc_1_half_0": [a1, a5, a0], "background_flat": ok_bg,
                           "depth_shift": ok_shift, "swap_texture_level_s025_s05_s1": lvl, "transplant_exact": ok_transplant,
                           "clip_share_counted": ok_clip,
                           "pass": bool(ok_plant and ok_auc and ok_bg and ok_shift and ok_level and ok_transplant and ok_clip)}
    save()
    log(f"self-test: plant {ok_plant}, auc {a1:.3f}/{a5:.3f}/{a0:.3f}, background {ok_bg}, shift {ok_shift}, "
        f"swap level {lvl}, transplant {ok_transplant}, clip count {ok_clip}")
    if not RESULTS["selftest"]["pass"]:
        RESULTS["status"] = "failed: self-test"
        save()
        raise SystemExit("self-test failed")


selftest()
if SELFTEST_ONLY:
    RESULTS["status"] = "done (self-test only)"
    save()
    raise SystemExit(0)

# ---------------------------------------------------------------- 3. inputs
wins = sorted(glob.glob(f"{ROOT}/**/windows.json", recursive=True))
if not wins:
    raise SystemExit(f"no windows.json under {ROOT}")
W = json.load(open(wins[0]))
if W.get("version") != 2:
    raise SystemExit("windows.json is not version 2")
MASKS = dict(np.load(glob.glob(f"{ROOT}/**/masks.npz", recursive=True)[0]))
import hashlib                                      # noqa: E402


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


RESULTS["inputs"] = {"windows": wins[0], "prereg": W.get("prereg"), "seed": W.get("seed"), "catalog_etag": W.get("catalog_etag"),
                     "sha256": {"windows.json": sha256(wins[0]),
                                "masks.npz": sha256(glob.glob(f"{ROOT}/**/masks.npz", recursive=True)[0])}}
w3 = sorted(glob.glob(f"{ROOT}/**/windows_day3.json", recursive=True))
if not w3:
    raise SystemExit(f"no windows_day3.json under {ROOT}")
W3 = json.load(open(w3[0]))
if W3.get("day") != 3 or W3.get("version") != 3:
    raise SystemExit("windows_day3.json is not day 3, version 3")
day1 = [p for p in sorted(glob.glob(f"{ROOT}/**/results.json", recursive=True))
        if json.load(open(p)).get("script_version", "").startswith("floor_kernel v5")
        and sum(1 for j in json.load(open(p))["jobs"].values() if j["kind"] == "clean") == 12]
if len(day1) != 1:
    raise SystemExit(f"expected day 1's full results.json once, found {len(day1)}")
DAY1 = json.load(open(day1[0]))
RENDERS = {}
for p in sorted(glob.glob(f"{ROOT}/**/render_segment_given.zarr", recursive=True)):
    m = re.search(r"pherc0846b-render-(s\d\d|1)\b", p)
    if m:
        RENDERS["s01" if m.group(1) == "1" else m.group(1)] = zarr.open(f"{p}/0", mode="r")
if sorted(RENDERS) != sorted(W3["surfaces"]):
    raise SystemExit(f"renders {sorted(RENDERS)} do not match the day-3 windows' surfaces {sorted(W3['surfaces'])}")
RESULTS["inputs"]["sha256"]["windows_day3.json"] = sha256(w3[0])
RESULTS["inputs"]["sha256"]["day1_results.json"] = sha256(day1[0])
RESULTS["inputs"]["renders"] = {s: list(a.shape) for s, a in RENDERS.items()}
PINNED = {"windows.json": "c3e90e83effc8f4adc61b44bb1b8bbda0425605031fa24d7401d300baa9e0828",   # amendment 1: the
          "masks.npz": "f87c5cf97f01fb545fb20171c51afe2ca90f1fc7dd3d493086ca93068249189c",      # inputs, pinned
          "windows_day3.json": "278eae907664a5e2f44ff8ab282c33adb34b0521280d24eb43373f6bf70317b0",
          "day1_results.json": "61f6af77bc64189f5442cb9ee56461ffb618a48d2a5191662f7c76d7ee2e2056"}
wrong = {k: v[:16] for k, v in RESULTS["inputs"]["sha256"].items() if k in PINNED and v != PINNED[k]}
if wrong or set(PINNED) - set(RESULTS["inputs"]["sha256"]):
    RESULTS["status"] = f"failed: inputs are not the pinned files {wrong}"
    save()
    raise SystemExit(RESULTS["status"])
src = sorted(glob.glob(f"{ROOT}/**/vesuvius/ink_detection/inference/infer.py", recursive=True))
if not src:
    tars = sorted(glob.glob(f"{ROOT}/**/villa_vesuvius_src.tar", recursive=True))
    if not tars:
        raise SystemExit("villa_vesuvius_src.tar not found")
    with tarfile.open(tars[0]) as tf:
        tf.extractall(TMP)
    src = sorted(glob.glob(f"{TMP}/**/vesuvius/ink_detection/inference/infer.py", recursive=True))
srcdir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(src[0]))))


def setup_villa(srcdir):
    os.environ["PYTHONPATH"] = srcdir + (":" + os.environ["PYTHONPATH"] if os.environ.get("PYTHONPATH") else "")
    sys.path.insert(0, srcdir)
    for _ in range(30):
        rr = subprocess.run([sys.executable, "-c", "from vesuvius.ink_detection.inference import infer; print('IMPORT_OK')"],
                            capture_output=True, text=True)
        if "IMPORT_OK" in rr.stdout:
            log("villa inference imports OK")
            return
        m = re.search(r"No module named '([A-Za-z0-9_.]+)", rr.stderr)
        if not m or not PIP:
            RESULTS["errors"]["villa_import"] = rr.stderr[-3000:]
            save()
            raise SystemExit(4)
        pip_install(PIP_NAMES.get(m.group(1).split(".")[0], m.group(1).split(".")[0]))
    raise SystemExit(4)


import urllib.request                               # noqa: E402
import urllib.error                                 # noqa: E402
try:                                                # some Pythons cannot verify S3 without certifi's bundle
    import certifi
    SSL_CTX = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    SSL_CTX = ssl.create_default_context()
save()


# ---------------------------------------------------------------- 4. read windows from the bucket
def fetch_chunk(url):
    last = None
    for attempt in range(5):
        try:
            return urllib.request.urlopen(url, timeout=120, context=SSL_CTX).read()
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None                          # this bucket answers 404 for a chunk never written: fill value 0
            last = e
        except Exception as e:                       # noqa: BLE001
            last = e
        time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"could not fetch {url}: {last!r}")


def read_box(prefix, box):
    """28 x h x w uint8 from a segment's 9.362 um surface volume (zarr v2, uncompressed 28 x 128 x 128 chunks)."""
    y0, y1, x0, x1 = box
    base = f"{HTTP}{prefix}{W['surface_volume']}/0"
    cy, cx = range(y0 // 128, (y1 - 1) // 128 + 1), range(x0 // 128, (x1 - 1) // 128 + 1)
    keys = [(a, b) for a in cy for b in cx]
    with ThreadPoolExecutor(16) as ex:
        blobs = list(ex.map(lambda ab: fetch_chunk(f"{base}/0/{ab[0]}/{ab[1]}"), keys))
    out = np.zeros((28, len(cy) * 128, len(cx) * 128), np.uint8)
    for (a, b), blob in zip(keys, blobs):
        if blob is not None:
            out[:, (a - cy[0]) * 128:(a - cy[0] + 1) * 128, (b - cx[0]) * 128:(b - cx[0] + 1) * 128] = \
                np.frombuffer(blob, np.uint8).reshape(28, 128, 128)
    oy, ox = y0 - cy[0] * 128, x0 - cx[0] * 128
    return out[:, oy:oy + (y1 - y0), ox:ox + (x1 - x0)]


# ---------------------------------------------------------------- 5. build the jobs
jobs_dir = f"{TMP}/jobs"
shutil.rmtree(jobs_dir, ignore_errors=True)
os.makedirs(jobs_dir, exist_ok=True)
SCORE = {}                     # job -> (positives, negatives, (y0, x0)) on the 1024 px window; maps kept for the core


def write_job(name, vol28):
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


def core_offset(rec):
    return rec["core"][0] - rec["box"][0], rec["core"][2] - rec["box"][2]


donors = []
for i, d in enumerate(W["donors"]):
    ink, neg = MASKS[f"donor{i}_ink"], MASKS[f"donor{i}_neg"]
    box = read_box(d["prefix"], d["box"])
    oy, ox = core_offset(d)
    name = f"ref{i}_{d['seg']}"                                       # the reference: these letters, in place
    write_job(name, box)
    pos_w, neg_w = np.zeros(box.shape[1:], bool), np.zeros(box.shape[1:], bool)
    pos_w[oy:oy + CORE, ox:ox + CORE], neg_w[oy:oy + CORE, ox:ox + CORE] = ink, neg
    SCORE[name] = (pos_w, neg_w, (oy, ox))
    RESULTS["jobs"][name] = {"kind": "reference", "seg": d["seg"], "donor": i}
    v = box[:, oy:oy + CORE, ox:ox + CORE].astype(np.float32)
    resid = v - background(v, neg)
    k_den = rstd(resid[LAYERS[0]:LAYERS[1]][:, neg])
    prof = [float(resid[z][ink].mean() - resid[z][neg].mean()) / max(k_den, 1e-6) for z in range(28)]
    donors.append({"ink": ink, "neg": neg, "resid": resid, "msoft": soft(ink), "rstd": k_den, "sheet": d["sheet_layer"]})
    RESULTS.setdefault("donors", []).append({"seg": d["seg"], "core": d["core"], "ink_px": int(ink.sum()),
                                             "resid_rstd": k_den, "sheet_layer": d["sheet_layer"],
                                             "ink_contrast_by_layer_in_texture_sd": [round(p, 3) for p in prof],
                                             "ink_contrast_at_sheet": round(prof[d["sheet_layer"]], 3)})
save()
log(f"{len(donors)} donors read; references written")

targets = W3["targets"][:LIMIT_TARGETS] if LIMIT_TARGETS else W3["targets"]
L28 = W3["layers28_from_render_planes"]


def read_render(sid, box):
    y0, y1, x0, x1 = box
    return np.asarray(RENDERS[sid][L28[0]:L28[1], y0:y1, x0:x1])


for t in targets:
    dn = donors[t["donor"]]
    sh = W3["shams"][t["sham"]]
    v = read_render(t["surface"], t["box"])
    cy0, cx0 = core_offset(t)
    core = v[:, cy0:cy0 + CORE, cx0:cx0 + CORE].astype(np.float32)
    core_resid = core - background(core, np.ones((CORE, CORE), bool))
    t_rstd = rstd(core_resid[LAYERS[0]:LAYERS[1]])
    k = t_rstd / dn["rstd"]
    t_resid = core - background(core, dn["neg"])                      # the swap replaces this
    r_d = dn["resid"]                                                 # surface to surface: no depth shift (amendment 1)
    sv = read_render(sh["surface"], sh["core"]).astype(np.float32)
    for rec, vol in ((t, core), (sh, sv)):                            # the renders are the ones the pick read
        prof = ndimage.uniform_filter1d(vol.reshape(vol.shape[0], -1).mean(1).astype(np.float32), 3)
        if max(abs(round(float(a_), 1) - b_) for a_, b_ in zip(prof, rec["profile"])) > 0.051:
            RESULTS["status"] = f"failed: the render under {rec.get('name', rec['surface'])} {rec['core']} has changed"
            save()
            raise SystemExit(RESULTS["status"])
    sham_r = sv - background(sv, dn["neg"])
    k_sham = t_rstd / rstd(sham_r[LAYERS[0]:LAYERS[1]][:, dn["neg"]])
    xs = W["shams"][t["sham"]]                                        # day 1's PHerc0139 blank sham, same index
    xv = read_box(xs["prefix"], xs["core"]).astype(np.float32)
    xsham_r = xv - background(xv, dn["neg"])                          # PHerc0139 texture, no ink, no depth shift
    k_x = t_rstd / rstd(xsham_r[LAYERS[0]:LAYERS[1]][:, dn["neg"]])
    pos = np.zeros(v.shape[1:], bool)
    neg = np.zeros(v.shape[1:], bool)
    pos[cy0:cy0 + CORE, cx0:cx0 + CORE], neg[cy0:cy0 + CORE, cx0:cx0 + CORE] = dn["ink"], dn["neg"]
    meta = {"surface": t["surface"], "donor": t["donor"], "sham_core": sh["core"], "sham_surface": sh["surface"],
            "k": k, "k_sham": k_sham, "xsham_seg": xs["seg"], "xsham_core": xs["core"], "k_xsham": k_x, "depth_shift": 0}
    name = f"{t['name']}__clean"
    write_job(name, v)
    SCORE[name] = (pos, neg, (cy0, cx0))
    RESULTS["jobs"][name] = dict(meta, kind="clean", strength=0.0)
    for mode in PLANTS:
        for s_ in STRENGTHS:
            name = f"{t['name']}__{mode}__s{s_:g}"
            vol, clipped = plant(v, r_d, s_, k, cy0, cx0, dn["msoft"], mode, t_resid)
            write_job(name, vol)
            SCORE[name] = (pos, neg, (cy0, cx0))
            RESULTS["jobs"][name] = dict(meta, kind="planted", plant=mode, strength=s_, clipped_share=clipped)
            name = f"{t['name']}__{mode}__sham{s_:g}"
            vol, clipped = plant(v, sham_r, s_, k_sham, cy0, cx0, dn["msoft"], mode, t_resid)
            write_job(name, vol)
            SCORE[name] = (pos, neg, (cy0, cx0))
            RESULTS["jobs"][name] = dict(meta, kind="sham", plant=mode, strength=s_, clipped_share=clipped)
            name = f"{t['name']}__{mode}__xsham{s_:g}"
            vol, clipped = plant(v, xsham_r, s_, k_x, cy0, cx0, dn["msoft"], mode, t_resid)
            write_job(name, vol)
            SCORE[name] = (pos, neg, (cy0, cx0))
            RESULTS["jobs"][name] = dict(meta, kind="xsham", plant=mode, strength=s_, clipped_share=clipped)
    log(f"{t['name']}: donor {t['donor']}, k {k:.3f}, sham k {k_sham:.3f}, PHerc0139 sham k {k_x:.3f}, surface to surface")
for sid in sorted(RENDERS):                                           # the models' own output on each whole surface
    write_job(f"whole_{sid}", np.asarray(RENDERS[sid][L28[0]:L28[1]]))
    RESULTS["jobs"][f"whole_{sid}"] = {"kind": "whole", "surface": sid}
save()
log(f"{len(RESULTS['jobs'])} jobs written")


# ---------------------------------------------------------------- 6. inference, per checkpoint, then score
if NO_INFER:
    RESULTS["status"] = "done (jobs built, no inference)"
    save()
    raise SystemExit(0)
setup_villa(srcdir)
ck_paths = {}
for tag, rel in CKPTS.items():
    dst = f"{TMP}/{tag}.pth"
    for attempt in range(5):
        if os.path.isfile(dst) and sha256(dst) == CKPT_SHA256[tag]:
            break
        log(f"downloading {rel} at revision {HF_REV} (attempt {attempt + 1})")
        try:
            urllib.request.urlretrieve(f"https://huggingface.co/scrollprize/ink_9um/resolve/{HF_REV}/{rel}", dst)
        except Exception as e:                      # noqa: BLE001
            RESULTS["errors"][f"download_{tag}_{attempt}"] = repr(e)
            time.sleep(10 * (attempt + 1))
    if not (os.path.isfile(dst) and sha256(dst) == CKPT_SHA256[tag]):
        RESULTS["status"] = f"failed: checkpoint {tag} missing or not the pre-registered file"
        save()
        raise SystemExit(RESULTS["status"])
    ck_paths[tag] = dst
RESULTS["checkpoints"] = {t: {"hf": CKPTS[t], "hf_revision": HF_REV, "bytes": os.path.getsize(p), "sha256": sha256(p)}
                          for t, p in ck_paths.items()}
save()
import torch                                         # noqa: E402
ngpu = torch.cuda.device_count()
RESULTS["gpus"] = ngpu


def infer_all(ck, tag):
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
        lf = open(f"{OUT}/infer_{tag}_g{g}.log", "w")
        procs.append((g, subprocess.Popen(cmd, env=env, stdout=lf, stderr=subprocess.STDOUT, start_new_session=True), lf))
    ok = True
    for g, p, lf in procs:
        rc = p.wait()
        lf.close()
        if rc != 0:
            ok = False
            RESULTS["errors"][f"infer_{tag}_g{g}"] = open(f"{OUT}/infer_{tag}_g{g}.log", errors="replace").read()[-1500:]
    return ok


prev = f"{OUT}/preview"
os.makedirs(prev, exist_ok=True)
for tag, ck in ck_paths.items():
    log(f"inference with {tag}")
    RESULTS[f"infer_ok_{tag}"] = infer_all(ck, tag)
    maps = {}
    for name, (pos, neg, (oy, ox)) in SCORE.items():
        row = RESULTS["jobs"][name].setdefault("auc", {}).setdefault(tag, {})
        stat = RESULTS["jobs"][name].setdefault("mean", {}).setdefault(tag, {})
        for d in ("forward", "reverse"):
            hits = sorted(glob.glob(f"{jobs_dir}/{name}/preds/*_{d}_*.tif"))
            if not hits:
                continue
            p = tifffile.imread(hits[-1]).astype(np.float32) / 255.0
            if p.shape != pos.shape:
                RESULTS["errors"][f"shape_{name}_{tag}_{d}"] = f"{p.shape} vs {pos.shape}"
                continue
            row[d] = auc(p, pos, neg)
            stat[d] = {"pos": float(p[pos].mean()), "neg": float(p[neg].mean())}
            maps[f"{name}__{d}"] = np.rint(p[oy:oy + CORE, ox:ox + CORE] * 255).astype(np.uint8)   # the raw map, kept
            if d == "forward" and RESULTS["jobs"][name]["kind"] in ("reference", "clean") or \
                    (d == "forward" and RESULTS["jobs"][name].get("strength") == 1.0):
                Image.fromarray((np.clip((p - 0.25) / 0.5, 0, 1)[::2, ::2] * 255).astype(np.uint8)).save(
                    f"{prev}/{name}__{tag}_fwd_ds2.png")
        shutil.rmtree(f"{jobs_dir}/{name}/preds", ignore_errors=True)   # the next checkpoint writes fresh maps
    np.savez_compressed(f"{OUT}/maps_{tag}.npz", **maps)
    save()                                                            # the scored maps are safe before the whole ones
    whole = {}
    try:                                   # a failure here is recorded and never costs the scored results
        for name in sorted(n for n in RESULTS["jobs"] if RESULTS["jobs"][n]["kind"] == "whole"):
            stat = RESULTS["jobs"][name].setdefault("mean", {}).setdefault(tag, {})
            for d in ("forward", "reverse"):
                hits = sorted(glob.glob(f"{jobs_dir}/{name}/preds/*_{d}_*.tif"))
                if not hits:
                    RESULTS["errors"][f"whole_{name}_{tag}_{d}"] = "no map"
                    continue
                p = tifffile.imread(hits[-1])
                whole[f"{name}__{d}"] = p
                stat[d] = float(p.astype(np.float32).mean() / 255.0)
                Image.fromarray((np.clip((p.astype(np.float32) / 255.0 - 0.25) / 0.5, 0, 1)[::4, ::4] * 255).astype(
                    np.uint8)).save(f"{prev}/{name}__{tag}_{d}_ds4.png")
            shutil.rmtree(f"{jobs_dir}/{name}/preds", ignore_errors=True)
        np.savez_compressed(f"{OUT}/whole_maps_{tag}.npz", **whole)
    except Exception as e:                                            # noqa: BLE001
        RESULTS["errors"][f"whole_maps_{tag}"] = repr(e)
    save()
    log(f"{tag} scored: {len(maps)} maps kept, {len(whole)} whole-surface maps")


# ---------------------------------------------------------------- 7. the day-3 readout (PREREG amendment 1)
def med(xs):
    xs = [x for x in xs if x == x]
    return float(np.median(xs)) if xs else float("nan")


def floor_at(curve, thr):
    """Smallest s whose median planted AUC reaches thr, linear between grid points; None means above 1."""
    ss = sorted(curve)
    if curve[ss[0]] >= thr:
        return ss[0]
    for a, b in zip(ss, ss[1:]):
        if curve[b] >= thr:
            return a + (thr - curve[a]) / (curve[b] - curve[a]) * (b - a)
    return None


J = RESULTS["jobs"]
SCORED = [n for n in J if J[n]["kind"] != "whole"]
complete = {tag: all(("forward" in J[n].get("auc", {}).get(tag, {}) and "reverse" in J[n]["auc"][tag]) for n in SCORED)
            for tag in ck_paths}
RESULTS["complete"] = complete
D1 = DAY1["jobs"]
readout, lines = {}, ["| checkpoint | dir | control (largest reference change) | clean | " +
                      " | ".join(f"{s:g}" for s in STRENGTHS) + " | sham " + " / ".join(f"{s:g}" for s in STRENGTHS) +
                      " | PHerc0139 sham " + " / ".join(f"{s:g}" for s in STRENGTHS) +
                      " | checks | detection floor | clear floor |",
                      "|---|---|---|---|" + "---|" * len(STRENGTHS) + "---|---|---|---|---|"]
for tag in ck_paths:
    if not complete[tag]:
        lines.append(f"| {tag} | INCOMPLETE: some jobs have no score; nothing is read |")
        continue
    primary = DAY1["gates"][f"{tag}/swap"]["primary_direction"]
    moved = max(abs(J[n]["auc"][tag][primary] - D1[n]["auc"][tag][primary]) for n in J if J[n]["kind"] == "reference")
    control = moved <= 0.01
    clean = med([J[n]["auc"][tag][primary] for n in J if J[n]["kind"] == "clean"])
    curve = {0.0: clean}
    curve.update({s_: med([J[n]["auc"][tag][primary] for n in J if J[n]["kind"] == "planted" and J[n]["strength"] == s_])
                  for s_ in STRENGTHS})
    shams = {s_: med([J[n]["auc"][tag][primary] for n in J if J[n]["kind"] == "sham" and J[n]["strength"] == s_])
             for s_ in STRENGTHS}
    sham_iqr = {s_: [float(np.percentile(v_, 25)), float(np.percentile(v_, 75))] for s_, v_ in
                ((s_, [J[n]["auc"][tag][primary] for n in J if J[n]["kind"] == "sham" and J[n]["strength"] == s_])
                 for s_ in STRENGTHS)}
    xshams = {s_: med([J[n]["auc"][tag][primary] for n in J if J[n]["kind"] == "xsham" and J[n]["strength"] == s_])
              for s_ in STRENGTHS}
    xsham_iqr = {s_: [float(np.percentile(v_, 25)), float(np.percentile(v_, 75))] for s_, v_ in
                 ((s_, [J[n]["auc"][tag][primary] for n in J if J[n]["kind"] == "xsham" and J[n]["strength"] == s_])
                  for s_ in STRENGTHS)}
    checks = ((0.40 <= clean <= 0.60) and all(0.40 <= shams[s_] <= 0.60 for s_ in STRENGTHS)
              and all(0.40 <= xshams[s_] <= 0.60 for s_ in STRENGTHS))
    det, clr = (floor_at(curve, 0.70), floor_at(curve, 0.80)) if (control and checks) else (None, None)
    readout[tag] = {"primary_direction": primary, "control_largest_reference_change": moved, "control_ok": control,
                    "curve": curve, "shams": shams, "sham_interquartile": sham_iqr, "xshams": xshams,
                    "xsham_interquartile": xsham_iqr, "checks_ok": checks,
                    "detection_floor": det, "clear_floor": clr, "read": bool(control and checks)}
    fmt = lambda f: "above 1" if f is None else f"{f:.2f}"
    lines.append(f"| {tag} | {primary} | {moved:.4f} ({'ok' if control else 'MOVED: not read'}) | {clean:.3f} | " +
                 " | ".join(f"{curve[s_]:.3f}" for s_ in STRENGTHS) + " | " +
                 " / ".join(f"{shams[s_]:.3f}" for s_ in STRENGTHS) + " | " +
                 " / ".join(f"{xshams[s_]:.3f}" for s_ in STRENGTHS) + f" | {'pass' if checks else 'FAIL'} | " +
                 (f"{fmt(det)} | {fmt(clr)} |" if control and checks else "not read | not read |"))
RESULTS["readout"] = readout
open(f"{OUT}/summary.md", "w").write("\n".join(lines) + "\n")
print("\n".join(lines))
RESULTS["status"] = "done" if all(complete.values()) else "done, incomplete"
RESULTS["finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
save()
log("DONE")
