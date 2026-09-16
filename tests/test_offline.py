#!/usr/bin/env python3
"""Offline checks. No network, no scan data, a few seconds.

  A.  The geometry the tool rests on: fit, invert, decompose, correlate. Each is given a transform or
      a shift chosen in advance and has to recover it.
  B.  The committed evidence, for results/ and robustness/ alike: every cell of each table that comes
      from a committed JSON file is re-derived from that file and compared.
  C.  The worked example: the inverse really inverts, and the report carries the same matrix.
  C2. The README's own hand-made table against the generated one.
  D.  The same pairs run on a second Python and a second numpy/scipy, committed under
      robustness/second_stack/, must agree with the first to better than 0.01 um.
  E.  The command line.
  F.  The landmark audit: the committed result, the README table and audit/README.md must be the
      same four rows with the same numbers.
  G.  The depth measurement behind the alignment budget: one window reads, the rest are at chance,
      and reversed depth order never rises anywhere.

A reviewer can run all of it before downloading a single voxel.

Run:  python tests/test_offline.py
Exit 0 if every check passes, 1 otherwise. Needs numpy, scipy and fsspec: nothing here touches the
network, but fsspec is imported at the top of scroll_lineup.py, so importing the tool needs it present.
s3fs and Pillow are not needed to run this file.
"""
import json
import re
import os
import subprocess
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from scroll_lineup import (FFTCorr, VERSION, apply, decompose, fit_affine,  # noqa: E402
                           fit_similarity, inv, masked_ncc_valid, nms, rot2)
from summarize import verdict  # noqa: E402

FAILED = []


def check(name, ok, detail=""):
    print(("  ok   " if ok else "  FAIL ") + name + (("   " + detail) if detail else ""))
    if not ok:
        FAILED.append(name)


def close(a, b, tol):
    return float(np.max(np.abs(np.asarray(a, float) - np.asarray(b, float)))) <= tol


