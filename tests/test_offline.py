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
  H.  The two published copies of each transform: counts, the differing pair's numbers, and agreement
      with the landmark audit, all re-derived from audit/copies.txt.
  I.  The reading test in downstream/: every row, difference, interval and depth figure in its README
      re-derived from its committed files, and its transforms checked against the committed ones.

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


def audit_rows():
    """Every row of audit/results.txt, read BY COLUMN POSITION from its header.

    Never by regex match: a pattern that fails to find the cell it wants does not error, it matches
    a different cell. That mistake has already produced a wrong number in this repository once.
    """
    lines = [l.rstrip("\n") for l in open(os.path.join(ROOT, "audit", "results.txt")) if l.startswith("|")]
    hdr = [c.strip() for c in lines[0].strip("|").split("|")]
    idx = {h.lower(): i for i, h in enumerate(hdr)}
    i_obj = next(i for h, i in idx.items() if h.startswith("object"))
    i_pair = next(i for h, i in idx.items() if "moving" in h)
    i_rms = next(i for h, i in idx.items() if h.startswith("rms"))
    i_worst = next(i for h, i in idx.items() if h.startswith("worst"))
    i_best = next((i for h, i in idx.items() if h.startswith("best affine")), None)
    out = []
    for l in lines[2:]:
        c = [x.strip() for x in l.strip("|").split("|")]
        if len(c) <= i_worst:
            continue
        clean = lambda s: s.replace("**", "").strip()
        out.append(dict(obj=clean(c[i_obj]), pair=clean(c[i_pair]),
                        rms=float(clean(c[i_rms])), worst=float(clean(c[i_worst])),
                        best=float(clean(c[i_best])) if i_best is not None and len(c) > i_best else None))
    return out


