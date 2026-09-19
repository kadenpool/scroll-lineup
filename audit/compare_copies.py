"""Does each official transform agree with the copy stored next to its volume?

The challenge publishes a transform in two places: in the catalogue, `metadata.json`, under the moving
volume's `properties.transforms`; and as a `transform.json` inside the moving volume's own zarr folder.
Readers use both. This checks, for every catalogue transform, whether a per-volume copy exists, whether
its matrix and landmarks match the catalogue's, and how well each copy fits its own landmarks.

    python audit/compare_copies.py                 # about 20 s: one small fetch per volume
    python audit/compare_copies.py local.json      # catalogue from a local copy; per-volume files
                                                   # are still fetched

Needs numpy and fsspec (plus s3fs for the bucket), all of which the tool already requires.

Two things this is careful about, because each has cost a wrong number before:
  * the voxel size comes from the volume's `long_id`, never from `data.origins`, where the last origin
    may be a prediction store whose path carries no voxel size;
  * a copy that disagrees is also tested in the OPPOSITE direction, target to source through the
    inverse matrix, so that "stored the other way round" is not reported as "wrong".
"""
import gzip
import json
import sys

import fsspec
import numpy as np

BUCKET = "vesuvius-challenge-open-data"
SECOND_HOST = "https://data.aws.ash2txt.org"


def load_meta(path=None):
    raw = open(path, "rb").read() if path else fsspec.filesystem("s3", anon=True).cat(f"{BUCKET}/metadata.json")
    return json.loads(gzip.decompress(raw) if raw[:2] == b"\x1f\x8b" else raw)


def voxel_um(vol):
    for part in str(vol.get("long_id") or "").split("-"):
        if part.endswith("um"):
            try:
                return float(part[:-2])
            except ValueError:
                pass
    return None


def zarr_paths(vol):
    """Every ome-zarr path the catalogue gives for a volume, with the host it says to read it from."""
    out = []
    for d in vol.get("data") or []:
        if d.get("type") != "ome-zarr":
            continue
        for o in d.get("origins") or []:
            p = (o.get("path") or "").rstrip("/")
            if not p:
                continue
            roots = [r.get("url") for r in (o.get("access_roots") or []) if r.get("url")]
            out.append((p, roots))
    return out


def fetch_copy(vol):
    """The per-volume transform.json for a volume, trying the bucket first and then the second host."""
    s3 = fsspec.filesystem("s3", anon=True)
    http = fsspec.filesystem("https")
    for path, roots in zarr_paths(vol):
        try:
            return json.loads(s3.cat(f"{BUCKET}/{path}/transform.json")), f"s3://{BUCKET}/{path}/transform.json"
        except Exception:
            pass
        for root in roots + [SECOND_HOST]:
            try:
                url = f"{root.rstrip('/')}/{path}/transform.json"
                return json.loads(http.cat(url)), url
            except Exception:
                pass
    return None, None


def fit_um(M, src, dst, um_dst):
    """RMS and median, in microns of the destination volume, of M applied to src against dst."""
    e = np.linalg.norm(src @ M[:3, :3].T + M[:3, 3] - dst, axis=1) * um_dst
    return float(np.sqrt((e ** 2).mean())), float(np.median(e))


def main():
    meta = load_meta(sys.argv[1] if len(sys.argv) > 1 else None)
    rows = []
    for sample, s in sorted(meta["samples"].items()):
        vols = s.get("volumes") or {}
        for vid, v in vols.items():
            for t in ((v.get("properties") or {}).get("transforms") or []):
                tgt = t["to_volume_id"]
                um_src, um_dst = voxel_um(v), voxel_um(vols.get(tgt, {}))
                Mc = np.array(t["transformation_matrix"], float)
                cs = np.array(t.get("from_landmarks") or [], float)
                cd = np.array(t.get("to_landmarks") or [], float)
                cat_fit = fit_um(Mc, cs, cd, um_dst) if cs.size and cs.shape == cd.shape else None

                copy, where = fetch_copy(v)
                r = dict(sample=sample, src=vid, dst=tgt, um_src=um_src, um_dst=um_dst,
                         n_cat=len(cs), cat_fit=cat_fit, where=where, status="no per-volume copy")
                if copy is not None:
                    Mv = np.array(copy["transformation_matrix"], float)
                    vs = np.array(copy.get("moving_landmarks") or copy.get("from_landmarks") or [], float)
                    vd = np.array(copy.get("fixed_landmarks") or copy.get("to_landmarks") or [], float)
                    r["n_copy"] = len(vs)
                    r["copy_target"] = str(copy.get("fixed_volume") or "")
                    r["same_matrix"] = bool(Mc.shape == Mv.shape and np.allclose(Mc, Mv, rtol=1e-9, atol=1e-6))
                    r["same_landmarks"] = bool(cs.shape == vs.shape and cd.shape == vd.shape
                                               and np.allclose(cs, vs) and np.allclose(cd, vd))
                    if vs.size and vs.shape == vd.shape:
                        r["copy_fit"] = fit_um(Mv, vs, vd, um_dst)
                        # the other direction: target to source through the inverse, in source microns
                        M4 = np.eye(4); M4[:3, :] = Mv[:3, :]
                        Mi = np.linalg.inv(M4)[:3, :]
                        r["copy_fit_inverse"] = fit_um(Mi, vd, vs, um_src)
                    r["status"] = ("identical" if r["same_matrix"] and r["same_landmarks"] else "DIFFERS")
                rows.append(r)

    n = len(rows)
    have = [r for r in rows if r["status"] != "no per-volume copy"]
    diff = [r for r in have if r["status"] == "DIFFERS"]
    print(f"catalogue transforms: {n}")
    print(f"  with a per-volume transform.json: {len(have)}")
    print(f"  of those, identical to the catalogue: {len(have) - len(diff)}")
    print(f"  of those, DIFFERENT from the catalogue: {len(diff)}")
    print()
    print("| object | moving -> fixed (um) | per-volume copy | catalogue fit RMS um | copy fit RMS um |")
    print("|---|---|---|---|---|")
    for r in rows:
        cf = f"{r['cat_fit'][0]:.1f}" if r.get("cat_fit") else "-"
        vf = f"{r['copy_fit'][0]:.1f}" if r.get("copy_fit") else "-"
        mark = " **" if r["status"] == "DIFFERS" else ""
        print(f"| {r['sample']}{mark} | {r['um_src']} -> {r['um_dst']} | {r['status']} | {cf} | {vf}{mark} |")
    for r in diff:
        print()
        print(f"{r['sample']}  {r['src']} -> {r['dst']}   {r['um_src']} -> {r['um_dst']} um")
        print(f"   catalogue copy : {r['n_cat']} landmarks, RMS {r['cat_fit'][0]:.1f} um, median {r['cat_fit'][1]:.1f} um")
        if r.get("copy_fit"):
            print(f"   per-volume copy: {r['n_copy']} landmarks, RMS {r['copy_fit'][0]:.1f} um, median {r['copy_fit'][1]:.1f} um")
            print(f"   per-volume copy read the other way (inverse, target to source): "
                  f"RMS {r['copy_fit_inverse'][0]:.1f} um, median {r['copy_fit_inverse'][1]:.1f} um in source microns")
        print(f"   same matrix: {r['same_matrix']}   same landmarks: {r['same_landmarks']}   "
              f"copy names target: {r.get('copy_target') or '(not stated)'}")
        print(f"   copy read from: {r['where']}")


if __name__ == "__main__":
    main()
