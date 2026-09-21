"""Blind human check. Row 1: 3 LABELLED examples of real text (published maps). Grid: 16 numbered 5 mm crops, 8 real
text (published 0139/343P maps, different crops) + 8 ours (densest crops of the strongest 1203 and 0846A responses),
shuffled. Same display scale. Key written separately (blind_key.json) - not shown on the sheet."""
import io, json, glob, numpy as np, fsspec, tifffile
from PIL import Image, ImageDraw
from scipy.ndimage import uniform_filter
Image.MAX_IMAGE_PIXELS = None
R = "<run-dir>"; rng = np.random.default_rng(20260911)
def crop_px(um): return int(round(5000 / um))
def densest(a, W):
    # densest 5 mm crop that is FULLY covered (no black out-of-zone edge: that would give ours away in a blind test)
    best = None
    for y in range(0, a.shape[0] - W + 1, 64):
        for x in range(0, a.shape[1] - W + 1, 64):
            w = a[y:y + W, x:x + W]
            if (w > 5).mean() < 0.9995: continue
            f = (w > 127).mean()
            if best is None or f > best[0]: best = (f, w)
    return None if best is None else best[1]
fs = fsspec.filesystem("s3", anon=True); B = "vesuvius-challenge-open-data"; text = []
for seg, um in (("PHerc0139/segments/20250108000000-w025_2025010863", 2.399), ("PHerc0139/segments/20250108000002-w027_2025010845", 2.399), ("PHerc0343P/segments/20250511003658-tifxyz", 2.215)):
    pn = [f for f in fs.ls(f"{B}/{seg}/ink-detection", detail=False) if f.endswith(".tif") and "new_canon" in f][0]
    P = tifffile.imread(io.BytesIO(fs.cat(pn))); W = crop_px(um); cands = []
    for _ in range(3000):
        y, x = rng.integers(0, P.shape[0] - W), rng.integers(0, P.shape[1] - W); w = P[y:y + W, x:x + W]
        if (w > 5).mean() > 0.97 and 0.12 <= (w > 127).mean() <= 0.30: cands.append(w)
        if len(cands) >= 12: break
    text += [(c, f"real text {seg.split('/')[0]}") for c in cands[:4]]
rng.shuffle(text)
ours_paths = [("kag_out/canoncen/p1203-sel-windows__auto_grown_20250925223153537_r35_c35/D", "1203"), ("kag_out/survey_b1/auto_grown_20250930104534929_s_r42_c126/D", "1203"),
              ("kag_out/survey_b0/auto_grown_20250930104534929_s_r2_c86/C", "1203"), ("kag_out/canoncen/p1203-sel-windows__auto_grown_20251005221856743_r190_c90/D", "1203"),
              ("kag_out/canoncen/p1203-sel-windows__auto_grown_20251005221856743_r145_c105/C", "1203"), ("kag_out/big3/auto_grown_20251005221856743_big_r170_c70/C", "1203"),
              ("kag_out/s0846a_b0/auto_grown_20260911025522741_r65_c75/D", "0846A"), ("kag_out/s0846a_b0/auto_grown_20260911024106966_r70_c75/D", "0846A"),
              ("kag_out/s0846a_b0/auto_grown_20260911024106908_r50_c40/C", "0846A"), ("kag_out/survey_b1/auto_grown_20251005221856743_s_r140_c64/C", "1203"),
              ("kag_out/big2/auto_grown_20250930104534929_big_r22_c106/C", "1203")]
ours = []
for p, tag in ours_paths:
    fl = glob.glob(f"{R}/{p}/canon_pred_asinput.png") or glob.glob(f"{R}/kag_out/*/{p.split('/', 2)[2]}/canon_pred_asinput.png")
    if not fl: print("missing", p); continue
    c = densest(np.asarray(Image.open(fl[0])), crop_px(2.403))
    if c is None: print('no fully covered crop in', p); continue
    ours.append((c, f"ours {tag} {p.split('/')[-2][-26:]}/{p.split('/')[-1]} ink {100 * (c > 127).mean():.0f}%"))
train, blind_text = text[:3], text[3:11]
items = blind_text + ours[:8]; order = rng.permutation(len(items)); key = {}
def tile(a, lab, n=380):
    im = Image.fromarray(a).convert("L").resize((n, n), Image.LANCZOS).convert("RGB"); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, n, 24], fill=(0, 0, 0)); d.text((6, 6), lab, fill=(255, 220, 0)); return np.pad(np.asarray(im), ((4, 4), (4, 4), (0, 0)), constant_values=255)
rows = [np.hstack([tile(a, f"EXAMPLE: real writing ({l.split()[-1]})") for a, l in train] + [np.full((388, 388 * 1, 3), 255, np.uint8)])]
grid = []
for k, i in enumerate(order):
    a, l = items[i]; key[str(k + 1)] = l; grid.append(tile(a, f"#{k + 1}"))
while len(grid) % 4: grid.append(np.full_like(grid[0], 255))
for r in range(len(grid) // 4): rows.append(np.hstack(grid[r * 4:(r + 1) * 4]))
Image.fromarray(np.vstack(rows)).save(f"{R}/kag_out/blind_sheet.png"); json.dump(key, open(f"{R}/kag_out/blind_key.json", "w"), indent=1)
print("sheet: 3 examples +", len(items), "blind crops; ours in grid:", len(ours[:8]))
