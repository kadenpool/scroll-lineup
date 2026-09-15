#!/usr/bin/env python3
"""Compare a fresh run against a committed one.

  python tests/compare_run.py runs/v9_MANBp results/v9_MANBp

Fails if the two transforms disagree by more than the tolerance anywhere in the overlap, or if the
error figures against the official transform have moved by more than a tenth of a micrometre. It does
NOT fail on an md5 mismatch: byte-identity holds within one set of library versions and is not
guaranteed across them (VALIDATION.md has the measurement). The md5s are printed either way.
"""
import argparse
import hashlib
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scroll_lineup import apply  # noqa: E402


def to4(M):
    T = np.eye(4)
    T[:3] = np.asarray(M, float)
    return T


def md5(path):
    return hashlib.md5(open(path, "rb").read()).hexdigest()


def main():
    a = argparse.ArgumentParser()
    a.add_argument("fresh")
    a.add_argument("committed")
    a.add_argument("--tol-um", type=float, default=1.0,
                   help="largest allowed disagreement between the two transforms, in fixed micrometres")
    a.add_argument("--tol-error-um", type=float, default=0.1,
                   help="largest allowed move in the median/p95/max error against the official transform")
    args = a.parse_args()

    bad = []
    Ta = to4(json.load(open(os.path.join(args.fresh, "transform.json")))["transformation_matrix"])
    Tb = to4(json.load(open(os.path.join(args.committed, "transform.json")))["transformation_matrix"])
    ra = json.load(open(os.path.join(args.fresh, "report.json")))
    rb = json.load(open(os.path.join(args.committed, "report.json")))

    ma, mb = md5(os.path.join(args.fresh, "transform.json")), md5(os.path.join(args.committed, "transform.json"))
    print(f"transform.json md5   fresh {ma}\n                 committed {mb}   "
          f"{'identical' if ma == mb else 'DIFFERENT (allowed; see the tolerance below)'}")

    # disagreement over the moving volume's own corners, converted to fixed micrometres
    shp = np.array(ra["volumes"]["moving"]["shape"], float)[::-1]          # zyx -> xyz
    um = ra["volumes"]["fixed"]["um"]
    corners = np.array([[x, y, z] for x in (0, shp[0]) for y in (0, shp[1]) for z in (0, shp[2])])
    d = float(np.max(np.linalg.norm(apply(Ta, corners) - apply(Tb, corners), axis=1)) * um)
    print(f"largest disagreement over the moving volume's corners: {d:.6f} um   (tolerance {args.tol_um} um)")
    if d > args.tol_um:
        bad.append(f"the two transforms disagree by {d:.3f} um, over the {args.tol_um} um tolerance")

    for k in ("n_tried", "n_matched", "n_used"):
        fa, fb = ra["blocks"][-1][k], rb["blocks"][-1][k]
        print(f"final block round {k}: fresh {fa}, committed {fb}")
    print(f"confidence: fresh {ra['confidence']['level']}, committed {rb['confidence']['level']}")
    if ra["confidence"]["level"] != rb["confidence"]["level"]:
        bad.append("the confidence level changed")

    va = os.path.join(args.fresh, "validation.json")
    vb = os.path.join(args.committed, "validation.json")
    if os.path.exists(va) and os.path.exists(vb):
        ea, eb = json.load(open(va))["error"], json.load(open(vb))["error"]
        for k in ("median_um", "p95_um", "max_um"):
            print(f"error vs official, {k}: fresh {ea[k]:.6f}, committed {eb[k]:.6f}, "
                  f"moved {abs(ea[k] - eb[k]):.6f} um")
            if abs(ea[k] - eb[k]) > args.tol_error_um:
                bad.append(f"{k} moved by {abs(ea[k] - eb[k]):.3f} um")

    print()
    if bad:
        print("FAILED: " + "; ".join(bad))
        sys.exit(1)
    print(f"the fresh run reproduces the committed one for {os.path.basename(args.committed.rstrip('/'))}")


if __name__ == "__main__":
    main()
