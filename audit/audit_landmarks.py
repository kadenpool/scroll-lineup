"""Do the published transforms fit their own published landmarks?

Every official transform in the Vesuvius open-data metadata may carry `from_landmarks` and
`to_landmarks`: the point pairs the transform was built from. Applying the matrix to the from-points
should land on the to-points. This measures how far it actually lands, for every transform in the
catalogue that publishes landmarks.

Nothing here depends on any third-party tool. It reads the challenge's own metadata.json and does
one matrix multiply per landmark.

    python audit_landmarks.py

Units: landmark coordinates are voxel indices of their own volume. Residuals are converted to
microns using the TARGET volume's voxel size, taken from its `long_id`.
"""
import gzip
import json
import sys

import fsspec
import numpy as np

BUCKET = "vesuvius-challenge-open-data"
# A transform whose own landmarks sit further than this from its own matrix is worth a look.
FLAG_UM = 30.0


def load_meta(path=None):
    if path:
        raw = open(path, "rb").read()
    else:
        raw = fsspec.filesystem("s3", anon=True).cat(f"{BUCKET}/metadata.json")
    if raw[:2] == b"\x1f\x8b":
        raw = gzip.decompress(raw)
    return json.loads(raw)


def voxel_um(vol):
    """Voxel size in microns from the volume's long_id. Never from data.origins: a volume can carry
    several origins and the last may be a prediction store with no voxel size, which silently
    yields None and turns microns into voxels without complaining."""
    for part in str(vol.get("long_id") or "").split("-"):
        if part.endswith("um"):
            try:
                return float(part[:-2])
            except ValueError:
                pass
    return None


def main():
    meta = load_meta(sys.argv[1] if len(sys.argv) > 1 else None)
    rows, n_transforms, n_no_landmarks = [], 0, 0

    for sample, s in sorted(meta["samples"].items()):
        vols = s.get("volumes") or {}
        for vid, v in vols.items():
            for t in ((v.get("properties") or {}).get("transforms") or []):
                n_transforms += 1
                tgt = t["to_volume_id"]
                src = np.array(t.get("from_landmarks") or [], float)
                dst = np.array(t.get("to_landmarks") or [], float)
                if src.size == 0 or dst.size == 0 or src.shape != dst.shape:
                    n_no_landmarks += 1
                    continue
                M = np.array(t["transformation_matrix"], float)
                pred = src @ M[:3, :3].T + M[:3, 3]
                err_vox = np.linalg.norm(pred - dst, axis=1)
                um = voxel_um(vols.get(tgt, {}))
                if um is None:
                    print(f"  !! no voxel size for {sample}/{tgt}, skipping", file=sys.stderr)
                    continue
                err = err_vox * um
                rows.append(dict(sample=sample, src=vid, dst=tgt,
                                 um_from=voxel_um(v), um_to=um, n=len(err),
                                 rms=float(np.sqrt((err ** 2).mean())),
                                 worst=float(err.max()), each=np.round(err, 1).tolist()))

    rows.sort(key=lambda r: -r["rms"])
    print(f"official transforms in the catalogue: {n_transforms}")
    print(f"  publish landmarks: {len(rows)}      publish none: {n_no_landmarks}")
    print()
    print("| object | moving -> fixed (um) | landmarks | RMS um | worst um |")
    print("|---|---|---|---|---|")
    for r in rows:
        mark = " **" if r["rms"] > FLAG_UM else ""
        print(f"| {r['sample']}{mark} | {r['um_from']} -> {r['um_to']} | {r['n']} | "
              f"{r['rms']:.1f}{mark} | {r['worst']:.1f} |")
    print()
    bad = [r for r in rows if r["rms"] > FLAG_UM]
    print(f"{len(bad)} of {len(rows)} sit further than {FLAG_UM:.0f} um from their own landmarks.")
    for r in bad:
        print(f"\n{r['sample']}  {r['src']} -> {r['dst']}   {r['um_from']} -> {r['um_to']} um")
        print(f"   per landmark (um): {r['each']}")
        print(f"   RMS {r['rms']:.1f} um, worst {r['worst']:.1f} um, n={r['n']}")


if __name__ == "__main__":
    main()
