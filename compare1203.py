#!/usr/bin/env python3
"""compare1203.py - PHerc1203 has no official transform. Compare four independent ones, all as maps from the
2.403 um scan (20260319130212) level-0 voxel (x, y, z) to the 9.362 um scan (20250820131727) level-0 voxel:

  ours_0911      our 11 Sep cross-section result: fine = (coarse - (7936, 20, -20)_zyx) * 3.8959634
  flummoxjr      github.com/flummoxjr/measure-before-you-hunt hunt/pherc1203_2403um_to_9362um.json (xyz)
  7jycwjmbfn     github.com/7jycwjmbfn-eng/pherc0139-physical-audit results/1203/pass3_final.npz:
                 M2, t2 map the 2.4 um level-4 index (z, y, x) to the 9.362 um level-2 index (z, y, x)
  scroll-lineup  this tool's transform.json (moving = 2.403 um, fixed = 9.362 um)

Usage: python compare1203.py SCROLL_LINEUP_transform.json FLUMMOX.json SEVEN.npz --out compare1203.json
"""
import argparse
import json
import sys

import numpy as np

sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
from scroll_lineup import Volume  # noqa: E402

B = "s3://vesuvius-challenge-open-data/PHerc1203/volumes"
FINE = f"{B}/20260319130212-2.403um-0.2m-77keV-masked.zarr"
COARSE = f"{B}/20250820131727-9.362um-1.2m-113keV-masked.zarr"
P = np.array([[0, 0, 1], [0, 1, 0], [1, 0, 0]], float)      # zyx <-> xyz


def to4(M):
    T = np.eye(4)
    T[:3] = np.asarray(M, float)
    return T


def ap(T, X):
    return X @ T[:3, :3].T + T[:3, 3]


def main():
    a = argparse.ArgumentParser()
    a.add_argument("scroll_lineup")
    a.add_argument("flummox")
    a.add_argument("seven")
    a.add_argument("--out", required=True)
    a.add_argument("--datacheck", action="store_true", help="also measure each transform against held-out image blocks")
    args = a.parse_args()
    T = {}
    S = 3.8959634
    T["ours_0911"] = to4(np.hstack([np.eye(3) / S, np.array([[-20.0], [20.0], [7936.0]])]))
    T["flummoxjr"] = to4(json.load(open(args.flummox))["transformation_matrix"])
    d = np.load(args.seven)
    M2, t2 = d["M2"], d["t2"]                    # coarse_L2_zyx = M2 fine_L4_zyx + t2
    # level index -> L0: fine_L4 = (fine_L0 - 7.5) / 16 ; coarse_L0 = 4 coarse_L2 + 1.5  (2x2x2 mean pyramid)
    A_zyx = M2 / 4.0
    t_zyx = 4.0 * t2 + 1.5 - A_zyx @ np.full(3, 7.5)
    T["7jycwjmbfn"] = to4(np.hstack([P @ A_zyx @ P, (P @ t_zyx)[:, None]]))
    T["scroll-lineup"] = to4(json.load(open(args.scroll_lineup))["transformation_matrix"])
    for k, v in T.items():
        print(f"{k:13s} scale {np.cbrt(np.linalg.det(v[:3, :3])):.7f} t_xyz {np.round(v[:3, 3], 2).tolist()}")
    # sample points: coarse L5 material mapped back into the fine volume through scroll-lineup, kept if inside it
    vc, vfn = Volume(COARSE), Volume(FINE)
    L = vc.maxlevel
    m = vc.read(L, (0, 0, 0), vc.shape(L)) > 0
    idx = np.argwhere(m)
    rng = np.random.default_rng(2)
    pick = idx[rng.integers(0, len(idx), 200000)]
    pc = (2 ** L * (pick + rng.random(pick.shape)) - 0.5)[:, ::-1]
    pf = ap(np.linalg.inv(T["scroll-lineup"]), pc)
    ok = np.all((pf >= 0) & (pf < np.array(vfn.shape(0))[::-1]), 1)
    pf = pf[ok][:5000]
    print(f"{len(pf)} material points inside the 2.403 um scan (fine z {pf[:, 2].min():.0f}..{pf[:, 2].max():.0f})")
    names = list(T)
    res = dict(transforms={k: v[:3].tolist() for k, v in T.items()}, n_points=len(pf), pairs=[])
    uc = 9.362
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            D = ap(T[names[i]], pf) - ap(T[names[j]], pf)
            e = np.linalg.norm(D, axis=1)
            row = dict(a=names[i], b=names[j], median_um=float(np.median(e) * uc), p95_um=float(np.percentile(e, 95) * uc),
                       max_um=float(e.max() * uc), mean_dxyz_um=(D.mean(0) * uc).tolist(),
                       z_only_median_um=float(np.median(np.abs(D[:, 2])) * uc),
                       xy_only_median_um=float(np.median(np.linalg.norm(D[:, :2], axis=1)) * uc))
            # split by fine height
            zq = np.percentile(pf[:, 2], [0, 33, 67, 100])
            row["by_height_median_um"] = [float(np.median(e[(pf[:, 2] >= lo) & (pf[:, 2] <= hi)]) * uc)
                                          for lo, hi in zip(zq[:-1], zq[1:])]
            res["pairs"].append(row)
            print(f"{names[i]:13s} vs {names[j]:13s}: median {row['median_um']:6.1f} um  p95 {row['p95_um']:6.1f}  "
                  f"max {row['max_um']:6.1f}  (z-only {row['z_only_median_um']:5.1f}, xy-only {row['xy_only_median_um']:5.1f}; "
                  f"mean dxyz {np.round(row['mean_dxyz_um'], 1).tolist()}; by height {np.round(row['by_height_median_um'], 1).tolist()})")
    if args.datacheck:
        res["datacheck"] = datacheck(T, vfn, vc, args)
    json.dump(res, open(args.out, "w"), indent=1)