def test_audit():
    """The audit's numbers must be RE-DERIVED from its committed output, not compared to constants.

    An earlier version of this test asserted against values typed into the test itself. A reviewer
    planted eight false numbers in the documents, including swapped scroll names and an invented
    extra row, and every check still passed. Nothing below is allowed to know an answer in advance:
    the counts, the range and the flagged set all come out of results.txt, and the documents are
    then required to agree with what came out.
    """
    print("F. the landmark audit")
    res = os.path.join(ROOT, "audit", "results.txt")
    check("audit/results.txt is committed", os.path.exists(res))
    if not os.path.exists(res):
        return
    rows = audit_rows()
    txt = open(res).read()

    # the threshold the audit itself declares, taken from its own output
    m = re.search(r"sit further than (\d+) um", txt)
    check("the output states its own threshold", m is not None)
    if not m:
        return
    thr = float(m.group(1))

    flagged = sorted([r for r in rows if r["rms"] > thr], key=lambda r: -r["rms"])
    rest = [r["rms"] for r in rows if r["rms"] <= thr]

    # the output's own summary line must match the rows above it in the same file
    m2 = re.search(r"(\d+) of (\d+) sit further than", txt)
    check("the summary line matches the rows in the same file",
          m2 and (int(m2.group(1)), int(m2.group(2))) == (len(flagged), len(rows)),
          f"says {m2.group(0) if m2 else '?'}, rows give {len(flagged)} of {len(rows)}")

    # both documents must reproduce the flagged set exactly: object, pair and RMS on one line
    for doc in ("README.md", os.path.join("audit", "README.md")):
        body = open(os.path.join(ROOT, doc)).read()
        bad = []
        norm = lambda s: s.replace("->", "to").replace("  ", " ")
        for r in flagged:
            pair = norm(r["pair"])
            hit = [l for l in body.splitlines()
                   if r["obj"] in l and f"{r['rms']:.1f}" in l and pair in norm(l)]
            if not hit:
                bad.append(f"{r['obj']} {pair} {r['rms']:.1f}")
        check(f"{doc} carries each flagged row with its own object and value", not bad, str(bad))

    # the prose counts, derived rather than assumed
    for doc in (os.path.join("audit", "README.md"),):
        body = open(os.path.join(ROOT, doc)).read()
        words = {11: "eleven", 12: "twelve", 13: "thirteen", 14: "fourteen", 15: "fifteen",
                 16: "sixteen", 17: "seventeen"}
        n_under = len([v for v in rest if v < 10])
        w = words.get(n_under, str(n_under))
        check(f"{doc} states the right count under 10 um ({n_under})",
              w in body or str(n_under) in body, f"expected '{w}'")
        span = f"{min(rest):.1f} and {max(rest):.1f}"
        check(f"{doc} states the right range for the unflagged", span in body,
              f"expected '{span}'")
        check(f"{doc} states the right number of unflagged rows ({len(rest)})",
              f"other {len(rest)} " in body or f"The other {len(rest)}" in body)

    # and the honest comparison: this tool is worse on most pairs, so the documents must say so
    ours_better, official_better, nolm = 0, 0, 0
    for folder in ("results", "robustness", "coverage"):
        tbl = os.path.join(ROOT, folder, "table.md")
        if not os.path.exists(tbl):
            continue
        lines = [l for l in open(tbl) if l.startswith("|")]
        hdr = [c.strip().lower() for c in lines[0].strip("|").split("|")]
        i_lm = next((i for i, h in enumerate(hdr) if "at official landmarks" in h), None)
        if i_lm is None:
            continue
        for l in lines[2:]:
            c = [x.strip() for x in l.strip("|").split("|")]
            mm = re.match(r"^([\d.]+) / ([\d.]+) \(n=(\d+)\)$", c[i_lm]) if len(c) > i_lm else None
            if not mm or int(mm.group(3)) == 0:
                nolm += 1
                continue
            a, b = float(mm.group(1)), float(mm.group(2))
            if a < b:
                ours_better += 1
            elif a > b:
                official_better += 1
    check("the tool loses the landmark comparison on most pairs, as the documents must admit",
          official_better > ours_better, f"ours {ours_better}, official {official_better}, no data {nolm}")
    # the count has to be bound to the claim it belongs to: an earlier version of this check passed
    # on any "19 of the" anywhere in the README, and so missed that the sentence said 21 pairs
    # publish landmarks when 20 of those did, and that it left out the five coverage pairs
    n_lm = ours_better + official_better
    n_all = n_lm + nolm
    for doc in ("README.md", os.path.join("audit", "README.md")):
        flat = " ".join(open(os.path.join(ROOT, doc)).read().replace("**", "").split())
        check(f"{doc} states the tool is worse on {official_better} of the {n_lm} pairs with landmarks",
              f"worse than the official transform on {official_better} of the {n_lm} pairs" in flat
              or (f"on {ours_better} of the {n_lm} pairs" in flat and f"worse on the other {official_better}" in flat))
        stated = sorted(set(re.findall(r"of the (\d+) pairs that publish", flat)))
        check(f"{doc}: every 'of the N pairs that publish' uses the real N ({n_lm})",
              stated == [str(n_lm)], f"found {stated}")
    # the best-affine column: the counts in the file and in both documents must be its own rows
    rows_b = [r for r in audit_rows() if r["best"] is not None]
    check("every row carries a best-affine figure", len(rows_b) == len(audit_rows()),
          f"{len(rows_b)} of {len(audit_rows())}")
    if rows_b:
        thr = float(re.search(r"to within (\d+) um", txt).group(1))
        at_limit = [r for r in rows_b if r["rms"] - r["best"] <= thr]
        fixable = [r for r in rows_b if r["rms"] - r["best"] > thr]
        check("the file's own 'already are the least-squares affine' count is its rows",
              f"{len(at_limit)} of {len(rows_b)} published matrices already are" in txt,
              f"{len(at_limit)} of {len(rows_b)}")
        check("exactly one published matrix is not that fit", len(fixable) == 1, str(len(fixable)))
        for doc in ("README.md", os.path.join("audit", "README.md")):
            body = " ".join(open(os.path.join(ROOT, doc)).read().split())
            check(f"{doc} states the split", f"For {len(at_limit)} of the {len(rows_b)}" in body)
            for r in fixable:
                check(f"{doc} carries the fixable pair's own two numbers",
                      f"{r['rms']:.1f} um" in body and f"{r['best']:.1f} um" in body,
                      f"{r['rms']:.1f} / {r['best']:.1f}")
        # a matrix that is not the best fit must be far from it, or the split means nothing
        for r in fixable:
            check(f"{r['obj']} {r['pair']}: the gap is large, not marginal", r["rms"] - r["best"] > 5 * thr,
                  f"{r['rms'] - r['best']:.1f} um")

    flat = " ".join(open(os.path.join(ROOT, "README.md")).read().split())
    check(f"README's context paragraph counts all {n_all} pairs",
          f"the only pair of the {n_all} where our" in flat and f"On {official_better} of the others" in flat)


