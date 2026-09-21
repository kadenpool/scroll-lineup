"""Before/after for a depth-corrected re-run: for every window in <rerun_dir>, the original survey's ink map (default
or mesh depth) vs the re-run's (measured depth), both depth orders. Prints ink share (>0.5) and writing-likeness
features side by side and saves a picture: rows = windows, columns = before C | before D | after C | after D.
Usage: compare_rerun.py <rerun_dir> <original_glob> <layer_windows.json> <out.png>"""
import json, glob, os, sys, numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, "<run-dir>"); from textlike import features
Image.MAX_IMAGE_PIXELS = None
rr, og, lwf, outp = sys.argv[1:5]
lw = json.load(open(lwf)) if os.path.exists(lwf) else {}
orig = {p.split("/")[-3] + "/" + p.split("/")[-2]: p for p in glob.glob(og + "/*/[CD]/canon_pred_asinput.png")}
names = sorted({p.split("/")[-3] for p in glob.glob(rr + "/*/[CD]/canon_pred_asinput.png")})
T = 360; rows, res = [], []
for n in names:
    tiles = []; line = {"window": n, "layers_after": [lw.get(n, {}).get("start"), lw.get(n, {}).get("end")], "ncc": lw.get(n, {}).get("ncc")}
    for tag, src in (("before", orig), ("after", None)):
        for s in "CD":
            p = src.get(f"{n}/{s}") if src is not None else f"{rr}/{n}/{s}/canon_pred_asinput.png"
            if not p or not os.path.exists(p): tiles.append(np.full((T, T), 40, np.uint8)); line[f"{tag}_{s}"] = None; continue
            A = np.asarray(Image.open(p)); f = features(A.astype(np.float32) / 255, 2.403)
            line[f"{tag}_{s}"] = {k: round(v, 3) for k, v in (f or {}).items() if isinstance(v, float)}
            tiles.append(np.asarray(Image.fromarray(A).resize((T, T), Image.BILINEAR)))
    res.append(line); rows.append(np.hstack([np.pad(t, 3, constant_values=255) for t in tiles]))
    b = [line[k]["ink_frac"] * 100 if line[k] else float("nan") for k in ("before_C", "before_D", "after_C", "after_D")]
    print(f"{n[-40:]:40s} ink% before C {b[0]:5.1f} D {b[1]:5.1f} | after C {b[2]:5.1f} D {b[3]:5.1f} | layers {line['layers_after']} ncc {line['ncc']}", flush=True)
json.dump(res, open(outp.replace(".png", ".json"), "w"), indent=1)
if rows:
    im = Image.fromarray(np.vstack(rows)).convert("RGB"); d = ImageDraw.Draw(im)
    for i, t in enumerate(["before C (old depth)", "before D", "after C (measured depth)", "after D"]): d.text((8 + i * (T + 6), 4), t, fill=(255, 60, 60))
    for j, n in enumerate(names): d.text((8, j * (T + 6) + T - 12), n[-28:], fill=(60, 200, 255))
    im.save(outp); print("saved", outp)
