"""Read a finished day-4 run (PREREG amendment 3) and recompute its readout from the per-job AUCs in its results.json,
apart from the job's own code: for each arm, the reference control against day 1, the clean and sham checks and the
two floors; the scale references (arm B, not a gate); and, for each checkpoint read in both arms, arm A minus arm B
at s = 0 and every strength, target by target and as the median over targets. The arm, target, kind and strength of
each job are taken from its name here, not from the fields the job wrote (which are checked against the names). Then
compare with the job's own readout and print AGREE or DIFFER. Reads only; changes nothing.

  python3 read_day4.py <day-4 run dir with out/results.json> <day-1 results.json>
exit 0 AGREE, 1 DIFFER, 2 no readout in the run to compare
"""
import hashlib, json, re, statistics, sys

DAY1_SHA256 = "61f6af77bc64189f5442cb9ee56461ffb618a48d2a5191662f7c76d7ee2e2056"   # pinned in the job (amendment 1)
run, day1 = sys.argv[1].rstrip("/"), sys.argv[2]
try:
    R = json.load(open(f"{run}/out/results.json"))
except FileNotFoundError:
    R = json.load(open(f"{run}/results.json"))
D1 = json.load(open(day1))
J, STR = R["jobs"], sorted(float(s) for s in R["strengths"])
S0 = [0.0] + STR
bad = []                                   # every way the job's own record or readout disagrees with this recompute
print(f"{R['script_version']}\nstatus: {R['status']}   {R['started_utc']} to {R.get('finished_utc')}   gpus {R.get('gpus')}")
print(f"errors: {sorted(R['errors']) or 'none'}   complete: {R.get('complete')}")
sha = hashlib.sha256(open(day1, "rb").read()).hexdigest()
print(f"day-1 results.json sha256 {sha[:16]}...: " + ("the pinned file" if sha == DAY1_SHA256 else "NOT the pinned file"))
if R.get("plants") != ["swap"]:
    bad.append(f"plants {R.get('plants')}, expected ['swap'] (carried forward from day 1)")

# ---- each job from its name: a_/b_ + target + clean or swap__s/sham/xsham + strength; b_ref*: scale references;
# ---- ref*: the control; whole_a_/whole_b_: the whole surfaces (not scored)
ARM_JOB = re.compile(r"(a|b)_(d4t\d\d_s\d\d)__(?:(clean)|swap__(xsham|sham|s)(\d+(?:\.\d+)?))")
KIND = {"s": "planted", "sham": "sham", "xsham": "xsham"}
parsed, scale, refs, whole = {}, {}, [], []
for n, j in J.items():
    m, ms, mw = ARM_JOB.fullmatch(n), re.fullmatch(r"b_(ref\d+_w\d+)", n), re.fullmatch(r"whole_(a|b)_s\d\d", n)
    if m:
        kind, s = ("clean", 0.0) if m.group(3) else (KIND[m.group(4)], float(m.group(5)))
        parsed[n] = (m.group(1), m.group(2), kind, s)
        if (j.get("arm"), j["kind"], float(j.get("strength", -1))) != (m.group(1), kind, s):
            bad.append(f"{n}: the record says arm {j.get('arm')}, {j['kind']}, s {j.get('strength')}")
    elif ms:
        scale[n] = ms.group(1)
        if (j.get("arm"), j["kind"], j.get("reference")) != ("b", "scale_reference", ms.group(1)):
            bad.append(f"{n}: the record says arm {j.get('arm')}, {j['kind']}, reference {j.get('reference')}")
    elif re.fullmatch(r"ref\d+_w\d+", n):
        refs.append(n)
        if j["kind"] != "reference" or "arm" in j:
            bad.append(f"{n}: the record says {j['kind']}, arm {j.get('arm')}")
    elif mw:
        whole.append(n)
        if (j["kind"], j.get("arm")) != ("whole", mw.group(1)):
            bad.append(f"{n}: the record says {j['kind']}, arm {j.get('arm')}")
    else:
        bad.append(f"{n}: a name this reader does not know")
n_t = {arm: sorted({p[1] for p in parsed.values() if p[0] == arm}) for arm in ("a", "b")}
if n_t["a"] != n_t["b"]:
    bad.append(f"the arms hold different targets: {n_t['a']} / {n_t['b']}")
