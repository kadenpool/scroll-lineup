"""Day 4 of the ink detection floor (PREREG amendment 3): choose every day-4 window on
the five PHerc0483B surfaces by day 3's fixed rules, on the arm-A renders (9.362 um), carry each to the arm-B renders
(the scan's own 8.64 um), and record both, before any model runs on them.

  python3 prep_day4.py [render.zarr ...]     # default: every render_segment_given.zarr under /kaggle/input
  -> day4/windows_day4.json beside this file

Each render is villa's vc_render_tifxyz output for one surface and arm: 31 planes along the normal, --flip-normals,
surface at plane 15. Arm A: --scale 0.92288 --slice-step 1.0835648, 9.362 um per pixel and per plane, 2806 px. Arm B:
--scale 1 --slice-step 1, 8.64 um, 3040 px. Planes [1, 29) are the 28-layer volume, so the surface is layer 14.
Rules (day 3's, unchanged, on arm A): cores 512 px inside 1024 px windows on a 64 px grid where the surface layer is
non-zero on at least 99 % of the core; whole windows on one surface do not overlap; at most 3 % of the surface layer
textureless (day 1's measure). All candidates of all surfaces are pooled and ordered by numpy seed 20260926; of the
windows that pass (at most 24 are taken), the first n are the targets and the next n the shams, n = min(12, half of
them); under 6 targets, day 4 is not run. Each chosen window is carried to arm B about its core's centre, times
9.362 / 8.64 (a 554 px core in a 1109 px window), must again be 99 % covered there, and its layer 14 must correlate with
arm A's at 0.5 or more; otherwise day 4 stops. Nothing here looks at any ink-model output.
"""
import glob, json, os, re, sys
import numpy as np, zarr
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "day4")
SEED, WIN, CORE, GRID = 20260926, 1024, 512, 64
N_TARGETS, FLAT_MAX, COVER, CORR_MIN = 12, 0.03, 0.99, 0.5
LAYERS28 = (1, 29)                         # render planes that form the 28-layer volume (surface: plane 15 = layer 14)
UM = {"a": 9.362, "b": 8.64}
CANVAS = {"a": 2806, "b": 3040}
R = UM["a"] / UM["b"]                      # arm-B pixels per arm-A pixel
CORE_B, WIN_B = int(CORE * R), int(WIN * R)   # 554 and 1109: the same physical sizes, inside the donor core when mapped


def arm_surface(path):
    m = re.search(r"pherc0483b-render-(a|b)-(s\d\d)\b", path)
    if not m:
        raise SystemExit("cannot tell which arm and surface %s is" % path)
    return m.group(1), m.group(2)


def level0_scale(p):
    """The render's own pixel size (um) on each axis, from its OME-Zarr metadata."""
    at = zarr.open_group(p, mode="r").attrs.asdict()
    ms = at.get("multiscales") or []
    for d in (ms[0].get("datasets", []) if ms else []):
        if d.get("path") in ("0", 0):
            for t in d.get("coordinateTransformations", []):
                if t.get("type") == "scale":
                    return [float(v) for v in t["scale"]]
    raise SystemExit("%s: no level-0 scale in its metadata" % p)


def flat_share(pl):
    """Day 1's measure: share of the layer whose local standard deviation over 9 px is under a quarter of its median."""
    pl = pl.astype(np.float32)
    m1, m2 = ndimage.uniform_filter(pl, 9), ndimage.uniform_filter(pl * pl, 9)
    ls = np.sqrt(np.maximum(m2 - m1 * m1, 0))
    return float((ls < 0.25 * np.median(ls)).mean())


def sheet(v):
    """Recorded for information only (the day-1 sheet rule does not apply on days 3 and 4)."""
    prof = ndimage.uniform_filter1d(v.reshape(v.shape[0], -1).mean(1).astype(np.float32), 3)
    pk = int(np.argmax(prof))
    return pk, float(prof[pk] - np.median(prof)), [round(float(p), 1) for p in prof]


def profile(v):
    return [round(float(p), 1) for p in ndimage.uniform_filter1d(v.reshape(v.shape[0], -1).mean(1).astype(np.float32), 3)]