def test_depth():
    """The depth claims must be re-derived from ctl_curve.json, not compared to constants."""
    print("G. the depth measurement")
    p = os.path.join(ROOT, "depth", "ctl_curve.json")
    check("depth/ctl_curve.json is committed", os.path.exists(p))
    if not os.path.exists(p):
        return
    data = json.load(open(p))
    rows = sorted(data["rows"], key=lambda r: r["start"])
    body = open(os.path.join(ROOT, "depth", "README.md")).read()

    # every row must appear in the document, with its own window and both its own AUCs
    missing = []
    for r in rows:
        lo, hi = r["layers"]
        want = [f"{lo} to {hi}", f"{r['auc_forward']:.3f}", f"{r['auc_reverse']:.3f}"]
        if not any(all(w in line for w in want) for line in body.splitlines()):
            missing.append(f"{lo}-{hi}")
    check("depth/README reproduces every row of the committed curve", not missing, str(missing))

    peak = max(rows, key=lambda r: r["auc_forward"])
    others = [r["auc_forward"] for r in rows if r is not peak]
    revs = [r["auc_reverse"] for r in rows]
    check("exactly one window stands clear of the rest",
          peak["auc_forward"] - max(others) > 0.25,
          f"peak {peak['auc_forward']:.3f} at {peak['layers']}, next {max(others):.3f}")
    check("the reverse arm never reaches the peak", max(revs) < peak["auc_forward"] - 0.25,
          f"reverse max {max(revs):.3f}")
    # the document must not overstate the off-peak band: state the real spread
    check("depth/README states the real off-peak range",
          f"{min(others):.3f}" in body and f"{max(others):.3f}" in body,
          f"expected {min(others):.3f} and {max(others):.3f}")
    check("depth/README states the real reverse maximum", f"{max(revs):.3f}" in body,
          f"expected {max(revs):.3f}")

    # any gate shipped in the data file has to be documented, or it is a hidden bar
    if "G0" in data:
        check("the gate shipped in ctl_curve.json is documented in depth/README",
              "G0" in body, "ctl_curve.json carries a G0 gate that the README does not mention")


