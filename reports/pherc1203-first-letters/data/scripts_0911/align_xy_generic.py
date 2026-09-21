"""Absolute xy offset between a scroll's sharp (fine) and official (coarse) scans at the heights solved by
align_generic.py (align_<TAG>.json: coarse L0 z at fine z=0, scale). Whole slices anchored at pixel (0,0): the phase
correlation peak IS the offset. Coarse L2 vs fine L4 rescaled onto the coarse grid, 5 heights.
argv: SCROLL COARSE_VOL FINE_VOL TAG. Writes align_<TAG>_xy.json and affine_<TAG>.json (vc_render_tifxyz --affine,
xyz rows: fine_L0 = (coarse_L0 - offset) * scale) and an overlay image."""
import sys, re, json, numpy as np, zarr, fsspec
from scipy import ndimage as ndi
from scipy.ndimage import zoom
from numpy.fft import fft2, ifft2
from PIL import Image
SCROLL, CVOL, FVOL, TAG = sys.argv[1:5]
B = "vesuvius-challenge-open-data"; W0 = "<work-dir>"
UC = float(re.search(r"-(\d+\.\d+)um-", CVOL).group(1)); UF = float(re.search(r"-(\d+\.\d+)um-", FVOL).group(1))
al = json.load(open(f"{W0}/align_{TAG}.json")); Z0L0 = al["coarse_L0_z_at_fine_z0"]; S = al["fine_per_coarse_scale"]
C = zarr.open(fsspec.get_mapper(f"s3://{B}/{SCROLL}/volumes/{CVOL}/2", anon=True), mode="r")
F = zarr.open(fsspec.get_mapper(f"s3://{B}/{SCROLL}/volumes/{FVOL}/4", anon=True), mode="r")
r = (16.0 / S) / 4.0          # fine L4 voxel in coarse L2 voxels (= 4/S)
def band(a):
    a = a.astype(np.float32); m = a > 0; b = ndi.gaussian_filter(a, 1.0) - ndi.gaussian_filter(a, 6.0); b[~m] = 0; return b / max(b[m].std(), 1e-6)
res = []
for frac in (0.1, 0.3, 0.5, 0.7, 0.9):
    zf = int(frac * (F.shape[0] - 1)); zc = int(round(Z0L0 / 4 + zf * r))
    if not 0 <= zc < C.shape[0]: continue
    f = zoom(np.asarray(F[zf]).astype(np.float32), r, order=1); c = np.asarray(C[zc]).astype(np.float32)
    H = max(f.shape[0], c.shape[0]) * 2; W = max(f.shape[1], c.shape[1]) * 2
    A = np.zeros((H, W), np.float32); Fb = np.zeros((H, W), np.float32)
    A[:c.shape[0], :c.shape[1]] = band(c); Fb[:f.shape[0], :f.shape[1]] = band(f)
    cc = np.real(ifft2(fft2(A) * np.conj(fft2(Fb)))); k = np.argmax(cc); dy, dx = np.unravel_index(k, cc.shape)
    dy = dy if dy < H // 2 else dy - H; dx = dx if dx < W // 2 else dx - W
    fsh = np.roll(np.roll(Fb, dy, 0), dx, 1); m = (A != 0) & (fsh != 0)
    ncc = float(np.corrcoef(A[m], fsh[m])[0, 1]) if m.sum() > 1000 else float("nan")
    res.append(dict(frac=frac, fine_L4_z=zf, coarse_L2_z=zc, dy_L2=int(dy), dx_L2=int(dx), ncc=ncc))
    print(f"height {frac:.0%}: fine L4 z {zf} <-> coarse L2 z {zc}: fine (0,0) at coarse L2 (y {dy}, x {dx}), ncc {ncc:.3f}", flush=True)
    if frac == 0.5:
        g = lambda x: np.clip((x - np.percentile(x, 2)) / max(np.percentile(x, 99.5) - np.percentile(x, 2), 1e-6), 0, 1)
        h, w = c.shape; ov = np.zeros((h, w, 3), np.float32); ov[..., 0] = g(A[:h, :w]); ov[..., 1] = g(fsh[:h, :w])
        Image.fromarray((ov * 255).astype(np.uint8)).save(f"{W0}/align_{TAG}_overlay.png")
oy = float(np.median([x["dy_L2"] for x in res])) * 4; ox = float(np.median([x["dx_L2"] for x in res])) * 4
out = dict(per_height=res, transform=dict(description="fine_L0 = (coarse_L0 - offset) * scale, zyx; rotation 0",
           offset_coarse_L0_zyx=[Z0L0, oy, ox], scale=S, precision_um=f"~{UC * 4:.0f} (L2) in xy"))
json.dump(out, open(f"{W0}/align_{TAG}_xy.json", "w"), indent=1)
json.dump({"schema_version": "1.0.0", "note": f"{SCROLL} {UC}um -> {UF}um, solved 11 Sep from cross-section matching",
           "transformation_matrix": [[S, 0, 0, -ox * S], [0, S, 0, -oy * S], [0, 0, S, -Z0L0 * S]]}, open(f"{W0}/affine_{TAG}.json", "w"), indent=1)
print(json.dumps(out["transform"]), flush=True); print("XY_DONE")