# ----------------------------------------------------------------------------------------------
# A. Geometry
# ----------------------------------------------------------------------------------------------
def test_geometry():
    print("A. geometry")
    rng = np.random.default_rng(7)

    # a known similarity: 0.25x, 23 degrees in plane, a 3-degree tilt, a translation
    th, sc = np.radians(23.0), 0.2566
    Rz = np.array([[np.cos(th), -np.sin(th), 0], [np.sin(th), np.cos(th), 0], [0, 0, 1]])
    ti = np.radians(3.0)
    Rx = np.array([[1, 0, 0], [0, np.cos(ti), -np.sin(ti)], [0, np.sin(ti), np.cos(ti)]])
    T = np.eye(4)
    T[:3, :3] = sc * Rz @ Rx
    T[:3, 3] = [-21.44, 24.95, 7935.29]

    P = rng.normal(0, 500, (400, 3))
    Q = apply(T, P)

    Tf = fit_similarity(P, Q)
    check("fit_similarity recovers a known similarity", close(Tf, T, 1e-8),
          f"max |dT| = {np.max(np.abs(Tf - T)):.2e}")

    Ta = fit_affine(P, Q)
    check("fit_affine recovers the same transform", close(Ta, T, 1e-8),
          f"max |dT| = {np.max(np.abs(Ta - T)):.2e}")

    # a genuine affine (unequal axis scales + shear) is out of reach of a similarity fit and in reach of affine
    A = np.diag([0.26, 0.24, 0.25]) @ Rz
    A[0, 1] += 0.01
    T2 = np.eye(4)
    T2[:3, :3], T2[:3, 3] = A, [5.0, -7.0, 100.0]
    Q2 = apply(T2, P)
    check("fit_affine recovers a sheared, anisotropic map", close(fit_affine(P, Q2), T2, 1e-8))
    check("fit_similarity cannot, and does not pretend to", not close(fit_similarity(P, Q2), T2, 1e-3))

    # weights: one point moved a long way is ignored when its weight is zero
    Qw = Q.copy()
    Qw[0] += 10_000.0
    w = np.ones(len(P))
    w[0] = 0.0
    check("fit_affine ignores a zero-weighted outlier", close(fit_affine(P, Qw, w), T, 1e-7))

    # inverse
    Ti = inv(T)
    check("inv(T) undoes T on points", close(apply(Ti, apply(T, P)), P, 1e-6),
          f"max |dP| = {np.max(np.abs(apply(Ti, apply(T, P)) - P)):.2e} um")
    check("inv(inv(T)) is T", close(inv(Ti), T, 1e-9))

    # decompose reads back what was built in
    d = decompose(T[:3, :3])
    check("decompose reads the scale", abs(d["scale"] - sc) < 1e-9, f"{d['scale']:.6f} vs {sc}")
    check("decompose reads the in-plane rotation", abs(d["rot_deg"] - 23.0) < 1e-6, f"{d['rot_deg']:.6f} deg")
    check("decompose reads the tilt", abs(d["tilt_deg"] - 3.0) < 1e-6, f"{d['tilt_deg']:.6f} deg")
    check("decompose sees no mirror and no flip", not d["improper"] and not d["z_axis_flipped"])

    # a mirrored, upside-down map must be flagged as both
    M = T[:3, :3] @ np.diag([1.0, 1.0, -1.0])
    dm = decompose(M)
    check("decompose flags a mirror and an upside-down z", dm["improper"] and dm["z_axis_flipped"])

    check("rot2 is a rotation", close(rot2(np.radians(37.0)) @ rot2(np.radians(37.0)).T, np.eye(2), 1e-12)
          and abs(np.linalg.det(rot2(np.radians(37.0))) - 1) < 1e-12)

    # FFT correlation finds a shift that was put in on purpose
    img = rng.normal(0, 1, (128, 128)).astype(np.float32)
    img = img + 3.0 * np.exp(-((np.arange(128)[:, None] - 40) ** 2 + (np.arange(128)[None] - 70) ** 2) / 200.0)
    dy0, dx0 = 9, -13
    shifted = np.roll(np.roll(img, dy0, 0), dx0, 1)
    fc = FFTCorr(128, 128, workers=1)
    v, dy, dx = fc.corr(fc.spec(img), fc.spec(shifted))
    check("FFTCorr finds a known whole-pixel shift", (int(dy), int(dx)) == (-dy0, -dx0) and v > 0.99,
          f"got dy {dy:.0f} dx {dx:.0f}, ncc {v:.4f}")
    check("FFTCorr scores an image against itself at 1.0", abs(fc.corr(fc.spec(img), fc.spec(img))[0] - 1.0) < 1e-4)

    # 3D masked NCC peaks where the block really sits
    big = rng.normal(0, 1, (40, 40, 40)).astype(np.float32)
    off = (7, 11, 5)
    small = big[off[0]:off[0] + 12, off[1]:off[1] + 12, off[2]:off[2] + 12].copy()
    w3 = np.ones_like(small)
    cc = masked_ncc_valid(big, small, w3)
    peak = np.unravel_index(int(np.argmax(cc)), cc.shape)
    check("masked_ncc_valid peaks at the true block position", tuple(peak) == off,
          f"peak at {tuple(int(p) for p in peak)}, ncc {cc.max():.4f}")
    check("its peak correlation is 1.0", abs(float(cc.max()) - 1.0) < 1e-3)

    # non-maximum suppression drops a near-duplicate candidate and keeps a distinct one
    def cand(rot, z, sgn=1, mirror=False):
        return dict(rot_deg=rot, z_mid_tall_um=z, sgn=sgn, mirror=mirror)
    kept = nms([cand(0, 0), cand(5, 500), cand(90, 0), cand(0, 40000)], 10)
    check("nms drops a near-duplicate and keeps the rest", len(kept) == 3, f"kept {len(kept)} of 4")
    check("nms respects keep_n", len(nms([cand(0, 0), cand(90, 0), cand(180, 0)], 2)) == 2)

    # the pre-registered verdict rule, at its two boundaries
    check("verdict rule: 30 um is PASS, 30.1 is WEAK, 150 is WEAK, 150.1 is FAIL",
          (verdict(30.0), verdict(30.1), verdict(150.0), verdict(150.1)) == ("PASS", "WEAK", "WEAK", "FAIL"))


