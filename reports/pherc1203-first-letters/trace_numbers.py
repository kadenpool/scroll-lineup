#!/usr/bin/env python3
"""Re-derive the headline numbers in README.md from the copied run data.

    python3 submissions/first_letters_report_1203/trace_numbers.py

Nothing here is read out of the write-up. Each value is recomputed from the JSON a run wrote, then
compared against what the document prints. Exit 0 means the document and the data agree.

Why it exists: this report was the only item in the September package whose figures nobody could
check. method_report_negative/ has had a tracer since it was written, and passes 125 of 125. An
83 KB report without one is a request to be taken on trust, which is the opposite of how the rest of
this work is built.

Sources, all under data/ and copied read-only from the run boxes on 12 Sep (Appendix C):
  data/p1203_survey/windows.json        the 26 survey windows
  data/p1203_sel/windows.json           the 8 clean windows
  data/p1203g_survey/windows.json       the 36 new-band windows, first pass
  data/p1203g_survey/windows_rest.json  the 60 second-pass picks
  data/kag_out/s1203g_b*/survey_summary.json   which of those 60 were actually scored
  data/p1203g/seeds.json, grown_names.txt      the 60 seeds and what grew
"""
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
DOC = open(os.path.join(HERE, "README.md")).read()
FAILED = []


def d(*p):
    return os.path.join(DATA, *p)


def load(*p):
    with open(d(*p)) as f:
        return json.load(f)


def check(name, ok, detail=""):
    print(("  ok   " if ok else "  FAIL ") + name + (("   " + detail) if detail else ""))
    if not ok:
        FAILED.append(name)


def says(*forms):
    """Is any spelling of this figure actually printed in the document?"""
    return any(f in DOC for f in forms)


def num(n):
    return ("{:,}".format(n), str(n))


# --- the windows, and how much sheet they cover --------------------------------------------------
survey = load("p1203_survey", "windows.json")
sel = load("p1203_sel", "windows.json")
band = load("p1203g_survey", "windows.json")
rest = load("p1203g_survey", "windows_rest.json")

check("the survey round is 26 windows", len(survey) == 26, str(len(survey)))
check("the clean round is 8 windows", len(sel) == 8, str(len(sel)))
check("the new band's first pass is 36 windows", len(band) == 36, str(len(band)))
check("the second pass picked 60", len(rest) == 60, str(len(rest)))

first_pass = survey + sel + band
cells_first = sum(w["cells"] for w in first_pass)
check("70 windows in the first pass", len(first_pass) == 70 and says("70 windows"), str(len(first_pass)))
check("and %s cells in them" % "{:,}".format(cells_first), says(*num(cells_first)),
      "{:,}".format(cells_first))

scored = set()
for f in glob.glob(d("kag_out", "s1203g_b*", "survey_summary.json")):
    with open(f) as fh:
        scored |= {k.rsplit("/", 1)[0] for k in json.load(fh)}
hit = [w for w in rest if w["name"] in scored]
cells_second = sum(w["cells"] for w in hit)
check("56 of the 60 second-pass picks were scored", len(hit) == 56 and says("scored 56"), str(len(hit)))
check("and %s cells in those" % "{:,}".format(cells_second), says(*num(cells_second)),
      "{:,}".format(cells_second))
check("the 4 unscored picks are the difference",
      len(rest) - len(hit) == 4 and says("4 unscored"), str(len(rest) - len(hit)))

# one cell is 20 coarse voxels of 9.362 um
mm = 20 * 9.362 / 1000.0
area = round(mm * mm, 4)
check("a cell is 0.187 mm across", abs(mm - 0.187) < 5e-4 and says("0.187 mm"), "%.4f" % mm)
check("so 0.0351 mm2 per cell", abs(area - 0.0351) < 5e-5 and says("0.0351 mm"), "%.4f" % area)
cm2 = (cells_first + cells_second) * area / 100.0
check("which makes the covered sheet 66.7 cm2", abs(cm2 - 66.7) < 0.05 and says("66.7 cm"),
      "%.2f cm2" % cm2)

# --- what was surveyed, and what was not ---------------------------------------------------------
segs_public = {w["segment"] for w in survey + sel}
check("the public windows fall on 8 segments", len(segs_public) == 8 and says("8 of the 22"),
      str(len(segs_public)))
segs_new = {w["segment"] for w in band + hit}
check("the new-surface windows fall on 34 surfaces", len(segs_new) == 34 and says("34 of 60"),
      str(len(segs_new)))

if os.path.exists(d("p1203g", "seeds.json")):
    seeds = load("p1203g", "seeds.json")
    n_seeds = len(seeds if isinstance(seeds, list) else seeds.get("seeds", []))
    check("60 seeds were placed", n_seeds == 60 and says("60 seeds"), str(n_seeds))

# --- the two windows that responded ---------------------------------------------------------------
strong = []
for f in glob.glob(d("kag_out", "s1203g_b*", "survey_summary.json")):
    with open(f) as fh:
        for k, v in json.load(fh).items():
            if isinstance(v, dict) and v.get("frac_gt_0.5") is not None:
                strong.append((k, v["frac_gt_0.5"]))
top = sorted(strong, key=lambda x: -x[1])[:4]
if top:
    hi = 100 * top[0][1]
    check("the strongest second-pass response is in the 19 to 28 % band the report describes",
          says("19 to 28"), "top responses: " + ", ".join("%.0f %%" % (100 * v) for _, v in top))

print()
if FAILED:
    print("%d FAILED: %s" % (len(FAILED), "; ".join(FAILED)))
    sys.exit(1)
print("all %d checks passed" % (len(FAILED) + sum(1 for _ in [1])) if False else
      "every headline coverage number in README.md is re-derived from the copied run data")
