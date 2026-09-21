"""Pick windows for the next PHerc1203 2 um ink check. For each of the 22 raw segments (coarse renders already in
p1203/sv, 28 layers, 20 px per mesh cell, no crop), score every 40x40-cell window lying inside the sharp scan's band
by how much of it looks like face-on papyrus (structure-tensor coherence < 0.45 on the surface layers, as in
p0343/mask343.py; streaks/swirls = the mesh cutting across sheets). Keep the best non-overlapping windows, at most 2
per segment. Writes p1203_sel/windows.json, one masked tifxyz per window, and a montage to check by eye."""
import os, json, glob, numpy as np, zarr
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
Image.MAX_IMAGE_PIXELS = None
R = "<run-dir>"; OUT = f"{R}/p1203_sel"; os.makedirs(OUT, exist_ok=True)
ZLO, ZHI = 7936 + 40, 11829 - 40; K = 40; P = 20; C_MAX = 0.45
cands = []; vis = {}
for zp in sorted(glob.glob(f"{R}/p1203/sv/*.zarr")):
    sid = os.path.basename(zp)[:-5]; t = f"{R}/p1203/tif/{sid}"
    X, Y, Z = (np.asarray(Image.open(f"{t}/{c}.tif")).astype(np.float32) for c in "xyz")
    band = (X != -1) & (Y != -1) & (Z != -1) & (Z > ZLO) & (Z < ZHI)
    if band.sum() < K * K * 0.9: continue
    a = zarr.open(f"{zp}/0", mode="r"); n = a.shape[0]
    sl = np.asarray(a[n // 2 - 1:n // 2 + 1]).astype(np.float32).mean(0)
    gh, gw = X.shape
    sl = sl[:gh * P, :gw * P]
    if sl.shape != (gh * P, gw * P):
        pad = np.zeros((gh * P, gw * P), np.float32); pad[:sl.shape[0], :sl.shape[1]] = sl; sl = pad
    data = sl > 0
    g = ndi.gaussian_filter(sl, 1.5); gx, gy = ndi.sobel(g, 1), ndi.sobel(g, 0)
    Jxx, Jyy, Jxy = (ndi.gaussian_filter(v, 16) for v in (gx * gx, gy * gy, gx * gy))
    coh = np.sqrt((Jxx - Jyy) ** 2 + 4 * Jxy ** 2) / (Jxx + Jyy + 1e-6)
    cc = coh.reshape(gh, P, gw, P).mean((1, 3)); cd = data.reshape(gh, P, gw, P).mean((1, 3)); ci = sl.reshape(gh, P, gw, P).mean((1, 3))
    lvl = np.percentile(ci[band & (cd > 0.9)], 60) if (band & (cd > 0.9)).any() else 0
    good = band & (cd > 0.9) & (cc < C_MAX) & (ci > 0.55 * lvl)
    ok = band & (cd > 0.9)
    fg = ndi.uniform_filter(good.astype(np.float32), K, mode="constant"); fo = ndi.uniform_filter(ok.astype(np.float32), K, mode="constant")
    for r in range(K // 2, gh - K // 2 + 1, 5):
        for c in range(K // 2, gw - K // 2 + 1, 5):
            if fo[r, c] >= 0.9: cands.append((float(fg[r, c]), sid, r - K // 2, c - K // 2))
    vis[sid] = sl
    print(f"{sid}: band cells {int(band.sum())}, good-papyrus share in band {good.sum() / max(1, ok.sum()):.2f}", flush=True)
cands.sort(reverse=True); pick = []; per = {}
for s, sid, r0, c0 in cands:
    if per.get(sid, 0) >= 2: continue
    if any(p[1] == sid and abs(p[2] - r0) < K and abs(p[3] - c0) < K for p in pick): continue
    pick.append((s, sid, r0, c0)); per[sid] = per.get(sid, 0) + 1
    if len(pick) == 8: break
wins = []; tiles = []
for s, sid, r0, c0 in pick:
    t = f"{R}/p1203/tif/{sid}"; X, Y, Z = (np.asarray(Image.open(f"{t}/{c}.tif")).astype(np.float32) for c in "xyz")
    win = np.zeros_like(X, bool); win[r0:r0 + K, c0:c0 + K] = True
    keep = win & (X != -1) & (Y != -1) & (Z != -1) & (Z > ZLO) & (Z < ZHI)
    name = f"{sid}_r{r0}_c{c0}"; d = f"{OUT}/{name}"; os.makedirs(d, exist_ok=True)
    for arr, cn in ((X, "x"), (Y, "y"), (Z, "z")):
        v = arr.copy(); v[~keep] = -1; Image.fromarray(v).save(f"{d}/{cn}.tif")
    meta = json.load(open(f"{t}/meta.json")); meta.pop("bbox", None); json.dump(meta, open(f"{d}/meta.json", "w"), indent=1)
    zc = float(np.median(Z[keep])); wins.append({"name": name, "segment": sid, "rows": [r0, r0 + K], "cols": [c0, c0 + K],
                 "papyrus_share": s, "cells": int(keep.sum()), "median_coarse_z": zc, "mm": round(zc * 9.362 / 1000, 1)})
    crop = vis[sid][r0 * P:(r0 + K) * P, c0 * P:(c0 + K) * P]; m = crop > 0
    lo, hi = np.percentile(crop[m], [1, 99]) if m.any() else (0, 1)
    im = Image.fromarray((np.clip((crop - lo) / max(hi - lo, 1), 0, 1) * 255).astype(np.uint8)).resize((400, 400)).convert("RGB")
    ImageDraw.Draw(im).text((5, 5), f"{sid[-9:]} r{r0} c{c0} papyrus {s:.2f}", fill=(255, 60, 60)); tiles.append(np.asarray(im))
    print(f"PICK {name}: papyrus share {s:.2f}, {int(keep.sum())} cells, z {zc:.0f} ({zc * 9.362 / 1000:.1f} mm)", flush=True)
json.dump(wins, open(f"{OUT}/windows.json", "w"), indent=1)
while len(tiles) % 4: tiles.append(np.full((400, 400, 3), 255, np.uint8))
rows = [np.hstack([np.pad(t, ((3, 3), (3, 3), (0, 0)), constant_values=255) for t in tiles[i:i + 4]]) for i in range(0, len(tiles), 4)]
Image.fromarray(np.vstack(rows)).save(f"{OUT}/montage.png"); print("SEL_DONE", len(wins), flush=True)
