"""Blind human check, SHEET 2: same format as sheet 1, but OUR crops come from the depth-CORRECTED maps (reruns and the
new-band survey) and the real-text crops come from published segments NOT used on sheet 1. Row 1: 3 labelled examples
of real text. Grid: numbered 5 mm crops, 8 real + up to 8 ours, shuffled. Key written separately.
Usage: blind_sheet2.py <ours_list.json: [[map_dir, tag], ...]>  -> kag_out/blind_sheet2.png + kag_out/blind_key2.json"""
import io, json, sys, glob, numpy as np, fsspec, tifffile
from PIL import Image, ImageDraw
Image.MAX_IMAGE_PIXELS = None
R = "<run-dir>"; rng = np.random.default_rng(20260912)
def crop_px(um): return int(round(5000 / um))
def densest(a, W):
    best = None                                  # densest FULLY covered 5 mm crop (a black edge would give ours away)
    for y in range(0, a.shape[0] - W + 1, 64):
        for x in range(0, a.shape[1] - W + 1, 64):
            w = a[y:y + W, x:x + W]
            if (w > 5).mean() < 0.9995: continue
            f = (w > 127).mean()
            if best is None or f > best[0]: best = (f, w)
    return None if best is None else best[1]
fs = fsspec.filesystem("s3", anon=True); B = "vesuvius-challenge-open-data"; text = []
for seg in ("PHerc0139/segments/20250108000001-w026_2025010854", "PHerc0139/segments/20250108000004-w029_2025010827", "PHerc0139/segments/20250831000000-w040_2025083102"):
    pn = [f for f in fs.ls(f"{B}/{seg}/ink-detection", detail=False) if f.endswith(".tif") and "new_canon" in f][0]
    P = tifffile.imread(io.BytesIO(fs.cat(pn))); W = crop_px(2.399); cands = []
    for _ in range(4000):
        y, x = rng.integers(0, P.shape[0] - W), rng.integers(0, P.shape[1] - W); w = P[y:y + W, x:x + W]
        if (w > 5).mean() > 0.97 and 0.12 <= (w > 127).mean() <= 0.30: cands.append(w)
        if len(cands) >= 12: break
    text += [(c, f"real text {seg.split('/')[0]} {seg.split('/')[2][15:19]}") for c in cands[:4]]
    del P
rng.shuffle(text)
ours = []
for d, tag in json.load(open(sys.argv[1])):
    fl = glob.glob(f"{R}/{d}/canon_pred_asinput.png")
    if not fl: print("missing", d); continue
    c = densest(np.asarray(Image.open(fl[0])), crop_px(2.403))
    if c is None: print("no fully covered crop in", d); continue
    ours.append((c, f"ours {tag} {d.split('/')[-2][-26:]}/{d.split('/')[-1]} ink {100 * (c > 127).mean():.0f}%"))
train, blind_text = text[:3], text[3:11]
items = blind_text + ours[:8]; order = rng.permutation(len(items)); key = {}
def tile(a, lab, n=380):
    im = Image.fromarray(a).convert("L").resize((n, n), Image.LANCZOS).convert("RGB"); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, n, 24], fill=(0, 0, 0)); d.text((6, 6), lab, fill=(255, 220, 0)); return np.pad(np.asarray(im), ((4, 4), (4, 4), (0, 0)), constant_values=255)
rows = [np.hstack([tile(a, "SHEET 2 EXAMPLE: real writing") for a, l in train] + [np.full((388, 388, 3), 255, np.uint8)])]
grid = []
for k, i in enumerate(order):
    a, l = items[i]; key[str(k + 1)] = l; grid.append(tile(a, f"#{k + 1}"))
while len(grid) % 4: grid.append(np.full_like(grid[0], 255))
for r in range(len(grid) // 4): rows.append(np.hstack(grid[r * 4:(r + 1) * 4]))
Image.fromarray(np.vstack(rows)).save(f"{R}/kag_out/blind_sheet2.png"); json.dump(key, open(f"{R}/kag_out/blind_key2.json", "w"), indent=1)
print("sheet 2: 3 examples +", len(items), "blind crops; ours in grid:", len(ours[:8]))