# ---- the job set (review 11): the rules' strengths; ten jobs per target in each arm; six references, six scale
# ---- references; whole surfaces in both arms (five each, or one each in a smoke run); eight targets unless a smoke run
if STR != [0.25, 0.5, 1.0]:
    bad.append(f"job set: strengths {STR}, the rules give [0.25, 0.5, 1.0]")
WANT = {("clean", 0.0)} | {(k, s) for k in ("planted", "sham", "xsham") for s in (0.25, 0.5, 1.0)}
for arm in ("a", "b"):
    for t in n_t[arm]:
        got = sorted((k, s) for (ar, tt, k, s) in parsed.values() if ar == arm and tt == t)
        if len(got) != len(set(got)) or set(got) != WANT:
            bad.append(f"job set: arm {arm.upper()} target {t} has {len(got)} jobs, not the rules' ten")
smoke = len(n_t["a"]) == 1
if not smoke and len(n_t["a"]) != 8:
    bad.append(f"job set: {len(n_t['a'])} targets, the windows give 8")
if len(refs) != 6 or len(scale) != 6:
    bad.append(f"job set: {len(refs)} references and {len(scale)} scale references, not 6 and 6")
if len(whole) != (2 if smoke else 10):
    bad.append(f"job set: {len(whole)} whole surfaces, not {2 if smoke else 10}")
print(f"jobs {len(J)}: targets {len(n_t['a'])} in arm A, {len(n_t['b'])} in arm B; {len(refs)} references; "
      f"{len(scale)} scale references; whole surfaces {sorted(whole)}" +
      ("   (SMOKE RUN: numbers not used)" if len(n_t["a"]) == 1 else ""))


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


