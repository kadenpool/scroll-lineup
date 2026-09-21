"""How far does our 1203 transform put the sheet off at the patch? Compare the native coarse render (29 layers at
9.362 um, centre 14) with the sharp render through affine_1203.json (109 layers at 2.403 um, centre 54), shrunk to the
coarse grid. Search depth shifts dw (coarse layers) and in-plane shifts; report the best, sub-layer refined, in
coarse and in fine voxels. Writes offset1203.json and offset1203.png."""
import json, glob, numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
from numpy.fft import rfft2, irfft2
Image.MAX_IMAGE_PIXELS = None
import sys
CD, FD, UC, UF, D = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4]), sys.argv[5]; S = UC / UF
cf = sorted(glob.glob(f"{CD}/*.tif")); ff = sorted(glob.glob(f"{FD}/*.tif"))
Cst = np.stack([np.asarray(Image.open(f)).astype(np.float32) for f in cf]); nC = len(cf); cc0 = (nC - 1) / 2
h, w = Cst.shape[1:]
F2 = np.stack([ndi.zoom(np.asarray(Image.open(f)).astype(np.float32), 1 / S, order=1) for f in ff]); nF = len(ff); fc0 = (nF - 1) / 2
print("coarse", Cst.shape, "fine shrunk", F2.shape, flush=True)
H, W = max(h, F2.shape[1]) + 64, max(w, F2.shape[2]) + 64
def band(a):
    m = a > 0; b = ndi.gaussian_filter(a, 1.0) - ndi.gaussian_filter(a, 5.0); b[~m] = 0
    ms = ndi.binary_erosion(m, iterations=6); b[~ms] = 0; return b / (b[ms].std + 1e-6) if ms.any else b
def pad(a):
    o = np.zeros((H, W), np.float32); o[:a.shape[0], :a.shape[1]] = a; return o
def fine_at(pos):   # fine shrunk stack linearly interpolated at fractional layer position
    k0 = int(np.floor(pos)); t = pos - k0
    if k0 < 0 or k0 + 1 >= nF: return None
    return (1 - t) * F2[k0] + t * F2[k0 + 1]
CB = [pad(band(Cst[j])) for j in range(nC)]; CFt = [rfft2(c) for c in CB]; Cn = [np.linalg.norm(c) for c in CB]
res = []
for dw in np.arange(-8.0, 8.01, 0.5):                           # depth shift in coarse layers
    acc = None; nn = 0.0
    for j in range(nC):
        f = fine_at(fc0 + ((j - cc0) + dw) * S)
        if f is None: continue
        fb = pad(band(f)); acc = (CFt[j] * np.conj(rfft2(fb))) if acc is None else acc + CFt[j] * np.conj(rfft2(fb)); nn += Cn[j] * np.linalg.norm(fb)
    cc = irfft2(acc, s=(H, W)); k = int(np.argmax(cc)); dy, dx = np.unravel_index(k, cc.shape)
    dy = dy if dy <= H // 2 else dy - H; dx = dx if dx <= W // 2 else dx - W
    res.append((float(cc.flat[k] / (nn + 1e-9)), float(dw), int(dy), int(dx)))
    print(f"  dw {dw:+5.1f} coarse layers: ncc {res[-1][0]:.3f} at dy {dy} dx {dx}", flush=True)
best = max(res); i = [r[1] for r in res].index(best[1])
if 0 < i < len(res) - 1:
    y0, y1, y2 = res[i - 1][0], res[i][0], res[i + 1][0]; den = y0 - 2 * y1 + y2
    dw_ref = best[1] + (0.5 * 0.5 * (y0 - y2) / den if den != 0 else 0.0)
else: dw_ref = best[1]
out = {"best_ncc": best[0], "dw_coarse_layers": dw_ref, "dw_fine_layers": dw_ref * S, "dw_um": dw_ref * 9.362,
       "inplane_shift_coarse_px": [best[2], best[3]], "inplane_shift_um": [best[2] * 9.362, best[3] * 9.362],
       "curve": [{"dw": r[1], "ncc": r[0], "dy": r[2], "dx": r[3]} for r in res],
       "meaning": "fine layer (54 + dw_fine_layers) sits where the coarse render has the mesh surface (layer 14); "
                  "positive = the sheet sits deeper in the fine stack than the mesh says"}
json.dump(out, open(f"{D}/offset.json", "w"), indent=1)
print(json.dumps({k: v for k, v in out.items if k != "curve"}), flush=True)
def g(x):
    m = x > 0; lo, hi = np.percentile(x[m], [1, 99]) if m.any else (0, 1); return (np.clip((x - lo) / max(hi - lo, 1e-6), 0, 1) * 255).astype(np.uint8)
j = int(round(cc0)); f0 = fine_at(fc0 + 0 * S); fb = fine_at(fc0 + dw_ref * S)
tiles = [g(Cst[j]), g(np.roll(np.roll(f0, best[2], 0), best[3], 1)[:h, :w]), g(np.roll(np.roll(fb, best[2], 0), best[3], 1)[:h, :w])]
labs = ["coarse render, mesh surface (layer 14)", "sharp render at layer 54 (as our transform says)", f"sharp render at layer {54 + dw_ref * S:.0f} (best match)"]
ims = []
for t, l in zip(tiles, labs):
    im = Image.fromarray(t).resize((700, 700)).convert("RGB"); d = ImageDraw.Draw(im); d.rectangle([0, 0, 700, 20], fill=(0, 0, 0)); d.text((5, 4), l, fill=(255, 80, 80))
    ims.append(np.pad(np.asarray(im), ((4, 4), (4, 4), (0, 0)), constant_values=255))
Image.fromarray(np.hstack(ims)).save(f"{D}/offset.png"); print("OFFSET_DONE", flush=True)