def test_copies():
    """The two-copy finding must be re-derived from audit/copies.txt, and must agree with the audit.

    Same rule as test_audit: nothing here knows an answer in advance. Counts come from the table
    rows, the differing pair's numbers come from its own detail block, and the catalogue column is
    required to match audit/results.txt row for row, since two scripts reading one catalogue should
    get one answer.
    """
    print("H. the two published copies of each transform")
    p = os.path.join(ROOT, "audit", "copies.txt")
    check("audit/copies.txt is committed", os.path.exists(p))
    if not os.path.exists(p):
        return
    txt = open(p).read()
    lines = [l.rstrip("\n") for l in txt.splitlines() if l.startswith("|")]
    hdr = [c.strip().lower() for c in lines[0].strip("|").split("|")]
    i_obj = next(i for i, h in enumerate(hdr) if h.startswith("object"))
    i_pair = next(i for i, h in enumerate(hdr) if "moving" in h)
    i_stat = next(i for i, h in enumerate(hdr) if h.startswith("per-volume"))
    i_cat = next(i for i, h in enumerate(hdr) if h.startswith("catalogue fit"))
    i_cp = next(i for i, h in enumerate(hdr) if h.startswith("copy fit"))
    clean = lambda s: s.replace("**", "").strip()
    rows = []
    for l in lines[2:]:
        c = [clean(x) for x in l.strip("|").split("|")]
        if len(c) > i_cp:
            rows.append(dict(obj=c[i_obj], pair=c[i_pair], status=c[i_stat], cat=c[i_cat], copy=c[i_cp]))

    have = [r for r in rows if r["status"] != "no per-volume copy"]
    diff = [r for r in have if r["status"] == "DIFFERS"]
    ident = [r for r in have if r["status"] == "identical"]
    check("every row with a copy is either identical or DIFFERS", len(ident) + len(diff) == len(have),
          str(sorted({r["status"] for r in have})))
    said = [int(x) for x in re.findall(r":\s*(\d+)\s*$", txt.split("|")[0], re.M)]
    check("the summary lines match the rows in the same file",
          said == [len(rows), len(have), len(ident), len(diff)],
          f"says {said}, rows give {[len(rows), len(have), len(ident), len(diff)]}")
    # an identical copy must fit exactly as the catalogue does, or 'identical' is not true
    bad = [f"{r['obj']} {r['pair']}" for r in ident if r["cat"] != r["copy"]]
    check("every copy marked identical fits exactly as the catalogue copy does", not bad, str(bad))

    # the catalogue column must be the landmark audit, row for row
    audit = sorted((r["obj"], r["pair"], f"{r['rms']:.1f}") for r in audit_rows())
    here = sorted((r["obj"], r["pair"], r["cat"]) for r in rows if r["cat"] != "-")
    check("the catalogue fits here are exactly the landmark audit's", audit == here,
          f"{len(audit)} rows in results.txt, {len(here)} here")

    # the documents must carry the counts and the differing pair's own numbers
    flat = lambda doc: " ".join(open(os.path.join(ROOT, doc)).read().split())
    aud, top, val = flat(os.path.join("audit", "README.md")), flat("README.md"), flat("VALIDATION.md")
    check("audit/README states the copy counts",
          f"{len(have)} also have a per-volume copy; {len(ident)} are identical" in aud)
    check("README states the copy counts",
          f"{len(have)} of the {len(rows)} transforms" in top and f"{len(ident)} match the catalogue" in top)
    check("VALIDATION states the copy counts",
          f"{len(have)} per-volume copies exist; {len(ident)} match" in val)

    thr = float(re.search(r"sit further than (\d+) um", open(os.path.join(ROOT, "audit", "results.txt")).read()).group(1))
    blocks = txt.split("\n\n")
    for r in diff:
        blk = next((b for b in blocks if b.startswith(r["obj"] + " ") and r["pair"] + " um" in b), "")
        cat = re.search(r"catalogue copy : (\d+) landmarks, RMS ([\d.]+) um, median ([\d.]+)", blk)
        cpy = re.search(r"per-volume copy: (\d+) landmarks, RMS ([\d.]+) um, median ([\d.]+)", blk)
        inv = re.search(r"other way .*?RMS ([\d.]+) um", blk)
        check(f"{r['obj']} {r['pair']}: the detail block is complete", bool(cat and cpy and inv))
        if not (cat and cpy and inv):
            continue
        check(f"{r['obj']}: the table and the detail block agree",
              (r["cat"], r["copy"]) == (cat.group(2), cpy.group(2)))
        for label, m in (("catalogue", cat), ("per-volume", cpy)):
            n, rms, med = m.groups()
            hit = [l for l in open(os.path.join(ROOT, "audit", "README.md")).read().splitlines()
                   if label in l and f"| {n} |" in l and rms in l and med in l]
            check(f"audit/README carries the {label} copy's own landmarks, RMS and median", bool(hit),
                  f"expected {n} / {rms} / {med}")
        c_rms, v_rms, i_rms = float(cat.group(2)), float(cpy.group(2)), float(inv.group(1))
        # 'it is not simply stored backwards' needs the inverse reading to miss too, and by far more
        # than the audit's own threshold
        check("the inverse reading also misses, so 'not stored backwards' holds",
              i_rms - c_rms > thr, f"inverse {i_rms}, catalogue {c_rms}, threshold {thr}")
        check("audit/README states the inverse result", f"{i_rms:.1f}" in aud)
        k = round(v_rms / c_rms)
        check(f"audit/README's 'about {k} times' is the real ratio ({v_rms / c_rms:.2f})",
              f"about {k} times" in aud)
        check("README carries both fits for the differing pair",
              f"{v_rms:.1f}" in top and f"{c_rms:.1f}" in top)

    # no document may call a reference sound when the audit counts it as a miss. Two did, for
    # coverage/x3_Paris4, whose catalogue copy misses its own landmarks by 35.1 um, until 20 Sep 2026
    runs = []
    for folder in ("results", "robustness", "coverage"):
        for name in sorted(os.listdir(os.path.join(ROOT, folder))):
            v = os.path.join(ROOT, folder, name, "validation.json")
            if os.path.exists(v) and ((json.load(open(v)).get("landmarks") or {}).get("official_rms_um") or 0) > thr:
                runs.append(name)
    check("some committed run is compared against a flagged reference", bool(runs))
    for d in ("README.md", os.path.join("docs", "method.md"), "VALIDATION.md"):
        paras = open(os.path.join(ROOT, d)).read().split("\n\n")
        bad = sorted({n for n in runs for p in paras if n in p and re.search(r"\bsound\b", p)})
        check(f"{d} calls no flagged reference sound", not bad, str(bad))


