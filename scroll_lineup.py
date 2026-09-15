#!/usr/bin/env python3
"""scroll-lineup - line up two CT scans of the same scroll.

Usage
  python scroll_lineup.py MOVING_URL FIXED_URL --out DIR [options]

  MOVING_URL, FIXED_URL: OME-Zarr volume roots, e.g.
    s3://vesuvius-challenge-open-data/PHerc1203/volumes/20260319130212-2.403um-0.2m-77keV-masked.zarr
    https://vesuvius-challenge-open-data.s3.amazonaws.com/PHerc1203/volumes/2025...-9.362um-...zarr/
  Output DIR/transform.json in the challenge's own format: a 3x4 "transformation_matrix" that maps a
  MOVING level-0 voxel (x, y, z) to a FIXED level-0 voxel (x, y, z), plus the automatic landmarks
  used to fit it. DIR/report.json has every intermediate number; DIR/qc.png is the picture to look at.

Method (details and limits in README.md)
  G1  whole-scroll search (~300 um, finer for small objects): every cross-section of the taller scan against
      5 cross-sections of the shorter one, compared as polar signatures around the material centroid (scroll
      outline + inner detail), so all 360 rotations, mirror images and upside-down placements are scored at
      once. If that is inconclusive or the shorter scan sees only part of the cross-section, a full 2D search
      (every 5 degrees, both mirror images) is added.
  G2  the best G1 answers re-scored at ~150 um with full 2D image matching (inner detail), refining rotation,
      height and height scale; the winner gives a first 3D transform (tilt from the xy drift with height).
  B   3D block matching at ~75, ~37 and ~19 um: dozens of small blocks of the shorter scan are matched inside
      the other scan (masked normalised cross-correlation, sub-voxel peak); the block centres become landmarks
      and a 12-parameter affine is fitted with outlier rejection, two rounds per level. The search box widens
      when too few blocks match. A final CONFIDENCE line says HIGH or CHECK (with the reasons).
"""
import argparse
import json
import math
import os
import re
import sys
import time
from collections import OrderedDict

import numpy as np
import fsspec
from scipy import ndimage as ndi
from scipy import fft as sfft

VERSION = "0.2.1"
T_START = time.time()


def log(msg):
    print(f"[{time.time() - T_START:7.1f}s] {msg}", flush=True)


# ------------------------------------------------------------------------------------------------
# Volume access: OME-Zarr v2 pyramid, chunks fetched in parallel, loud on network errors
# ------------------------------------------------------------------------------------------------
def _resolve(url):
    url = url.rstrip("/")
    if url.startswith("s3://"):
        return fsspec.filesystem("s3", anon=True), url[5:]
    m = re.match(r"https?://([^./]+)\.s3[.\w-]*\.amazonaws\.com/(.+)", url)
    if m:
        return fsspec.filesystem("s3", anon=True), m.group(1) + "/" + m.group(2)
    if url.startswith("http://") or url.startswith("https://"):
        return fsspec.filesystem("http"), url
    return fsspec.filesystem("file"), os.path.abspath(url)


def _um_from_name(name):
    m = re.search(r"(\d+(?:\.\d+)?)um", name)
    if not m:
        raise SystemExit(f"cannot read the voxel size from '{name}'; pass --um-moving/--um-fixed")
    return float(m.group(1))


