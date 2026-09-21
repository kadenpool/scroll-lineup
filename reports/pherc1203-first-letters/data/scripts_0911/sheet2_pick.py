"""Pick OUR crops for blind sheet 2 from depth-corrected results: for each window the depth order with more ink, then
the top N windows by ink share per source. Usage: sheet2_pick.py <out.json> <src_glob>:<tag>:<N> ...
Summaries are read from each source's survey_summary.json."""
import json, glob, sys
out = []
for spec in sys.argv[2:]:
    g, tag, n = spec.rsplit(":", 2); best = {}
    for f in glob.glob(f"{g}/survey_summary.json"):
        base = f.rsplit("/", 1)[0]
        for k, v in json.load(open(f)).items:
            w, s = k.split("/"); fr = v.get("frac_gt_0.5") or 0
            if fr > best.get(w, (0, ""))[0]: best[w] = (fr, f"{base}/{w}/{s}")
    top = sorted(best.values, reverse=True)[:int(n)]
    out += [[d.split("<run-dir>/", 1)[-1], tag] for fr, d in top]
    print(tag, [(round(100 * fr, 1), d.split("/")[-2][-14:] + "/" + d.split("/")[-1]) for fr, d in top])
json.dump(out, open(sys.argv[1], "w"), indent=1); print(len(out), "crops listed ->", sys.argv[1])
