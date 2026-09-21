"""Full survey of PHerc1203's overlap zone: tile every raw segment's in-band cells into 40x40-cell windows (stride 40),
keep windows with >= 50% of cells in the sharp band, skip the 8 windows already checked. Writes one masked tifxyz per
window under p1203_survey/ and p1203_survey/windows.json (batches of 8)."""
import os, json, glob, numpy as np
from PIL import Image
R = "<run-dir>"; OUT = f"{R}/p1203_survey"; os.makedirs(OUT, exist_ok=True)
ZLO, ZHI = 7936 + 40, 11829 - 40; K = 40
done = [(w["segment"], w["rows"][0], w["cols"][0]) for w in json.load(open(f"{R}/p1203_sel/windows.json"))]
wins = []
for t in sorted(glob.glob(f"{R}/p1203/tif/*")):
    sid = os.path.basename(t); X, Y, Z = (np.asarray(Image.open(f"{t}/{c}.tif")).astype(np.float32) for c in "xyz")
    band = (X != -1) & (Y != -1) & (Z != -1) & (Z > ZLO) & (Z < ZHI)
    if band.sum() < 800: continue
    rr, cc = np.nonzero(band); r_lo, c_lo = rr.min(), cc.min()
    for r0 in range(r_lo, rr.max() + 1, K):
        for c0 in range(c_lo, cc.max() + 1, K):
            keep = np.zeros_like(band); keep[r0:r0 + K, c0:c0 + K] = True; keep &= band
            n = int(keep.sum())
            if n < 800: continue
            if any(s == sid and abs(r - r0) < K // 2 and abs(c - c0) < K // 2 for s, r, c in done): continue
            name = f"{sid}_s_r{r0}_c{c0}"; d = f"{OUT}/{name}"; os.makedirs(d, exist_ok=True)
            for arr, cn in ((X, "x"), (Y, "y"), (Z, "z")):
                v = arr.copy(); v[~keep] = -1; Image.fromarray(v).save(f"{d}/{cn}.tif")
            meta = json.load(open(f"{t}/meta.json")); meta.pop("bbox", None); json.dump(meta, open(f"{d}/meta.json", "w"), indent=1)
            wins.append({"name": name, "segment": sid, "rows": [int(r0), int(r0 + K)], "cols": [int(c0), int(c0 + K)], "cells": n,
                         "median_coarse_z": float(np.median(Z[keep])), "batch": len(wins) // 8})
json.dump(wins, open(f"{OUT}/windows.json", "w"), indent=1)
from collections import Counter
print(len(wins), "windows in", len({w['segment'] for w in wins}), "segments; batches:", max(w["batch"] for w in wins) + 1, "; per segment:", dict(Counter(w["segment"][-9:] for w in wins)))
