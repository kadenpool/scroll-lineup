"""Read a finished day-1 run (PREREG.md section 7) and recompute every gate from the per-job AUCs, independently of
the kernel's own gate code, then compare the two. Reads only; changes nothing.

  python3 read_day1.py <dir holding out/results.json>      # e.g. the folder the run's output was saved to
"""
import json, statistics, sys

d = sys.argv[1].rstrip("/")
try:
    R = json.load(open(f"{d}/out/results.json"))
except FileNotFoundError:
    R = json.load(open(f"{d}/results.json"))
J = R["jobs"]
STR = [float(s) for s in R["strengths"]]
print(f"{R['script_version']}\nstatus: {R['status']}   started {R['started_utc']}   finished {R.get('finished_utc')}")
print(f"gpus {R.get('gpus')}   errors: {sorted(R['errors']) or 'none'}   complete: {R.get('complete')}")
n_ref = sum(1 for j in J.values() if j["kind"] == "reference")
n_tgt = sum(1 for j in J.values() if j["kind"] == "clean")
print(f"jobs {len(J)}: {n_ref} references, {n_tgt} targets" + ("   (SMOKE RUN: numbers not used)" if n_tgt == 1 else ""))


def med(xs):
    return statistics.median(xs) if xs else float("nan")


mine = {}
for tag in R.get("checkpoints", {}):
    have = all(d_ in J[n].get("auc", {}).get(tag, {}) for n in J for d_ in ("forward", "reverse"))
    print(f"\n== {tag}: every job scored in both directions: {have}")
    if not have:
        missing = [n for n in J if set(J[n].get("auc", {}).get(tag, {})) != {"forward", "reverse"}]
        print(f"   INCOMPLETE ({len(missing)} jobs), no gate is read: {missing[:6]}")
        continue
    a = {n: J[n]["auc"][tag] for n in J}
    refs = [n for n in J if J[n]["kind"] == "reference"]
    ref_med = {dd: med([a[n][dd] for n in refs]) for dd in ("forward", "reverse")}
    prim = "forward" if ref_med["forward"] >= ref_med["reverse"] else "reverse"
    print(f"   reference median: forward {ref_med['forward']:.3f}, reverse {ref_med['reverse']:.3f} -> primary {prim}")
    print("   per donor (primary): " + ", ".join(f"{J[n]['seg']}#{J[n]['donor']} {a[n][prim]:.3f}" for n in refs))
    by_donor = {J[n]["donor"]: a[n][prim] for n in refs}
    trans = {n.split("__")[0]: a[n][prim] for n in J if J[n]["kind"] == "transplant"}
    gap = med([a[n][prim] - by_donor[J[n]["donor"]] for n in J if J[n]["kind"] == "transplant"])
    print(f"   transplants (primary): median {med(list(trans.values())):.3f}; context gap (transplant - own reference) "
          f"median {gap:+.3f}")
    cleans = [n for n in J if J[n]["kind"] == "clean"]
    clean_med = med([a[n][prim] for n in cleans])
    print(f"   clean targets (primary): median {clean_med:.3f}; " +
          ", ".join(f"{n.split('__')[0][6:]} {a[n][prim]:.3f}" for n in cleans))
    for mode in R["plants"]:
        curve = {0.0: clean_med}
        sham = {}
        for s in STR:
            curve[s] = med([a[n][prim] for n in J if J[n]["kind"] == "planted" and J[n]["plant"] == mode and J[n]["strength"] == s])
            sham[s] = med([a[n][prim] for n in J if J[n]["kind"] == "sham" and J[n]["plant"] == mode and J[n]["strength"] == s])
        at1 = [n for n in J if J[n]["kind"] == "planted" and J[n]["plant"] == mode and J[n]["strength"] == 1.0]
        paired = med([a[n][prim] - trans[n.split("__")[0]] for n in at1])       # G1: like for like
        vs_ref = med([a[n][prim] - by_donor[J[n]["donor"]] for n in at1])
        ss = sorted(curve)
        g = {"G0": ref_med[prim] >= 0.70, "G1": abs(paired) <= 0.05,
             "G2": all(0.40 <= sham[s] <= 0.60 for s in STR),
             "G3": 0.40 <= clean_med <= 0.60 and all(curve[b] >= curve[x] - 0.02 for x, b in zip(ss, ss[1:]))
                   and curve[1.0] >= 0.70}
        g["go"] = all(g[k] for k in ("G0", "G1", "G2", "G3"))
        mine[f"{tag}/{mode}"] = g
        print(f"   {mode}: planted " + " ".join(f"s{s:g} {curve[s]:.3f}" for s in ss) +
              " | sham " + " ".join(f"s{s:g} {sham[s]:.3f}" for s in STR) +
              f" | at s1: planted - transplant {paired:+.3f}, planted - own reference {vs_ref:+.3f}")
        print("      " + "  ".join(f"{k} {'PASS' if g[k] else 'fail'}" for k in ("G0", "G1", "G2", "G3")) +
              f"  -> {'GO' if g['go'] else 'no go'}")
        per_t = []
        for n in cleans:
            t = n.split("__")[0]
            per_t.append(f"{t[6:]} {a[f'{t}__{mode}__s1'][prim]:.2f}/{a[f'{t}__transplant'][prim]:.2f}/"
                         f"{a[f'{t}__{mode}__sham1'][prim]:.2f}")
        print("      per target at s1, planted/transplant/sham: " + ", ".join(per_t))
        clip = [J[n].get("clipped_share", 0) for n in at1]
        if clip:
            print(f"      clipped share of changed voxels at s1: median {med(clip):.4f}, max {max(clip):.4f}")

