"""Where each mesh finds the labelled ink, on PHerc0139 w029 (ScrollPrize/villa#1845). Same scan, same model
(seed43 step 60000), same depth window (layers 40-61); only the mesh differs. Each prediction is scored against
the labels mapped onto its own render, exactly as ../sweep.py scores it (V & valid; ink = prediction > 0.5).

  python3 plot_mesh_choice.py            # reads the four files beside it, writes mesh_choice.png
"""
import sys
import numpy as np, tifffile
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch

cp, cl, fp, fl, out = (sys.argv[1:6] if len(sys.argv) > 5 else
    ["coarse_pred_layers40-61.tif", "coarse_labels_on_render.npz", "fine_pred_layers40-61.tif", "fine_labels_on_render.npz", "mesh_choice.png"])
EXPECT = {"coarse": 0.5437, "fine": 0.7219}      # share_on_ink_forward in each arm's sweep_results.json


def classes(pred_tif, labels_npz):
    p = tifffile.imread(pred_tif).astype(np.float32) / 255.0
    L = np.load(labels_npz)
    vv = L["V"] & L["valid"]
    ink, hit = L["I"], p > 0.5
    c = np.zeros(p.shape, np.uint8)                 # 0 not scored
    c[vv & ~ink & ~hit] = 1                          # 1 background, left alone
    c[vv & ~ink & hit] = 2                           # 2 marked outside the labels
    c[vv & ink & ~hit] = 3                           # 3 labelled ink missed
    c[vv & ink & hit] = 4                            # 4 labelled ink found
    cover = (c == 4).sum() / float((c == 3).sum() + (c == 4).sum())
    return c, cover


arms = [("coarse", "Coarse mesh: made on the 9.362 um scan, 187 um grid,\ncarried in by the catalogue's transform", cp, cl, "0.857"),
        ("fine", "Fine mesh: made on the 2.399 um scan, 48 um grid,\nno transform needed", fp, fl, "0.897")]
maps = [(key, title, auc) + classes(pred, lab) for key, title, pred, lab, auc in arms]
for key, title, auc, c, cover in maps:
    assert abs(cover - EXPECT[key]) < 5e-5, (key, cover)      # the picture must say what #1845 says

# crop to the scored regions; the same crops for both rows, so they compare directly
scored = (maps[0][3] > 0) | (maps[1][3] > 0)
cols = np.where(scored.any(axis=0))[0]
spans = np.split(cols, np.where(np.diff(cols) > 50)[0] + 1)
rows = np.where(scored.any(axis=1))[0]
r0, r1 = max(rows.min() - 12, 0), min(rows.max() + 12, scored.shape[0])
crops = [(max(s.min() - 12, 0), min(s.max() + 12, scored.shape[1])) for s in spans]

cmap = ListedColormap(["#bdbdbd", "#111111", "#4c9be8", "#e04b3c", "#35b24a", "#ffffff"])
def row_image(c):
    parts = []
    for k, (a, b) in enumerate(crops):
        if k:
            parts.append(np.full((r1 - r0, 14), 5, np.uint8))      # a white divider between the two regions
        parts.append(c[r0:r1, a:b])
    return np.concatenate(parts, axis=1)
fig, axes = plt.subplots(2, 1, figsize=(6.6, 9.8), dpi=130)
for ax, (key, title, auc, c, cover) in zip(axes, maps):
    ax.imshow(row_image(c), cmap=cmap, vmin=0, vmax=5, interpolation="nearest")
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_title(title + "\nAUC " + auc + "; finds %.1f %% of the labelled ink" % (100 * cover), fontsize=10, loc="left")
fig.legend(handles=[Patch(color="#35b24a", label="labelled ink, found"), Patch(color="#e04b3c", label="labelled ink, missed"),
                    Patch(color="#4c9be8", label="marked outside the labels"), Patch(color="#111111", label="background, left alone"),
                    Patch(color="#bdbdbd", label="not scored")], loc="lower center", ncol=3, fontsize=9, frameon=False)
fig.suptitle("PHerc0139 segment 20250108000004-w029_2025010827, its two labelled regions:\n"
             "same scan, same model, same depth window; only the mesh differs", fontsize=10, x=0.02, ha="left")
fig.tight_layout(rect=(0, 0.07, 1, 0.94))
fig.savefig(out)
print("wrote %s: %d regions, coverage %.4f and %.4f" % (out, len(crops), maps[0][4], maps[1][4]))