def carry(core_a, H, W):
    """Arm-A core [y0, y1, x0, x1] to arm B: the same centre times R, a CORE_B core in a WIN_B window."""
    cy, cx = (core_a[0] + CORE / 2) * R, (core_a[2] + CORE / 2) * R
    y, x = int(round(cy - CORE_B / 2)), int(round(cx - CORE_B / 2))
    wy = min(max(int(round(cy - WIN_B / 2)), 0), H - WIN_B)
    wx = min(max(int(round(cx - WIN_B / 2)), 0), W - WIN_B)
    return [y, y + CORE_B, x, x + CORE_B], [wy, wy + WIN_B, wx, wx + WIN_B]


def corr_layer14(a_arr, core_a, b_arr, core_b):
    """Pearson r of arm A's surface layer on its core against arm B's, sampled at the same physical points."""
    la = np.asarray(a_arr[15, core_a[0]:core_a[1], core_a[2]:core_a[3]]).astype(np.float64)
    pad = 2
    y0, x0 = core_b[0] - pad, core_b[2] - pad
    lb = np.asarray(b_arr[15, max(y0, 0):core_b[1] + pad, max(x0, 0):core_b[3] + pad]).astype(np.float64)
    ii, jj = np.mgrid[0:CORE, 0:CORE].astype(np.float64)
    yb = (core_a[0] + ii + 0.5) * R - 0.5 - max(y0, 0)
    xb = (core_a[2] + jj + 0.5) * R - 0.5 - max(x0, 0)
    lbs = ndimage.map_coordinates(lb, [yb, xb], order=1, mode="nearest")
    return float(np.corrcoef(la.ravel(), lbs.ravel())[0, 1])


