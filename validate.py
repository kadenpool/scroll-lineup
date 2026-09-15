#!/usr/bin/env python3
"""validate.py - how far is a scroll-lineup transform.json from the challenge's official transform?

Usage
  python validate.py SAMPLE MOVING_ID FIXED_ID OURS_transform.json --out result.json [--meta metadata.json]

The official matrix comes from the open-data metadata.json (the volume's properties.transforms entry, the same
numbers as <volume>.zarr/transform.json). Both matrices map a MOVING level-0 voxel (x, y, z) to a FIXED level-0
voxel (x, y, z). Error = distance between where the two put the same moving point, in fixed voxels and in um.

Points
  * material: 4000 random points inside the scroll material of the moving scan that land inside the fixed scan
    (material read from the smaller of the two scans' coarsest pyramid level);
  * named: 5 heights through the overlap (5/25/50/75/95 %) x (centre, +x, -x, +y, -y at 70 % of the material radius);
  * landmarks: the official transform's own landmark pairs (where published): error of ours vs the clicked
    landmark, next to the official affine's own residual there (the reference's noise floor).
"""
import argparse
import gzip
import json
import sys

import numpy as np

sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
from scroll_lineup import Volume, load_whole  # noqa: E402

B = "s3://vesuvius-challenge-open-data"


def to4(M):
    T = np.eye(4)
    T[:3] = np.asarray(M, float)
    return T


def load_meta(path):
    if path:
        raw = open(path, "rb").read()
    else:
        import fsspec
        raw = fsspec.filesystem("s3", anon=True).cat("vesuvius-challenge-open-data/metadata.json")
    if raw[:2] == b"\x1f\x8b":
        raw = gzip.decompress(raw)
    return json.loads(raw)


def official(meta, sample, mid, fid):
    vols = meta["samples"][sample]["volumes"]
    for t in (vols[mid].get("properties") or {}).get("transforms") or []:
        if t["to_volume_id"] == fid:
            return to4(t["transformation_matrix"]), np.array(t.get("from_landmarks") or []), \
                np.array(t.get("to_landmarks") or []), "direct"
    for t in (vols[fid].get("properties") or {}).get("transforms") or []:
        if t["to_volume_id"] == mid:
            T = np.linalg.inv(to4(t["transformation_matrix"]))
            return T, np.array(t.get("to_landmarks") or []), np.array(t.get("from_landmarks") or []), "inverted"
    raise SystemExit(f"no direct official transform between {mid} and {fid} in {sample}")


def vol_url(meta, sample, vid):
    """Where the catalogue says the volume lives: open-data bucket, or data.aws.ash2txt.org for 'samples/...' paths."""
    v = meta["samples"][sample]["volumes"][vid]
    paths = [o["path"] for d in v.get("data", []) if d["type"] == "ome-zarr" for o in d["origins"]]
    for p in paths:
        if not p.startswith("samples/"):
            return f"{B}/{p.rstrip('/')}"
    if paths:
        return "https://data.aws.ash2txt.org/" + paths[0].rstrip("/")
    return f"{B}/{sample}/volumes/{v['long_id']}"


def ap(T, P):
    return P @ T[:3, :3].T + T[:3, 3]


def material_points(vm, vf, Toff, n, rng):
    """Random moving-voxel points in material whose official image lies inside the fixed volume."""
    # pick the volume whose coarsest level is smaller for the material mask
    use_m = np.prod(vm.shape(vm.maxlevel)) <= np.prod(vf.shape(vf.maxlevel))
    v = vm if use_m else vf
    arr, L = load_whole(v, v.maxlevel, cap=1.5e8)                 # uint8; pooled in memory if still too big
    vol = arr > 0
    del arr
    idx = np.argwhere(vol)
    if len(idx) == 0:
        raise SystemExit("no material found")
    pts = []
    Ti = np.linalg.inv(Toff)
    shp_m = np.array(vm.shape(0))[::-1]
    shp_f = np.array(vf.shape(0))[::-1]
    for _ in range(20):
        pick = idx[rng.integers(0, len(idx), n)]
        p0 = (2 ** L * (pick + rng.random(pick.shape)) - 0.5)[:, ::-1]           # L0 voxel xyz of that volume
        if use_m:
            pm = p0
        else:
            pm = ap(Ti, p0)
        pf = ap(Toff, pm)
        ok = np.all((pm >= 0) & (pm < shp_m), 1) & np.all((pf >= 0) & (pf < shp_f), 1)
        pts.append(pm[ok])
        if sum(len(p) for p in pts) >= n:
            break
    P = np.concatenate(pts)[:n]
    return P, ("moving" if use_m else "fixed"), L


