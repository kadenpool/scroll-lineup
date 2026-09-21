"""Check where a sharp scan sits inside a scroll's coarse scan, using cross-section IMAGES (lesson L34).
Usage: xsec_check.py SCROLL COARSE_VOL FINE_VOL MM_HINT [OUT_TAG]
  1. Orientation from the OUTLINE: the scroll's outline changes slowly with height, so comparing outlines near
     MM_HINT finds the sharp scan's rotation even when MM_HINT is several mm off. The best unmirrored and the
     best mirrored orientation both go forward.
  2. Full height scan on INTERNAL DETAIL (band-passed: cracks and wraps): for every coarse height, compare with the
     sharp scan's cross-sections at 20/50/80% of its height, for each orientation +-1 degree. The true placement
     matches at all heights at once; a wrong one does not.
  3. Refine angle (0.25 deg) and height at the winner with 5 sharp heights. Report the score, the best score more
     than 3 mm away (the margin), the score at MM_HINT and the scan median.
Positive control: PHerc1203 with MM_HINT 90.5 (the wrong 1D answer) must return ~74.3 mm (align1203.json: 0.82).
Writes xsec_<SCROLL>.json and xsec_<SCROLL>.png (sharp | coarse at best | coarse at MM_HINT)."""
import sys, re, json, time, numpy as np, zarr, fsspec
from scipy import ndimage as ndi
from scipy.fft import rfft2, irfft2, next_fast_len
from PIL import Image, ImageDraw
t0 = time.time; B = "vesuvius-challenge-open-data"; WK = 4
scroll, CVOL, FVOL, mm_hint = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4])
TAG = sys.argv[5] if len(sys.argv) > 5 else scroll
um = lambda v: float(re.search(r"-(\d+\.\d+)um-", v).group(1))
# levels chosen so both cross-sections are ~75 um/px (e.g. 9.36 um -> L3, 45.5 um -> L1); fall back to the
# deepest level that exists (1.1 um scans may stop at L5)
op = lambda v, l: zarr.open(fsspec.get_mapper(f"s3://{B}/{scroll}/volumes/{v}/{l}", anon=True), mode="r")
def open_level(v, want):
    for l in range(want, -1, -1):
        try: return op(v, l), l
        except Exception: continue
    raise RuntimeError(f"no readable level for {v}")
C, LC = open_level(CVOL, min(5, max(0, int(round(np.log2(75.0 / um(CVOL)))))))
vc = um(CVOL) * 2**LC
F, LF = open_level(FVOL, max(0, int(round(np.log2(vc / um(FVOL))))))
vf = um(FVOL) * 2**LF; r = vf / vc; NC = C.shape[0]
log = lambda s: print(f"{s} ({time.time-t0:.0f}s)", flush=True)
log(f"{scroll}: coarse L{LC} {C.shape} {vc:.1f}um | fine L{LF} {F.shape} {vf:.1f}um | ratio {r:.4f}")
H = next_fast_len(int(max(C.shape[1], F.shape[1] * r) * 1.5) + 8); W = next_fast_len(int(max(C.shape[2], F.shape[2] * r) * 1.5) + 8)
def pad(a):
    o = np.zeros((H, W), np.float32); h, w = min(a.shape[0], H), min(a.shape[1], W); o[:h, :w] = a[:h, :w]; return o
def band(a):      # internal detail: cracks, wraps
    a = a.astype(np.float32); m = a > 0; b = ndi.gaussian_filter(a, 1.0) - ndi.gaussian_filter(a, 6.0); b[~m] = 0
    s = b[m].std if m.sum > 100 else 1.0; return b / max(s, 1e-6)
def outline(a):   # material mask, smoothed, zero-mean: the scroll's outline
    m = ndi.gaussian_filter((a > 0).astype(np.float32), 2.0); return m - m.mean
