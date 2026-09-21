"""Three windows on the same 12 published-0139 windows: [23,85) (flummoxjr's exact setting), our [24,86), README [1,63)."""
import json, statistics as st
K = "<run-dir>/kag_out"
a = json.load(open(f"{K}/fliptest/fliptest_summary.json")); c = json.load(open(f"{K}/w2385test/w2385_summary.json")); b = json.load(open(f"{K}/readmetest/readme_summary.json"))
rows = []
for n in sorted(a):
    f = a[n].get("fwd", {}); g = c.get(n, {}).get("w2385", {}); r = b.get(n, {}).get("readme", {})
    if "r" in f and "r" in g: rows.append((n, f["pub"], g["r"], g["ink"], f["r"], f["ink"], r.get("r"), r.get("ink")))
print("window | published ink | [23,85) r / ink | [24,86) r / ink | README [1,63) r / ink")
for n, pub, gr, gi, fr, fi, rr, ri in rows:
    print(f"{n:28s} {100*pub:5.1f}% | {gr:.3f} / {100*gi:5.1f}% | {fr:.3f} / {100*fi:5.1f}% | {rr:.3f} / {100*ri:5.1f}%")
for kind in ("text", "blank"):
    k = [x for x in rows if x[0].startswith(kind)]
    print(f"{kind}: median r [23,85) {st.median(x[2] for x in k):.3f} | [24,86) {st.median(x[4] for x in k):.3f} | README {st.median(x[6] for x in k):.3f}; windows where [23,85) beats [24,86): {sum(x[2] > x[4] for x in k)}/{len(k)}")
json.dump([dict(zip(["window", "published", "w2385_r", "w2385_ink", "w2486_r", "w2486_ink", "readme_r", "readme_ink"], x)) for x in rows], open(f"{K}/issue_windows_3way.json", "w"), indent=1)