def named_points(P):
    """5 heights x centre/+x/-x/+y/-y from the material sample (moving voxels)."""
    z = P[:, 2]
    out = []
    for q in (5, 25, 50, 75, 95):
        zq = np.percentile(z, q)
        band = P[np.abs(z - zq) <= max(np.ptp(z) * 0.03, 2)]
        if len(band) < 10:
            continue
        c = np.median(band[:, :2], 0)
        r = np.percentile(np.linalg.norm(band[:, :2] - c, axis=1), 90)
        for name, d in (("centre", (0, 0)), ("+x", (0.7, 0)), ("-x", (-0.7, 0)), ("+y", (0, 0.7)), ("-y", (0, -0.7))):
            out.append((f"z{q}%/{name}", np.array([c[0] + d[0] * r, c[1] + d[1] * r, zq])))
    return out


def compare(Ta, Tb, P, uf):
    e = np.linalg.norm(ap(Ta, P) - ap(Tb, P), axis=1)
    return dict(median_vox=float(np.median(e)), p95_vox=float(np.percentile(e, 95)), max_vox=float(e.max()),
                median_um=float(np.median(e) * uf), p95_um=float(np.percentile(e, 95) * uf), max_um=float(e.max() * uf)), e


def main():
    a = argparse.ArgumentParser()
    a.add_argument("sample")
    a.add_argument("moving_id")
    a.add_argument("fixed_id")
    a.add_argument("ours")
    a.add_argument("--out", required=True)
    a.add_argument("--meta")
    a.add_argument("--n", type=int, default=4000)
    args = a.parse_args()
    rng = np.random.default_rng(1)
    meta = load_meta(args.meta)
    Toff, lm_m, lm_f, how = official(meta, args.sample, args.moving_id, args.fixed_id)
    Tours = to4(json.load(open(args.ours))["transformation_matrix"])
    # the official answer in the same direction and format, for datacheck.py
    json.dump({"schema_version": "1.0.0", "source": f"open-data metadata.json, {args.sample} {args.moving_id}->{args.fixed_id} ({how})",
               "transformation_matrix": Toff[:3].tolist(), "moving_landmarks": lm_m.tolist(), "fixed_landmarks": lm_f.tolist()},
              open(__import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(args.out)),
                                              "official_transform.json"), "w"), indent=1)
    vm = Volume(vol_url(meta, args.sample, args.moving_id))
    vf = Volume(vol_url(meta, args.sample, args.fixed_id))
    P, mask_from, Lmask = material_points(vm, vf, Toff, args.n, rng)
    stats, e = compare(Tours, Toff, P, vf.um)
    res = dict(sample=args.sample, moving=vm.name, fixed=vf.name, official=how, n_points=len(P),
               material_mask=f"{mask_from} L{Lmask}", fixed_um=vf.um, moving_um=vm.um, error=stats)
    # error split by height (moving z) and by radius
    zq = np.percentile(P[:, 2], [0, 20, 40, 60, 80, 100])
    res["error_by_height"] = []
    for lo, hi in zip(zq[:-1], zq[1:]):
        s = (P[:, 2] >= lo) & (P[:, 2] <= hi)
        res["error_by_height"].append(dict(moving_z=[float(lo), float(hi)], median_um=float(np.median(e[s]) * vf.um),
                                           max_um=float(e[s].max() * vf.um)))
    res["named_points"] = []
    for name, p in named_points(P):
        d = float(np.linalg.norm(ap(Tours, p[None]) - ap(Toff, p[None])))
        res["named_points"].append(dict(name=name, moving_xyz=p.tolist(), err_vox=d, err_um=d * vf.um))
    if len(lm_m):
        eo = np.linalg.norm(ap(Tours, lm_m) - lm_f, axis=1)
        ef = np.linalg.norm(ap(Toff, lm_m) - lm_f, axis=1)
        res["landmarks"] = dict(n=len(lm_m), ours_err_um=(eo * vf.um).tolist(), official_resid_um=(ef * vf.um).tolist(),
                                ours_rms_um=float(np.sqrt((eo ** 2).mean()) * vf.um),
                                official_rms_um=float(np.sqrt((ef ** 2).mean()) * vf.um))
    # decomposition of the difference: official^-1 o ours in moving physical units
    D = np.linalg.inv(Toff) @ Tours
    res["difference_map_moving_vox"] = D[:3].tolist()
    json.dump(res, open(args.out, "w"), indent=1)
    print(json.dumps({k: res[k] for k in ("sample", "moving", "fixed", "n_points", "error")}, indent=1))
    if "landmarks" in res:
        print("landmarks: ours rms %.1f um vs official's own rms %.1f um (n=%d)" %
              (res["landmarks"]["ours_rms_um"], res["landmarks"]["official_rms_um"], res["landmarks"]["n"]))
    for r in res["error_by_height"]:
        print("  height band moving z %.0f-%.0f: median %.1f um, max %.1f um" % (*r["moving_z"], r["median_um"], r["max_um"]))


if __name__ == "__main__":
    main()
