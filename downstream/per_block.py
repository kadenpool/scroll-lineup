"""Where does an arm lose its reading? AUC per block of the label grid, arm against arm.

Each arm's forward prediction at the centre window [40,61) is carried back onto the label grid through that
arm's own registration (render_px = s * label_px + t), so every arm is scored on the same label pixels,
block by block. Blocks with too few labelled pixels of either class are left out.

    python per_block.py            # official, ours, ours_v2 -> per_block.json
"""
import glob, json, os
import numpy as np, tifffile
from scipy import ndimage as ndi
from scipy.stats import rankdata

HERE = os.path.dirname(os.path.abspath(__file__))
L = np.load(os.path.join(HERE, "labels_w016_crop.npz"))
V, I = L["validation_mask"] > 0, L["inklabels"] > 0
B = 128                                   # label px per block (about 1.2 mm)
MIN_EACH = 300                            # labelled px of each class a block needs to be scored


def auc(s, y):
    y = y.astype(bool); n1 = int(y.sum()); n0 = y.size - n1
    if n1 < MIN_EACH or n0 < MIN_EACH:
        return None
    r = rankdata(s)
    return float((r[y].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def on_labels(tag):
    reg = json.load(open(os.path.join(HERE, f"{tag}_register.json")))
    p = tifffile.imread(sorted(glob.glob(os.path.join(HERE, f"{tag}_sweep", "cuts", "ctl_d40", "preds", "*_forward_*.tif")))[-1])
    p = p.astype(np.float32) / 255.0
    yy, xx = np.mgrid[0:V.shape[0], 0:V.shape[1]].astype(np.float32)
    ry, rx = reg["sy"] * yy + reg["ty"], reg["sx"] * xx + reg["tx"]
    cov = ndi.map_coordinates(np.ones_like(p), [ry, rx], order=0, cval=0.0) > 0.5
    return ndi.map_coordinates(p, [ry, rx], order=1, cval=0.0), cov


def main():
    arms = [t for t in ("official", "ours", "ours_v2") if os.path.exists(os.path.join(HERE, f"{t}_register.json"))]
    preds = {t: on_labels(t) for t in arms}
    common = V & np.logical_and.reduce([c for _, c in preds.values()])
    out = {"block_label_px": B, "arms": arms, "whole": {}, "blocks": []}
    for t in arms:
        out["whole"][t] = auc(preds[t][0][common], I[common])
    H, W = V.shape
    for y0 in range(0, H - B + 1, B):
        for x0 in range(0, W - B + 1, B):
            m = np.zeros_like(common); m[y0:y0 + B, x0:x0 + B] = True; m &= common
            row = {"y0": y0, "x0": x0, "n_val": int(m.sum())}
            for t in arms:
                row[t] = auc(preds[t][0][m], I[m])
            if all(row[t] is not None for t in arms):
                out["blocks"].append(row)
    json.dump(out, open(os.path.join(HERE, "per_block.json"), "w"), indent=1)
    print("whole region, common pixels:", {t: round(v, 4) for t, v in out["whole"].items()})
    print(f"{len(out['blocks'])} blocks scored")
    if "official" in arms:
        for t in arms:
            if t == "official":
                continue
            d = np.array([b["official"] - b[t] for b in out["blocks"]])
            print(f"official minus {t}: median {np.median(d):+.3f}, blocks where {t} is worse {int((d > 0).sum())} of {len(d)}")


if __name__ == "__main__":
    main()
