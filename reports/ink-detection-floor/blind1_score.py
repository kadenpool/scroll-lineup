"""Score blind check 1 exactly as BLIND1_DESIGN.md fixed it, from Kaden's answers and the key.

  python3 blind1_score.py <answers .json> <key.json> [expected key sha256]

<answers .json>: {"01": "y" | "n", ...} for every picture (read from the page's store, collection "answers").
Stops unless the key's sha256 equals the one recorded before Kaden saw the page (blind1/KEY_SHA256.txt), and unless
every picture has an answer. Prints hits at s = 1 and s = 0.5, false alarms on the shams, and a one-sided Fisher
exact test of each strength's hits against the false alarms.
"""
import hashlib, json, os, re, sys
from scipy.stats import fisher_exact

ans_path, key_path = sys.argv[1], sys.argv[2]
HERE = os.path.dirname(os.path.abspath(__file__))
want = sys.argv[3] if len(sys.argv) > 3 else re.search(r"[0-9a-f]{64}", open(f"{HERE}/blind1/KEY_SHA256.txt").read()).group(0)
blob = open(key_path, "rb").read()
got = hashlib.sha256(blob).hexdigest()
if got != want:
    raise SystemExit(f"key sha256 {got} is not the recorded {want}: not scored")
K = json.loads(blob)["key"]
A = json.load(open(ans_path))
missing = [f"{k['n']:02d}" for k in K if A.get(f"{k['n']:02d}") not in ("y", "n")]
if missing:
    raise SystemExit(f"no answer for pictures {missing}: not scored")
by = {}
for k in K:
    by.setdefault(k["condition"], []).append(A[f"{k['n']:02d}"] == "y")
sham = by["sham s=1"]
fa = sum(sham)
print(f"false alarms (sham s=1): {fa} of {len(sham)}")
for cond in ("planted s=1", "planted s=0.5"):
    hits = sum(by[cond])
    _, p = fisher_exact([[hits, len(by[cond]) - hits], [fa, len(sham) - fa]], alternative="greater")
    print(f"hits ({cond}): {hits} of {len(by[cond])}; one-sided Fisher exact against the shams p = {p:.4f}"
          f"{' (below 0.05: seen more often than in shams)' if p < 0.05 else ''}")
print("\nevery answer:")
for k in K:
    n = f"{k['n']:02d}"
    print(f"  {n} {A[n]}  {k['condition']:14s} {k['target']}")
