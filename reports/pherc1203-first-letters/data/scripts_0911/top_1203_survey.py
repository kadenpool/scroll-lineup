"""Top windows of the ORIGINAL 1203 survey (kag_out/survey_b*), by the larger ink share of the two depth orders.
Prints them and writes p1203_survey/rerun_windows.json (top 8, batch 0) for survey_pipeline_1203_rr.sh."""
import json, glob, os
best = {}
for f in glob.glob("kag_out/survey_b*/survey_summary.json"):
    for k, v in json.load(open(f)).items():
        n, s = k.split("/"); fr = v.get("frac_gt_0.5") or 0
        if fr > best.get(n, (0, ""))[0]: best[n] = (fr, s)
rows = sorted(best.items(), key=lambda kv: -kv[1][0])
print(len(rows), "windows in the original survey")
for n, (fr, s) in rows[:12]: print(f"  {n:44s} {s} {100 * fr:5.1f}%  tifxyz={'yes' if os.path.exists(f'p1203_survey/{n}/x.tif') else 'MISSING'}")
top = [n for n, _ in rows[:8]]
json.dump([{"name": n, "batch": 0, "why": "top-8 ink share (either order) in the original 1203 survey, mesh-centred windows"} for n in top],
          open("p1203_survey/rerun_windows.json", "w"), indent=1)
print("wrote p1203_survey/rerun_windows.json")