def main():
    paths = sys.argv[1:] or sorted(glob.glob("/kaggle/input/**/render_segment_given.zarr", recursive=True))
    if not paths:
        raise SystemExit("no renders found")
    surf = {"a": {}, "b": {}}
    for p in paths:
        arm, sid = arm_surface(p)
        a = zarr.open_array(os.path.join(p, "0"), mode="r")
        sc = level0_scale(p)
        if a.shape[0] != 31 or tuple(a.shape[1:]) != (CANVAS[arm], CANVAS[arm]):
            raise SystemExit("%s: shape %s, expected (31, %d, %d)" % (p, a.shape, CANVAS[arm], CANVAS[arm]))
        if max(abs(v - UM[arm]) for v in sc) > 0.001:
            raise SystemExit("%s: level-0 scale %s, expected %s um on every axis" % (p, sc, UM[arm]))
        surf[arm][sid] = {"path": p, "array": a, "shape": list(a.shape), "scale_um": sc}
    if sorted(surf["a"]) != sorted(surf["b"]) or len(surf["a"]) != 5:
        raise SystemExit("arms do not hold the same five surfaces: %s / %s" % (sorted(surf["a"]), sorted(surf["b"])))
    cands = []
    for sid in sorted(surf["a"]):
        a = surf["a"][sid]["array"]
        H, W = a.shape[1:]
        cov = (np.asarray(a[15]) > 0).astype(np.int64)
        ii = np.pad(cov.cumsum(0).cumsum(1), ((1, 0), (1, 0)))
        for y in range(0, H - CORE + 1, GRID):
            for x in range(0, W - CORE + 1, GRID):
                s = ii[y + CORE, x + CORE] - ii[y, x + CORE] - ii[y + CORE, x] + ii[y, x]
                if s >= COVER * CORE * CORE:
                    cands.append((sid, y, x))
    rng = np.random.default_rng(SEED)
    order = rng.permutation(len(cands))
    taken, chosen, log = {}, [], []
    for k in order:
        sid, y, x = cands[k]
        H, W = surf["a"][sid]["array"].shape[1:]
        wy = min(max(y + CORE // 2 - WIN // 2, 0), H - WIN)
        wx = min(max(x + CORE // 2 - WIN // 2, 0), W - WIN)
        if any(abs(wy - a) < WIN and abs(wx - b) < WIN for a, b in taken.get(sid, [])):
            continue
        v = np.asarray(surf["a"][sid]["array"][LAYERS28[0]:LAYERS28[1], y:y + CORE, x:x + CORE])
        fl = flat_share(v[14])
        pk, prom, prof = sheet(v)
        ok = fl <= FLAT_MAX
        log.append({"surface": sid, "core": [y, x], "flat_share": fl, "sheet_peak_info": pk, "prominence_info": prom,
                    "kept": ok})
        if not ok:
            continue
        taken.setdefault(sid, []).append((wy, wx))
        chosen.append({"surface": sid, "core": [y, y + CORE, x, x + CORE], "box": [wy, wy + WIN, wx, wx + WIN],
                       "flat_share": fl, "surface_layer": 14, "profile": prof})
        if len(chosen) == 2 * N_TARGETS:
            break
    n = min(N_TARGETS, len(chosen) // 2)          # fewer than 24 pass: split them evenly, n targets and n shams
    if n < 6:
        raise SystemExit("only %d windows pass; fewer than 6 targets with shams: day 4 is not run" % len(chosen))
    targets, shams = chosen[:n], chosen[n:2 * n]
    for rec in targets + shams:                   # carry to arm B, and check it shows the same papyrus
        b = surf["b"][rec["surface"]]["array"]
        HB, WB = b.shape[1:]
        core_b, box_b = carry(rec["core"], HB, WB)
        if core_b[0] < 0 or core_b[2] < 0 or core_b[1] > HB or core_b[3] > WB:
            raise SystemExit("%s %s: the arm-B core %s leaves the canvas: day 4 stops" % (rec["surface"], rec["core"], core_b))
        cov_b = float((np.asarray(b[15, core_b[0]:core_b[1], core_b[2]:core_b[3]]) > 0).mean())
        r = corr_layer14(surf["a"][rec["surface"]]["array"], rec["core"], b, core_b)
        rec.update({"core_b": core_b, "box_b": box_b, "coverage_b": cov_b, "corr_layer14_a_b": r,
                    "profile_b": profile(np.asarray(b[LAYERS28[0]:LAYERS28[1], core_b[0]:core_b[1], core_b[2]:core_b[3]]))})
        if cov_b < COVER or not r >= CORR_MIN:
            raise SystemExit("%s %s: arm-B coverage %.4f, layer-14 correlation %.3f: day 4 stops"
                             % (rec["surface"], rec["core"], cov_b, r))
    for i, t in enumerate(targets):
        t["name"] = "d4t%02d_%s" % (i, t["surface"])
        t["donor"] = i % 6
        t["sham"] = i
    info = {"prereg": "PREREG.md, amendment 3", "version": 4, "day": 4, "scroll": "PHerc0483B",
            "volume": "20251124083638", "seed": SEED, "window_px": WIN, "core_px": CORE, "grid_px": GRID,
            "arm_b": {"ratio": R, "core_px": CORE_B, "window_px": WIN_B, "corr_min": CORR_MIN},
            "um_per_px": UM, "layers28_from_render_planes": list(LAYERS28), "surface_layer": 14, "flat_max": FLAT_MAX,
            "coverage_min": COVER, "depth_shift": 0,
            "surfaces": {arm: {sid: {"path": os.path.relpath(v["path"], "/kaggle/input") if v["path"].startswith("/kaggle")
                                     else os.path.basename(os.path.dirname(os.path.dirname(v["path"]))),
                                     "shape": v["shape"], "scale_um": v["scale_um"]} for sid, v in surf[arm].items()}
                         for arm in ("a", "b")},
            "candidates": len(cands), "targets": targets, "shams": shams, "selection_log": log}
    os.makedirs(OUT, exist_ok=True)
    json.dump(info, open(os.path.join(OUT, "windows_day4.json"), "w"), indent=1)
    for t in targets:
        print(t["name"], t["core"][::2], "flat %.3f donor %d | arm B %s r %.3f" % (t["flat_share"], t["donor"],
                                                                              t["core_b"][::2], t["corr_layer14_a_b"]))
    print("shams:", [(s["surface"], s["core"][::2], round(s["corr_layer14_a_b"], 3)) for s in shams])
    print("surfaces:", {k: v["shape"] for k, v in surf["a"].items()}, "| candidates", len(cands), "| examined",
          len(log), "| kept", sum(1 for r in log if r["kept"]), "| n", n)


if __name__ == "__main__":
    main()
