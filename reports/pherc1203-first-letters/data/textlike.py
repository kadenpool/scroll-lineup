"""Writing-likeness features of an ink-probability map window (values 0..1). All lengths in mm.
ink_frac        share of the window's papyrus flagged >0.5
huge_frac       share of flagged ink sitting in blobs larger than 4 mm2 (a letter is ~2x2 mm; folds/patches are bigger)
median_blob_mm2 median area of flagged blobs
stroke_mm       area-weighted median of each blob's thickest point (2 x max distance to the blob edge)
row_score       best, over 36 directions, of the autocorrelation of the ink profile across that direction at a lag of
                2.5-8 mm (text lines repeat; a single fold/band does not). Needs >= 2 lines in the window: weak at 7.5 mm.
"""
import numpy as np
from scipy import ndimage as ndi
def features(P, um_per_px, down=4):
    P = np.asarray(P, np.float32)
    h, w = P.shape[0] // down * down, P.shape[1] // down * down
    Pd = P[:h, :w].reshape(h // down, down, w // down, down).mean((1, 3)); px = um_per_px * down / 1000.0
    valid = ndi.binary_erosion(Pd > 0.02, iterations=3)
    if valid.sum < 1000: return None
    B = (Pd > 0.5) & valid
    out = {"ink_frac": float(B.sum / valid.sum)}
    lab, n = ndi.label(B)
    if n == 0:
        out.update(huge_frac=0.0, median_blob_mm2=0.0, stroke_mm=0.0, n_blobs=0)
    else:
        idx = np.arange(1, n + 1); areas = ndi.sum(B, lab, idx) * px * px
        dt = ndi.distance_transform_edt(B) * px; thick = 2 * ndi.maximum(dt, lab, idx)
        o = np.argsort(thick); cw = np.cumsum(areas[o]) / areas.sum
        # elongation: major/minor axis ratio of each blob > 0.05 mm2 (second moments); area-weighted median.
        # Letter strokes are long; spots are round (the visual difference seen on 1203 vs 343P, 11 Sep).
        el, wts = [], []
        for i, sl in enumerate(ndi.find_objects(lab)):
            if sl is None or areas[i] < 0.05: continue
            yy, xx = np.nonzero(lab[sl] == i + 1)
            if len(yy) < 5: continue
            cv = np.cov(np.vstack([yy, xx])); ev = np.sort(np.linalg.eigvalsh(cv))
            el.append(float(np.sqrt(ev[1] / max(ev[0], 1e-6)))); wts.append(areas[i])
        if el:
            o2 = np.argsort(el); cw2 = np.cumsum(np.array(wts)[o2]) / np.sum(wts); out['elongation'] = float(np.array(el)[o2][np.searchsorted(cw2, 0.5)])
        else: out['elongation'] = 0.0
        out.update(huge_frac=float(areas[areas > 4.0].sum / areas.sum), median_blob_mm2=float(np.median(areas)),
                   stroke_mm=float(thick[o][np.searchsorted(cw, 0.5)]), n_blobs=int(n))
    X = np.where(valid, Pd - Pd[valid].mean, 0.0).astype(np.float32); best = 0.0
    lo, hi = int(round(2.5 / px)), int(round(8.0 / px))
    for ang in range(0, 180, 5):
        R = ndi.rotate(X, ang, reshape=False, order=1); M = ndi.rotate(valid.astype(np.float32), ang, reshape=False, order=0)
        prof = R.sum(1) / np.maximum(M.sum(1), 1); prof = prof[M.sum(1) > 0.5 * M.shape[1]]
        if len(prof) < hi + 5: continue
        prof = prof - prof.mean; den = (prof * prof).sum
        if den <= 0: continue
        ac = np.array([(prof[:-L] * prof[L:]).sum / den for L in range(lo, min(hi, len(prof) - 5))])
        if len(ac): best = max(best, float(ac.max))
    out["row_score"] = best
    return out