mine, mine_diff, mine_scale = {"a": {}, "b": {}}, {}, {}
for tag in R.get("checkpoints", {}):
    scored = [n for n in J if J[n]["kind"] != "whole"]
    has = lambda n: set(J[n].get("auc", {}).get(tag, {})) >= {"forward", "reverse"}
    part = {"a": [n for n in scored if J[n].get("arm") in ("a", None) and J[n]["kind"] != "scale_reference"],
            "b": [n for n in scored if J[n].get("arm") in ("b", None) and J[n]["kind"] != "scale_reference"],
            "scale": [n for n in scored if J[n]["kind"] in ("scale_reference", "reference")]}
    ok = {p_: all(has(n) for n in v) for p_, v in part.items()}    # each arm, and the scale references, on their own
    if not any(ok.values()):
        print(f"\n== {tag}: INCOMPLETE, nothing is read")
        mine_diff[tag] = {"read": False}
        continue
    d = D1["gates"][f"{tag}/swap"]["primary_direction"]
    a = {n: J[n]["auc"][tag][d] for n in scored if has(n)}
    change = {n: a[n] - D1["jobs"][n]["auc"][tag][d] for n in refs}
    moved = max(abs(v) for v in change.values())
    control = moved <= 0.01
    print(f"\n== {tag}, direction {d}")
    print("   reference change from day 1: " + ", ".join(f"{n.split('_')[0]} {v:+.4f}" for n, v in change.items()) +
          f"  -> control {'ok' if control else 'MOVED: not read'} (both arms)")
    by = {}                                                           # (arm, target, kind, s) -> AUC
    for n, p in parsed.items():
        if n in a:
            by[p] = a[n]
    for arm in ("a", "b"):
        if not ok[arm]:
            print(f"   arm {arm.upper()}: INCOMPLETE, some of its jobs have no score; not read")
            continue
        def m_(kind, s):
            return med([v for (ar, t, k, ss), v in by.items() if ar == arm and k == kind and ss == s])
        curve = {s: m_("clean" if s == 0 else "planted", s) for s in S0}
        shams = {s: m_("sham", s) for s in STR}
        xshams = {s: m_("xsham", s) for s in STR}
        checks = (0.40 <= curve[0.0] <= 0.60 and all(0.40 <= v <= 0.60 for v in shams.values())
                  and all(0.40 <= v <= 0.60 for v in xshams.values()))
        det, clr = (crossing(curve, 0.70), crossing(curve, 0.80)) if control and checks else (None, None)
        mine[arm][tag] = {"control_ok": control, "moved": moved, "checks_ok": checks, "read": control and checks,
                          "detection_floor": det, "clear_floor": clr, "curve": curve, "shams": shams, "xshams": xshams}
        fmt = lambda f: "above 1" if f is None else f"{f:.3f}"
        print(f"   arm {arm.upper()}: clean {curve[0.0]:.3f}; planted " + " ".join(f"s{s:g} {curve[s]:.3f}" for s in STR) +
              "; shams " + " ".join(f"s{s:g} {shams[s]:.3f}" for s in STR) + "; PHerc0139 shams " +
              " ".join(f"s{s:g} {xshams[s]:.3f}" for s in STR) + f"  -> checks {'pass' if checks else 'FAIL'}")
        print(f"          detection floor {fmt(det) if control and checks else 'not read'}; clear floor "
              f"{fmt(clr) if control and checks else 'not read'}")
        print("          per target, clean/planted s1/sham s1/PHerc0139 sham s1: " + ", ".join(
            f"{t} " + "/".join(f"{by.get((arm, t, k, s), float('nan')):.2f}" for k, s in
                               (("clean", 0.0), ("planted", 1.0), ("sham", 1.0), ("xsham", 1.0))) for t in n_t[arm]))
    for arm in ("a", "b"):                                            # margins and leave-one-target-out (review 11)
        if not mine[arm].get(tag) or not mine[arm][tag]["control_ok"]:
            continue
        def summary(drop):
            def m_(kind, s):
                return med([v for (ar, t, k, ss), v in by.items() if ar == arm and k == kind and ss == s and t != drop])
            c = {s: m_("clean" if s == 0 else "planted", s) for s in S0}
            sh, xs = {s: m_("sham", s) for s in STR}, {s: m_("xsham", s) for s in STR}
            ok_ = (0.40 <= c[0.0] <= 0.60 and all(0.40 <= v <= 0.60 for v in sh.values())
                   and all(0.40 <= v <= 0.60 for v in xs.values()))
            return c, sh, xs, ok_, (crossing(c, 0.70) if ok_ else None), (crossing(c, 0.80) if ok_ else None)
        c, sh, xs, ok_, det, clr = summary(None)
        edge = min([min(v - 0.40, 0.60 - v) for v in [c[0.0]] + list(sh.values()) + list(xs.values())])
        loo = {t: summary(t) for t in n_t[arm]}
        flips = [t for t, r in loo.items() if r[3] != ok_ or (r[4] is None) != (det is None) or (r[5] is None) != (clr is None)]
        dets = [r[4] for r in loo.values() if r[4] is not None]
        print(f"   arm {arm.upper()} sensitivity: nearest check to its limit {edge:+.3f} (negative: failing); curve at s1 "
              f"{c[1.0]:.3f} against 0.70 and 0.80; leaving out one target changes a check or whether a floor is found "
              f"for {len(flips)} of {len(loo)} ({', '.join(flips) or 'none'}); detection floor without one target "
              + (f"{min(dets):.3f} to {max(dets):.3f}" if dets else "never found") +
              f" ({len(loo) - len(dets)} without)")
    if mine["a"].get(tag, {}).get("read") and mine["b"].get(tag, {}).get("read"):
        per = {t: {s: by[("a", t, "clean" if s == 0 else "planted", s)] - by[("b", t, "clean" if s == 0 else "planted", s)]
                   for s in S0} for t in n_t["a"]}
        mid = {s: med([per[t][s] for t in per]) for s in S0}
        mine_diff[tag] = {"read": True, "median": mid, "per": per}
        print("   arm A minus arm B, median over targets: " + " ".join(f"s{s:g} {mid[s]:+.3f}" for s in S0))
        print("          per target at s1: " + ", ".join(f"{t} {per[t][1.0]:+.3f}" for t in per))
        loo_d = {t: med([per[u][1.0] for u in per if u != t]) for t in per}
        flip_d = [t for t, v in loo_d.items() if (v > 0) != (mid[1.0] > 0)]
        print(f"          sign of the median at s1 without one target: changes for {len(flip_d)} of {len(per)} "
              f"({', '.join(flip_d) or 'none'})")
    else:
        mine_diff[tag] = {"read": False}
        print("   arm A minus arm B: not read in both arms, no difference")
    if not ok["scale"]:
        print("   scale references: INCOMPLETE, not read")
        continue
    sr = {n: (a[r], a[n]) for n, r in scale.items()}
    mine_scale[tag] = {"median_auc_a": med([x for x, _ in sr.values()]), "median_auc_b": med([y for _, y in sr.values()]),
                       "median_a_minus_b": med([x - y for x, y in sr.values()])}
    print(f"   scale references (arm B, not a gate): median AUC {mine_scale[tag]['median_auc_a']:.3f} at 9.362 um, "
          f"{mine_scale[tag]['median_auc_b']:.3f} at 8.64 um, A minus B {mine_scale[tag]['median_a_minus_b']:+.3f}; " +
          ", ".join(f"{r.split('_')[0]} {x:.3f}/{y:.3f}" for (n, r), (x, y) in zip(scale.items(), sr.values())))


