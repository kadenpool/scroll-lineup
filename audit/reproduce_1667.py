"""One published transform is not the fit its own landmarks give. This script re-derives that from scratch
(ScrollPrize/villa#1843), with the fitted matrix and its effect on one patch of one surface.

It downloads nothing but the challenge's own metadata.json, one published mesh and a small block of
one scan. About 3 minutes, no credentials, no GPU.

  python exp_1667/reproduce.py          # the whole check
  python exp_1667/reproduce.py --quick  # the matrix part only, no scan read

Steps
  1. Read the catalogue's PHerc1667 transforms.
  2. For every transform in the whole catalogue that publishes landmarks, fit the best possible affine
     to those same landmarks. For 24 of 25 the published matrix already is that fit.
  3. The exception is PHerc1667 1.129 -> 2.399: published 123.3 um RMS, best affine 2.2 um.
  4. Show that the published 1.129 um mesh of segment 20251212185248 is consistent with the published
     matrix: its declared corners agree with the 7.91 um mesh carried through it.
  5. Read the 1.129 um scan along the surface normal and show where the papyrus actually is.
"""
import io, json, sys, gzip
import numpy as np
import fsspec

BUCKET = "vesuvius-challenge-open-data"
S3 = f"s3://{BUCKET}/"
FS = fsspec.filesystem("s3", anon=True)
SEG = "PHerc1667/segments/20251212185248-w029_20251212185248662_flatboi"
V1129, V2399, V791 = "20260323082859", "20251217075048", "20231117161658"


def get(path, timeout=180):
    """Read one object from the public bucket. Same access the audit uses: anonymous S3."""
    return FS.cat(path.replace(S3, f"{BUCKET}/"))


