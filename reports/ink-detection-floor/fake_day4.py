"""Test data for read_day4.py and the day-4 readout, as fake_day3.py is for day 3: made-up day-4 AUCs (both arms, the
six references copied from day 1, the six scale references, whole surfaces), run through floor_day4.py's own readout
code and saved as a run. With "all", every case is built in its own folder, read back by read_day4.py (a separate
process), and checked: read_day4.py must print AGREE, and the job's readout must give the case's expected verdict.

  python3 fake_day4.py <out dir> <case: normal | moved | sham | xsham | low | onearm | incomplete | missing | all> <day-1 results.json>

Cases: normal (both arms read; arm A's curve tops at 0.86, arm B's at 0.82); moved (a seed-43 reference moves 0.02:
seed 43 is read in neither arm); sham (the PHerc0483B sham reads 0.65 at s = 1 in both arms: no floor anywhere); xsham
(the PHerc0139 sham reads 0.66 at s = 1 in both arms: no floor anywhere); low (curves top at 0.76 and 0.74: detection
floors, clear floors above 1); onearm (arm B's PHerc0139 sham reads 0.30 at s = 1: arm A read, arm B not, so no
difference is given); incomplete (one arm-B job has no seed-43 reverse score: seed 43 is read in arm A only, so no
difference is given for it; arm B still reads seed 42); missing (one arm-A sham job is absent from the run: the
reader must print DIFFER, naming the job set).
"""
import contextlib, io, json, os, subprocess, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
TAGS = ("seed42_step010000", "seed43_step060000")
STRENGTHS = [0.25, 0.5, 1.0]
CASES = ("normal", "moved", "sham", "xsham", "low", "onearm", "incomplete", "missing")
TOP = {"a": 0.86, "b": 0.82}                        # the planted curve at s = 1; "low": 0.76 and 0.74
READ, CHECK_FAIL, MOVED, NO_CLEAR = (True, True, True, True), (True, False, False, False), (False, True, False, False), \
    (True, True, True, False)                       # (control ok, checks ok, detection floor found, clear floor found)


def expect(case):
    """The expected verdict: per arm and checkpoint the tuple above, and per checkpoint whether a difference is given."""
    arms = {arm: {t: READ for t in TAGS} for arm in ("a", "b")}
    if case == "moved":
        arms = {arm: {TAGS[0]: READ, TAGS[1]: MOVED} for arm in ("a", "b")}
    if case in ("sham", "xsham"):
        arms = {arm: {t: CHECK_FAIL for t in TAGS} for arm in ("a", "b")}
    if case == "low":
        arms = {arm: {t: NO_CLEAR for t in TAGS} for arm in ("a", "b")}
    if case == "onearm":
        arms["b"] = {t: CHECK_FAIL for t in TAGS}
    if case == "incomplete":
        arms = {"a": {t: READ for t in TAGS}, "b": {TAGS[0]: READ}}
    return arms, {t: t in arms["a"] and t in arms["b"] and arms["a"][t][:2] == arms["b"][t][:2] == (True, True)
                  for t in TAGS}


