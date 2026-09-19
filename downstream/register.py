"""Stitch a rendered arm, register it to the label grid, and write the labels onto it.

Our arm is the PHerc0139 w016 control mesh rendered from the 2.399 um scan through OUR transform
(affine_0139c_9to2.json) at level 2: 9.596 um per pixel and per layer, 101 layers, --flip-normals, which
is the same recipe as the 9.362 um control in depth/ apart from the volume and the transform.

Steps, each checked before the next:
  1. stitch tiles_lab/t_<y>_<x>/ into ours_lab.zarr, shape (101, 768, 2304), canvas origin (4800, 1728);
  2. register the label grid to it the way the 9.362 um control was registered: a scale grid, an FFT
     shift search on the surface layer against the aligned input's centre slice, then residual shifts
     in six sub-windows, which must be small or the registration is not trusted;
  3. write labels_on_render.npz with V, I, S and valid built exactly as the 9.362 um control built them.

    python ours_arm.py            # arm c: v6_0139c, tiles_lab/ -> ours_lab.zarr, ours_register.json, ...
    python ours_arm.py a          # arm a: v2_0139a, tiles_lab_v2/ -> ours_v2_lab.zarr, ours_v2_register.json, ...
    python ours_arm.py o          # the control: the OFFICIAL transform, same scan, same pipeline -> official_*

A note on what the registration absorbs, so nobody reads more into the result than it can carry:
both arms are registered to the label grid in 2D by image correlation, so an in-plane error in either
transform is taken out before scoring. What the ink model can still see is whether the surface sits at
the right DEPTH, and the quality of the image there. That is the part of a transform the ink model is
sensitive to (depth/README.md), and it is the same treatment for both arms.
"""
import glob, json, os, sys
import numpy as np, tifffile, zarr
from numcodecs import Blosc
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
ARM = sys.argv[1] if len(sys.argv) > 1 else "c"
TAG = {"c": "ours", "a": "ours_v2", "o": "official"}[ARM]
TILES = os.path.join(HERE, {"c": "tiles_lab", "a": "tiles_lab_v2", "o": "tiles_lab_off"}[ARM])
Y0, X0, TILE, NY, NX, DEPTH = 4800, 1728, 384, 2, 6, 101
LAB = np.load(os.path.join(HERE, "labels_w016_crop.npz"))
LY0, LX0 = map(int, LAB["crop_label_px_y0x0"])          # (4608, 1536): label px of the crop origin


def stitch():
    out = np.zeros((DEPTH, NY * TILE, NX * TILE), np.uint8)
    for j in range(NY):
        for i in range(NX):
            d = os.path.join(TILES, f"t_{Y0 + j * TILE}_{X0 + i * TILE}")
            if not os.path.exists(os.path.join(d, ".done")):
                raise SystemExit(f"tile missing or incomplete: {d}")
            for k in range(DEPTH):
                out[k, j * TILE:(j + 1) * TILE, i * TILE:(i + 1) * TILE] = tifffile.imread(os.path.join(d, f"{k:03d}.tif"))
    path = os.path.join(HERE, f"{TAG}_lab.zarr")
    g = zarr.open_group(path, mode="w", zarr_format=2)
    g.attrs.update({"what": {"c": "PHerc0139 w016 control mesh, 2.399 um scan via affine_0139c_9to2.json (v6_0139c), level 2",
                             "a": "PHerc0139 w016 control mesh, 2.403 um scan 20250820105138 via affine_0139_9to2.json (v2_0139a), level 2",
                             "o": "PHerc0139 w016 control mesh, 2.399 um scan via the OFFICIAL transform inverted (affine_0139c_official_9to2.json), level 2"}[ARM],
                    "canvas_origin_yx": [Y0, X0], "um_per_px": 9.596, "um_per_layer": 9.596,
                    "flags": "-g 2 --scale 1 --slice-step 1 --flip-normals --num-slices 101"})
    a = g.create_array("0", shape=out.shape, chunks=(DEPTH, 128, 128), dtype="uint8",
                       compressors=Blosc(cname="zstd", clevel=5, shuffle=Blosc.BITSHUFFLE), fill_value=0,
                       chunk_key_encoding={"name": "v2", "separator": "/"})
    a[:] = out
    back = np.asarray(zarr.open(path, mode="r")["0"][:, :64, :64])
    assert np.array_equal(back, out[:, :64, :64]), "read-back mismatch"
    print(f"stitched {out.shape}, nonzero in layer 50: {(out[50] > 0).mean():.3f}; brightest mean layer "
          f"{int(np.argmax([out[k][out[50] > 0].mean() for k in range(DEPTH)]))}", flush=True)
    return out


def hp(x):                                               # the control's normalisation, unchanged
    m = x > 0; y = x - ndi.gaussian_filter(x, 6); y = ndi.gaussian_filter(y, 1.0)
    s = y[m].std() + 1e-6; y = np.clip(y / s, -3, 3); y[~m] = 0; return y


def warp(A, sy, sx, ty, tx, shape):
    """Sample the label-grid image A at label coords ((y - ty)/sy, (x - tx)/sx) for every render pixel."""
    yy, xx = np.mgrid[0:shape[0], 0:shape[1]].astype(np.float32)
    return ndi.map_coordinates(A, [(yy - ty) / sy, (xx - tx) / sx], order=1, cval=0)


