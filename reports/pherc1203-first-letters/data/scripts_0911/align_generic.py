"""Precise alignment (generic; argv: SCROLL COARSE_VOL FINE_VOL I_HINT_L3 TAG) of PHerc1203's 2.403um scan (fine) to its eligible 9.362um scan (coarse).
Known from cross-section images: fine L5 slice 0 ~ coarse L3 slice 992 (74.3 mm), rotation ~0.
Model: per fine height, the fine cross-section is the coarse cross-section at coarse height zc(zf), shifted
in xy and scaled by s (nominal 9.362/2.403). Cross-sections are compared after a band-pass (detail) filter,
which keys on internal structure (cracks, wraps) rather than the outline, so the height match is sharper.
Stage A at ~75 um (coarse L3 vs fine L5), Stage B at ~37 um (coarse L2 vs fine L4) around the Stage A answer.
Writes align1203.json and align1203_check.png."""
import json, numpy as np, zarr, fsspec, time
from scipy import ndimage as ndi
from scipy.ndimage import zoom
from numpy.fft import fft2, ifft2
from PIL import Image
t0 = time.time(); B = "vesuvius-challenge-open-data"
import sys
SCROLL, CVOL, FVOL, IH, TAG = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), sys.argv[5]
CV = f"{SCROLL}/volumes/{CVOL}"; FV = f"{SCROLL}/volumes/{FVOL}"
import re as _re
UC = float(_re.search(r"-(\d+\.\d+)um-", CVOL).group(1)); UF = float(_re.search(r"-(\d+\.\d+)um-", FVOL).group(1))
op = lambda v, l: zarr.open(fsspec.get_mapper(f"s3://{B}/{v}/{l}", anon=True), mode="r")
def band(a):
    a = a.astype(np.float32); m = a > 0; b = ndi.gaussian_filter(a, 1.0) - ndi.gaussian_filter(a, 6.0); b[~m] = 0
    s = b[m].std() if m.any() else 1.0; return b / max(s, 1e-6)
def ncc_shift(a, b):
    H = max(a.shape[0], b.shape[0]); W = max(a.shape[1], b.shape[1]); A = np.zeros((H, W), np.float32); Bp = np.zeros((H, W), np.float32)
    A[:a.shape[0], :a.shape[1]] = a; Bp[:b.shape[0], :b.shape[1]] = b
    cc = np.real(ifft2(fft2(A) * np.conj(fft2(Bp)))); k = np.argmax(cc); dy, dx = np.unravel_index(k, cc.shape)
    dy = dy if dy <= H // 2 else dy - H; dx = dx if dx <= W // 2 else dx - W
    return float(cc.flat[k] / (np.linalg.norm(A) * np.linalg.norm(Bp) + 1e-9)), int(dy), int(dx)
def stage(cl, fl, i_center, i_rad, i_step, fracs, scale_eps=(0.0,), crop=None):
    C, F = op(CV, cl), op(FV, fl); vc, vf = UC * 2**cl, UF * 2**fl
    print(f"stage: coarse L{cl} {C.shape} ({vc:.1f}um) vs fine L{fl} {F.shape} ({vf:.1f}um)", flush=True)
    fsl = {}
    for fr in fracs:
        zf = int(fr * (F.shape[0] - 1)); s = np.asarray(F[zf]).astype(np.float32)
        if crop: cy, cx = s.shape[0] // 2, s.shape[1] // 2; s = s[cy-crop:cy+crop, cx-crop:cx+crop]
        fsl[zf] = s
    results = []
    for eps in scale_eps:
        r = vf / vc * (1 + eps)
        fb = {zf: band(zoom(s, r, order=1)) for zf, s in fsl.items()}
        for i in range(i_center - i_rad, i_center + i_rad + 1, i_step):
            per = []
            for zf, f in fb.items():
                zc = int(round(i + zf * vf / vc))
                if zc < 0 or zc >= C.shape[0]: continue
                c = np.asarray(C[zc]).astype(np.float32)
                if crop:
                    cyc, cxc = c.shape[0] // 2, c.shape[1] // 2; m = int(crop * r * 1.6); c = c[max(0, cyc-m):cyc+m, max(0, cxc-m):cxc+m]
                n, dy, dx = ncc_shift(band(c), f); per.append((zf, n, dy, dx))
            if per: results.append((float(np.mean([p[1] for p in per])), i, eps, per))
    results.sort(key=lambda x: -x[0])
    print(f"  top offsets: " + "; ".join(f"i={r[1]} eps={r[2]:+.3f} ncc={r[0]:.3f}" for r in results[:5]), flush=True)
    print(f"  median of scan {np.median([r[0] for r in results]):.3f}   ({time.time()-t0:.0f}s)", flush=True)
    return results, vc, vf