def same(x, y):
    if x is None or y is None or isinstance(x, bool) or isinstance(y, bool):
        return x is y or x == y
    return abs(x - y) < 1e-9


def check(where, job, here):
    if not same(job, here):
        bad.append(f"{where}: job {job!r}, here {here!r}")


def by_s(d):
    return {float(s): v for s, v in d.items()}


k = R.get("readout")
if k is None:
    print("\nno readout in this run to compare")
    for b in bad:
        print("   " + b)
    sys.exit(2)
for arm in ("a", "b"):
    if set(k.get(arm, {})) != set(mine[arm]):
        bad.append(f"arm {arm}: checkpoints read by the job {sorted(k.get(arm, {}))}, here {sorted(mine[arm])}")
    for tag in sorted(set(k.get(arm, {})) & set(mine[arm])):
        kt, mt = k[arm][tag], mine[arm][tag]
        for f in ("control_ok", "checks_ok", "read", "detection_floor", "clear_floor"):
            check(f"{arm}/{tag}/{f}", kt[f], mt[f])
        check(f"{arm}/{tag}/control change", kt["control_largest_reference_change"], mt["moved"])
        for f in ("curve", "shams", "xshams"):
            job_f = by_s(kt[f])
            if set(job_f) != set(mt[f]):
                bad.append(f"{arm}/{tag}/{f}: strengths {sorted(job_f)} in the job, {sorted(mt[f])} here")
            for s in mt[f]:
                check(f"{arm}/{tag}/{f}/s{s:g}", job_f.get(s), mt[f][s])
kd, ks = R.get("difference", {}), R.get("scale_references", {})
if set(kd) != set(mine_diff) or set(ks) != set(mine_scale):
    bad.append(f"difference or scale references for {sorted(kd)} / {sorted(ks)} in the job, {sorted(mine_diff)} here")
for tag in sorted(set(kd) & set(mine_diff)):
    check(f"difference/{tag}/read", kd[tag]["read"], mine_diff[tag]["read"])
    if kd[tag]["read"] and mine_diff[tag]["read"]:
        for s, v in mine_diff[tag]["median"].items():
            check(f"difference/{tag}/median s{s:g}", by_s(kd[tag]["median_a_minus_b"]).get(s), v)
        if set(kd[tag]["a_minus_b_by_target"]) != set(mine_diff[tag]["per"]):
            bad.append(f"difference/{tag}: targets {sorted(kd[tag]['a_minus_b_by_target'])} in the job")
        for t, row in mine_diff[tag]["per"].items():
            for s, v in row.items():
                check(f"difference/{tag}/{t}/s{s:g}", by_s(kd[tag]["a_minus_b_by_target"].get(t, {})).get(s), v)
for tag in sorted(set(ks) & set(mine_scale)):
    for f, v in mine_scale[tag].items():
        check(f"scale references/{tag}/{f}", ks[tag][f], v)
print(f"\nJob readout vs recomputed here: {'AGREE' if not bad else 'DIFFER'}")
for b in bad:
    print("   " + b)
sys.exit(0 if not bad else 1)