def test_image_quality_paragraph_matches_its_data():
    """The last-0.016 paragraph is re-derived from downstream/image_quality.json, not typed in.

    It used to say the gap was not explained. It now makes four quantitative claims, and each one
    has to come back out of the measurement file or this fails.
    """
    q = json.load(open(os.path.join(ROOT, "downstream", "image_quality.json")))
    a, t = q["arms"], q["pyramid_level_test"]
    text = open(os.path.join(ROOT, "downstream", "README.md")).read()

    assert "is not explained here" not in text, "the paragraph still says the gap is unexplained"

    ours, theirs = a["ours_theirmesh"], a["challenge_input"]
    assert "%.2f grey levels here against %.2f" % (ours["class_gap"], theirs["class_gap"]) in text
    assert "d %.3f to d %.3f" % (theirs["cohens_d"], ours["cohens_d"]) in text

    ours_sd = (ours["ink_std"] + ours["notink_std"]) / 2
    their_sd = (theirs["ink_std"] + theirs["notink_std"]) / 2
    wider = 100 * (ours_sd / their_sd - 1)
    assert "%.1f %% wider here" % wider in text, "the spread figure does not match the data"

    sharper = 100 * (t["sharpness_ratio_B_over_A"] - 1)
    assert "%.0f %%\nsharper" % sharper in text or "%.0f %% sharper" % sharper in text
    assert "%.3f AUC worse" % abs(t["raw_auc_B_minus_A"]) in text

    # the direction is the whole point: sharper AND worse at separating ink
    assert t["sharpness_ratio_B_over_A"] > 1, "B was supposed to be the sharper one"
    assert t["raw_auc_B_minus_A"] < 0, "B was supposed to separate ink worse"
    assert "rejected" in t["verdict"]

    # and the claim that no signal is lost: the class gaps must really be close
    assert abs(ours["class_gap"] - theirs["class_gap"]) < 0.5, (
        "the class gaps are no longer close, so 'no ink signal is being lost' is wrong")