# ----------------------------------------------------------------------------------------------
# B. The committed evidence
# ----------------------------------------------------------------------------------------------
def to4(M):
    T = np.eye(4)
    T[:3] = np.asarray(M, float)
    return T


def parse_table(path):
    rows = {}
    for line in open(path):
        if not line.startswith("| ") or line.startswith("|---") or line.startswith("| run "):
            continue
        c = [x.strip() for x in line.strip().strip("|").split("|")]
        rows[c[0]] = c
    return rows


def test_committed(folder="results", pairs_file="pairs.txt"):
    print(f"B. the committed evidence in {folder}/")
    table = parse_table(os.path.join(ROOT, folder, "table.md"))
    tags = sorted(d for d in os.listdir(os.path.join(ROOT, folder))
                  if os.path.isdir(os.path.join(ROOT, folder, d)) and d != "second_stack")
    check(f"{folder}/table.md has a row for every committed run",
          set(table) == set(tags), f"{len(tags)} run folders, {len(table)} table rows")

    pairs = [l.split()[0] for l in open(os.path.join(ROOT, pairs_file)) if l.strip() and not l.startswith("#")]
    check(f"{pairs_file} lists exactly those runs", sorted(pairs) == tags)

    bad = []
    for tag in tags:
        d = os.path.join(ROOT, folder, tag)
        rep = json.load(open(os.path.join(d, "report.json")))
        val = json.load(open(os.path.join(d, "validation.json")))
        off = json.load(open(os.path.join(d, "official_transform.json")))
        ours = json.load(open(os.path.join(d, "transform.json")))
        row = table.get(tag)
        T = to4(ours["transformation_matrix"])

        def bad_if(cond, what):
            if cond:
                bad.append(f"{tag}: {what}")

        bad_if(not np.all(np.isfinite(T)), "transform.json has a non-finite entry")
        bad_if(abs(np.linalg.det(T[:3, :3])) < 1e-12, "transform.json is singular")
        bad_if(rep.get("tool") != "scroll-lineup", f"report.json tool is {rep.get('tool')!r}")
        bad_if(not os.path.exists(os.path.join(d, "qc.png")), "no qc.png")
        bad_if(not close(rep["transform_moving_to_fixed_voxels_xyz"], ours["transformation_matrix"], 0),
               "report.json and transform.json disagree about the matrix")
        for b in rep["blocks"]:
            bad_if(not (b["n_used"] <= b["n_matched"] <= b["n_tried"]),
                   f"block round at {b['level_um']} um: used/matched/tried out of order")
            if "blocks" not in b:
                # an abandoned round: it says so, keeps no landmark list, and used nothing
                bad_if("status" not in b, f"block round at {b['level_um']} um: no blocks and no status")
                bad_if(b["n_used"] != 0, f"block round at {b['level_um']} um: no blocks listed but n_used {b['n_used']}")
                continue
            bad_if(len(b["blocks"]) != b["n_matched"] or len(b["used"]) != b["n_matched"],
                   f"block round at {b['level_um']} um: {len(b['blocks'])} blocks listed, n_matched {b['n_matched']}")
            bad_if(sum(b["used"]) != b["n_used"],
                   f"block round at {b['level_um']} um: {sum(b['used'])} kept by the mask, n_used {b['n_used']}")

        e = val["error"]
        bad_if(row[5] != f"{e['median_um']:.0f} / {e['p95_um']:.0f} / {e['max_um']:.0f}",
               f"error column {row[5]!r} != validation.json")
        bad_if(row[6] != verdict(e["p95_um"]), f"verdict {row[6]!r} does not follow the pre-registered rule")
        bad_if(row[4] != rep["confidence"]["level"], f"confidence column {row[4]!r} != report.json")
        g2 = rep["g2"]["results"]
        bad_if(row[3] != f"{g2[0]['score']:.2f} / {g2[1]['score']:.2f}", f"G2 column {row[3]!r} != report.json")
        bad_if(abs(rep["g2"]["margin"] - (g2[0]["score"] - g2[1]["score"])) > 1e-9,
               "g2.margin is not winner minus runner-up")
        bad_if(row[10] != str(rep["version"]), f"version column {row[10]!r} != report.json")
        bad_if(row[11] != f"{rep['seconds'] / 60:.1f}", f"minutes column {row[11]!r} != report.json")
        bad_if(row[12] != f"{rep['downloaded_MB']:.0f}", f"MB column {row[12]!r} != report.json")

        # the landmark columns, recomputed from the two committed matrices and the committed landmarks
        lm = val.get("landmarks")
        if lm:
            Lm = np.asarray(off["moving_landmarks"], float)
            Lf = np.asarray(off["fixed_landmarks"], float)
            um = val["fixed_um"]
            eo = np.linalg.norm(apply(T, Lm) - Lf, axis=1) * um
            ef = np.linalg.norm(apply(to4(off["transformation_matrix"]), Lm) - Lf, axis=1) * um
            bad_if(abs(float(np.sqrt((eo ** 2).mean())) - lm["ours_rms_um"]) > 1e-6,
                   "landmark RMS in validation.json is not what the committed matrices give")
            bad_if(abs(float(np.sqrt((ef ** 2).mean())) - lm["official_rms_um"]) > 1e-6,
                   "the official landmark RMS in validation.json is not what its own matrix gives")
            bad_if(row[7] != f"{lm['ours_rms_um']:.0f} / {lm['official_rms_um']:.0f} (n={lm['n']})",
                   f"landmark column {row[7]!r} != validation.json")
            bad_if(len(off["moving_landmarks"]) != lm["n"], "landmark count disagrees with the committed landmarks")
        else:
            bad_if(row[7] != "-", f"landmark column {row[7]!r} where validation.json has no landmarks")
            bad_if(len(off["moving_landmarks"]) != 0,
                   "validation.json has no landmarks but official_transform.json publishes some")

        # the two held-out block columns, exactly as summarize.py formats them
        for col, fname in ((8, "datacheck_heldout.json"), (9, "datacheck_landmarks.json")):
            p = os.path.join(d, fname)
            if not os.path.exists(p):
                bad_if(row[col] != "-", f"{fname} is absent but the column says {row[col]!r}")
                continue
            r = json.load(open(p))["results"]
            o, f = r.get("ours", {}), r.get("official", {})
            if o.get("median_move_um") is None or f.get("median_move_um") is None:
                want = f"n={o.get('n_common', 0)}"
            else:
                want = f"{o['median_move_um']:.0f} / {f['median_move_um']:.0f} (n={o['n_common']})"
            bad_if(row[col] != want, f"{fname} column {row[col]!r} != {want!r}")

    check(f"every cell of {folder}/table.md is re-derived from the committed JSON ({len(tags)} runs)",
          not bad, "" if not bad else "\n       " + "\n       ".join(bad))