def build(out, case, day1):
    os.makedirs(f"{out}/out", exist_ok=True)
    DAY1 = json.load(open(day1))
    ck_paths = {t: "" for t in TAGS}
    rng = np.random.default_rng(7)
    top = {"a": 0.76, "b": 0.74} if case == "low" else TOP
    J = {}
    for n, j in DAY1["jobs"].items():
        if j["kind"] == "reference":
            J[n] = {"kind": "reference", "seg": j["seg"], "donor": j["donor"], "auc": {t: dict(j["auc"][t]) for t in TAGS}}
            if case == "moved" and j["donor"] == 2:
                J[n]["auc"]["seed43_step060000"]["forward"] += 0.02
            J[f"b_{n}"] = {"kind": "scale_reference", "arm": "b", "seg": j["seg"], "donor": j["donor"], "reference": n,
                           "auc": {t: {d: v - 0.03 + float(rng.normal(0, 0.01)) for d, v in j["auc"][t].items()}
                                   for t in TAGS}}
    for i in range(8):
        t = f"d4t{i:02d}_s0{1 + i % 5}"
        for arm in ("a", "b"):
            ks = {"arm": arm, "surface": t.split("_")[1], "donor": i % 6, "k": 0.9 + 0.02 * i, "k_sham": 1.0,
                  "k_xsham": 0.8}                                   # every job of a target carries them, as the real job does
            J[f"{arm}_{t}__clean"] = dict(ks, kind="clean", strength=0.0)
            for s in STRENGTHS:
                J[f"{arm}_{t}__swap__s{s:g}"] = dict(ks, kind="planted", plant="swap", strength=s, clipped_share=0.001 * s)
                J[f"{arm}_{t}__swap__sham{s:g}"] = dict(ks, kind="sham", plant="swap", strength=s, clipped_share=0.0)
                J[f"{arm}_{t}__swap__xsham{s:g}"] = dict(ks, kind="xsham", plant="swap", strength=s, clipped_share=0.0)
    for n, j in J.items():
        if j["kind"] in ("reference", "scale_reference"):
            continue
        mu = 0.50 + (top[j["arm"]] - 0.50) * j["strength"] if j["kind"] == "planted" else 0.50
        if case == "sham" and j["kind"] == "sham" and j["strength"] == 1.0:
            mu = 0.65
        if case == "xsham" and j["kind"] == "xsham" and j["strength"] == 1.0:
            mu = 0.66
        if case == "onearm" and j["arm"] == "b" and j["kind"] == "xsham" and j["strength"] == 1.0:
            mu = 0.30
        j["auc"] = {t: {"forward": float(mu + rng.normal(0, 0.01)), "reverse": float(0.5 + rng.normal(0, 0.01))}
                    for t in TAGS}
    if case == "incomplete":
        del J["b_d4t03_s04__swap__xsham0.5"]["auc"]["seed43_step060000"]["reverse"]
    if case == "missing":                         # a job the rules require is not in the run at all
        del J["a_d4t02_s03__swap__sham0.5"]
    for arm in ("a", "b"):
        for s in ("s01", "s02", "s03", "s04", "s05"):
            J[f"whole_{arm}_{s}"] = {"kind": "whole", "surface": s, "arm": arm}
    RESULTS = {"script_version": f"fake day 4 ({case})", "started_utc": "x", "status": "running", "errors": {},
               "jobs": J, "plants": ["swap"], "strengths": STRENGTHS, "checkpoints": {t: {} for t in TAGS}, "gpus": 2}
    src = open(os.path.join(HERE, "floor_day4.py")).read()
    code = src[src.index("def med(xs):"):src.index('RESULTS["status"] = "done" if all(complete.values()) else "done, incomplete"')]
    env = {"np": np, "RESULTS": RESULTS, "DAY1": DAY1, "ck_paths": ck_paths, "STRENGTHS": STRENGTHS, "OUT": f"{out}/out"}
    with contextlib.redirect_stdout(io.StringIO()):                   # the summary is in out/summary.md
        exec(code, env)
    RESULTS["status"] = "done"
    json.dump(RESULTS, open(f"{out}/out/results.json", "w"), indent=1)
    return RESULTS


def verdict(R):
    arms = {arm: {t: (r["control_ok"], r["checks_ok"], r["detection_floor"] is not None, r["clear_floor"] is not None)
                  for t, r in R["readout"][arm].items()} for arm in ("a", "b")}
    return arms, {t: d["read"] for t, d in R["difference"].items()}


def difference_sign(R, case):
    """Where a difference is given, it is arm A minus arm B: about TOP a - b at s = 1, about 0 at s = 0."""
    top = {"a": 0.76, "b": 0.74} if case == "low" else TOP
    return all(abs(d["median_a_minus_b"][1.0] - (top["a"] - top["b"])) < 0.015 and abs(d["median_a_minus_b"][0.0]) < 0.015
               for d in R["difference"].values() if d["read"])


if __name__ == "__main__":
    out, case, day1 = sys.argv[1], sys.argv[2], sys.argv[3]
    fails = 0
    for c in (CASES if case == "all" else (case,)):
        folder = f"{out}/{c}" if case == "all" else out
        R = build(folder, c, day1)
        rd = subprocess.run([sys.executable, os.path.join(HERE, "read_day4.py"), folder, day1], capture_output=True,
                            text=True)
        open(f"{folder}/read_day4.txt", "w").write(rd.stdout + rd.stderr)
        agree = rd.returncode == 0 and "Job readout vs recomputed here: AGREE" in rd.stdout
        got, want = verdict(R), expect(c)
        ok = agree and got == want and difference_sign(R, c)
        if c == "missing":                        # here the reader must refuse: the job set is not the rules'
            ok = not agree and "job set: arm A target d4t02_s03 has 9 jobs" in rd.stdout
        fails += not ok
        print(f"{c:7s} read_day4 {'AGREE' if agree else 'DIFFER (see ' + folder + '/read_day4.txt)'}; verdict "
              f"{'as expected' if got == want else 'NOT as expected: ' + repr(got)}; difference sign "
              f"{'right' if difference_sign(R, c) else 'WRONG'}; differences given for "
              f"{[t for t, v in got[1].items() if v] or 'no checkpoint'} -> {'PASS' if ok else 'FAIL'}")
    sys.exit(1 if fails else 0)
