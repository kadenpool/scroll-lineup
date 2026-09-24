"""Day 3 of the ink detection floor (PREREG amendment 1): choose every day-3 window on the seven PHerc0846B surfaces by
the fixed rules, before any model runs on them.

  python3 prep_day3.py [render.zarr ...]     # default: every render_segment_given.zarr under /kaggle/input
  -> day3/windows_day3.json beside this file

Each render is villa's vc_render_tifxyz output for one surface: 31 planes, one voxel apart, --flip-normals, surface at
plane 15. Planes [1, 29) are the 28-layer volume, so the surface is layer 14, as in PHerc0139's surface volumes.
Rules: cores 512 px inside 1024 px windows on a 64 px grid where the surface layer is non-zero on at least 99 % of the
core; whole windows do not overlap; at most 3 % of the surface layer textureless (day 1's measure). All candidates of
all surfaces are pooled and ordered by numpy seed 20260924; of the windows that pass (at most 24 are taken), the
first n are the targets and the next n the shams, n = min(12, half of them); under 6 targets, day 3 is not run. Nothing here looks at any ink-model output.
"""
import glob, json, os, re, sys
import numpy as np, zarr
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "day3")
SEED, WIN, CORE, GRID = 20260924, 1024, 512, 64
N_TARGETS, FLAT_MAX, COVER = 12, 0.03, 0.99
LAYERS28 = (1, 29)                         # render planes that form the 28-layer volume (surface: plane 15 = layer 14)


def surface_id(path):
    """s01 for the probe-2 render (kernel pherc0846b-render-1), sNN for pherc0846b-render-sNN."""
    m = re.search(r"pherc0846b-render-(s\d\d|1)\b", path)
    if m:
        return "s01" if m.group(1) == "1" else m.group(1)
    m = re.search(r"(s\d\d)", path)
    if not m:
        raise SystemExit("cannot tell which surface %s is" % path)
    return m.group(1)


def flat_share(pl):
    """Day 1's measure: share of the layer whose local standard deviation over 9 px is under a quarter of its median."""
    pl = pl.astype(np.float32)
    m1, m2 = ndimage.uniform_filter(pl, 9), ndimage.uniform_filter(pl * pl, 9)
    ls = np.sqrt(np.maximum(m2 - m1 * m1, 0))
    return float((ls < 0.25 * np.median(ls)).mean())


def sheet(v):
    """Recorded for information only (the day-1 sheet rule does not apply on day 3)."""
    prof = ndimage.uniform_filter1d(v.reshape(v.shape[0], -1).mean(1).astype(np.float32), 3)
    pk = int(np.argmax(prof))
    return pk, float(prof[pk] - np.median(prof)), [round(float(p), 1) for p in prof]


def main():
    paths = sys.argv[1:] or sorted(glob.glob("/kaggle/input/**/render_segment_given.zarr", recursive=True))
    if not paths:
        raise SystemExit("no renders found")
    surf = {}
    for p in paths:
        sid, p = (p.split("=", 1) if "=" in p else (surface_id(p), p))      # "s01=path" names a surface by hand
        a = zarr.open_array(os.path.join(p, "0"), mode="r")
        if a.shape[0] != 31:
            raise SystemExit("%s: %d planes, expected 31" % (p, a.shape[0]))
        surf[sid] = {"path": p, "array": a, "shape": list(a.shape)}
    cands = []
    for sid in sorted(surf):
        a = surf[sid]["array"]
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
        H, W = surf[sid]["array"].shape[1:]
        wy = min(max(y + CORE // 2 - WIN // 2, 0), H - WIN)
        wx = min(max(x + CORE // 2 - WIN // 2, 0), W - WIN)
        if any(abs(wy - a) < WIN and abs(wx - b) < WIN for a, b in taken.get(sid, [])):
            continue
        v = np.asarray(surf[sid]["array"][LAYERS28[0]:LAYERS28[1], y:y + CORE, x:x + CORE])
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
        raise SystemExit("only %d windows pass; fewer than 6 targets with shams: day 3 is not run" % len(chosen))
    targets, shams = chosen[:n], chosen[n:2 * n]
    for i, t in enumerate(targets):
        t["name"] = "d3t%02d_%s" % (i, t["surface"])
        t["donor"] = i % 6
        t["sham"] = i
    info = {"prereg": "PREREG.md, amendment 1", "version": 3, "day": 3, "scroll": "PHerc0846B",
            "volume": "20250804142305", "seed": SEED, "window_px": WIN, "core_px": CORE, "grid_px": GRID,
            "layers28_from_render_planes": list(LAYERS28), "surface_layer": 14, "flat_max": FLAT_MAX,
            "coverage_min": COVER, "depth_shift": 0,
            "surfaces": {sid: {"path": os.path.relpath(v["path"], "/kaggle/input") if v["path"].startswith("/kaggle")
                               else os.path.basename(os.path.dirname(os.path.dirname(v["path"]))),
                               "shape": v["shape"]} for sid, v in surf.items()},
            "candidates": len(cands), "targets": targets, "shams": shams, "selection_log": log}
    os.makedirs(OUT, exist_ok=True)
    json.dump(info, open(os.path.join(OUT, "windows_day3.json"), "w"), indent=1)
    for t in targets:
        print(t["name"], t["core"][::2], "flat %.3f donor %d" % (t["flat_share"], t["donor"]))
    print("shams:", [(s["surface"], s["core"][::2]) for s in shams])
    print("surfaces:", {k: v["shape"] for k, v in surf.items()}, "| candidates", len(cands), "| examined", len(log),
          "| kept", sum(1 for r in log if r["kept"]))


if __name__ == "__main__":
    main()
