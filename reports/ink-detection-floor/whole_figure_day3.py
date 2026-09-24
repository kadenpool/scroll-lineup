"""One figure of the models' own output on the seven PHerc0846B surfaces: for each surface, the CT (plane 15, where
the surface lies) beside each checkpoint's map in its primary direction (forward), all at the same size, each map
labelled with its checkpoint's floor from the run's readout (PREREG amendment 1: shown with the floor beside it).

  python3 whole_figure_day3.py <folder with whole_maps_<checkpoint>.npz> <surfaces folder> <day-3 results.json> <out .png>

The maps are the raw ones the job saved (uint8, 0 to 255 for 0 to 1), shown as the job's own previews are: every
4th pixel, value 0.25 to 0.75 stretched to black to white.
"""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw

maps, surf, res, dst = sys.argv[1].rstrip("/"), sys.argv[2].rstrip("/"), sys.argv[3], sys.argv[4]
READ = json.load(open(res))["readout"]


def floor(t):
    g = READ[t]
    if not g["read"]:
        return "no floor, " + ("control moved" if not g["control_ok"] else "checks failed")
    return "floor " + ("above 1" if g["detection_floor"] is None else "%.2f" % g["detection_floor"])


TAGS = ("seed42_step010000", "seed43_step060000")
PX, LABEL = 380, 22
Z = {t: np.load(f"{maps}/whole_maps_{t}.npz") for t in TAGS}


def preview(p):
    return Image.fromarray((np.clip((p.astype(np.float32) / 255.0 - 0.25) / 0.5, 0, 1)[::4, ::4] * 255).astype(np.uint8))


rows = []
for s in sorted(d for d in os.listdir(surf) if d.startswith("s0")):
    tiles = [Image.open(f"{surf}/{s}/preview_plane15.png").convert("L")]
    tiles += [preview(Z[t][f"whole_{s}__forward"]) for t in TAGS]
    row = Image.new("L", (3 * PX + 2 * 8, PX + LABEL), 0)
    names = ["CT, plane 15"] + [f"{t.split('_')[0]}, forward ({floor(t)})" for t in TAGS]
    for i, (im, name) in enumerate(zip(tiles, names)):
        row.paste(im.resize((PX, PX), Image.BILINEAR), (i * (PX + 8), LABEL))
        ImageDraw.Draw(row).text((i * (PX + 8) + 4, 4), f"{s}  {name}", fill=255)
    rows.append(np.asarray(row))
gap = np.zeros((10, rows[0].shape[1]), np.uint8)
out = np.concatenate([x for r in rows for x in (r, gap)][:-1], 0)
Image.fromarray(out).save(dst, optimize=True)
print(f"wrote {dst}: {out.shape[1]} x {out.shape[0]} px, {os.path.getsize(dst) / 1e6:.1f} MB")
