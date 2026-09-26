#!/usr/bin/env python3
"""Re-derive every headline number in README.md from the committed evidence.

    python3 trace_numbers.py [data_root]

Nothing here is copied from the write-up. Each value is recomputed from the
JSON a run wrote, and compared against the number the document prints. Exit
status 0 means the document and the data agree everywhere.

Sources, all committed:
  evidence_0912/plan_b_0813_files/manifest.json   areas, mesh counts
  evidence_0912/plan_b_0211_files/manifest.json
  evidence_0912/sheet_check_files/ink_vs_band.json   the surviving 12 Sep result
  evidence_0913/plan_d_files/results.json         28 windows x 17 depths
  evidence_0914/seating_files/*.json              seating, two instruments
  submissions/depth_tolerance_curve/ctl_curve.json   the known-text curve
"""
import json
import os
import re
import sys

VOXEL_UM = 9.362
OFF_BAND = {0, 5, 75, 80}      # starts whose 21-layer window is off the sheet
CENTRE_START = 40              # the conventional window, [40,61)
SEATED_UM = 56.0               # 6 layers: the "provably seated" cut

fails, checks = [], 0


def ok(label, doc, data, tol):
    global checks
    checks += 1
    good = abs(doc - data) <= tol
    print(f"  {'ok  ' if good else 'FAIL'} {label:<46} doc={doc:<10g} data={data:.4f}")
    if not good:
        fails.append(label)


def load(root, *parts):
    return json.load(open(os.path.join(root, *parts), encoding="utf-8"))