print("\nTexture scale per target (k, sham k, depth shift): " + ", ".join(
    f"{n.split('__')[0][6:]} {J[n]['k']:.2f}/{J[n]['k_sham']:.2f}/{J[n]['depth_shift']:+d}"
    for n in J if J[n]["kind"] == "clean"))
if "donors" in R:
    print("Donor ink contrast at the sheet layer (texture SD): " +
          ", ".join(f"{x['seg']} {x['ink_contrast_at_sheet']:+.2f}" for x in R["donors"]))

# positives only, beside G1 (PREREG section 2): the model's median output on the letters, planted at s = 1 against the
# transplant, from the kept maps; ink the map misses sits among the negatives, so it cannot move this number
import glob, os
import numpy as np
mk = sorted(glob.glob(f"{d}/**/masks.npz", recursive=True)) or sorted(glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)), "day1", "masks.npz")))
for tag in R.get("checkpoints", {}):
    mp = sorted(glob.glob(f"{d}/**/maps_{tag}.npz", recursive=True))
    if not mp or not mk:
        continue
    M, Mk = np.load(mp[0]), np.load(mk[0])
    prim = next((g_["primary_direction"] for k, g_ in R.get("gates", {}).items() if k.startswith(tag)), "forward")
    for mode in R["plants"]:
        diffs = []
        for n in J:
            if J[n]["kind"] != "clean":
                continue
            t, ink = n.split("__")[0], Mk[f"donor{J[n]['donor']}_ink"]
            a1, a2 = f"{t}__{mode}__s1__{prim}", f"{t}__transplant__{prim}"
            if a1 in M and a2 in M:
                diffs.append(float(np.median(M[a1][ink]) - np.median(M[a2][ink])) / 255)
        if diffs:
            print(f"{tag}/{mode}: positives only, planted - transplant median output on the letters: "
                  f"median {np.median(diffs):+.4f} over {len(diffs)} targets")

k_gates = R.get("gates", {})
if k_gates:
    agree = all(k_gates[t]["day1_go"] == mine[t]["go"] and all(k_gates[t][k] == mine[t][k] for k in ("G0", "G1", "G2", "G3"))
                for t in mine)
    print(f"\nKernel gates vs recomputed here: {'AGREE' if agree and set(k_gates) == set(mine) else 'DIFFER'}"
          f"   kernel carry-forward plant: {R.get('carry_forward_plant')}")