def test_downstream():
    """The reading test: every number in downstream/README.md re-derived from its committed files.

    Same rule as the audit and depth parts: the documents are required to agree with the data, and
    each ordering or difference the prose states is computed here rather than trusted.
    """
    print("I. the downstream reading test")
    D = os.path.join(ROOT, "downstream")
    p = os.path.join(D, "results.json")
    check("downstream/results.json is committed", os.path.exists(p))
    if not os.path.exists(p):
        return
    res = json.load(open(p))
    blk = json.load(open(os.path.join(D, "per_block.json")))
    dmaps = json.load(open(os.path.join(D, "depth_maps.json")))
    flat = lambda path: " ".join(open(path).read().split())
    doc = flat(os.path.join(D, "README.md"))
    top = flat(os.path.join(ROOT, "README.md"))
    doc_lines = open(os.path.join(D, "README.md")).read().splitlines()
    arms = res["arms"]

    # the three rendered arms: peak must be the centre window, and its row must carry its own numbers
    rendered = {"official": "the official transform | this folder", "v6_0139c": "v6_0139c", "v2_0139a": "v2_0139a"}
    for tag, key in rendered.items():
        a = arms[tag]
        # the stored peak is a convenience; the curve is the record, so derive the peak from it
        derived = max(a["curve"], key=lambda r: r["auc_forward"])
        check(f"{tag}: the stored peak is the curve's maximum", derived == a["peak"],
              f"curve max {derived['layers']} {derived['auc_forward']:.4f}, stored {a['peak']['auc_forward']:.4f}")
        a = dict(a, peak=derived)
        arms[tag] = a
        check(f"{tag} peaks at the centre window", a["peak"]["layers"] == [40, 61], str(a["peak"]["layers"]))
        want = [f"{a['peak']['auc_forward']:.3f}", f"{a['peak']['auc_reverse']:.3f}",
                f"{100 * a['peak']['share_on_ink_forward']:.1f} %", f"{100 * a['peak']['share_on_bg_forward']:.1f} %"]
        hit = [l for l in doc_lines if l.startswith("|") and key in l and all(w in l for w in want)]
        check(f"downstream/README's {tag} row carries its own four numbers", bool(hit), str(want))
        check(f"{tag} registers within 1 px in every sub-window", a["registration"]["worst_subwindow_px"] <= 1)
        if a.get("graded"):
            check(f"{tag}'s grade in results.json matches results/table.md",
                  a["graded"]["error_median_p95_max_um"] in open(os.path.join(ROOT, "results", "table.md")).read())
            check(f"downstream/README states {tag}'s grade", a["graded"]["error_median_p95_max_um"] in doc)
    al = arms["aligned"]["centre"]
    want = [f"{al['auc_forward']:.3f}", f"{al['auc_reverse']:.3f}", f"{100 * al['share_on_ink_forward']:.1f} %",
            f"{100 * al['share_on_bg_forward']:.1f} %"]
    check("downstream/README's aligned row carries its own four numbers",
          any(l.startswith("|") and "the challenge (its own aligned input)" in l and all(x in l for x in want)
              for l in doc_lines), str(want))
    ctl = next(r for r in arms["ctl"]["curve"] if r["layers"][0] == 40)
    check("downstream/README quotes the no-transform control", f"reads {ctl['auc_forward']:.3f}" in doc)
    check("the validation pixel count is stated", f"{arms['aligned']['n_val_px']:,} pixels" in doc)

    # every ordering and difference the prose states, computed
    o, c, w = (arms[t]["peak"]["auc_forward"] for t in ("official", "v6_0139c", "v2_0139a"))
    check("the stated order holds: official > v6_0139c > v2_0139a", o > c > w, f"{o:.4f} {c:.4f} {w:.4f}")
    check("the render-path cost and both transform costs are the real differences",
          f"costs {al['auc_forward'] - o:.3f}" in doc and f"{o - c:.3f} and {o - w:.3f}" in doc)
    check("the v6/v2 AUC gap is the real one", f"only {c - w:.3f} lower" in doc)
    s6, s2 = arms["v6_0139c"]["peak"]["share_on_ink_forward"], arms["v2_0139a"]["peak"]["share_on_ink_forward"]
    check("'about half as much ink' is true", 0.4 < s2 / s6 < 0.6, f"{s2 / s6:.2f}")

    # the paired block tests
    for B, tag_ in ((64, "v6_0139c"), (96, "v6_0139c")):
        t = blk["paired_tests"][f"B{B}_{tag_}"]
        lo, hi = t["ci95"]
        phrase_n = f"{t['worse']} of {t['n_blocks']}"
        check(f"{B} px blocks: counts, p and interval as stated",
              phrase_n in doc and f"{t['sign_p']:.2f}" in doc and f"{lo:+.3f}".replace("+", "") in doc.replace("+", "")
              and f"{hi:+.3f}" in doc, f"{phrase_n}, p {t['sign_p']:.2f}, {lo:+.3f} to {hi:+.3f}")
    wh = blk["per_block_128px"]["whole"]
    check("whole-region AUCs on the label grid as stated",
          f"({wh['official']:.3f}, {wh['v6_0139c']:.3f}, {wh['v2_0139a']:.3f})" in doc)
    check("the label-grid AUCs agree with the render-frame ones to 0.002",
          all(abs(wh[t] - arms[t]["peak"]["auc_forward"]) < 0.002 for t in ("official", "v6_0139c", "v2_0139a")))

    # the depth maps table, re-derived
    for tag in ("v6_0139c", "v2_0139a"):
        m = dmaps[tag]
        off = np.array(m["offset_layers"], float) * m["um_per_layer"]
        pk = np.array(m["peak_ncc"], float)
        ok = np.isfinite(pk) & (pk >= 0.5)
        o_ = off[ok]
        row = [f"{int(ok.sum())} of {ok.size}", f"{np.median(o_):+.1f} um", f"{o_.min():+.0f} to {o_.max():+.0f} um",
               f"{np.percentile(np.abs(o_), 90):.0f} um"]
        hit = [l for l in doc_lines if l.startswith(f"| {tag} |") and all(x in l for x in row)]
        check(f"downstream/README's depth row for {tag} is the real one", bool(hit), str(row))
    o6 = np.array(dmaps["v6_0139c"]["offset_layers"], float) * dmaps["v6_0139c"]["um_per_layer"]
    check("the stated end-to-end tilt of v6_0139c is the real span", f"({o6.max() - o6.min():.0f} um)" in doc)

    # the transforms really are the inverses of committed ones
    for f, src in (("v6_0139c_9to2.json", "results/v6_0139c/transform.json"),
                   ("v2_0139a_9to2.json", "results/v2_0139a/transform.json"),
                   ("official_9to2.json", "results/v6_0139c/official_transform.json")):
        M = to4(np.array(json.load(open(os.path.join(ROOT, src)))["transformation_matrix"], float))
        A = np.array(json.load(open(os.path.join(D, "transforms", f)))["transformation_matrix"], float)
        check(f"transforms/{f} is the inverse of {src}", np.allclose(np.linalg.inv(M)[:3], A[:3], atol=1e-6))

    # the render-path decomposition added on 20 Sep: every arm's own peak, and the two new block tests
    doc_d = flat(os.path.join(D, "README.md"))
    doc_lines_d = open(os.path.join(D, "README.md")).read().splitlines()
    for tag, label in (("theirmesh", "the challenge's own 2.399 um mesh"),
                       ("official_bicubic", "villa #1818's smooth surface interpolation"),
                       ("aligned_nopool", "the 4-plane depth averaging removed")):
        a = arms.get(tag)
        check(f"{tag} is in results.json", a is not None)
        if a is None:
            continue
        v = (a.get("peak") or a.get("centre"))["auc_forward"]
        # the number must be on the arm's own row, not merely somewhere in the file: a wrong number
        # in the prose passed a bare "is it present" check on 20 Sep
        key = {"theirmesh": "48 um grid", "official_bicubic": "smooth surface interpolation",
               "aligned_nopool": "depth averaging removed"}[tag]
        row = [l for l in doc_lines_d if l.startswith("|") and key in l]
        check(f"downstream/README's {tag} row carries its own AUC", bool(row) and any(f"{v:.3f}" in l for l in row),
              f"{v:.3f} on a row mentioning {key!r}")
        sh = (a.get("peak") or a.get("centre")).get("share_on_ink_forward")
        if sh is not None:
            check(f"downstream/README's {tag} row carries its own ink share",
                  any(f"{100 * sh:.1f} %" in l for l in row), f"{100 * sh:.1f} %")
        if "peak" in a:
            check(f"{tag} peaks at the centre window", a["peak"]["layers"] == [40, 61], str(a["peak"]["layers"]))
            check(f"{tag} registers within 1 px in every sub-window", a["registration"]["worst_subwindow_px"] <= 1)
    # the gap arithmetic the prose states has to be the arithmetic of the file
    g_all = arms["aligned"]["centre"]["auc_forward"] - arms["official"]["peak"]["auc_forward"]
    g_mesh = arms["theirmesh"]["peak"]["auc_forward"] - arms["official"]["peak"]["auc_forward"]
    check("the '72 % of the gap' claim is this file's arithmetic",
          f"{round(100 * g_mesh / g_all)} % of the gap" in doc_d, f"{100 * g_mesh / g_all:.1f} %")
    # and the sentence that compares the two arms must carry BOTH numbers, in that order
    tm, of = arms["theirmesh"]["peak"], arms["official"]["peak"]
    check("the prose sentence compares the two arms with their own AUCs",
          f"reads **{tm['auc_forward']:.3f} against {of['auc_forward']:.3f}**" in doc_d,
          f"{tm['auc_forward']:.3f} against {of['auc_forward']:.3f}")
    check("and with their own ink shares",
          f"**{100 * tm['share_on_ink_forward']:.1f} % of the labelled ink against\n{100 * of['share_on_ink_forward']:.1f} %**"
          .replace("\n", " ") in doc_d,
          f"{100 * tm['share_on_ink_forward']:.1f} % against {100 * of['share_on_ink_forward']:.1f} %")
    check("the averaging arm really reads higher than the pooled one, as the prose says",
          arms["aligned_nopool"]["centre"]["auc_forward"] > arms["aligned"]["centre"]["auc_forward"])
    for key, expect_excludes_zero in (("B64_theirmesh", True), ("B64_official_bicubic", False)):
        t = blk["paired_tests"][key]
        lo, hi = t["ci95"]
        check(f"{key}: the interval in the README is this file's", f"{lo:.3f}" in doc_d and f"{hi:.3f}" in doc_d,
              f"{lo:.3f} to {hi:.3f}")
        check(f"{key}: excludes zero is {expect_excludes_zero}", (lo < 0 and hi < 0) == expect_excludes_zero,
              f"{lo:.3f} to {hi:.3f}")
        check(f"{key}: the block count and the worse count are stated",
              f"{t['worse']} of {t['n_blocks']}" in doc_d or f"{t['n_blocks'] - t['worse']} of {t['n_blocks']}" in doc_d,
              f"{t['worse']}/{t['n_blocks']}")

    # the main README's two new passages carry the same numbers
    check("README Limits carries the three arms and the interval",
          f"reads {o:.3f}" in top and f"transform {c:.3f}" in top and f"transform {w:.3f}" in top
          and f"{blk['paired_tests']['B64_v6_0139c']['ci95'][1]:+.3f}" in top and f"reads {al['auc_forward']:.3f}" in top)
    check("README budget note carries the v2 and official numbers",
          f"read {w:.3f} against the official transform's {o:.3f}" in top)
    # the budget's own page must carry the same qualification; it did not until 20 Sep 2026
    bud = flat(os.path.join(ROOT, "docs", "alignment-budget.md"))
    check("docs/alignment-budget.md carries the reading test's qualification",
          f"read {w:.3f} against the official transform's {o:.3f}" in bud and f"({c:.3f})" in bud
          and "downstream/" in bud)


if __name__ == "__main__":
    test_geometry()
    test_committed("results", "pairs.txt")
    test_committed("robustness", "pairs_robustness.txt")
    test_committed("coverage", "pairs_coverage.txt")
    test_example()
    test_readme_table()
    test_cross_stack()
    test_cli()
    test_audit()
    test_depth()
    test_copies()
    test_downstream()
    print()
    if FAILED:
        print(f"{len(FAILED)} FAILED: " + "; ".join(FAILED))
        sys.exit(1)
    print("all offline checks passed")