def test_example():
    print("C. the worked example")
    ex = os.path.join(ROOT, "examples", "pherc1203")
    T = to4(json.load(open(os.path.join(ex, "transform.json")))["transformation_matrix"])
    Ti = to4(json.load(open(os.path.join(ex, "transform_inverse.json")))["transformation_matrix"])
    P = np.random.default_rng(3).normal(0, 3000, (200, 3))
    check("the example's transform_inverse.json really is the inverse",
          close(apply(Ti, apply(T, P)), P, 1e-6),
          f"max round-trip error {np.max(np.abs(apply(Ti, apply(T, P)) - P)):.2e} moving voxels")
    rep = json.load(open(os.path.join(ex, "report.json")))
    check("the example's report.json carries the same matrix",
          close(rep["transform_moving_to_fixed_voxels_xyz"], T[:3], 0))
    b = rep["blocks"][-1]
    check("the example's final block round is self-consistent",
          b["n_used"] <= b["n_matched"] <= b["n_tried"] and len(b["blocks"]) == b["n_matched"]
          and sum(b["used"]) == b["n_used"],
          f"{b['n_tried']} tried, {b['n_matched']} matched, {b['n_used']} used")


def test_readme_table():
    """The README's own twelve-row table is hand-made from the generated one. This checks it did not
    drift: every row must match a row of results/table.md on the error triple, the verdict and the
    held-out pair."""
    print("C2. the README's table against the generated one")
    gen = parse_table(os.path.join(ROOT, "results", "table.md"))
    rows = []
    for line in open(os.path.join(ROOT, "README.md")):
        c = [x.strip() for x in line.strip().strip("|").split("|")]
        if len(c) == 5 and re.fullmatch(r"\d+ / \d+ / \d+", c[2] or ""):
            rows.append(c)
    check("the README table has twelve rows", len(rows) == 12, f"{len(rows)} found")
    bad = []
    for r in rows:
        match = [g for g in gen.values() if g[5] == r[2]]
        if len(match) != 1:
            bad.append(f"{r[0]}: error triple {r[2]!r} matches {len(match)} generated rows")
            continue
        g = match[0]
        if not r[3].startswith(g[6]):
            bad.append(f"{g[0]}: README verdict {r[3]!r} does not start with {g[6]!r}")
        if not g[8].startswith(r[4]):
            bad.append(f"{g[0]}: README held-out {r[4]!r} does not match {g[8]!r}")
    check("every README row agrees with results/table.md", not bad,
          "" if not bad else "\n       " + "\n       ".join(bad))