def datacheck(T, vfn, vc, args):
    """Which transform do the images agree with? Held-out blocks (different chunks and a different position inside
    each chunk than scroll-lineup's own blocks) at ~19 um: under each transform, how far must each block move to match?"""
    import types
    from scroll_lineup import block_pass, choose_blocks
    from scipy import ndimage as ndi
    rng = np.random.default_rng(12345)
    Lt2 = vc.level_for(150)
    tall2 = vc.read(Lt2, (0, 0, 0), vc.shape(Lt2)) > 0
    tall_m = ndi.binary_erosion(tall2, iterations=1)
    Ls = vfn.level_for(19.0)
    Lt = vc.level_for(vfn.vox(Ls))
    phys = {}
    for k, M in T.items():
        Q = M[:3, :3] * vc.um / vfn.um
        c = M[:3, 3] * vc.um
        P4 = np.eye(4)
        P4[:3, :3], P4[:3, 3] = Q, c
        phys[k] = P4
    bsz = 48
    centers = choose_blocks(vfn, vc, phys["scroll-lineup"], Ls, bsz, tall_m, Lt2, 60, rng)
    cs = np.array(vfn.levels[Ls]["chunks"])
    centers = [np.clip(c - (cs - bsz) // 2 + 70, 0, np.array(vfn.shape(Ls)) - bsz) for c in centers]   # other spot in chunk
    a = types.SimpleNamespace(min_material=0.35, dog=(1.0, 4.0))
    out = {}
    for k, P4 in phys.items():
        bl = block_pass(vfn, vc, P4, Ls, Lt, centers, bsz, 6, a, k)
        good = [b for b in bl if b["ncc"] >= 0.3 and not b["at_edge"]]
        d = np.array([np.linalg.norm(np.array(b["shift_vox"]) * vfn.vox(Ls)) for b in good])
        dz = np.array([abs(b["shift_vox"][0]) * vfn.vox(Ls) for b in good])
        out[k] = dict(n_blocks=len(bl), n_good=len(good), median_move_um=float(np.median(d)) if len(d) else None,
                      p90_move_um=float(np.percentile(d, 90)) if len(d) else None,
                      median_z_move_um=float(np.median(dz)) if len(dz) else None,
                      ncc_median=float(np.median([b["ncc"] for b in good])) if good else None)
        print(f"datacheck {k:13s}: {len(good)}/{len(bl)} blocks, blocks must move median {out[k]['median_move_um']:.1f} um "
              f"(p90 {out[k]['p90_move_um']:.1f}, height part {out[k]['median_z_move_um']:.1f}) to match", flush=True)
    return out


if __name__ == "__main__":
    main()