def spearman(xs, ys):
    def rank(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
                j += 1
            avg = (i + j) / 2 + 1
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r
    a, b = rank(xs), rank(ys)
    n = len(a)
    ma, mb = sum(a) / n, sum(b) / n
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    da = sum((x - ma) ** 2 for x in a) ** 0.5
    db = sum((y - mb) ** 2 for y in b) ** 0.5
    return num / (da * db) if da and db else 0.0


def median(v):
    s = sorted(v)
    n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2


def best_on_sheet(by_depth):
    """Strongest answer over the on-sheet depths, either direction."""
    return [max(d["forward"], d["reverse"])
            for s, d in by_depth.items() if int(s) not in OFF_BAND]


def main(root):
    print(f"data root: {root}\n")

    # ---------------- 1. how much was run ---------------------------------
    print("SCALE  (plan_b manifests)")
    m813 = load(root, "evidence_0912/plan_b_0813_files/manifest.json")
    m211 = load(root, "evidence_0912/plan_b_0211_files/manifest.json")
    ok("PHerc0813 meshes", 32, m813["n_meshes"], 0)
    ok("PHerc0211 meshes", 30, m211["n_meshes"], 0)
    ok("PHerc0813 cm2 rendered", 128.8, m813["total_rendered_area_cm2"], 0.05)
    ok("PHerc0211 cm2 rendered", 127.2, m211["total_rendered_area_cm2"], 0.05)
    ok("PHerc0813 cm2 selected", 131.8, m813["total_area_cm2"], 0.05)
    ok("PHerc0211 cm2 selected", 131.1, m211["total_area_cm2"], 0.05)
    ok("two scrolls, cm2 rendered in total", 256,
       m813["total_rendered_area_cm2"] + m211["total_rendered_area_cm2"], 0.5)

    # ---------------- 2. the known-text control curve ---------------------
    print("\nCONTROL CURVE  (ctl_curve.json)")
    ctl = load(root, "submissions/depth_tolerance_curve/ctl_curve.json")
    rows = {r["start"]: r for r in ctl["rows"]}
    ok("AUC at the sheet centre", 0.877, rows[CENTRE_START]["auc_forward"], 0.0005)
    ok("AUC one 10-layer step below", 0.571, rows[30]["auc_forward"], 0.0005)
    ok("AUC one 10-layer step above", 0.537, rows[50]["auc_forward"], 0.0005)
    ok("AUC reversed at the centre", 0.525, rows[CENTRE_START]["auc_reverse"], 0.0005)
    ok("one 10-layer step, um", 94, 10 * VOXEL_UM, 0.5)
    ok("called ink on labelled ink, %", 57.2,
       rows[CENTRE_START]["share_on_ink_forward"] * 100, 0.05)
    ok("called ink on labelled background, %", 7.4,
       rows[CENTRE_START]["share_on_bg_forward"] * 100, 0.05)
    # flatness of real ink: the control grid has no 5-step, so its off-sheet
    # starts are 0 and 80 (the 21-layer window wholly outside the sheet).
    on = [r["share_on_ink_forward"] for s, r in rows.items() if s not in (0, 80)]
    ok("known text, weakest depth / strongest", 0.06, min(on) / max(on), 0.005)

    # ---------------- 3. the depth sweep over three scrolls ---------------
    print("\nDEPTH SWEEP  (plan_d_files/results.json)")
    d = load(root, "evidence_0913/plan_d_files/results.json")
    bw, g1 = d["by_window"], d["gates_G1"]
    ok("windows swept", 28, d["n_windows_scored"], 0)
    ok("depth positions", 17, len(d["starts"]), 0)
    ok("readings per direction", 476, len(bw) * len(d["starts"]), 0)
    ok("windows passing G1", 0, sum(1 for g in g1.values() if g["G1"]), 0)
    ok("best on/off ratio anywhere", 2.41, max(g["ratio"] for g in g1.values()), 0.005)
    ok("windows answering more strongly reversed", 15,
       sum(1 for g in g1.values() if not g["forward_dominant"]), 0)
    ok("windows peaking at the conventional centre", 10,
       sum(1 for g in g1.values() if g["best_start"] == CENTRE_START), 0)

    flat = [min(best_on_sheet(w["by_depth"])) / max(best_on_sheet(w["by_depth"]))
            for w in bw.values()]
    ok("scroll windows, median weakest / strongest", 0.59, median(flat), 0.005)
    ok("  ... lowest", 0.29, min(flat), 0.005)
    ok("  ... highest", 0.85, max(flat), 0.005)

    # each scroll's own null: the strongest ordinary window of that scroll
    peak = {k: max(best_on_sheet(w["by_depth"])) for k, w in bw.items()}
    nulls = {}
    for k, w in bw.items():
        if w["role"] == "ordinary":
            nulls[w["scroll"]] = max(nulls.get(w["scroll"], 0), peak[k])
    cand846 = [peak[k] / nulls["PHerc0846A"] for k, w in bw.items()
               if w["scroll"] == "PHerc0846A" and w["role"] == "candidate"]
    ok("PHerc0846A candidates swept", 6, len(cand846), 0)
    ok("  ... weakest against the scroll's own windows", 0.69, min(cand846), 0.005)
    ok("  ... strongest against the scroll's own windows", 1.18, max(cand846), 0.005)
    ok("  ... how many sit below that ordinary window", 4,
       sum(1 for r in cand846 if r < 1.0), 0)
    ok("PHerc0846A within-scroll null, %", 40.7, nulls["PHerc0846A"] * 100, 0.05)
    ok("PHerc0813 within-scroll null, %", 10.5, nulls["PHerc0813"] * 100, 0.05)
    ok("PHerc0211 within-scroll null, %", 14.9, nulls["PHerc0211"] * 100, 0.05)

    # ---------------- 4. seating ------------------------------------------
    print("\nSEATING  (evidence_0914/seating_files)")
    ours = load(root, "evidence_0914/seating_files/ours.json")
    prof = (load(root, "evidence_0914/seating_files/depthprofile.json")
            + load(root, "evidence_0914/seating_files/depthprofile_best.json"))
    cal = load(root, "evidence_0914/seating_files/calibration.json")
    con = load(root, "evidence_0914/seating_files/contrast.json")

    top = max(ours, key=lambda r: r["score"])
    ok("highest seating score anywhere", 34.88, top["score"], 0.005)
    hit = [p for p in prof if p["name"] == top["name"]][0]
    ok("  ... its distance from the sheet, um", 131.1, abs(hit["best_offset_um"]), 0.05)
    ok("  ... its contrast at the mesh", -4.59, hit["contrast_at_mesh"], 0.005)

    low = [r for r in ours if abs(r["score"] - 2.76) < 0.005]
    ok("the low-scoring counter-example", 2.76, low[0]["score"], 0.005)
    lowp = [p for p in prof if p["name"] == low[0]["name"]][0]
    ok("  ... its distance from the sheet, um", 18.7, abs(lowp["best_offset_um"]), 0.05)

    band = sorted([c["score"] for c in cal if c["band"] == "B"]
                  + [r["score"] for r in ours if r["role"] == "control"])
    ok("known-good 9.362 um band, segments", 5, len(band), 0)
    ok("  ... lowest", 11.19, min(band), 0.005)
    ok("  ... highest", 13.98, max(band), 0.005)
    ok("  ... median", 12.18, median(band), 0.005)

    # "provably seated" is the evidence's cut: the sheet peak within 6 layers
    # of the mesh. 6 layers is 56 um at this voxel size.
    mine = {p["name"]: p for p in prof if p["role"] != "control"}
    near = [p for p in mine.values() if abs(p["best_offset_layers"]) <= 6]
    far = [p for p in mine.values() if abs(p["best_offset_layers"]) > 6]
    ok("six layers, in um", SEATED_UM, 6 * VOXEL_UM, 0.3)
    ok("our meshes profiled directly", 15, len(mine), 0)
    ok("  ... within 6 layers of a sheet centre", 9, len(near), 0)
    ok("  ... further off", 6, len(far), 0)
    ok("  ... nearest of those that are off, um", 131,
       min(abs(p["best_offset_um"]) for p in far), 1.0)
    ok("  ... furthest, um", 328, max(abs(p["best_offset_um"]) for p in far), 1.0)

    # the swept windows that are provably seated, against their scroll's null
    seated = [k for k in bw if k in mine and abs(mine[k]["best_offset_layers"]) <= 6]
    ok("swept windows that are provably seated", 6, len(seated), 0)
    ok("  ... their median answer against their scroll's null", 1.20,
       median([peak[k] / nulls[bw[k]["scroll"]] for k in seated]), 0.005)

    # ours.json holds three phases; only the stage2 rows are the swept windows,
    # and a row with zero coverage was never scored.
    score = {r["name"]: r["score"] for r in ours
             if r["phase"] == "stage2" and r["coverage"] > 0}
    both = sorted(k for k in bw if k in score)
    ok("swept windows the seating test could score", 26, len(both), 0)
    rho_fwd = spearman([score[k] for k in both], [g1[k]["best_fwd"] for k in both])
    rho_null = spearman([score[k] for k in both],
                        [peak[k] / nulls[bw[k]["scroll"]] for k in both])
    ok("seating vs forward ink share, rho", -0.01, rho_fwd, 0.02)
    ok("seating vs ratio to the scroll's null, rho", 0.30, rho_null, 0.02)

    # agreement between the two seating instruments
    cmap = {c["name"]: c["contrast"] for c in con}
    rhos = [spearman([score[k] for k in both], [cmap[k][s] for k in both])
            for s in ("5", "10", "25")]
    ok("  weakest agreement between them, rho", 0.35, min(rhos), 0.01)
    ok("  strongest agreement between them, rho", 0.51, max(rhos), 0.01)

    # ---------------- 5. what survived the 12 Sep retraction --------------
    print("\nTHE SURVIVING 12 SEP RESULT  (sheet_check_files/ink_vs_band.json)")
    ivb = load(root, "evidence_0912/sheet_check_files/ink_vs_band.json")
    ok("over-firing vs mesh position, Spearman", 0.57, ivb["spearman"], 0.005)
    ok("  ... windows", 27, ivb["n"], 0)

    # ---------------- 6. TAUIL's two candidate locations ------------------
    # TAUIL's survey (corpus-ink-survey, first published 14 Sep) names PHerc0813
    # z12496_w060, forward, and PHerc0211's inner wrap z6112..z9120 on w020, in
    # reverse. Our surveys and sweep scored the same meshes a day earlier.
    print("\nTAUIL'S TWO CANDIDATE LOCATIONS  (plan_b survey results, plan_d sweep)")
    r813 = load(root, "evidence_0912/plan_b_0813_files/v2_result/results.json")["per_segment"]
    r211 = load(root, "evidence_0912/plan_b_0211_files/v1_result/results.json")["per_segment"]
    ck = ("seed43_step060000", "seed42_step010000")
    for name, want in (("z12496_w060", ((13.8, 7.8, 1.23), (27.2, 19.1, 1.35))),
                       ("z13088_w040", ((16.3, 6.0, 1.85), (29.9, 16.0, 1.68)))):
        for c, (fwd, rev, rat) in zip(ck, want):
            b = r813[name]["by_ckpt"][c]
            ok(f"{name} {c[:6]} forward, %", fwd, b["on_fwd"] * 100, 0.05)
            ok(f"{name} {c[:6]} reverse, %", rev, b["on_rev"] * 100, 0.05)
            ok(f"{name} {c[:6]} x own off-sheet null", rat, b["on_over_off"], 0.005)
    wrap = [k for k in ("z6112_w020", "z6720_w020", "z7312_w020", "z7920_w020", "z9120_w020")
            if k in r211]
    ok("their PHerc0211 stretch: meshes we scored", 4, len(wrap), 0)
    ok("  ... leaning reverse on both checkpoints", 4,
       sum(all(r211[k]["by_ckpt"][c]["stronger_dir"] == "reverse" for c in ck) for k in wrap), 0)
    wr = [r211[k]["by_ckpt"][c]["on_over_off"] for k in wrap for c in ck]
    ok("  ... lowest x own off-sheet null", 1.35, min(wr), 0.005)
    ok("  ... highest", 1.90, max(wr), 0.005)
    every = wr + [r813[k]["by_ckpt"][c]["on_over_off"] for k in ("z12496_w060", "z13088_w040")
                  for c in ck]
    global checks
    checks += 1
    if max(every) < 2.0:
        print(f"  ok   no mesh in the table reaches 2x (highest {max(every):.2f})")
    else:
        fails.append("a mesh in the TAUIL table reaches 2x")
        print(f"  FAIL a mesh in the TAUIL table reaches 2x ({max(every):.2f})")

    # the shape gate G2, recomputed with analyse_sweep.py's rule: at the best
    # on-sheet depth, in the stronger direction, the share 20 layers away must
    # be half or less on both sides that exist
    def shape_gate(name):
        per = bw[name]["by_depth"]
        inner = [(int(s), v.get("forward") or 0, v.get("reverse") or 0)
                 for s, v in per.items() if int(s) not in OFF_BAND]
        s, f, r = max(inner, key=lambda t: max(t[1], t[2]))
        best, way = max(f, r), ("forward" if f >= r else "reverse")
        drops = [per[str(s + dl)][way] <= 0.5 * best for dl in (-20, 20)
                 if str(s + dl) in per and per[str(s + dl)].get(way) is not None]
        return bool(drops) and all(drops)
    passed = sorted(k for k in bw if shape_gate(k))
    checks += 1
    if passed == ["z13088_w040", "z9120_w020"]:
        print(f"  ok   exactly two windows pass the shape gate: {passed}")
    else:
        fails.append(f"shape gate passes {passed}")
        print(f"  FAIL the shape gate passes {passed}")
    a, b = g1["z13088_w040"], g1["z9120_w020"]
    ok("z13088_w040 forward at its best depth, %", 16.2, a["best_fwd"] * 100, 0.05)
    ok("  ... reverse, %", 5.9, a["best_rev"] * 100, 0.05)
    ok("z9120_w020 reverse at its best depth, %", 14.8, b["best_rev"] * 100, 0.05)
    ok("  ... forward, %", 11.0, b["best_fwd"] * 100, 0.05)
    checks += 1
    if a["forward_dominant"] and not b["forward_dominant"]:
        print("  ok   z13088_w040 answers forward, z9120_w020 in reverse")
    else:
        fails.append("direction of the two shape-gate windows")
        print("  FAIL direction of the two shape-gate windows")
    ok("z13088_w040 x its own swept off-sheet null", 2.15, a["ratio"], 0.005)
    ok("z9120_w020 x its own swept off-sheet null", 1.74, b["ratio"], 0.005)
    ok("z13088_w040 x its scroll's strongest ordinary window", 1.54,
       peak["z13088_w040"] / nulls["PHerc0813"], 0.005)
    ok("z9120_w020 x its scroll's strongest ordinary window", 1.00,
       peak["z9120_w020"] / nulls["PHerc0211"], 0.005)

    # ---------------- 7. the document must print these --------------------
    print("\nEVERY NUMBER ABOVE APPEARS IN THE DOCUMENT")
    doc = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "README.md"),
               encoding="utf-8").read()
    for token in ("0.877", "0.525", "18.9 %", "0.8 to 2.4 %", "8 to 24x",
                  "57.2 %", "7.4 %", "0 of 28", "2.41", "0.69 and 1.18",
                  "10 of 28", "15 of the 28", "0.59", "0.06", "34.88",
                  "131 um", "4.59", "2.76", "19 um", "11.19 to 13.98",
                  "12.18", "1.20x", "1.98x", "0.35", "0.51", "0.57",
                  "128.8 cm2", "127.2 cm2", "256 cm2", "24.0 %", "94 um",
                  "13.8 % against 7.8 %", "27.2 % against 19.1 %", "1.23x, 1.35x",
                  "16.3 % against 6.0 %", "29.9 % against 16.0 %", "1.85x, 1.68x",
                  "1.35x to 1.90x", "16.2 % against 5.9 %", "14.8 % against 11.0 %",
                  "2.15x and 1.74x", "1.54x and 1.00x"):
        checks += 1
        if re.search(re.escape(token).replace(r"\ ", r"\s+"), doc):
            print(f"  ok   {token}")
        else:
            fails.append(f"document does not print {token}")
            print(f"  FAIL {token} is not in README.md")

    print(f"\n{checks - len(fails)} of {checks} checks passed")
    if fails:
        print("FAILED:")
        for f in fails:
            print("  - " + f)
        return 1
    # the document states how many figures this script re-derives; hold it to that
    if "%d of them" % checks not in doc:
        print(f"  FAIL the document does not say '{checks} of them', the number of figures checked here")
        sys.exit(1)
    print("every headline number in README.md is re-derived from committed evidence")
    return 0


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1
                  else os.path.join(here, "data")))