def test_cross_stack():
    """The same pairs re-run on a different Python and a different numpy/scipy, committed so the
    claim can be checked without running anything."""
    print("D. the same pair on a second software stack")
    base = os.path.join(ROOT, "robustness", "second_stack")
    tags = sorted(d for d in os.listdir(base) if os.path.isdir(os.path.join(base, d)))
    check("there is a second-stack transform for at least three pairs", len(tags) >= 3, f"{len(tags)} pairs")
    worst = 0.0
    bad = []
    for tag in tags:
        home = os.path.join(ROOT, "robustness", tag)
        if not os.path.isdir(home):
            home = os.path.join(ROOT, "results", tag)
        A = to4(json.load(open(os.path.join(home, "transform.json")))["transformation_matrix"])
        B = to4(json.load(open(os.path.join(base, tag, "transform.json")))["transformation_matrix"])
        rep = json.load(open(os.path.join(home, "report.json")))
        shp = np.array(rep["volumes"]["moving"]["shape"], float)[::-1]          # zyx -> xyz
        um = rep["volumes"]["fixed"]["um"]
        corners = np.array([[x, y, z] for x in (0, shp[0]) for y in (0, shp[1]) for z in (0, shp[2])])
        d = float(np.max(np.linalg.norm(apply(A, corners) - apply(B, corners), axis=1)) * um)
        worst = max(worst, d)
        if d > 0.01:
            bad.append(f"{tag}: {d:.4f} um")
    check("every pair agrees across the two stacks to better than 0.01 um",
          not bad, f"worst {worst:.6f} um" if not bad else "; ".join(bad))