def spec(img): return rfft2(pad(img), workers=WK), float(np.linalg.norm(img))
def ncc(A, Bs):   # A, Bs from spec; returns (ncc, dy, dx): image B shifted by (dy, dx) best matches image A
    cc = irfft2(A[0] * np.conj(Bs[0]), s=(H, W), workers=WK); k = int(np.argmax(cc)); dy, dx = np.unravel_index(k, cc.shape)
    return float(cc.flat[k] / (A[1] * Bs[1] + 1e-9)), int(dy if dy <= H // 2 else dy - H), int(dx if dx <= W // 2 else dx - W)
def orient(a, ang, flip):
    a = a[:, ::-1] if flip else a
    return ndi.rotate(a, ang, reshape=True, order=1) if ang else a
fine_raw, fcache, ccache, cout = {}, {}, {}, {}
def fraw(zf):
    if zf not in fine_raw: fine_raw[zf] = ndi.zoom(np.asarray(F[zf]).astype(np.float32), r, order=1)
    return fine_raw[zf]
def fband(zf, an, fl):
    k = (zf, round(float(an), 3), fl)
    if k not in fcache: fcache[k] = spec(band(orient(fraw(zf), an, fl)))
    return fcache[k]
def cband(zc):
    if zc not in ccache: ccache[zc] = spec(band(np.asarray(C[zc])))
    return ccache[zc]
def coutl(zc):
    zc = min(max(zc, 0), NC - 1)
    if zc not in cout: cout[zc] = spec(outline(np.asarray(C[zc])))
    return cout[zc]
zof = lambda fr: int(round(fr * (F.shape[0] - 1)))
czc = lambda start, zf: int(round(start + zf * r))
i_hint = int(round(mm_hint * 1000 / vc)); zmid = zof(0.5)
# --- 1. orientation from the outline, near the hint (+-3 mm) ---
def out_score(ang, flip):
    f = spec(outline(orient(fraw(zmid), ang, flip)))
    return max(ncc(coutl(czc(i_hint + d, zmid)), f)[0] for d in (-40, 0, 40))
cand = []
for flip in (False, True):
    sc = [(out_score(a, flip), float(a)) for a in range(0, 360, 3)]
    s0, a0 = max(sc)
    s1, a1 = max((out_score(a, flip), float(a)) for a in np.arange(a0 - 2, a0 + 2.01, 0.5))
    other = max(s for s, a in sc if min(abs(a - a0), 360 - abs(a - a0)) > 15)
    cand.append(dict(mirrored=flip, deg=a1, outline_ncc=s1, outline_best_other_angle=other))
    log(f"outline: mirrored={flip} best {a1:+.1f} deg ncc={s1:.3f} (best >15 deg away {other:.3f})")
# --- 2. full height scan on internal detail ---
VARS = [(c["mirrored"], c["deg"] + da) for c in cand for da in (-1.0, 0.0, 1.0)]
z3 = [zof(fr) for fr in (0.2, 0.5, 0.8)]
M = np.full((NC, len(VARS), len(z3)), np.nan, np.float32); step = C.chunks[0] if C.chunks else 64
for z0 in range(0, NC, step):
    slab = np.asarray(C[z0:z0 + step])
    for k in range(slab.shape[0]):
        if (slab[k] > 0).sum < 1000: continue
        Cs = spec(band(slab[k]))
        for v, (fl, an) in enumerate(VARS):
            for j, zf in enumerate(z3): M[z0 + k, v, j] = ncc(Cs, fband(zf, an, fl))[0]
    if (z0 // step) % 4 == 0: log(f"  scanned {min(z0 + step, NC)}/{NC} coarse slices")
starts = np.arange(-czc(0, z3[-1]), NC); S = np.full((len(starts), len(VARS)), np.nan)
for n, i in enumerate(starts):
    idx = [czc(i, zf) for zf in z3]
    if all(0 <= q < NC for q in idx): S[n] = np.mean([M[q, :, j] for j, q in enumerate(idx)], axis=0)
Sb = np.where(np.isfinite(S).any(1), np.nanmax(np.where(np.isfinite(S), S, -9), 1), np.nan)
bn = int(np.nanargmax(Sb)); bv = int(np.nanargmax(S[bn])); ib = int(starts[bn]); fl_b, an_b = VARS[bv]
other_flip = [v for v, (fl, _) in enumerate(VARS) if fl != fl_b]
log(f"height scan: best start {ib} ({ib*vc/1000:.1f} mm) mirrored={fl_b} {an_b:+.1f} deg score3={Sb[bn]:.3f}")
# --- 3. refine angle and height with 5 sharp heights ---
z5 = [zof(fr) for fr in (0.1, 0.3, 0.5, 0.7, 0.9)]
def score5(start, fl, an):   # heights outside the coarse scan are skipped (needs >= 3); 4 entries failed without this
    q = [(czc(start, zf), zf) for zf in z5]; q = [(x, zf) for x, zf in q if 0 <= x < NC]
    if len(q) < 3: return np.nan, []
    per = [ncc(cband(x), fband(zf, an, fl))[0] for x, zf in q]; return float(np.mean(per)), per
ref = [(score5(i, fl_b, a)[0], i, float(a)) for a in np.arange(an_b - 1, an_b + 1.001, 0.25) for i in range(ib - 3, ib + 4)]
sF, iF, aF = max(x for x in ref if np.isfinite(x[0])); sF, perF = score5(iF, fl_b, aF)
far = np.abs(starts - iF) * vc > 3000
rn = int(np.where(far)[0][np.nanargmax(np.where(far, Sb, np.nan)[far])]) if far.any else None
hn = int(np.where(starts == i_hint)[0][0]) if (starts == i_hint).any else None
out = dict(scroll=scroll, coarse=CVOL, fine=FVOL, level_pair=f"coarse L{LC} / fine L{LF}", ratio=r, orientation_candidates=cand,
           mirrored=bool(fl_b), rotation_deg=aF, best_start_slice=iF, best_mm_start=iF * vc / 1000,
           best_mm_end=(iF + (F.shape[0] - 1) * r) * vc / 1000, score5=sF, per_height5=perF,
           score3_best=float(Sb[bn]), runner_up_mm=None if rn is None else float(starts[rn] * vc / 1000),
           runner_up_score3=None if rn is None else float(Sb[rn]),
           other_mirror_best_score3=float(np.nanmax(S[:, other_flip])) if other_flip else None,
           hint_mm=mm_hint, hint_score3=None if hn is None else float(Sb[hn]), scan_median3=float(np.nanmedian(Sb)),
           seconds=time.time - t0)
json.dump(out, open(f"<work-dir>/xsec_{TAG}.json", "w"), indent=1)
print(json.dumps(out, indent=1), flush=True)
# --- picture: rows = 10/50/90% heights; columns = sharp | coarse at best (aligned) | coarse at hint (aligned) ---
def g(x):
    lo, hi = np.percentile(x[x > 0], [1, 99]) if (x > 0).sum > 100 else (0, 1); return np.clip((x - lo) / max(hi - lo, 1), 0, 1)
rows = []
for zf, fr in zip((z5[0], z5[2], z5[4]), (0.1, 0.5, 0.9)):
    f = orient(fraw(zf), aF, fl_b); tiles, labels = [g(f)], [f"sharp {fr:.0%} height ({'mirrored, ' if fl_b else ''}{aF:+.1f} deg)"]
    for start, name in ((iF, f"coarse @ best {iF*vc/1000:.1f} mm"), (i_hint, f"coarse @ hint {mm_hint:.1f} mm")):
        zc = czc(start, zf)
        if not 0 <= zc < NC: tiles.append(np.zeros_like(tiles[0])); labels.append(name + " (outside)"); continue
        c = np.asarray(C[zc]).astype(np.float32); _, dy, dx = ncc(spec(band(f)), spec(band(c)))
        tiles.append(g(np.roll(np.roll(pad(c), dy, 0), dx, 1)[:f.shape[0], :f.shape[1]])); labels.append(name)
    row = []
    for t, lab in zip(tiles, labels):
        im = Image.fromarray((t * 255).astype(np.uint8)).resize((420, 420)).convert("RGB"); ImageDraw.Draw(im).text((6, 6), lab, fill=(255, 60, 60))
        row.append(np.pad(np.asarray(im), ((4, 4), (4, 4), (0, 0)), constant_values=255))
    rows.append(np.hstack(row))
Image.fromarray(np.vstack(rows)).save(f"<work-dir>/xsec_{TAG}.png"); log("XSEC_DONE")
