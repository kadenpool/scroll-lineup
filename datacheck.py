#!/usr/bin/env python3
"""datacheck.py - which of several transforms do the images agree with?

When our transform and a reference disagree, the images decide. For each transform, small cubes of the shorter
scan (held out: other chunks and another spot inside each chunk than scroll-lineup's own blocks) are matched
inside the other scan; the answer is how far each cube must still move to match. A correct transform needs ~0
movement.
Optionally cubes are centred on a reference's own landmarks (--at-landmarks).

Usage
  python datacheck.py MOVING_URL FIXED_URL NAME=transform.json [NAME=transform.json ...] --out dc.json
         [--level-um 19] [--radius 10] [--blocks 48] [--at-landmarks NAME]
transform.json files: anything with a 3x4 "transformation_matrix" moving voxel (x, y, z) -> fixed voxel (x, y, z).
"""
import argparse
import json
import os
import sys
import types

import numpy as np
from scipy import ndimage as ndi

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scroll_lineup import Volume, block_pass, choose_blocks, inv, load_whole  # noqa: E402


def phys(M, vm, vf):
    """moving voxel -> fixed voxel matrix to moving um -> fixed um."""
    T = np.eye(4)
    T[:3, :3] = np.asarray(M)[:, :3] * vf.um / vm.um
    T[:3, 3] = np.asarray(M)[:, 3] * vf.um
    return T


def main():
    a = argparse.ArgumentParser()
    a.add_argument("moving")
    a.add_argument("fixed")
    a.add_argument("transforms", nargs="+")
    a.add_argument("--out", required=True)
    a.add_argument("--level-um", type=float, default=19.0)
    a.add_argument("--radius", type=int, default=10)
    a.add_argument("--blocks", type=int, default=48)
    a.add_argument("--bsz", type=int, default=48)
    a.add_argument("--at-landmarks", help="NAME of a transform whose moving_landmarks become the block centres")
    a.add_argument("--seed", type=int, default=12345)
    args = a.parse_args()
    vm, vf = Volume(args.moving), Volume(args.fixed)
    short_is_moving = vm.extent_um()[0] <= vf.extent_um()[0]
    vs, vt = (vm, vf) if short_is_moving else (vf, vm)
    Ts, files = {}, {}
    for s in args.transforms:
        name, path = s.split("=", 1)
        d = json.load(open(path))
        T = phys(d["transformation_matrix"], vm, vf)                     # moving um -> fixed um
        Ts[name] = T if short_is_moving else inv(T)                      # short um -> tall um
        files[name] = d
    first = list(Ts)[0]
    Ls = vs.level_for(args.level_um)
    Lt = vt.level_for(vs.vox(Ls))
    bsz = args.bsz
    if args.at_landmarks:
        d = files[args.at_landmarks]
        key = "moving_landmarks" if short_is_moving else "fixed_landmarks"
        if not d.get(key):
            sys.exit(f"--at-landmarks {args.at_landmarks}: that transform has no '{key}'. Official transforms do not all "
                     f"carry landmarks. Drop --at-landmarks to use held-out blocks chosen from the volume instead.")
        lm = np.array(d[key], float)                                      # short voxels xyz
        cen = vs.p2i(Ls, lm[:, ::-1] * vs.um)                            # level-Ls (z, y, x)
        centers = [np.round(c - (bsz - 1) / 2.0).astype(int) for c in cen]
    else:
        tall_u8, Lt2 = load_whole(vt, vt.level_for(150))          # uint8, pooled in memory if the level is huge
        tall_m = ndi.binary_erosion(tall_u8 > 0, iterations=1)
        del tall_u8
        rng = np.random.default_rng(args.seed)
        centers = choose_blocks(vs, vt, Ts[first], Ls, bsz, tall_m, Lt2, args.blocks, rng)
        cs = np.array(vs.levels[Ls]["chunks"])
        off = (cs - bsz) // 2
        centers = [np.clip(c - off + min(70, int(cs[0]) - bsz - 8), 0, np.array(vs.shape(Ls)) - bsz) for c in centers]
    opts = types.SimpleNamespace(min_material=0.2 if args.at_landmarks else 0.35, dog=(1.0, 4.0))
    out = dict(moving=vm.url, fixed=vf.url, level_um=vs.vox(Ls), radius_vox=args.radius, n_centres=len(centers),
               at_landmarks=args.at_landmarks, results={})
    per_block = {}
    for name, T in Ts.items():
        bl = block_pass(vs, vt, T, Ls, Lt, centers, bsz, args.radius, opts, name)
        per_block[name] = {tuple(b["block"]): b for b in bl}
    # compare on the blocks every transform matched well
    common = set.intersection(*[set(k for k, b in pb.items() if b["ncc"] >= 0.3 and not b["at_edge"]) for pb in per_block.values()])
    for name in Ts:
        sh = np.array([per_block[name][k]["shift_vox"] for k in common]) * vs.vox(Ls) if common else np.zeros((0, 3))
        mv = np.linalg.norm(sh, axis=1)
        out["results"][name] = dict(
            n_common=len(common), n_matched=len(per_block[name]),
            median_move_um=float(np.median(mv)) if len(mv) else None,
            p90_move_um=float(np.percentile(mv, 90)) if len(mv) else None,
            max_move_um=float(mv.max()) if len(mv) else None,
            median_abs_zyx_um=np.median(np.abs(sh), 0).tolist() if len(mv) else None,
            ncc_median=float(np.median([per_block[name][k]["ncc"] for k in common])) if common else None,
            per_block=[dict(block=list(k), shift_um_zyx=(np.array(per_block[name][k]["shift_vox"]) * vs.vox(Ls)).tolist(),
                            ncc=per_block[name][k]["ncc"]) for k in sorted(common)])
        r = out["results"][name]
        if len(mv):
            print(f"{name:12s}: {len(common)} common blocks at {vs.vox(Ls):.0f} um; must move median {r['median_move_um']:.1f} um, "
                  f"p90 {r['p90_move_um']:.1f}, max {r['max_move_um']:.1f} (|z,y,x| median {np.round(r['median_abs_zyx_um'], 1).tolist()}), "
                  f"ncc {r['ncc_median']:.2f}", flush=True)
    json.dump(out, open(args.out, "w"), indent=1)


if __name__ == "__main__":
    main()