def test_cli():
    print("E. the command line")
    py = sys.executable
    r = subprocess.run([py, os.path.join(ROOT, "scroll_lineup.py"), "--version"],
                       capture_output=True, text=True)
    check("--version prints the tool's name and version",
          r.returncode == 0 and r.stdout.strip() == f"scroll-lineup {VERSION}", r.stdout.strip())
    r = subprocess.run([py, os.path.join(ROOT, "scroll_lineup.py"), "--help"], capture_output=True, text=True)
    check("--help exits 0 and names the output option", r.returncode == 0 and "--out" in r.stdout)
    r = subprocess.run([py, os.path.join(ROOT, "scroll_lineup.py")], capture_output=True, text=True)
    check("no arguments is an error, not a crash", r.returncode != 0 and "usage:" in r.stderr.lower())


def test_audit():
    """The landmark audit's committed result must agree with the README and its own README.

    The audit reads the live catalogue, so it cannot be re-run here without the network. What CAN be
    checked offline is that the committed output, the table in the main README and the table in
    audit/README.md are the same four rows with the same numbers. That is the drift these tables
    would otherwise be free to have.
    """
    print("F. the landmark audit")
    res = os.path.join(ROOT, "audit", "results.txt")
    check("audit/results.txt is committed", os.path.exists(res))
    if not os.path.exists(res):
        return
    txt = open(res).read()
    m = re.search(r"(\d+) of (\d+) sit further than", txt)
    check("the audit states how many transforms it flagged", m is not None,
          m.group(0) if m else "")
    if not m:
        return
    n_flag, n_total = int(m.group(1)), int(m.group(2))
    check("four of twenty five are flagged", (n_flag, n_total) == (4, 25), f"{n_flag} of {n_total}")

    # every flagged RMS in the committed output must appear in both READMEs
    rms = sorted({round(float(x), 1) for x in
                  re.findall(r"RMS (\d+\.\d) um, worst", txt)}, reverse=True)
    check("the output lists one RMS per flagged transform", len(rms) == n_flag, str(rms))
    for doc in ("README.md", os.path.join("audit", "README.md")):
        body = open(os.path.join(ROOT, doc)).read()
        missing = [v for v in rms if f"{v}" not in body]
        check(f"{doc} quotes every flagged RMS", not missing, f"missing {missing}")


def test_depth():
    """The depth curve behind the alignment budget must match what the documents claim about it."""
    print("G. the depth measurement")
    p = os.path.join(ROOT, "depth", "ctl_curve.json")
    check("depth/ctl_curve.json is committed", os.path.exists(p))
    if not os.path.exists(p):
        return
    rows = json.load(open(p))["rows"]
    check("nine depth windows", len(rows) == 9, str(len(rows)))
    peak = max(rows, key=lambda r: r["auc_forward"])
    others = [r["auc_forward"] for r in rows if r is not peak]
    check("exactly one window reads, at AUC 0.877",
          round(peak["auc_forward"], 3) == 0.877, f"{peak['auc_forward']:.3f} at {peak['layers']}")
    check("every other window is under 0.60",
          max(others) < 0.60, f"worst other {max(others):.3f}")
    rev = max(r["auc_reverse"] for r in rows)
    check("reversed depth order never rises above 0.56 anywhere", rev < 0.56, f"{rev:.3f}")
    # the two numbers the budget quotes, one step either side of the peak
    order = sorted(rows, key=lambda r: r["start"])
    i = order.index(peak)
    for side, j in (("below", i - 1), ("above", i + 1)):
        if 0 <= j < len(order):
            v = round(order[j]["auc_forward"], 3)
            body = open(os.path.join(ROOT, "depth", "README.md")).read()
            check(f"depth/README quotes the window one step {side} ({v})", f"{v}" in body)


if __name__ == "__main__":
    test_geometry()
    test_committed("results", "pairs.txt")
    test_committed("robustness", "pairs_robustness.txt")
    test_example()
    test_readme_table()
    test_cross_stack()
    test_cli()
    test_audit()
    test_depth()
    print()
    if FAILED:
        print(f"{len(FAILED)} FAILED: " + "; ".join(FAILED))
        sys.exit(1)
    print("all offline checks passed")