class Volume:
    def __init__(self, url, um=None, cache_mb=1200):
        self.url = url.rstrip("/")
        self.fs, self.root = _resolve(self.url)
        self.name = self.root.rsplit("/", 1)[-1]
        self.um = float(um) if um else _um_from_name(self.name)
        self.levels = {}
        for L in range(0, 12):
            try:
                za = json.loads(self.fs.cat(f"{self.root}/{L}/.zarray"))
            except Exception:
                break
            if za.get("zarr_format", 2) != 2:
                raise SystemExit("only zarr v2 pyramids are supported")
            self.levels[L] = za
        if not self.levels:
            raise SystemExit(f"no pyramid levels found under {self.url}")
        self.codec = {}
        for L, za in self.levels.items():
            if za.get("compressor"):
                import numcodecs
                self.codec[L] = numcodecs.get_codec(za["compressor"])
        self.cache, self.cache_bytes, self.cache_max = OrderedDict(), 0, cache_mb * 1e6
        self.bytes_fetched, self.chunks_fetched, self.chunks_missing = 0, 0, 0

    maxlevel = property(lambda self: max(self.levels))

    def shape(self, L):
        return tuple(self.levels[L]["shape"])

    def vox(self, L):
        return self.um * 2 ** L

    # level index <-> physical micrometres (pyramid levels are 2x2x2 means: voxel i covers 2^L*i .. 2^L*(i+1)-1)
    def i2p(self, L, i):
        return self.um * (2 ** L * np.asarray(i, np.float64) + (2 ** L - 1) / 2.0)

    def p2i(self, L, X):
        return (np.asarray(X, np.float64) / self.um - (2 ** L - 1) / 2.0) / 2 ** L

    def extent_um(self):
        return np.array(self.shape(0), float) * self.um      # z, y, x

    def level_for(self, target_um):
        L = int(round(math.log2(max(target_um / self.um, 1.0))))
        return int(np.clip(L, 0, self.maxlevel))

    def _fetch(self, L, keys):
        za = self.levels[L]
        sep = za.get("dimension_separator", ".")
        need = [k for k in keys if (L, k) not in self.cache]
        if need:
            paths = [f"{self.root}/{L}/{sep.join(str(c) for c in k)}" for k in need]
            got = {}
            for attempt in range(4):
                todo = [(k, p) for k, p in zip(need, paths) if k not in got]
                if not todo:
                    break
                res = self.fs.cat([p for _, p in todo], on_error="return")
                fails = []
                for k, p in todo:
                    v = res.get(p)
                    if isinstance(v, (FileNotFoundError,)) or (isinstance(v, Exception) and "404" in str(v)):
                        got[k] = None
                    elif isinstance(v, Exception) or v is None:
                        fails.append((p, repr(v)[:200]))
                    else:
                        got[k] = v
                if fails and attempt == 3:
                    raise RuntimeError(f"{len(fails)} chunk reads failed after retries, e.g. {fails[0]}")
                if fails:
                    time.sleep(2 * (attempt + 1))
            dt = np.dtype(za["dtype"])
            cs = tuple(za["chunks"])
            for k in need:
                b = got[k]
                if b is None:
                    arr = None
                    self.chunks_missing += 1
                else:
                    self.bytes_fetched += len(b)
                    self.chunks_fetched += 1
                    if L in self.codec:
                        b = self.codec[L].decode(b)
                    arr = np.frombuffer(b, dtype=dt).reshape(cs, order=za.get("order", "C"))
                self.cache[(L, k)] = arr
                self.cache_bytes += 0 if arr is None else arr.nbytes
            while self.cache_bytes > self.cache_max and self.cache:
                _, old = self.cache.popitem(last=False)
                self.cache_bytes -= 0 if old is None else old.nbytes
        return {k: self.cache[(L, k)] for k in keys}

    def read(self, L, lo, hi):
        """Voxels [lo, hi) (z, y, x) at level L; outside the volume = 0. Returns float32."""
        za = self.levels[L]
        shp, cs = za["shape"], za["chunks"]
        lo = [int(v) for v in lo]
        hi = [int(v) for v in hi]
        out = np.zeros([h - l for l, h in zip(lo, hi)], np.float32)
        a = [max(l, 0) for l in lo]
        b = [min(h, s) for h, s in zip(hi, shp)]
        if any(bb <= aa for aa, bb in zip(a, b)):
            return out
        rng = [range(aa // c, (bb - 1) // c + 1) for aa, bb, c in zip(a, b, cs)]
        keys = [(i, j, k) for i in rng[0] for j in rng[1] for k in rng[2]]
        # fetch in batches so a big read does not hold every chunk twice
        for s in range(0, len(keys), 256):
            got = self._fetch(L, keys[s:s + 256])
            for key, arr in got.items():
                if arr is None:
                    continue
                c0 = [kk * c for kk, c in zip(key, cs)]
                s0 = [max(aa, cc) for aa, cc in zip(a, c0)]
                s1 = [min(bb, cc + c) for bb, cc, c in zip(b, c0, cs)]
                if any(y <= x for x, y in zip(s0, s1)):
                    continue
                out[s0[0] - lo[0]:s1[0] - lo[0], s0[1] - lo[1]:s1[1] - lo[1], s0[2] - lo[2]:s1[2] - lo[2]] = \
                    arr[s0[0] - c0[0]:s1[0] - c0[0], s0[1] - c0[1]:s1[1] - c0[1], s0[2] - c0[2]:s1[2] - c0[2]]
        return out

    def drop_cache(self, L):
        for k in [k for k in self.cache if k[0] == L]:
            a = self.cache.pop(k)
            self.cache_bytes -= 0 if a is None else a.nbytes

    def occupied_z(self, L):
        """z range [z0, z1) at level L that has any stored chunk (masked volumes omit empty chunks)."""
        try:
            keys = self.fs.ls(f"{self.root}/{L}", detail=False)
            zs = sorted(int(k.rstrip("/").rsplit("/", 1)[-1]) for k in keys if k.rstrip("/").rsplit("/", 1)[-1].isdigit())
            if zs:
                c = self.levels[L]["chunks"][0]
                return zs[0] * c, min((zs[-1] + 1) * c, self.shape(L)[0])
        except Exception:
            pass
        return 0, self.shape(L)[0]


# ------------------------------------------------------------------------------------------------
# 2D images on a physical grid: pixel (a, b) <-> (y, x) = (a*g, b*g) micrometres
# ------------------------------------------------------------------------------------------------
def to_grid(sl, vol, L, g):
    """Resample one level-L slice (y, x) of vol onto the physical grid with spacing g um."""
    v = vol.vox(L)
    f = g / v
    src = sl.astype(np.float32)
    msk = (sl > 0).astype(np.float32)
    if f > 1.3:
        src = ndi.gaussian_filter(src, 0.42 * f)
        msk = ndi.gaussian_filter(msk, 0.42 * f)
    off = -(2 ** L - 1) / 2.0 ** (L + 1)
    shp = (int(math.ceil(sl.shape[0] / f)), int(math.ceil(sl.shape[1] / f)))
    img = ndi.affine_transform(src, [f, f], offset=[off, off], output_shape=shp, order=1)
    m = ndi.affine_transform(msk, [f, f], offset=[off, off], output_shape=shp, order=1) > 0.5
    img[~m] = 0
    return img, m


def detail(img, m, s1=1.0, s2=4.0):
    """Band-pass (inner structure: cracks, gaps between wraps), zero outside the material, unit std."""
    d = ndi.gaussian_filter(img, s1) - ndi.gaussian_filter(img, s2)
    me = ndi.binary_erosion(m, iterations=2) if m.sum() > 400 else m
    d[~me] = 0
    s = d[me].std() if me.sum() > 50 else 1.0
    return d / max(s, 1e-6)


def outline(m, s=1.0):
    o = ndi.gaussian_filter(m.astype(np.float32), s)
    return o - o.mean()


def centroid(m):
    yy, xx = np.nonzero(m)
    return np.array([yy.mean(), xx.mean()]) if len(yy) else np.array([m.shape[0] / 2, m.shape[1] / 2])


def polar(img, c, R, NR, NA):
    r = (np.arange(NR) + 0.5) * R / NR
    ph = np.arange(NA) * 2 * np.pi / NA
    yy = c[0] + r[:, None] * np.sin(ph)[None]
    xx = c[1] + r[:, None] * np.cos(ph)[None]
    p = ndi.map_coordinates(img, [yy, xx], order=1, mode="constant", cval=0.0) * np.sqrt(r)[:, None]
    p = p - p.mean()
    return p / max(np.linalg.norm(p), 1e-9)


def rot2(th):
    c, s = math.cos(th), math.sin(th)
    return np.array([[c, -s], [s, c]])


MIR = np.diag([-1.0, 1.0])          # mirror x


def warp_short(img, g, A, t, out_shape):
    """out(q) = img(A^-1 (q - t)) for q on an (y, x)-pixel grid with spacing g; A, t act on physical (x, y)."""
    Ai = np.linalg.inv(A)
    P = np.array([[0.0, 1.0], [1.0, 0.0]])       # (x, y) <-> (row=y, col=x)
    M = P @ Ai @ P
    off = -(P @ Ai @ t) / g
    return ndi.affine_transform(img, M, offset=off, output_shape=out_shape, order=1)


class FFTCorr:
    """Circular 2D cross-correlation with fixed padding; returns (ncc, dy, dx) where shifting B by (dy, dx) matches A."""

    def __init__(self, H, W, workers=8):
        self.H, self.W, self.wk = H, W, workers

    def pad(self, a):
        o = np.zeros((self.H, self.W), np.float32)
        h, w = min(a.shape[0], self.H), min(a.shape[1], self.W)
        o[:h, :w] = a[:h, :w]
        return o

    def spec(self, a):
        p = self.pad(a)
        return sfft.rfft2(p, workers=self.wk), float(np.linalg.norm(p))

    def corr(self, A, B, subpix=False):
        cc = sfft.irfft2(A[0] * np.conj(B[0]), s=(self.H, self.W), workers=self.wk)
        k = int(np.argmax(cc))
        dy, dx = np.unravel_index(k, cc.shape)
        v = float(cc.flat[k] / (A[1] * B[1] + 1e-9))
        fy = fx = 0.0
        if subpix:
            def par(m1, c0, p1):
                den = m1 - 2 * c0 + p1
                return 0.5 * (m1 - p1) / den if den < 0 else 0.0
            fy = par(cc[dy - 1, dx], cc[dy, dx], cc[(dy + 1) % self.H, dx])
            fx = par(cc[dy, dx - 1], cc[dy, dx], cc[dy, (dx + 1) % self.W])
        dy = dy if dy <= self.H // 2 else dy - self.H
        dx = dx if dx <= self.W // 2 else dx - self.W
        return v, dy + fy, dx + fx


# ------------------------------------------------------------------------------------------------
# 3D transforms (physical micrometres, x y z order): X_tall = Q X_short + c
# ------------------------------------------------------------------------------------------------
def apply(T, X):
    return X @ T[:3, :3].T + T[:3, 3]


def inv(T):
    Ti = np.eye(4)
    Ti[:3, :3] = np.linalg.inv(T[:3, :3])
    Ti[:3, 3] = -Ti[:3, :3] @ T[:3, 3]
    return Ti


def fit_affine(P, Q, w=None):
    """Least-squares affine with Q ~ A P + t (rows are points)."""
    w = np.ones(len(P)) if w is None else w
    X = np.hstack([P, np.ones((len(P), 1))]) * np.sqrt(w)[:, None]
    Y = Q * np.sqrt(w)[:, None]
    B, *_ = np.linalg.lstsq(X, Y, rcond=None)
    T = np.eye(4)
    T[:3, :3] = B[:3].T
    T[:3, 3] = B[3]
    return T


def fit_similarity(P, Q):
    """Umeyama: Q ~ s R P + t, R may be improper if the data say so."""
    mp, mq = P.mean(0), Q.mean(0)
    Pc, Qc = P - mp, Q - mq
    U, S, Vt = np.linalg.svd(Qc.T @ Pc / len(P))
    D = np.eye(3)
    det = np.linalg.det(U @ Vt)
    R = U @ Vt
    s = S.sum() / (Pc ** 2).sum() * len(P)
    T = np.eye(4)
    T[:3, :3] = s * R
    T[:3, 3] = mq - s * R @ mp
    return T


def decompose(Q):
    """scale, mirror flag, in-plane rotation (deg), tilt of the z axis (deg) of a linear map in physical units."""
    det = np.linalg.det(Q)
    s = abs(det) ** (1 / 3)
    z = Q[:, 2] / np.linalg.norm(Q[:, 2])
    tilt = math.degrees(math.acos(min(1.0, abs(z[2]))))
    ang = math.degrees(math.atan2(Q[1, 0], Q[0, 0]))
    return dict(scale=s, improper=bool(det < 0), z_axis_flipped=bool(z[2] < 0), rot_deg=ang, tilt_deg=tilt,
                column_scales=np.linalg.norm(Q, axis=0).tolist())


# ------------------------------------------------------------------------------------------------
# Stage G1: global search with polar signatures
# ------------------------------------------------------------------------------------------------
def load_short_slices(vs, Ls, fracs, zr):
    """Level-Ls slices of the short volume at the given fractions of its occupied z range [zr0, zr1)."""
    z0, z1 = zr
    zs = [int(round(z0 + f * (z1 - 1 - z0))) for f in fracs]
    Y, X = vs.shape(Ls)[1:]
    out = {}
    for z in zs:
        out[z] = vs.read(Ls, (z, 0, 0), (z + 1, Y, X))[0]
    return out


def g1_prepare(vt, Lt, tall, vs, Ls, sl, g):
    """Tall slices and short cross-sections on the physical grid g."""
    Nt = tall.shape[0]
    t_img, t_m = [], []
    for j in range(Nt):
        im, m = to_grid(tall[j], vt, Lt, g)
        t_img.append(im)
        t_m.append(m)
    areas = np.array([m.sum() for m in t_m], float)
    s_img, s_m, s_z = [], [], []
    for z, a in sl.items():
        im, m = to_grid(a, vs, Ls, g)
        s_img.append(im)
        s_m.append(m)
        s_z.append(float(vs.i2p(Ls, z)))
    # usable tall slices: enough material. Reference = 75th percentile of the non-empty slices, not the maximum:
    # One 8.64 um scan has an unmasked slice that is 80 % "material", which silenced every other slice.
    ref_area = np.percentile(areas[areas > 0], 75) if (areas > 0).any() else 1.0
    ok = areas > 0.15 * ref_area
    return dict(Nt=Nt, t_img=t_img, t_m=t_m, areas=areas, ok=ok, ref_area=ref_area, s_img=s_img, s_m=s_m,
                s_z=np.array(s_z), s_areas=np.array([m.sum() for m in s_m], float))


def g1_polar(D, NA=360, NR=72):
    """Scores (Nt, K, 2 mirror, NA rotations) from polar signatures around the material centroids."""
    R = 0.0
    for m in D["s_m"]:
        c = centroid(m)
        yy, xx = np.nonzero(m)
        if len(yy):
            R = max(R, np.percentile(np.hypot(yy - c[0], xx - c[1]), 99))
    R *= 1.08
    feats = {}
    Nt, ok = D["Nt"], D["ok"]
    for name in ("outline", "detail"):
        Pt = np.zeros((Nt, NR, NA), np.float32)
        for j in range(Nt):
            if not ok[j]:
                continue
            f = outline(D["t_m"][j]) if name == "outline" else detail(D["t_img"][j], D["t_m"][j])
            Pt[j] = polar(f, centroid(D["t_m"][j]), R, NR, NA)
        K = len(D["s_m"])
        Ps = np.zeros((K, NR, NA), np.float32)
        for k in range(K):
            f = outline(D["s_m"][k]) if name == "outline" else detail(D["s_img"][k], D["s_m"][k])
            Ps[k] = polar(f, centroid(D["s_m"][k]), R, NR, NA)
        Pm = Ps[:, :, (NA // 2 - np.arange(NA)) % NA]          # mirrored short: phi -> pi - phi
        Ft = sfft.rfft(Pt, axis=-1)
        Fs = sfft.rfft(np.stack([Ps, Pm], 1), axis=-1)            # (K, 2, NR, F)
        C = np.einsum("jrf,kmrf->jkmf", Ft, np.conj(Fs), optimize=True)
        cc = sfft.irfft(C, n=NA, axis=-1).astype(np.float32)       # (Nt, K, 2, NA): peak at the rotation
        cc[~ok] = np.nan
        feats[name] = cc
    return feats, R


def g1_bruteforce(D, g, step_deg=5.0, wk=8):
    """Scores (Nt, K, 2, NA) from full 2D correlation of inner detail at every rotation step. Needs no centroid,
    so it also works when the short scan sees only part of the cross-section (partial field of view)."""
    Nt, ok = D["Nt"], D["ok"]
    NA = int(round(360 / step_deg))
    t_det = [detail(D["t_img"][j], D["t_m"][j]) if ok[j] else None for j in range(Nt)]
    s_det = [detail(im, m) for im, m in zip(D["s_img"], D["s_m"])]
    ht = max(a.shape[0] for a in D["t_img"])
    wt = max(a.shape[1] for a in D["t_img"])
    ds = int(math.ceil(max(math.hypot(*a.shape) for a in s_det))) + 2
    H, W = sfft.next_fast_len(ht + ds), sfft.next_fast_len(wt + ds)
    fc = FFTCorr(H, W, wk)
    idx = [j for j in range(Nt) if ok[j]]
    TF = np.zeros((len(idx), H, W // 2 + 1), np.complex64)
    tn = np.zeros(len(idx), np.float32)
    for i, j in enumerate(idx):
        TF[i], tn[i] = fc.spec(t_det[j])
    cc = np.full((Nt, len(s_det), 2, NA), np.nan, np.float32)
    for m in (0, 1):
        Mm = MIR if m else np.eye(2)
        for a in range(NA):
            A = rot2(math.radians(a * step_deg)) @ Mm
            for k, s in enumerate(s_det):
                cs = centroid(D["s_m"][k])[::-1] * g
                t = np.array([ds / 2.0, ds / 2.0]) * g - A @ cs
                w = warp_short(s, g, A, t, (ds, ds))
                SF, sn = fc.spec(w)
                for c0 in range(0, len(idx), 256):
                    out = sfft.irfft2(TF[c0:c0 + 256] * np.conj(SF)[None], s=(H, W), workers=wk)
                    cc[np.array(idx[c0:c0 + 256]), k, m, a] = out.reshape(out.shape[0], -1).max(1) / (tn[c0:c0 + 256] * sn + 1e-9)
    return {"detail": cc}, NA


def g1_hypotheses(feats, NA, zv, Lt, D, args, label):
    """Combine per-slice scores into placements: upside-down or not, height scale, mirror, rotation, height."""
    s_z = D["s_z"]
    Nt = D["Nt"]
    K = len(s_z)
    k0 = K // 2
    zt = zv.i2p(Lt, np.arange(Nt))
    span = abs(s_z[-1] - s_z[0])
    eps_list = [0.0] if span < 40000 else [-0.01, -0.005, 0.0, 0.005, 0.01]
    allsc = {}
    for sgn in (1, -1):
        for eps in eps_list:
            dz = sgn * (1 + eps) * (s_z - s_z[k0])                 # physical offsets of the K slices
            idx = np.rint(zv.p2i(Lt, zt[:, None] + dz[None, :])).astype(int)   # (Nt start, K)
            inside = (idx >= 0) & (idx < Nt)
            idc = np.clip(idx, 0, Nt - 1)
            for name, cc in feats.items():
                g_ = cc[idc, np.arange(K)[None, :]]               # (Nt, K, 2, NA)
                g_ = np.where(inside[:, :, None, None], g_, np.nan)
                n_in = np.isfinite(g_).sum(1)
                sc = np.where(n_in >= 3, np.nansum(g_, 1) / np.maximum(n_in, 1), np.nan)   # (Nt, 2, NA)
                allsc[(sgn, eps, name)] = sc
    # standardise each feature over the whole hypothesis space and add
    for name in feats:
        v = np.concatenate([allsc[(s, e, name)].ravel() for s in (1, -1) for e in eps_list])
        v = v[np.isfinite(v)]
        med, mad = np.median(v), np.median(np.abs(v - np.median(v))) * 1.4826 + 1e-9
        for s in (1, -1):
            for e in eps_list:
                allsc[(s, e, name)] = (allsc[(s, e, name)] - med) / mad
    cands = []
    for s in (1, -1):
        for e in eps_list:
            tot = sum(allsc[(s, e, name)] for name in feats)
            flat = np.where(np.isfinite(tot), tot, -1e9)
            order = np.argsort(flat.ravel())[::-1][:4000]
            for o in order:
                j, m, a = np.unravel_index(o, flat.shape)
                cands.append(dict(score=float(flat[j, m, a]), sgn=s, eps=e, mirror=int(m), rot_deg=float(a * 360.0 / NA),
                                  z_mid_tall_um=float(zt[j]), source=label,
                                  outline=float(allsc[(s, e, "outline")][j, m, a]) if "outline" in feats else None,
                                  detail=float(allsc[(s, e, "detail")][j, m, a])))
    cands.sort(key=lambda c: -c["score"])
    return cands


def nms(cands, keep_n, keep=None):
    keep = [] if keep is None else keep
    for c in cands:
        dup = False
        for k in keep:
            if k["sgn"] == c["sgn"] and k["mirror"] == c["mirror"] and abs(k["z_mid_tall_um"] - c["z_mid_tall_um"]) < 3000 \
                    and min(abs(k["rot_deg"] - c["rot_deg"]) % 360, 360 - abs(k["rot_deg"] - c["rot_deg"]) % 360) < 20:
                dup = True
                break
        if not dup:
            keep.append(c)
        if len(keep) >= keep_n:
            break
    return keep


def g1_search(zv, Lt, tall, vs, Ls, sl, g, args, rep, partial):
    D = g1_prepare(zv, Lt, tall, vs, Ls, sl, g)
    rep["g1"] = dict(grid_um=g, tall_level=Lt, n_tall_slices=D["Nt"], usable_tall_slices=int(D["ok"].sum()),
                     short_level=Ls, short_z_um=D["s_z"].tolist(), short_area_px=D["s_areas"].tolist(),
                     tall_area_ref_px=float(D["ref_area"]), partial_field_of_view=bool(partial))
    feats, R = g1_polar(D)
    rep["g1"]["radius_px"] = R
    cp = g1_hypotheses(feats, 360, zv, Lt, D, args, "polar")
    kp = nms(cp, args.g1_keep)
    # the polar search is conclusive when its best placement clearly beats the next distinct one; if not (partial
    # field of view, round featureless outline, ...) add the slower 2D search. PHerc0139's 1.129 um scan needed it.
    best = kp[0]["score"] if kp else 0.0
    second = kp[1]["score"] if len(kp) > 1 else 0.0
    inconclusive = best < 10.0 or best < 1.3 * second
    rep["g1"]["polar_best_vs_second"] = [best, second]
    if partial or inconclusive:
        t0 = time.time()
        fb, NAb = g1_bruteforce(D, g)
        cb = g1_hypotheses(fb, NAb, zv, Lt, D, args, "2d")
        why = "partial field of view" if partial else f"polar search inconclusive ({best:.1f} vs {second:.1f})"
        log(f"G1 2D search added: {why} ({time.time() - t0:.0f}s)")
        rep["g1"]["search_2d"] = why
        keep = nms(cb, args.g1_keep // 2 + 1)
        keep = nms(cp, args.g1_keep + 2, keep)
    else:
        keep = kp
    rep["g1"]["candidates"] = keep
    for c in keep:
        log(f"G1 cand ({c['source']}): score {c['score']:6.2f} "
            f"{'UPSIDE-DOWN ' if c['sgn'] < 0 else ''}{'MIRROR ' if c['mirror'] else ''}rot {c['rot_deg']:5.1f} "
            f"zscale {1 + c['eps']:.3f} middle slice at tall z {c['z_mid_tall_um'] / 1000:.2f} mm")
    return keep, D


# ------------------------------------------------------------------------------------------------
# Stage G2: re-score candidates with full 2D matching of inner detail at ~150 um
# ------------------------------------------------------------------------------------------------
def g2_refine(vt, Lt2, tall2, vs, Ls, sl, g2, cands, args, rep):
    Nt = tall2.shape[0]
    zt = vt.i2p(Lt2, np.arange(Nt))
    t_cache = {}

    def tall_feat(j):
        if j not in t_cache:
            im, m = to_grid(tall2[j], vt, Lt2, g2)
            t_cache[j] = (detail(im, m), m)
        return t_cache[j]

    im0, m0 = tall_feat(Nt // 2)
    s_img, s_m, s_z = [], [], []
    for z, a in sl.items():
        im, m = to_grid(a, vs, Ls, g2)
        s_img.append(detail(im, m))
        s_m.append(m)
        s_z.append(float(vs.i2p(Ls, z)))
    s_z = np.array(s_z)
    K = len(s_z)
    k0 = K // 2
    diag_s = max(max(a.shape) for a in s_img) * math.sqrt(2)
    H = sfft.next_fast_len(int(max(im0.shape[0], diag_s) * 1.6) + 8)
    W = sfft.next_fast_len(int(max(im0.shape[1], diag_s) * 1.6) + 8)
    fc = FFTCorr(H, W)
    t_spec = {}

    def tspec(j):
        if j not in t_spec:
            f, m = tall_feat(j)
            t_spec[j] = (fc.spec(f), m)
        return t_spec[j]

    results = []
    for ci, c in enumerate(cands):
        sgn, mir = c["sgn"], c["mirror"]
        Mm = MIR if mir else np.eye(2)
        # centroid alignment for the translation prior (the FFT searches the full shift range anyway)
        jm = int(np.clip(round(float(vt.p2i(Lt2, c["z_mid_tall_um"]))), 0, Nt - 1))
        ct = centroid(tall_feat(jm)[1])[::-1] * g2                    # (x, y) physical
        best = None
        zstep = vt.vox(Lt2)
        for eps in sorted(set([c["eps"] - 0.005, c["eps"], c["eps"] + 0.005])):
            for dth in np.arange(-3.0, 3.01, 1.0):
                th = math.radians(c["rot_deg"] + dth)
                A = rot2(th) @ Mm
                specs = []
                for k in range(K):
                    cs = centroid(s_m[k])[::-1] * g2
                    t = ct - A @ cs
                    w = warp_short(s_img[k], g2, A, t, im0.shape)
                    specs.append((fc.spec(w), t))
                for dz in np.arange(-5, 6):
                    zmid = c["z_mid_tall_um"] + dz * zstep
                    per = []
                    for k in range(K):
                        Z = zmid + sgn * (1 + eps) * (s_z[k] - s_z[k0])
                        j = int(round(float(vt.p2i(Lt2, Z))))
                        if not 0 <= j < Nt:
                            continue
                        v, dy, dx = fc.corr(tspec(j)[0], specs[k][0])
                        per.append(v)
                    if len(per) >= 3:
                        sc = float(np.mean(per))
                        if best is None or sc > best[0]:
                            best = (sc, eps, c["rot_deg"] + dth, zmid)
        # finer rotation around the best
        sc0, eps, rdeg, zmid = best
        for dth in np.arange(-0.75, 0.76, 0.25):
            th = math.radians(rdeg + dth)
            A = rot2(th) @ Mm
            for dz in (-1, 0, 1):
                zm = zmid + dz * zstep
                per = []
                for k in range(K):
                    cs = centroid(s_m[k])[::-1] * g2
                    t = ct - A @ cs
                    w = warp_short(s_img[k], g2, A, t, im0.shape)
                    Z = zm + sgn * (1 + eps) * (s_z[k] - s_z[k0])
                    j = int(round(float(vt.p2i(Lt2, Z))))
                    if not 0 <= j < Nt:
                        continue
                    v, dy, dx = fc.corr(tspec(j)[0], fc.spec(w))
                    per.append(v)
                if len(per) >= 3 and np.mean(per) > best[0]:
                    best = (float(np.mean(per)), eps, rdeg + dth, zm)
        results.append(dict(cand=ci, score=best[0], sgn=sgn, mirror=mir, eps=best[1], rot_deg=best[2] % 360,
                            z_mid_tall_um=best[3], ct=ct.tolist()))
        log(f"G2 cand {ci}: detail ncc {best[0]:.3f} rot {best[2] % 360:.2f} zscale {1 + best[1]:.4f} "
            f"mid at {best[3] / 1000:.2f} mm{' UPSIDE-DOWN' if sgn < 0 else ''}{' MIRROR' if mir else ''}")
    results.sort(key=lambda r: -r["score"])
    win = results[0]
    # per-height placement of the winner: best tall z (sub-slice) and xy shift, for more heights
    sgn, mir, eps = win["sgn"], win["mirror"], win["eps"]
    A = rot2(math.radians(win["rot_deg"])) @ (MIR if mir else np.eye(2))
    ct = np.array(win["ct"])
    rows = []
    for k in range(K):
        cs = centroid(s_m[k])[::-1] * g2
        t = ct - A @ cs
        w = warp_short(s_img[k], g2, A, t, im0.shape)
        sw = fc.spec(w)
        Z = win["z_mid_tall_um"] + sgn * (1 + eps) * (s_z[k] - s_z[k0])
        j0 = int(round(float(vt.p2i(Lt2, Z))))
        prof = []
        for j in range(j0 - 4, j0 + 5):
            if 0 <= j < Nt:
                v, dy, dx = fc.corr(tspec(j)[0], sw, subpix=True)
                prof.append((j, v, dy, dx))
        if len(prof) < 3:
            continue
        i = int(np.argmax([p[1] for p in prof]))
        jb, vb, dy, dx = prof[i]
        fj = 0.0
        if 0 < i < len(prof) - 1:
            y0, y1, y2 = prof[i - 1][1], prof[i][1], prof[i + 1][1]
            den = y0 - 2 * y1 + y2
            fj = 0.5 * (y0 - y2) / den if den < 0 else 0.0
        zt_best = float(vt.i2p(Lt2, jb + fj))
        # short point: the short centroid at height s_z[k] -> tall (x, y) = A cs + t + shift
        q = A @ cs + t + np.array([dx, dy]) * g2
        rows.append(dict(k=k, short_z_um=float(s_z[k]), short_xy_um=cs.tolist(), tall_z_um=zt_best, tall_xy_um=q.tolist(),
                         ncc=vb))
    win["per_height"] = rows
    rep["g2"] = dict(grid_um=g2, tall_level=Lt2, results=results,
                     margin=(results[0]["score"] - results[1]["score"]) if len(results) > 1 else None)
    return win


def initial_transform(win):
    """3D physical transform short -> tall from the G2 per-height placements."""
    rows = win["per_height"]
    zs = np.array([r["short_z_um"] for r in rows])
    zt = np.array([r["tall_z_um"] for r in rows])
    xs = np.array([r["short_xy_um"] for r in rows])
    xt = np.array([r["tall_xy_um"] for r in rows])
    A2 = rot2(math.radians(win["rot_deg"])) @ (MIR if win["mirror"] else np.eye(2))
    bz, az = np.polyfit(zs, zt, 1)
    # xy of the tall point minus the in-plane map of the short point, as a linear function of short z
    resid = xt - xs @ A2.T
    tx = np.polyfit(zs, resid[:, 0], 1)
    ty = np.polyfit(zs, resid[:, 1], 1)
    c1 = np.array([A2[0, 0], A2[1, 0], 0.0])
    c2 = np.array([A2[0, 1], A2[1, 1], 0.0])
    c3 = np.array([tx[0], ty[0], bz])
    n = c3 / np.linalg.norm(c3)
    s = float(np.clip(np.linalg.norm(c3), 0.98, 1.02))   # oblique cuts make the drift-derived scale noisy
    c1p = c1 - (c1 @ n) * n
    c1p /= np.linalg.norm(c1p)
    c2p = c2 - (c2 @ n) * n - (c2 @ c1p) * c1p
    c2p /= np.linalg.norm(c2p)
    Q = np.stack([c1p, c2p, n], 1) * s
    # anchor: the middle row
    i = len(rows) // 2
    Ps = np.array([xs[i, 0], xs[i, 1], zs[i]])
    Pt = np.array([xt[i, 0], xt[i, 1], zt[i]])
    T = np.eye(4)
    T[:3, :3] = Q
    T[:3, 3] = Pt - Q @ Ps
    return T


# ------------------------------------------------------------------------------------------------
# Stage B: 3D block matching -> automatic landmarks -> affine
# ------------------------------------------------------------------------------------------------
def masked_ncc_valid(big, small, w):
    """NCC of `small` (weights w) against every valid placement inside `big`. Returns array of shifts."""
    shp = [b - s + 1 for b, s in zip(big.shape, small.shape)]
    fs = [sfft.next_fast_len(b) for b in big.shape]
    sw = small * w
    sw = sw - w * (sw.sum() / max(w.sum(), 1e-9))
    Fb = sfft.rfftn(big, fs, workers=8)
    Fb2 = sfft.rfftn(big * big, fs, workers=8)

    def corr(F, k):
        Fk = sfft.rfftn(k[::-1, ::-1, ::-1], fs, workers=8)
        full = sfft.irfftn(F * Fk, fs, workers=8)
        s0 = [s - 1 for s in small.shape]
        return full[s0[0]:s0[0] + shp[0], s0[1]:s0[1] + shp[1], s0[2]:s0[2] + shp[2]]

    num = corr(Fb, sw)
    sb = corr(Fb, w)
    sb2 = corr(Fb2, w)
    n = w.sum()
    varb = np.maximum(sb2 - sb * sb / max(n, 1e-9), 1e-9)
    return num / (np.sqrt(varb) * np.sqrt((sw * sw).sum()) + 1e-9)


def dog3(a, s1, s2):
    return ndi.gaussian_filter(a, s1) - ndi.gaussian_filter(a, s2)


def block_pass(vs, vt, T, Ls, Lt, centers, bsz, rad, args, tag):
    """centers: level-Ls block corner indices (z, y, x). Returns list of dicts with landmark pairs (physical xyz)."""
    out = []
    mg = 6                                          # filter margin
    n_ext = bsz + 2 * rad
    for ci, c0 in enumerate(centers):
        c0 = np.asarray(c0, int)
        S = vs.read(Ls, c0 - mg, c0 + bsz + mg)
        mS = S > 0
        if mS[mg:-mg, mg:-mg, mg:-mg].mean() < args.min_material:
            continue
        # extended grid in short level-Ls indices, mapped to tall level-Lt indices
        g = [np.arange(c - rad - mg, c + bsz + rad + mg, dtype=np.float64) for c in c0]
        Zs, Ys, Xs = np.meshgrid(*[vs.i2p(Ls, gg) for gg in g], indexing="ij")
        Xp = np.stack([Xs.ravel(), Ys.ravel(), Zs.ravel()], 1)        # physical xyz in short
        Xt = apply(T, Xp)
        it = vt.p2i(Lt, Xt[:, ::-1])                                     # tall level index (z, y, x)
        lo = np.floor(it.min(0)).astype(int) - 1
        hi = np.ceil(it.max(0)).astype(int) + 2
        if np.prod(hi - lo) > 64e6:
            continue
        Treg = vt.read(Lt, lo, hi)
        Tq = ndi.map_coordinates(Treg, (it - lo).T, order=1, mode="constant", cval=0.0).reshape(Zs.shape)
        mT = Tq > 0
        if mT.mean() < 0.3:
            continue
        s1, s2 = args.dog
        Sd = dog3(S, s1, s2)[mg:-mg, mg:-mg, mg:-mg]
        Td = dog3(Tq, s1, s2)[mg:-mg, mg:-mg, mg:-mg]
        w = ndi.binary_erosion(mS, iterations=2)[mg:-mg, mg:-mg, mg:-mg].astype(np.float32)
        Tm = ndi.binary_erosion(mT, iterations=1)[mg:-mg, mg:-mg, mg:-mg]
        Td = Td * Tm
        if w.sum() < 0.2 * w.size:
            continue
        ncc = masked_ncc_valid(Td, Sd, w)
        k = int(np.argmax(ncc))
        p = np.array(np.unravel_index(k, ncc.shape))
        v = float(ncc.flat[k])
        at_edge = bool(((p == 0) | (p == np.array(ncc.shape) - 1)).any())
        f = np.zeros(3)
        for ax in range(3):
            if 0 < p[ax] < ncc.shape[ax] - 1:
                i0 = p.copy(); i0[ax] -= 1
                i2 = p.copy(); i2[ax] += 1
                y0, y1, y2 = ncc[tuple(i0)], v, ncc[tuple(i2)]
                den = y0 - 2 * y1 + y2
                f[ax] = float(np.clip(0.5 * (y0 - y2) / den, -0.5, 0.5)) if den < 0 else 0.0
        # second peak outside +-2
        nc2 = ncc.copy()
        sl = tuple(slice(max(0, q - 2), q + 3) for q in p)
        nc2[sl] = -1
        v2 = float(nc2.max()) if nc2.size > 125 else float("nan")
        d = p + f - rad                                                  # shift in level-Ls voxels (z, y, x)
        cen = c0 + (bsz - 1) / 2.0
        Ps = vs.i2p(Ls, cen)[::-1]                                       # physical xyz of the block centre
        Pt = apply(T, (vs.i2p(Ls, cen + d)[::-1])[None])[0]
        out.append(dict(block=[int(x) for x in c0], ncc=v, second=v2, at_edge=at_edge, shift_vox=d.tolist(),
                        short_xyz_um=Ps.tolist(), tall_xyz_um=Pt.tolist(), material=float(w.mean())))
    return out


def robust_fit(blocks, T_prev, args, vox_um):
    P = np.array([b["short_xyz_um"] for b in blocks])
    Q = np.array([b["tall_xyz_um"] for b in blocks])
    ok = np.array([(b["ncc"] >= args.min_ncc) and not b["at_edge"] and
                   (not np.isfinite(b["second"]) or b["ncc"] - b["second"] >= args.min_peak_gap) for b in blocks])
    if ok.sum() < 6:
        return None, ok, None
    use = ok.copy()
    for it in range(6):
        if use.sum() >= 12 and np.ptp(P[use, 2]) > 0 and not args.similarity:
            T = fit_affine(P[use], Q[use])
        else:
            T = fit_similarity(P[use], Q[use])
        r = np.linalg.norm(apply(T, P) - Q, axis=1)
        med = np.median(r[use])
        mad = np.median(np.abs(r[use] - med)) * 1.4826
        thr = max(med + 3.5 * mad, 1.0 * vox_um)
        new = ok & (r <= thr)
        if (new == use).all():
            break
        use = new
    return T, use, r


def choose_blocks(vs, vt, T, Ls, bsz, tall_m, Lt_lo, n_target, rng, per_chunk=1):
    """Block corners on the short level-Ls grid, one block centred in each storage chunk (so a block costs one
    chunk read) or, with per_chunk=2, two per chunk and axis (coarsest level: small scans have few chunks there),
    inside material of the tall scan under T, spread over height and area."""
    shp = np.array(vs.shape(Ls))
    cs = np.array(vs.levels[Ls]["chunks"])
    grid = []
    for s, c in zip(shp, cs):
        if per_chunk == 2 and c >= 2 * bsz + 16:
            starts = (np.arange(0, s, c)[:, None] + np.array([8, c - bsz - 8])[None]).ravel()
        else:
            starts = np.arange(0, s, c) + (c - bsz) // 2
        starts = np.clip(starts, 0, max(0, s - bsz))
        grid.append(np.unique(starts))
    cand = np.array([(z, y, x) for z in grid[0] for y in grid[1] for x in grid[2]], float)
    cen = cand + (bsz - 1) / 2.0
    Xp = vs.i2p(Ls, cen)[:, ::-1]
    Xt = apply(T, Xp)
    it = np.rint(vt.p2i(Lt_lo, Xt[:, ::-1])).astype(int)
    inb = np.all((it >= 0) & (it < np.array(tall_m.shape)), 1)
    good = np.zeros(len(cand), bool)
    good[inb] = tall_m[it[inb, 0], it[inb, 1], it[inb, 2]]
    cand, Xp = cand[good], Xp[good]
    if len(cand) == 0:
        return []
    # stratify by height: pick farthest-point samples within each height band
    zb = np.linspace(Xp[:, 2].min(), Xp[:, 2].max() + 1e-6, 7)
    per = max(2, n_target // 6)
    chosen = []
    for a, b in zip(zb[:-1], zb[1:]):
        idx = np.where((Xp[:, 2] >= a) & (Xp[:, 2] < b))[0]
        if len(idx) == 0:
            continue
        sel = [idx[rng.integers(len(idx))]]
        dmin = np.linalg.norm(Xp[idx] - Xp[sel[0]], axis=1)
        while len(sel) < min(per, len(idx)):
            i = idx[int(np.argmax(dmin))]
            sel.append(i)
            dmin = np.minimum(dmin, np.linalg.norm(Xp[idx] - Xp[i], axis=1))
        chosen += sel
    return [cand[i].astype(int) for i in chosen]


def load_whole(vt, L, cap=4.0e8):
    """The whole volume at level L (or coarser) as uint8. If even the coarsest stored level holds more than `cap`
    voxels (e.g. a 180 mm tall 2.4 um scan), it is read slab by slab and 2x2x2-mean-pooled in memory, which is
    exactly what the next pyramid level would hold; the returned level number says which level it stands for."""
    while np.prod(vt.shape(L)) > cap and L < vt.maxlevel:
        L += 1
    f = 1
    while np.prod(vt.shape(L)) / f ** 3 > cap:
        f *= 2
    if f == 1:
        a = vt.read(L, (0, 0, 0), vt.shape(L)).astype(np.uint8)
        vt.drop_cache(L)
        return a, L
    Z, Y, X = vt.shape(L)
    cz = vt.levels[L]["chunks"][0]
    step = max(cz, f) // f * f
    out = np.zeros((-(-Z // f), -(-Y // f), -(-X // f)), np.uint8)
    for z0 in range(0, Z, step):
        a = vt.read(L, (z0, 0, 0), (z0 + step, -(-Y // f) * f, -(-X // f) * f))
        n = a.shape[0] // f
        out[z0 // f:z0 // f + n] = np.rint(a.reshape(n, f, a.shape[1] // f, f, a.shape[2] // f, f).mean((1, 3, 5)))[:out.shape[0] - z0 // f]
        vt.drop_cache(L)
    return out, L + int(round(math.log2(f)))


def qc_figure(path, vs, Ls, sl, vt, Lt2, tall2, T, title):
    """Rows: bottom / middle / top cross-section of the short scan. Columns: short scan | the other scan sampled
    on the same plane through the transform | checkerboard of the two (lines must run on across tile edges)."""
    from PIL import Image, ImageDraw
    zs = sorted(sl)
    rows = []
    tv = tall2.astype(np.float32)

    def norm(x, m):
        if m.sum() < 50:
            return np.zeros_like(x)
        lo, hi = np.percentile(x[m], [1, 99])
        return np.clip((x - lo) / max(hi - lo, 1e-6), 0, 1)

    for z in (zs[0], zs[len(zs) // 2], zs[-1]):
        a = sl[z].astype(np.float32)
        m = a > 0
        if m.sum() < 50:
            continue
        yy, xx = np.nonzero(m)
        y0, y1, x0, x1 = yy.min(), yy.max() + 1, xx.min(), xx.max() + 1
        a, m = a[y0:y1, x0:x1], m[y0:y1, x0:x1]
        gy, gx = np.mgrid[y0:y1, x0:x1]
        Pp = np.stack([vs.i2p(Ls, gx.ravel()), vs.i2p(Ls, gy.ravel()), np.full(gx.size, float(vs.i2p(Ls, z)))], 1)
        it = vt.p2i(Lt2, apply(T, Pp)[:, ::-1])
        b = ndi.map_coordinates(tv, it.T, order=1, cval=0.0, output=np.float32).reshape(a.shape)
        A, Bn = norm(a, m), norm(b, b > 0)
        tsz = max(16, max(A.shape) // 14)
        cb = ((np.arange(A.shape[0])[:, None] // tsz + np.arange(A.shape[1])[None, :] // tsz) % 2).astype(bool)
        chk = np.where(cb, A, Bn)
        tiles = [np.stack([A] * 3, -1), np.stack([Bn] * 3, -1), np.stack([chk] * 3, -1)]
        labels = [f"short scan z={z} (level {Ls})", "other scan on the same plane", "checkerboard: lines must run on"]
        row = []
        for t, lab in zip(tiles, labels):
            im = Image.fromarray((t * 255).astype(np.uint8)).resize((460, int(460 * t.shape[0] / t.shape[1])))
            d = ImageDraw.Draw(im)
            d.rectangle([0, 0, 460, 14], fill=(0, 0, 0))
            d.text((4, 2), lab, fill=(255, 220, 0))
            row.append(np.asarray(im))
        h = max(r.shape[0] for r in row)
        row = [np.pad(r, ((0, h - r.shape[0]), (3, 3), (0, 0)), constant_values=255) for r in row]
        rows.append(np.hstack(row))
    if not rows:
        return
    w = max(r.shape[1] for r in rows)
    rows = [np.pad(r, ((3, 3), (0, w - r.shape[1]), (0, 0)), constant_values=255) for r in rows]
    img = Image.fromarray(np.vstack(rows))
    head = Image.new("RGB", (img.width, 22), (255, 255, 255))
    ImageDraw.Draw(head).text((6, 5), title, fill=(0, 0, 0))
    out = Image.new("RGB", (img.width, img.height + 22), (255, 255, 255))
    out.paste(head, (0, 0))
    out.paste(img, (0, 22))
    out.save(path)


# ------------------------------------------------------------------------------------------------
# main
# ------------------------------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--version", action="version", version=f"scroll-lineup {VERSION}")
    ap.add_argument("moving")
    ap.add_argument("fixed")
    ap.add_argument("--out", required=True)
    ap.add_argument("--um-moving", type=float)
    ap.add_argument("--um-fixed", type=float)
    ap.add_argument("--g1-um", type=float, default=300.0, help="grid of the whole-scroll search")
    ap.add_argument("--g2-um", type=float, default=150.0, help="grid of the 2D re-scoring")
    ap.add_argument("--g1-keep", type=int, default=6)
    ap.add_argument("--block-levels-um", default="75,37,19", help="block matching resolutions (short scan)")
    ap.add_argument("--blocks", type=int, default=36)
    ap.add_argument("--block-size", type=int, default=48)
    ap.add_argument("--radius", type=int, default=6, help="block search radius (voxels at each block level)")
    ap.add_argument("--dog", type=float, nargs=2, default=(1.0, 4.0))
    ap.add_argument("--min-material", type=float, default=0.35)
    ap.add_argument("--min-ncc", type=float, default=0.15)
    ap.add_argument("--min-peak-gap", type=float, default=0.03)
    ap.add_argument("--similarity", action="store_true", help="fit 7-parameter similarity instead of affine")
    ap.add_argument("--fixed-name", help="value for fixed_volume in transform.json (default: fixed volume name)")
    ap.add_argument("--write-inverse", action="store_true",
                    help="also write transform_inverse.json (fixed -> moving, same format)")
    ap.add_argument("--stop-after", choices=["g1", "g2", "b"], default=None)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    rng = np.random.default_rng(args.seed)
    rep = dict(tool="scroll-lineup", version=VERSION, started=time.strftime("%Y-%m-%d %H:%M:%S %Z"), args=vars(args))

    vm = Volume(args.moving, args.um_moving)
    vf = Volume(args.fixed, args.um_fixed)
    for v, role in ((vm, "moving"), (vf, "fixed")):
        log(f"{role}: {v.name} {v.um} um, L0 {v.shape(0)}, levels 0..{v.maxlevel}, extent z {v.extent_um()[0] / 1000:.1f} mm")
    # roles for the search: the shorter scan (in z, physically) slides along the taller one
    short_is_moving = vm.extent_um()[0] <= vf.extent_um()[0]
    vs, vt = (vm, vf) if short_is_moving else (vf, vm)
    rep["volumes"] = dict(moving=dict(url=vm.url, um=vm.um, shape=vm.shape(0)), fixed=dict(url=vf.url, um=vf.um, shape=vf.shape(0)),
                          short_is_moving=short_is_moving)
    log(f"short (sliding) scan: {vs.name}; tall scan: {vt.name}")

    # ---- the short scan's 5 cross-sections at ~75 um first: the size of the material sets the search grids
    Ls = vs.level_for(75.0)
    zr = vs.occupied_z(Ls)
    fracs = (0.1, 0.3, 0.5, 0.7, 0.9)
    t0 = time.time()
    sl = load_short_slices(vs, Ls, fracs, zr)
    for z in list(sl):
        if (sl[z] > 0).mean() < 0.01:
            log(f"short slice z={z} is empty; dropped")
            del sl[z]
    log(f"short L{Ls} slices {list(sl)} loaded ({vs.bytes_fetched / 1e6:.0f} MB, {time.time() - t0:.0f}s)")
    if len(sl) < 3:
        raise SystemExit("fewer than 3 non-empty cross-sections in the short scan")
    ext = 0.0
    for a in sl.values():
        yy, xx = np.nonzero(a > 0)
        if len(yy):
            ext = max(ext, (np.ptp(yy) + 1) * vs.vox(Ls), (np.ptp(xx) + 1) * vs.vox(Ls))
    g1 = float(np.clip(ext / 120.0, 60.0, args.g1_um))
    g2 = float(np.clip(ext / 250.0, max(30.0, vs.vox(Ls)), args.g2_um))

    # ---- the tall scan, whole, at ~g2
    t0 = time.time()
    tall2, Lt2 = load_whole(vt, vt.level_for(g2))
    log(f"tall L{Lt2} {tall2.shape} loaded ({vt.bytes_fetched / 1e6:.0f} MB, {time.time() - t0:.0f}s)")
    # partial field of view: the short scan sees much less material per cross-section than the tall one
    t_area = (tall2 > 0).sum((1, 2)).astype(float) * vt.vox(Lt2) ** 2
    s_area = max(float((a > 0).sum()) for a in sl.values()) * vs.vox(Ls) ** 2
    ref = float(np.percentile(t_area[t_area > 0], 75)) if (t_area > 0).any() else 1.0
    partial = s_area < 0.5 * ref
    rep["grids"] = dict(short_material_extent_um=ext, g1_um=g1, g2_um=g2, tall_level=Lt2,
                        short_to_tall_area_ratio=s_area / ref, partial_field_of_view=bool(partial))
    log(f"material extent {ext / 1000:.1f} mm -> search grids {g1:.0f} / {g2:.0f} um; area ratio {s_area / ref:.2f}"
        f"{' (partial field of view: adding the 2D search)' if partial else ''}")

    # ---- G1
    Lt1 = max(Lt2, vt.level_for(g1))
    t0 = time.time()
    cands, _ = g1_search_wrapper(vt, Lt2, tall2, Lt1, vs, Ls, sl, g1, args, rep, partial)
    log(f"G1 done ({time.time() - t0:.0f}s)")
    json.dump(rep, open(os.path.join(args.out, "report.json"), "w"), indent=1, default=float)
    if args.stop_after == "g1":
        return

    # ---- G2
    t0 = time.time()
    win = g2_refine(vt, Lt2, tall2, vs, Ls, sl, g2, cands, args, rep)
    T = initial_transform(win)
    rep["g2"]["initial_T_short_to_tall_um"] = T.tolist()
    rep["g2"]["initial_decomposition"] = decompose(T[:3, :3])
    log(f"G2 done ({time.time() - t0:.0f}s): {decompose(T[:3, :3])}")
    json.dump(rep, open(os.path.join(args.out, "report.json"), "w"), indent=1, default=float)
    if args.stop_after == "g2":
        return

    # ---- B: block matching rounds
    tall_m = ndi.binary_erosion(tall2 > 0, iterations=1)
    rep["blocks"] = []
    for li, bum in enumerate(float(x) for x in args.block_levels_um.split(",")):
        Lb_s = vs.level_for(bum)
        Lb_t = vt.level_for(vs.vox(Lb_s))
        centers = choose_blocks(vs, vt, T, Lb_s, args.block_size, tall_m, Lt2, args.blocks, rng, per_chunk=2 if li == 0 else 1)
        rad0 = args.radius + (2 if li == 0 else 0)
        rad = rad0
        for rnd in range(2):
            t0 = time.time()
            while True:
                blocks = block_pass(vs, vt, T, Lb_s, Lb_t, centers, args.block_size, rad, args, f"{bum}")
                Tn, use, r = robust_fit(blocks, T, args, vs.vox(Lb_s))
                if Tn is not None or rnd > 0 or rad >= 4 * rad0:
                    break
                rad *= 2                                           # starting transform too far off: look wider
                log(f"B {vs.vox(Lb_s):.0f} um: only {int(use.sum())} good blocks of {len(blocks)}; search radius -> {rad} voxels")
            info = dict(level_um=vs.vox(Lb_s), short_level=Lb_s, tall_level=Lb_t, round=rnd, radius_vox=rad, n_tried=len(centers),
                        n_matched=len(blocks), n_used=int(use.sum()) if Tn is not None else 0,
                        ncc_median=float(np.median([b["ncc"] for b in blocks])) if blocks else None)
            if Tn is None:
                info["status"] = "too few good blocks; transform unchanged"
                rep["blocks"].append(info)
                log(f"B {bum} um round {rnd}: only {int(use.sum())} good blocks of {len(blocks)}; unchanged")
                continue
            move = np.linalg.norm(apply(Tn, np.array([b["short_xyz_um"] for b in blocks])) -
                                  apply(T, np.array([b["short_xyz_um"] for b in blocks])), axis=1)
            T = Tn
            ru = r[use]
            info.update(resid_rms_um=float(np.sqrt((ru ** 2).mean())), resid_max_um=float(ru.max()),
                        change_median_um=float(np.median(move)), change_max_um=float(move.max()),
                        decomposition=decompose(T[:3, :3]), blocks=blocks, used=use.tolist())
            rep["blocks"].append(info)
            log(f"B {vs.vox(Lb_s):.0f} um round {rnd}: {int(use.sum())}/{len(blocks)} blocks used (tried {len(centers)}), "
                f"ncc med {info['ncc_median']:.2f}, resid rms {info['resid_rms_um']:.1f} um max {info['resid_max_um']:.1f}, "
                f"moved median {np.median(move):.1f} um ({time.time() - t0:.0f}s)")
            json.dump(rep, open(os.path.join(args.out, "report.json"), "w"), indent=1, default=float)

    # ---- how much to trust it (reported, never used to change the answer)
    reasons = []
    margin = rep["g2"].get("margin")
    if margin is not None and margin < 0.15:
        reasons.append(f"placement margin small: G2 winner beats the runner-up by only {margin:.2f}")
    fits = [b for b in rep["blocks"] if b.get("n_used")]
    last = rep["blocks"][-1] if rep["blocks"] else {}
    if not fits:
        reasons.append("block matching never produced a fit: the transform is the coarse G2 estimate")
    else:
        if not last.get("n_used"):
            reasons.append("the finest block level did not produce a fit")
        elif last["n_used"] < 12:
            reasons.append(f"only {last['n_used']} blocks in the final fit")
        elif last["n_used"] < 0.6 * last["n_matched"]:
            reasons.append(f"only {last['n_used']} of {last['n_matched']} blocks agree")
        if last.get("resid_rms_um") is not None and last["resid_rms_um"] > 30:
            reasons.append(f"block residual RMS {last['resid_rms_um']:.0f} um > 30 um (scans not related by one affine?)")
    rep["confidence"] = dict(level="HIGH" if not reasons else "CHECK", reasons=reasons)
    log(f"CONFIDENCE: {rep['confidence']['level']}" + (": " + "; ".join(reasons) if reasons else ""))

    # ---- outputs
    Tm2f = T if short_is_moving else inv(T)                  # physical um, moving -> fixed
    A = Tm2f[:3, :3] * vm.um / vf.um
    t = Tm2f[:3, 3] / vf.um
    M = np.hstack([A, t[:, None]])
    last = rep["blocks"][-1] if rep["blocks"] else {}
    lm_m, lm_f = [], []
    if last.get("blocks"):
        for b, u in zip(last["blocks"], last["used"]):
            if not u:
                continue
            Ps, Pt = np.array(b["short_xyz_um"]), np.array(b["tall_xyz_um"])
            pm, pf = (Ps, Pt) if short_is_moving else (Pt, Ps)
            lm_m.append((pm / vm.um).tolist())
            lm_f.append((pf / vf.um).tolist())
    tj = {"schema_version": "1.0.0", "fixed_volume": args.fixed_name or vf.name.replace(".zarr", ""),
          "transformation_matrix": M.tolist(), "fixed_landmarks": lm_f, "moving_landmarks": lm_m}
    json.dump(tj, open(os.path.join(args.out, "transform.json"), "w"), indent=1)
    if args.write_inverse:
        Mi = inv(np.vstack([M, [0, 0, 0, 1]]))[:3]
        json.dump({"schema_version": "1.0.0", "fixed_volume": vm.name.replace(".zarr", ""), "transformation_matrix": Mi.tolist(),
                   "fixed_landmarks": lm_m, "moving_landmarks": lm_f},
                  open(os.path.join(args.out, "transform_inverse.json"), "w"), indent=1)
    rep["transform_moving_to_fixed_voxels_xyz"] = M.tolist()
    rep["decomposition_moving_to_fixed_um"] = decompose(Tm2f[:3, :3])
    try:
        qc_figure(os.path.join(args.out, "qc.png"), vs, Ls, sl, vt, Lt2, tall2, T,
                  f"scroll-lineup {VERSION}: {vs.name} on {vt.name}")
    except Exception as e:                                    # the picture must never cost the transform
        log(f"qc picture failed: {e!r}")
    rep["downloaded_MB"] = (vm.bytes_fetched + vf.bytes_fetched) / 1e6
    rep["seconds"] = time.time() - T_START
    rep["finished"] = time.strftime("%Y-%m-%d %H:%M:%S %Z")
    json.dump(rep, open(os.path.join(args.out, "report.json"), "w"), indent=1, default=float)
    log(f"wrote {args.out}/transform.json ({rep['downloaded_MB']:.0f} MB downloaded)")


def g1_search_wrapper(vt, Lt2, tall2, Lt1, vs, Ls, sl, g1, args, rep, partial=False):
    """Run G1 on the tall stack averaged in z to ~g1 spacing (xy resampled inside g1_search)."""
    f = 2 ** max(0, Lt1 - Lt2)
    if f > 1:
        Z = tall2.shape[0] // f * f
        stack = tall2[:Z].astype(np.float32).reshape(Z // f, f, *tall2.shape[1:]).mean(1)
    else:
        stack = tall2
    # a z-averaged level-Lt2 stack behaves like level Lt2+log2(f) in z; xy stays at Lt2 (to_grid handles xy)
    class _ZView:
        pass
    zv = _ZView()
    zv.um, zv.name = vt.um, vt.name
    Lz = Lt2 + int(round(math.log2(f)))
    zv.i2p = lambda L, i: vt.i2p(Lz, i)
    zv.p2i = lambda L, X: vt.p2i(Lz, X)
    zv.vox = lambda L: vt.vox(Lt2)                     # xy pixel size used by to_grid
    return g1_search(zv, Lt2, stack, vs, Ls, sl, g1, args, rep, partial)


if __name__ == "__main__":
    main()
