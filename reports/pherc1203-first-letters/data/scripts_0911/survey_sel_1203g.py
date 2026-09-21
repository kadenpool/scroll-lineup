"""1203 NEW-SURFACE (94-111 mm) survey selection: for each grown surface (p1203g/grown), a quick 3-layer coarse render from the ELIGIBLE scan,
face-on papyrus score per 40x40-cell window inside the sharp band (structure-tensor coherence < 0.45, as sel1203.py),
best 3 non-overlapping windows per surface. Writes p1203g_survey/<name>/ tifxyz + windows.json (batches of 8)."""
import os, json, glob, subprocess, numpy as np
from PIL import Image
from scipy import ndimage as ndi
R = "<run-dir>"; OUT = f"{R}/p1203g_survey"; os.makedirs(OUT, exist_ok=True)
H = "https://vesuvius-challenge-open-data.s3.amazonaws.com/"; C = "PHerc1203/volumes/20250820131727-9.362um-1.2m-113keV-masked.zarr/"
ZLO, ZHI = 7936 + 40, 11829 - 40; K = 40; P = 20
done = {w["name"] for w in json.load(open(f"{OUT}/windows.json"))} if os.path.exists(f"{OUT}/windows.json") else set
wins = json.load(open(f"{OUT}/windows.json")) if done else []
for d in sorted(glob.glob(f"{R}/p1203g/grown/*/")):
    sid = d.rstrip("/").split("/")[-1]
    if any(w["segment"] == sid for w in wins): continue
    try: X, Y, Z = (np.asarray(Image.open(f"{d}{c}.tif")).astype(np.float32) for c in "xyz")
    except Exception as e: print("!!! SKIP (unreadable, maybe still being written):", sid, e, flush=True); continue
    band = (X != -1) & (Z > ZLO) & (Z < ZHI)
    if band.sum < 1200: continue
    rd = f"{OUT}/_coarse_{sid}"
    fl = sorted(glob.glob(f"{rd}/*.tif"))
    if not (len(fl) == 3 and all(os.path.getsize(f) > 1024 for f in fl)):        # reuse a good earlier render, else render
        subprocess.run(["rm", "-rf", rd]); os.makedirs(rd)
        subprocess.run([f"{R}/villa-src/volume-cartographer/build/bin/vc_render_tifxyz", "--volume", H + C, "--remote-url", H + C, "-s", d, "--scale", "1", "-g", "0",
                        "--num-slices", "3", "--slice-step", "1", "--tif-output", rd, "--timeout", "30", "--cache-gb", "4"], capture_output=True)
        fl = sorted(glob.glob(f"{rd}/*.tif"))
    if not fl: print("!!! SKIP", sid, "coarse render failed (no files)", flush=True); continue
    try: sl = np.asarray(Image.open(fl[len(fl) // 2])).astype(np.float32)
    except Exception as e: print("!!! SKIP", sid, "coarse render unreadable:", [os.path.getsize(f) for f in fl], "bytes;", e, flush=True); continue
    gh, gw = X.shape
    pad = np.zeros((gh * P, gw * P), np.float32); pad[:min(sl.shape[0], gh * P), :min(sl.shape[1], gw * P)] = sl[:gh * P, :gw * P]; sl = pad
    g = ndi.gaussian_filter(sl, 1.5); gx, gy = ndi.sobel(g, 1), ndi.sobel(g, 0)
    Jxx, Jyy, Jxy = (ndi.gaussian_filter(v, 16) for v in (gx * gx, gy * gy, gx * gy))
    coh = np.sqrt((Jxx - Jyy) ** 2 + 4 * Jxy ** 2) / (Jxx + Jyy + 1e-6)
    cc = coh.reshape(gh, P, gw, P).mean((1, 3)); cd = (sl > 0).reshape(gh, P, gw, P).mean((1, 3))
    good = band & (cd > 0.9) & (cc < 0.45); ok = band & (cd > 0.9)
    fg = ndi.uniform_filter(good.astype(np.float32), K, mode="constant"); fo = ndi.uniform_filter(ok.astype(np.float32), K, mode="constant")
    cands = sorted(((float(fg[r, c]), r - K // 2, c - K // 2) for r in range(K // 2, gh - K // 2 + 1, 5) for c in range(K // 2, gw - K // 2 + 1, 5) if fo[r, c] >= 0.75), reverse=True)
    picked = []
    for s, r0, c0 in cands:
        if any(abs(r0 - a) < K and abs(c0 - b) < K for _, a, b in picked): continue
        picked.append((s, r0, c0))
        if len(picked) == 3: break
    for s, r0, c0 in picked:
        keep = np.zeros_like(band); keep[r0:r0 + K, c0:c0 + K] = True; keep &= band
        name = f"{sid}_r{r0}_c{c0}"; wd = f"{OUT}/{name}"; os.makedirs(wd, exist_ok=True)
        for arr, cn in ((X, "x"), (Y, "y"), (Z, "z")):
            v = arr.copy; v[~keep] = -1; Image.fromarray(v).save(f"{wd}/{cn}.tif")
        meta = json.load(open(f"{d}meta.json")); meta.pop("bbox", None); json.dump(meta, open(f"{wd}/meta.json", "w"), indent=1)
        wins.append({"name": name, "segment": sid, "rows": [r0, r0 + K], "cols": [c0, c0 + K], "cells": int(keep.sum), "papyrus_share": s,
                     "median_coarse_z": float(np.median(Z[keep])), "batch": len(wins) // 8})
    print(sid, "band cells", int(band.sum), "picked", [(round(s, 2), r, c) for s, r, c in picked], flush=True)
    json.dump(wins, open(f"{OUT}/windows.json", "w"), indent=1)                    # save after every surface (a crash loses one, not all)
json.dump(wins, open(f"{OUT}/windows.json", "w"), indent=1); print("WINDOWS", len(wins))