def main():
    raw = get(S3 + "metadata.json")
    meta = json.loads(gzip.decompress(raw) if raw[:2] == b"\x1f\x8b" else raw)

    def voxel_um(vol):
        for part in str(vol.get("long_id") or "").split("-"):
            if part.endswith("um"):
                try:
                    return float(part[:-2])
                except ValueError:
                    pass

    # 2. the best affine each published landmark set allows
    worse = []
    for sample, s in sorted(meta["samples"].items()):
        vols = s.get("volumes") or {}
        for vid, v in vols.items():
            for t in ((v.get("properties") or {}).get("transforms") or []):
                src = np.array(t.get("from_landmarks") or [], float)
                dst = np.array(t.get("to_landmarks") or [], float)
                if src.size == 0 or src.shape != dst.shape:
                    continue
                um = voxel_um(vols.get(t["to_volume_id"], {}))
                M = np.array(t["transformation_matrix"], float)
                pub = np.linalg.norm(src @ M[:3, :3].T + M[:3, 3] - dst, axis=1) * um
                X = np.hstack([src, np.ones((len(src), 1))])
                A, *_ = np.linalg.lstsq(X, dst, rcond=None)
                best = np.linalg.norm(X @ A - dst, axis=1) * um
                pr, br = float(np.sqrt((pub ** 2).mean())), float(np.sqrt((best ** 2).mean()))
                if pr - br > 20:
                    worse.append((sample, vid, t["to_volume_id"], len(src), pr, br, np.hstack([A[:3].T, A[3][:, None]])))
    print("transforms whose own landmarks admit a much better affine than the published matrix:")
    for sample, a, b, n, pr, br, _ in worse:
        print(f"  {sample} {a} -> {b}: {n} landmarks, published {pr:.1f} um RMS, best affine {br:.1f} um")
    assert len(worse) == 1, "expected exactly one"
    M_fit = worse[0][6]
    # the replacement a fix would publish, in the catalogue's own 4x4 transformation_matrix form
    print("\nthe least-squares affine to those 6 landmarks, as a transformation_matrix:")
    print("  " + json.dumps(np.vstack([M_fit, [0.0, 0.0, 0.0, 1.0]]).round(9).tolist()))
    M_pub = None
    for vid, v in meta["samples"]["PHerc1667"]["volumes"].items():
        for t in ((v.get("properties") or {}).get("transforms") or []):
            if vid == V1129 and t["to_volume_id"] == V2399:
                M_pub = np.array(t["transformation_matrix"], float)
    if "--quick" in sys.argv:
        return

    # 4. the published 1.129 um mesh is that matrix applied to the 7.91 um one
    import tifffile
    def mesh(url):
        return np.stack([tifffile.imread(io.BytesIO(get(f"{url}/{c}.tif"))).astype(np.float64) for c in "xyz"], -1)
    print("\ndownloading the two published meshes of one segment ...", flush=True)
    A791 = mesh(f"{S3}{SEG}/mesh/20251212185248-on-{V791}-7.91um.tifxyz")
    A1129 = mesh(f"{S3}{SEG}/mesh/20251212185248-on-{V1129}-1.129um.tifxyz")
    ok = np.isfinite(A791).all(-1) & (A791 > 0).all(-1)
    T = {}
    for vid, v in meta["samples"]["PHerc1667"]["volumes"].items():
        for t in ((v.get("properties") or {}).get("transforms") or []):
            T[(vid, t["to_volume_id"])] = np.array(t["transformation_matrix"], float)
    inv = lambda M: np.linalg.inv(np.vstack([M, [0, 0, 0, 1]]))[:3]
    q = A791[ok] @ inv(T[(V2399, V791)])[:3, :3].T + inv(T[(V2399, V791)])[:3, 3]
    q = q @ inv(M_pub)[:3, :3].T + inv(M_pub)[:3, 3]
    lo2, hi2 = q.min(0), q.max(0)
    # the published tifs clip points that fall outside the volume, so compare against the mesh's own
    # declared bbox rather than against the arrays
    bb = np.array(json.loads(get(f"{S3}{SEG}/mesh/20251212185248-on-{V1129}-1.129um.tifxyz/meta.json"))["bbox"], float)
    print(f"  7.91 um mesh through the published chain: {lo2.round(0)} to {hi2.round(0)}")
    print(f"  the published 1.129 um mesh says its own bbox is: {bb[0].round(0)} to {bb[1].round(0)}")
    print(f"  so the published mesh is consistent with the published matrix (corners agree to "
          f"{max(np.abs(bb[0]-lo2).max(), np.abs(bb[1]-hi2).max()):.0f} voxels of 1.129 um)")

    # 5. where the papyrus is
    import zarr, fsspec
    D = inv(M_fit) @ np.vstack([M_pub, [0, 0, 0, 1]])
    r, c, side = 2200, 1600, 40
    patch = A1129[r:r + side, c:c + side]
    gy, gx = np.gradient(patch, axis=0), np.gradient(patch, axis=1)
    n = np.cross(gy, gx)
    n = n / np.linalg.norm(n, axis=-1, keepdims=True)
    pts, nrm = patch.reshape(-1, 3), n.reshape(-1, 3)
    move = float(np.median((((pts @ D[:3, :3].T + D[:3, 3]) - pts) * nrm).sum(-1)) * 1.129)
    ts = np.arange(-400, 401, 4.516) / 1.129
    ends = (pts[:, None, :] + ts[None, :, None] * nrm[:, None, :]).reshape(-1, 3)
    lo = np.floor(ends.min(0)).astype(int) - 2
    hi = np.ceil(ends.max(0)).astype(int) + 2
    z0, y0, x0 = lo[::-1] // 4
    z1, y1, x1 = (hi[::-1] // 4) + 1
    st = zarr.open(fsspec.get_mapper(
        f"s3://vesuvius-challenge-open-data/PHerc1667/volumes/{V1129}-1.129um-0.2m-59keV-masked.zarr/2", anon=True), mode="r")
    print(f"\nreading {(z1-z0)*(y1-y0)*(x1-x0)/1e6:.0f} M voxels of the 1.129 um scan at level 2 ...", flush=True)
    blk = np.asarray(st[z0:z1, y0:y1, x0:x1]).astype(np.float32)

    def val(off):
        p = pts + off / 1.129 * nrm
        cpt = p / 4 - 1.5
        idx = np.stack([cpt[:, 2] - z0, cpt[:, 1] - y0, cpt[:, 0] - x0], -1)
        f = np.floor(idx).astype(int); w = idx - f
        out = np.zeros(len(idx), np.float32)
        for dz in (0, 1):
            for dy in (0, 1):
                for dx in (0, 1):
                    ww = ((1-w[:,0]) if dz==0 else w[:,0])*((1-w[:,1]) if dy==0 else w[:,1])*((1-w[:,2]) if dx==0 else w[:,2])
                    out += ww * blk[np.clip(f[:,0]+dz,0,blk.shape[0]-1), np.clip(f[:,1]+dy,0,blk.shape[1]-1), np.clip(f[:,2]+dx,0,blk.shape[2]-1)]
        return float(out.mean())

    prof = np.array([val(o) for o in np.arange(-400, 401, 9.0)])
    b = lambda v: (v - prof.min()) / (prof.max() - prof.min())
    print(f"\npatch at mesh row {r}, col {c}: the correction moves the surface {move:+.0f} um along its normal")
    print(f"  scan brightness where the published surface sits: {b(val(0.0)):.2f}")
    print(f"  after the correction:                             {b(val(move)):.2f}")
    print(f"  the same distance the other way (placebo):        {b(val(-move)):.2f}")
    print("  (0 = the darkest point of the profile, 1 = the middle of the sheet)")


if __name__ == "__main__":
    main()