fr = (0.1, 0.3, 0.5, 0.7, 0.9)
A, vcA, vfA = stage(3, 5, IH, 12, 1, fr)
bestA = A[0]
A2, _, _ = stage(3, 5, bestA[1], 2, 1, fr, scale_eps=(-0.01, -0.005, 0.0, 0.005, 0.01))
bestA2 = A2[0]
Bres, vcB, vfB = stage(2, 4, 2 * bestA2[1], 6, 1, fr, scale_eps=(bestA2[2],), crop=500)
bestB = Bres[0]
per = bestB[3]; zfs = np.array([p[0] for p in per]); dys = np.array([p[2] for p in per]); dxs = np.array([p[3] for p in per])
tilt_y = np.polyfit(zfs, dys, 1)[0] if len(per) > 2 else 0.0; tilt_x = np.polyfit(zfs, dxs, 1)[0] if len(per) > 2 else 0.0
out = dict(
    stageA=dict(level_pair="coarse L3 / fine L5", best_i=bestA[1], ncc=bestA[0], scan_median=float(np.median([r[0] for r in A]))),
    stageA_scale=dict(best_i=bestA2[1], scale_eps=bestA2[2], ncc=bestA2[0]),
    stageB=dict(level_pair="coarse L2 / fine L4", best_i=bestB[1], ncc=bestB[0], scan_median=float(np.median([r[0] for r in Bres])),
                per_height=[dict(fine_L4_z=int(p[0]), ncc=p[1], dy=p[2], dx=p[3]) for p in per],
                xy_drift_px_per_fine_slice=dict(dy=float(tilt_y), dx=float(tilt_x))),
    coarse_L0_z_at_fine_z0=float(bestB[1] * 4), coarse_mm_at_fine_z0=float(bestB[1] * 4 * UC / 1000),
    fine_per_coarse_scale=float(UC / UF * (1 + bestA2[2])),
    note="xy shifts are measured on centre crops at L2/L4 in L2 coarse pixels after rescaling; see per_height")
json.dump(out, open(f"<work-dir>/align_{TAG}.json", "w"), indent=1)
print(json.dumps(out, indent=1)[:1500], flush=True)
# visual check at the final solution
C2, F4 = op(CV, 2), op(FV, 4); zf = int(0.5 * (F4.shape[0] - 1)); zc = int(round(bestB[1] + zf * vfB / vcB))
f = zoom(np.asarray(F4[zf]).astype(np.float32), vfB / vcB * (1 + bestA2[2]), order=1); c = np.asarray(C2[zc]).astype(np.float32)
def g(x): lo, hi = np.percentile(x[x > 0], [1, 99]) if (x > 0).any() else (0, 1); return (np.clip((x - lo) / max(hi - lo, 1), 0, 1) * 255).astype(np.uint8)
h = min(f.shape[0], c.shape[0]); w = min(f.shape[1], c.shape[1])
Image.fromarray(np.hstack([g(f[:h, :w]), np.full((h, 8), 255, np.uint8), g(c[:h, :w])])).resize((1400, int(1400 * h / (2 * w + 8)))).save(f"<work-dir>/align_{TAG}_check.png")
print("ALIGN_DONE", f"({time.time()-t0:.0f}s)", flush=True)
