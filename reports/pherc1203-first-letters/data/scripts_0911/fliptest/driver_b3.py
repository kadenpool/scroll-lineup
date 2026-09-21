# JOB B3 (12 Sep): window [23,85) (flummoxjr's exact reproduction) on the same 12 windows as jobs B and B2. Selection code and seed unchanged.
# (Original job B header follows.) FLIP-TEST CALIBRATION (job B, 11 Sep): does real ink disappear when the layer order is reversed, and does the model's
# false ink not? On the PUBLISHED 109-layer surface volumes of PHerc0139 (known text), 2048 px windows: 8 text windows
# (published ink 10-60%) and 4 blank ones (published ink < 0.5%) over 3 segments. Each window: centred 24-85 as stored
# and the same window reversed. Prints ink share both ways, their ratio, and the match with the published prediction.
import os, subprocess, json, time, io, glob, numpy as np
t0 = time.time()
NPV = __import__("numpy").__version__
subprocess.run(f"pip install -q 'zarr<3' fsspec s3fs tifffile imagecodecs 'numpy=={NPV}'", shell=True)
assert __import__("numpy").__version__ == NPV
import fsspec, zarr, tifffile
fs = fsspec.filesystem("s3", anon=True); B = "vesuvius-challenge-open-data"; W = 2048; rng = np.random.default_rng(11)
SEGS = ["20250108000000-w025_2025010863", "20250108000001-w026_2025010854", "20250108000002-w027_2025010845"]
wins = {}
for si, s in enumerate(SEGS):
    base = f"{B}/PHerc0139/segments/{s}"
    pn = [f for f in fs.ls(base + "/ink-detection", detail=False) if f.endswith(".tif") and "78keV" in f and "new_canon" in f][0]
    sv = [f for f in fs.ls(base + "/surface-volumes", detail=False) if "2.399um" in f and "78keV" in f and f.endswith(".zarr")][0]
    P = tifffile.imread(io.BytesIO(fs.cat(pn))); Z = zarr.open(fsspec.get_mapper(f"s3://{sv}/0", anon=True), mode="r")
    print(s[:24], "prediction", P.shape, "volume", Z.shape, flush=True)
    text, blank = [], []
    for _ in range(6000):
        y, x = int(rng.integers(0, P.shape[0] - W)), int(rng.integers(0, P.shape[1] - W)); p = P[y:y + W:8, x:x + W:8]
        if (p > 5).mean() < 0.99: continue
        fr = (p > 127).mean()
        if 0.10 <= fr <= 0.60 and len(text) < (3 if si < 2 else 2): text.append((y, x, fr))
        elif fr < 0.005 and len(blank) < (2 if si < 2 else 0): blank.append((y, x, fr))
        if len(text) >= (3 if si < 2 else 2) and len(blank) >= (2 if si < 2 else 0): break
    for kind, lst in (("text", text), ("blank", blank)):
        for y, x, fr in lst:
            name = f"{kind}_{s[15:19]}_y{y}_x{x}"; d = f"/tmp/{name}"; os.makedirs(d, exist_ok=True)
            vol = np.asarray(Z[:, y:y + W, x:x + W])
            for i in range(vol.shape[0]): tifffile.imwrite(f"{d}/{i:03d}.tif", vol[i])
            wins[name] = {"y": y, "x": x, "pub": P[y:y + W, x:x + W].copy(), "layers": vol.shape[0]}
            print("fetched", name, "published ink %.1f%%" % (100 * fr), f"[{time.time() - t0:.0f}s]", flush=True)
VARS = {"w2385": {"CANON_START_LAYER": "23", "CANON_END_LAYER": "85"}}   # job B3: flummoxjr's exact window [23,85) on the SAME 12 windows   # job B2: the README window on the SAME 12 windows (same seed, same selection code)
jobs = [(n, v) for n in wins for v in VARS]; res = {}
from PIL import Image
def launch(n, v, gpu, extra):
    out = f"/kaggle/working/{n}/{v}"; os.makedirs(out, exist_ok=True)
    env = dict(os.environ, CANON_LAYERS_DIR=f"/tmp/{n}", CANON_OUT_DIR=out, CUDA_VISIBLE_DEVICES=str(gpu), **VARS[v], **extra)
    return subprocess.Popen(["python", "-u", "/kaggle/working/run_canon.py"], env=env, stdout=open(f"{out}/run.log", "w"), stderr=subprocess.STDOUT), out
def collect(n, v, out, rc):
    pw = wins[n]["pub"].astype(np.float32) / 255
    try:
        o = np.asarray(Image.open(f"{out}/canon_pred_asinput.png")).astype(np.float32) / 255; h, w = min(o.shape[0], W), min(o.shape[1], W)
        res.setdefault(n, {})[v] = {"exit": rc, "r": float(np.corrcoef(o[:h, :w].ravel(), pw[:h, :w].ravel())[0, 1]), "ink": float((o > 0.5).mean()), "pub": float((pw > 0.5).mean())}
    except Exception as e: res.setdefault(n, {})[v] = {"exit": rc, "error": repr(e)}
    print(n, v, res[n][v], f"[{time.time() - t0:.0f}s]", flush=True); json.dump(res, open("/kaggle/working/w2385_summary.json", "w"), indent=1)
n, v = jobs[0]; p, out = launch(n, v, 0, {}); collect(n, v, out, p.wait())
ck = sorted(glob.glob("/tmp/canon_models/**/*.ckpt", recursive=True)); extra = {"CANON_CKPT_PATH": ck[0]} if ck else {}
pending = jobs[1:]; running = {}
while pending or running:
    for g in (0, 1):
        if g not in running and pending:
            n, v = pending.pop(0); p, out = launch(n, v, g, extra); running[g] = (p, n, v, out)
    time.sleep(5)
    for g, (p, n, v, out) in list(running.items()):
        if p.poll() is not None: collect(n, v, out, p.returncode); del running[g]
print("ALL_DONE", flush=True)
for n in sorted(res):
    f = res[n].get("w2385", {})
    if "ink" in f: print(f"{n:34s} published {100 * f['pub']:5.1f}% | window [23,85): {100 * f['ink']:5.1f}% (match {f['r']:.2f})")
