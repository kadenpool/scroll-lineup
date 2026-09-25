"""Build blind check 1 (BLIND1_DESIGN.md) from a finished day-3 run: 36 shuffled maps, the private key, and the page.

  python3 blind1_build.py <day-3 run dir> <output dir>

Writes <out>/img/01.png ... (the maps in the order shown), <out>/key.json (number -> target and condition; never
published with the page) and <out>/page.html. Prints the key's sha256, to be recorded before Kaden sees the page.
Everything is fixed by the design: checkpoint seed43_step060000, forward; planted s = 1, planted s = 0.5 and the
PHerc0846B sham at s = 1 for every target; numpy default_rng(20260925); the job's own preview stretch.
"""
import hashlib, json, os, sys
import numpy as np
from PIL import Image

run, out = sys.argv[1].rstrip("/"), sys.argv[2].rstrip("/")
TAG, D, SEED = "seed43_step060000", "forward", 20260925
CONDITIONS = (("planted s=1", "swap__s1"), ("planted s=0.5", "swap__s0.5"), ("sham s=1", "swap__sham1"))
R = json.load(open(f"{run}/out/results.json"))
Z = np.load(f"{run}/out/maps_{TAG}.npz")
targets = sorted(n.split("__")[0] for n, j in R["jobs"].items() if j["kind"] == "clean")
items = [(t, cond, f"{t}__{job}__{D}") for t in targets for cond, job in CONDITIONS]
missing = [k for _, _, k in items if k not in Z.files]
if missing:
    raise SystemExit(f"maps missing from maps_{TAG}.npz: {missing}")
order = np.random.default_rng(SEED).permutation(len(items))
os.makedirs(f"{out}/img", exist_ok=True)
key = []
for shown, i in enumerate(order, start=1):
    t, cond, k = items[i]
    p = Z[k].astype(np.float32) / 255.0
    Image.fromarray((np.clip((p - 0.25) / 0.5, 0, 1) * 255).astype(np.uint8)).save(f"{out}/img/{shown:02d}.png")
    key.append({"n": shown, "target": t, "condition": cond, "map": k})
blob = json.dumps({"design": "BLIND1_DESIGN.md", "checkpoint": TAG, "direction": D, "seed": SEED, "key": key}, indent=1)
open(f"{out}/key.json", "w").write(blob)
tpl = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "blind1_page.html")).read()
open(f"{out}/page.html", "w").write(tpl.replace("__COUNT__", str(len(items))))
print(f"{len(items)} maps from {len(targets)} targets; key sha256 {hashlib.sha256(blob.encode()).hexdigest()}")
