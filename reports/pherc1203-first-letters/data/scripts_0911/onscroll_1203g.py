"""Are the grown new-1203 surfaces on the scroll? For each surface: share of its points whose 128^3 chunk exists in the
ELIGIBLE masked volume (level 0; missing chunk = all zero = outside the mask), plus a picture: level-3 cross-section at
z ~ 11000 with every surface's points (within +-150 z) drawn on it. Writes p1203g/onscroll.json + onscroll.png."""
import glob, json, numpy as np, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageDraw
H = "https://vesuvius-challenge-open-data.s3.amazonaws.com/PHerc1203/volumes/20250820131727-9.362um-1.2m-113keV-masked.zarr/"
def exists(k, lvl=0):
    try: urllib.request.urlopen(urllib.request.Request(f"{H}{lvl}/{k}", method="HEAD"), timeout=60); return True
    except urllib.error.HTTPError: return False
import os
res = json.load(open("p1203g/onscroll.json")) if os.path.exists("p1203g/onscroll.json") else {}; cache = {}
for d in sorted(glob.glob("p1203g/grown/*/")):
    sid = d.rstrip("/").split("/")[-1]
    if sid in res: continue
    X, Y, Z = (np.asarray(Image.open(f"{d}{c}.tif")).astype(np.float32) for c in "xyz"); m = X != -1
    keys = {f"{int(z)//128}/{int(y)//128}/{int(x)//128}" for z, y, x in zip(Z[m][::7], Y[m][::7], X[m][::7])}
    todo = [k for k in keys if k not in cache]
    with ThreadPoolExecutor(32) as ex:
        for k, v in zip(todo, ex.map(exists, todo)): cache[k] = v
    pk = [f"{int(z)//128}/{int(y)//128}/{int(x)//128}" for z, y, x in zip(Z[m][::7], Y[m][::7], X[m][::7])]
    share = float(np.mean([cache[k] for k in pk]))
    res[sid] = {"points": int(m.sum), "share_on_stored_chunks": share, "z": [float(Z[m].min), float(Z[m].max)],
                "y": [float(Y[m].min), float(Y[m].max)], "x": [float(X[m].min), float(X[m].max)]}
    print(sid, res[sid], flush=True)
json.dump(res, open("p1203g/onscroll.json", "w"), indent=1)
# level-3 slice at z 11000 (raw uncompressed 128^3 chunks)
L = 3; zs = 11000 // 8; zc, zo = zs // 128, zs % 128; n = (6844 // 8 + 127) // 128
img = np.zeros((n * 128, n * 128), np.uint8)
def get(yx):
    y, x = yx
    try: return yx, np.frombuffer(urllib.request.urlopen(f"{H}{L}/{zc}/{y}/{x}", timeout=60).read, np.uint8).reshape(128, 128, 128)[zo]
    except urllib.error.HTTPError: return yx, None
with ThreadPoolExecutor(16) as ex:
    for (y, x), a in ex.map(get, [(y, x) for y in range(n) for x in range(n)]):
        if a is not None: img[y * 128:(y + 1) * 128, x * 128:(x + 1) * 128] = a
im = Image.fromarray(img).convert("RGB"); dr = ImageDraw.Draw(im)
for i, d in enumerate(f"p1203g/grown/{k}/" for k in sorted(res)):   # only surfaces checked above (growth continues meanwhile)
    X, Y, Z = (np.asarray(Image.open(f"{d}{c}.tif")).astype(np.float32) for c in "xyz"); m = (X != -1) & (abs(Z - 11000) < 150)
    col = (255, 60, 60) if res[d.rstrip("/").split("/")[-1]]["share_on_stored_chunks"] < 0.5 else (60, 255, 60)
    for y, x in zip(Y[m][::5] / 8, X[m][::5] / 8): dr.point((x, y), fill=col)
im.save("p1203g/onscroll.png"); print("ONSCROLL_DONE", flush=True)