def xcorr(a, b, maxs):                                   # the control's masked NCC, unchanged
    H, W = a.shape
    F = np.fft.rfft2(a) * np.conj(np.fft.rfft2(b)); cc = np.fft.irfft2(F, s=(H, W))
    ma = (a != 0).astype(np.float32); mb = (b != 0).astype(np.float32)
    ov = np.fft.irfft2(np.fft.rfft2(ma) * np.conj(np.fft.rfft2(mb)), s=(H, W)); ncc = cc / np.maximum(ov, 2e3)
    ncc = np.fft.fftshift(ncc); c0y, c0x = H // 2, W // 2
    win = ncc[c0y - maxs:c0y + maxs + 1, c0x - maxs:c0x + maxs + 1]
    iy, ix = np.unravel_index(np.argmax(win), win.shape)
    return iy - maxs, ix - maxs, float(win[iy, ix])


def register(R):
    A = np.asarray(zarr.open(os.path.join(HERE, "aligned_w016.zarr"), mode="r")["0"][10]).astype(np.float32)
    surf = R[50].astype(np.float32)
    Rh = hp(surf)
    # prediction from the geometry alone: our canvas is 19.444 px per mesh grid step, the label grid
    # 20/1.028 = 19.455 (the ctl registration), so canvas ~ label_full * 0.9994
    import re
    log = open(os.path.join(TILES, f"t_{Y0}_{X0}", "render.log")).read()
    render_scale = float(re.search(r"render_scale=([0-9.]+)", log).group(1))
    s0 = (render_scale / 0.05) / (20 / 1.028)            # our px per grid step over the label grid's
    ty0, tx0 = LY0 * s0 - Y0, LX0 * s0 - X0
    print(f"predicted: s {s0:.4f}, ty {ty0:.1f}, tx {tx0:.1f}", flush=True)
    best = None
    for s in np.round(np.arange(0.994, 1.0061, 0.001), 4):
        Aw = hp(warp(A, s, s, ty0, tx0, surf.shape))
        dy, dx, pk = xcorr(Rh, Aw, 60)
        if best is None or pk > best[4]:
            best = (float(s), float(s), ty0 + dy, tx0 + dx, pk)
    s1 = best[0]
    for sy in np.round(np.arange(s1 - 0.002, s1 + 0.0021, 0.001), 4):
        for sx in np.round(np.arange(s1 - 0.002, s1 + 0.0021, 0.001), 4):
            Aw = hp(warp(A, sy, sx, best[2], best[3], surf.shape))
            dy, dx, pk = xcorr(Rh, Aw, 10)
            if pk > best[4]:
                best = (float(sy), float(sx), best[2] + dy, best[3] + dx, pk)
    sy, sx, ty, tx, pk = best
    print(f"BEST sy {sy} sx {sx} ty {ty:.1f} tx {tx:.1f} ncc {pk:.3f}", flush=True)
    Aw = hp(warp(A, sy, sx, ty, tx, surf.shape))
    subs = []
    H, W = surf.shape
    for y0 in (40, H - 40 - 320):
        for x0 in (40, (W - 640) // 2, W - 40 - 640):
            a = Rh[y0:y0 + 320, x0:x0 + 640]; b = Aw[y0:y0 + 320, x0:x0 + 640]
            if (a != 0).mean() < 0.5 or (b != 0).mean() < 0.5:
                print(f"  sub-window ({y0},{x0}) skipped: mostly empty"); continue
            dy, dx, p2 = xcorr(a, b, 20)
            subs.append([y0, x0, int(dy), int(dx), p2])
            print(f"  sub-window ({y0},{x0}) residual shift ({dy},{dx}) ncc {p2:.3f}", flush=True)
    reg = {"sy": sy, "sx": sx, "ty": ty, "tx": tx, "ncc": pk, "subwindows": subs,
           "predicted": {"s": s0, "ty": ty0, "tx": tx0},
           "frame": f"render_px = s * label_crop_px + t, render = {TAG}_lab.zarr (canvas origin 4800, 1728)"}
    json.dump(reg, open(os.path.join(HERE, f"{TAG}_register.json"), "w"), indent=1)
    worst = max((max(abs(s[2]), abs(s[3])) for s in subs), default=99)
    if worst > 2:
        raise SystemExit(f"registration not trusted: a sub-window is off by {worst} px")
    return reg


def labels_on_render(R, reg):
    surf = R[50]; shape = surf.shape
    yy, xx = np.mgrid[0:shape[0], 0:shape[1]].astype(np.float32)
    coords = [(yy - reg["ty"]) / reg["sy"], (xx - reg["tx"]) / reg["sx"]]
    tr = lambda m: ndi.map_coordinates((m > 0).astype(np.float32), coords, order=0, cval=0.0) > 0.5
    V, I, S = tr(LAB["validation_mask"]), tr(LAB["inklabels"]), tr(LAB["supervision_mask"])
    valid = ndi.binary_erosion(surf > 0, iterations=4)
    np.savez_compressed(os.path.join(HERE, f"{TAG}_labels_on_render.npz"), V=V, I=I, S=S, valid=valid)
    n_lab = int((LAB["validation_mask"] > 0).sum())
    print(f"labels on render: validation px {int((V & valid).sum())} of {n_lab} in the label crop "
          f"({(V & valid).sum() / n_lab:.3f}), ink in validation {int((V & I & valid).sum())}", flush=True)


if __name__ == "__main__":
    R = stitch()
    reg = register(R)
    labels_on_render(R, reg)
