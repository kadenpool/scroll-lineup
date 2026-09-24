"""Read a finished day-3 run (PREREG amendment 1) and recompute its readout from the per-job AUCs, apart from the
kernel's own code: the reference control against day 1, the sham and clean checks, and the two floors. Then compare
with the kernel's readout. Reads only; changes nothing.

  python3 read_day3.py <day-3 run dir with out/results.json> <day-1 results.json>
"""
import json, statistics, sys

run, day1 = sys.argv[1].rstrip("/"), sys.argv[2]
try:
    R = json.load(open(f"{run}/out/results.json"))
except FileNotFoundError:
    R = json.load(open(f"{run}/results.json"))
D1 = json.load(open(day1))
J, STR = R["jobs"], sorted(float(s) for s in R["strengths"])
print(f"{R['script_version']}\nstatus: {R['status']}   {R['started_utc']} to {R.get('finished_utc')}   gpus {R.get('gpus')}")
print(f"errors: {sorted(R['errors']) or 'none'}   complete: {R.get('complete')}")
n_t = sum(1 for j in J.values() if j["kind"] == "clean")
print(f"jobs {len(J)}: {n_t} targets, {sum(1 for j in J.values() if j['kind'] == 'whole')} whole surfaces"
      + ("   (SMOKE RUN: numbers not used)" if n_t == 1 else ""))


def med(xs):
    return statistics.median(xs) if xs else float("nan")


def crossing(curve, thr):
    """First s where the straight line between grid points reaches thr; None if the curve never does."""
    pts = sorted(curve.items())
    if pts[0][1] >= thr:
        return pts[0][0]
    for (s0, c0), (s1, c1) in zip(pts, pts[1:]):
        if c1 >= thr:
            return s0 + (s1 - s0) * (thr - c0) / (c1 - c0)
    return None


mine = {}
for tag in R.get("checkpoints", {}):
    scored = [n for n in J if J[n]["kind"] != "whole"]
    if not all(set(J[n].get("auc", {}).get(tag, {})) >= {"forward", "reverse"} for n in scored):
        print(f"\n== {tag}: INCOMPLETE, nothing is read")
        continue
    d = D1["gates"][f"{tag}/swap"]["primary_direction"]
    a = {n: J[n]["auc"][tag][d] for n in scored}
    refs = [n for n in scored if J[n]["kind"] == "reference"]
    change = {n: a[n] - D1["jobs"][n]["auc"][tag][d] for n in refs}
    control = max(abs(v) for v in change.values()) <= 0.01
    clean = med([a[n] for n in scored if J[n]["kind"] == "clean"])
    curve = {0.0: clean}
    shams, xshams = {}, {}
    for s in STR:
        curve[s] = med([a[n] for n in scored if J[n]["kind"] == "planted" and J[n]["strength"] == s])
        shams[s] = med([a[n] for n in scored if J[n]["kind"] == "sham" and J[n]["strength"] == s])
        xshams[s] = med([a[n] for n in scored if J[n]["kind"] == "xsham" and J[n]["strength"] == s])
    checks = (0.40 <= clean <= 0.60 and all(0.40 <= v <= 0.60 for v in shams.values())
              and all(0.40 <= v <= 0.60 for v in xshams.values()))
    det, clr = (crossing(curve, 0.70), crossing(curve, 0.80)) if control and checks else (None, None)
    mine[tag] = {"control_ok": control, "checks_ok": checks, "detection_floor": det, "clear_floor": clr}
    print(f"\n== {tag}, direction {d}")
    print("   reference change from day 1: " + ", ".join(f"{n.split('_')[0]} {v:+.4f}" for n, v in change.items()) +
          f"  -> control {'ok' if control else 'MOVED: not read'}")
    print(f"   clean {clean:.3f}; planted " + " ".join(f"s{s:g} {curve[s]:.3f}" for s in STR) +
          "; shams " + " ".join(f"s{s:g} {shams[s]:.3f}" for s in STR) +
          "; PHerc0139 shams " + " ".join(f"s{s:g} {xshams[s]:.3f}" for s in STR) + f"  -> checks {'pass' if checks else 'FAIL'}")
    fmt = lambda f: "above 1" if f is None else f"{f:.3f}"
    print(f"   detection floor {fmt(det) if control and checks else 'not read'}; clear floor "
          f"{fmt(clr) if control and checks else 'not read'}")
    per_t = []
    for n in scored:
        if J[n]["kind"] == "clean":
            t = n.split("__")[0]
            per_t.append(f"{t} {a[n]:.2f}/{a.get(f'{t}__swap__s1', float('nan')):.2f}/{a.get(f'{t}__swap__sham1', float('nan')):.2f}")
    print("   per target, clean/planted s1/sham s1: " + ", ".join(per_t))
k = R.get("readout", {})
if k:
    same = set(k) == set(mine) and all(
        k[t]["control_ok"] == mine[t]["control_ok"] and k[t]["checks_ok"] == mine[t]["checks_ok"] and
        all((k[t][f] is None and mine[t][f] is None) or
            (k[t][f] is not None and mine[t][f] is not None and abs(k[t][f] - mine[t][f]) < 1e-9)
            for f in ("detection_floor", "clear_floor")) for t in mine)
    print(f"\nKernel readout vs recomputed here: {'AGREE' if same else 'DIFFER'}")
