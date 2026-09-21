"""Score Kaden's blind-check answers against the sealed key.
Usage: python3 score_blind.py [--sheet2] "1W 2N 3? 4W ..."   (W = writing, N = not writing, ? = can't tell; any separator)
Prints per-crop truth + answer, then the W rate on real text vs on ours. Ours reading as W about as often as real text
= a human sees writing in our maps; ours mostly N while real text is mostly W = our spots are not writing."""
import json, re, sys, os
sheet2 = len(sys.argv) > 1 and sys.argv[1] == "--sheet2"; args = sys.argv[2:] if sheet2 else sys.argv[1:]   # --sheet2: score sheet 2
key = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "blind_key2_DO_NOT_OPEN_until_answered.json" if sheet2 else "blind_key_DO_NOT_OPEN_until_answered.json")))
ans = {m.group(1): m.group(2).upper for m in re.finditer(r"(\d+)\s*[:=.-]?\s*([WwNn?])", " ".join(args))}
missing = [k for k in key if k not in ans]
if missing: print("no answer for:", ", ".join(sorted(missing, key=int)))
rows = {"real": [], "ours": []}
for k in sorted(key, key=int):
    kind = "real" if key[k].startswith("real text") else "ours"; a = ans.get(k, "-"); rows[kind].append(a)
    print(f"#{k:>2}  {a}  {key[k]}")
for kind, a in rows.items:
    n = len(a); print(f"{kind:4s}: W {a.count('W')}/{n}   N {a.count('N')}/{n}   ? {a.count('?')}/{n}")
