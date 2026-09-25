"""Re-derive every number in this folder's README from the surface files themselves.

  python3 trace_numbers.py        (needs numpy, scipy and Pillow, as scroll-lineup does; a few minutes)

A tifxyz grid stores the x, y and z of each point in voxels of the scan, one point per 20 voxels along the surface;
a point the grower did not reach is -1. The grower measures a surface as two triangles in each cell, split along the
diagonal from its first corner to its opposite one. For each surface this prints its grid, its segment id, and its
area measured from the grid that way. Then how much of each preview shows no scan data (the air outside the scroll is
0 in the masked scan), and where two surfaces come within 4 voxels of each other: first at the grid points alone;
then the least distance between every two surfaces, measured exactly on those triangles, and how much of each lies
within 4 voxels of the other (each of its triangles cut into 12 by 12 small ones, each counted when its centre lies
within 4 voxels of the other surface's triangles, measured exactly).
"""
import itertools, json, os, re
import numpy as np
from PIL import Image
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
# the scan's voxel size, as the grower recorded it (every surface here is on one scan, so they must agree)
VOXEL_MM = {json.load(open(os.path.join(HERE, d, "meta.json")))["vc_gsfs_params"]["voxelsize"] / 1000.0
            for d in sorted(os.listdir(HERE)) if re.fullmatch(r"s\d{2}", d) and os.path.isdir(os.path.join(HERE, d))}
assert len(VOXEL_MM) == 1, f"surfaces on different voxel sizes: {VOXEL_MM}"
VOXEL_MM = VOXEL_MM.pop()
STEP, NEAR, K = 20, 4.0, 12
NAMES = sorted(d for d in os.listdir(HERE) if re.fullmatch(r"s\d{2}", d) and os.path.isdir(os.path.join(HERE, d)))
INDEX = {r["surface"]: r for r in json.load(open(os.path.join(HERE, "index.json")))}


def grid(s):
    x, y, z = (np.asarray(Image.open(os.path.join(HERE, s, f"{a}.tif")), dtype=np.float64) for a in "xyz")
    ok = (x > 0) & (y > 0) & (z > 0) & np.isfinite(x) & np.isfinite(y) & np.isfinite(z)
    p = np.stack([x, y, z], -1)
    a, b, c, d = p[:-1, :-1], p[1:, :-1], p[:-1, 1:], p[1:, 1:]
    cell = ok[:-1, :-1] & ok[1:, :-1] & ok[:-1, 1:] & ok[1:, 1:]
    area = np.where(cell, 0.5 * np.linalg.norm(np.cross(b - a, d - a), axis=-1)
                    + 0.5 * np.linalg.norm(np.cross(d - a, c - a), axis=-1), 0.0)
    return p, ok, cell, area


G, total, ids = {}, 0.0, []
print("| surface | segment id | grid | valid points | area cm2 (grower) | area cm2 (from the grid) |")
print("|---|---|---|---|---|---|")
for s in NAMES:
    G[s] = g = grid(s)
    M = json.load(open(os.path.join(HERE, s, "meta.json")))
    here = g[3].sum() * (VOXEL_MM / 10) ** 2
    same = abs(g[3].sum() - M["area_vx2"]) < 1e-6 * M["area_vx2"] and [int(v) for v in M["seed"]] == INDEX[s]["seed_xyz"]
    total += M["area_cm2"]
    ids.append(M["uuid"])
    print(f"| {s} | {M['uuid']} | {g[1].shape[0]} x {g[1].shape[1]} | {int(g[1].sum())} | {M['area_cm2']:.2f} | "
          f"{here:.2f}{'' if same else ' (DIFFERS from meta.json or index.json)'} |")
flat = {s: int(G[s][2].sum()) * (STEP * VOXEL_MM / 10) ** 2 for s in NAMES}
print(f"\nTotal: {total:.2f} cm2 over {len(NAMES)} surfaces; segment ids all different: {len(set(ids)) == len(ids)}")
print("Area the valid cells would cover lying flat, 20 voxels a side: " +
      ", ".join(sorted({f'{v:.2f} cm2' for v in flat.values()})))
print("\nShare of each preview (plane 15, inside the area its grid covers) that is black, value 0: no scan data, "
      "or the darkest papyrus after the stretch, so an upper bound on the share with no scan data:")
for s in NAMES:
    z = np.asarray(Image.open(os.path.join(HERE, s, "preview_plane15.png"))) == 0
    r, c = np.nonzero(~z.all(1))[0], np.nonzero(~z.all(0))[0]
    print(f"  {s}: {100 * z[r.min():r.max() + 1, c.min():c.max() + 1].mean():.2f} %")
print(f"\nPoints within {NEAR:g} voxels of another surface, at the grid points (one per {STEP} voxels):")
T = {s: cKDTree(G[s][0][G[s][1]]) for s in NAMES}
for a, b in itertools.combinations(NAMES, 2):
    d, _ = T[b].query(G[a][0][G[a][1]], k=1)
    if (d <= NEAR).any():
        d2, _ = T[a].query(G[b][0][G[b][1]], k=1)
        print(f"  {a} and {b}: {int((d <= NEAR).sum())} points of {a} and {int((d2 <= NEAR).sum())} of {b}; "
              f"nearest {d.min():.1f} voxels")
def _dot(u, v):
    return np.einsum("...i,...i->...", u, v)


def pt_seg(p, a, b):
    """Distance from each point p to the segment a-b (arrays n x 3)."""
    ab = b - a
    t = np.clip(_dot(p - a, ab) / np.maximum(_dot(ab, ab), 1e-300), 0.0, 1.0)
    return np.linalg.norm(p - a - t[:, None] * ab, axis=1)


def pt_tri(p, a, b, c):
    """Distance from each point p to the triangle a, b, c: to its plane where p projects inside it, else to its
    nearest edge (a triangle with no area is only its edges)."""
    n = np.cross(b - a, c - a)
    nn = _dot(n, n)
    edge = np.minimum.reduce([pt_seg(p, a, b), pt_seg(p, b, c), pt_seg(p, c, a)])
    inside = ((_dot(np.cross(b - a, p - a), n) >= 0) & (_dot(np.cross(c - b, p - b), n) >= 0)
              & (_dot(np.cross(a - c, p - c), n) >= 0) & (nn > 0))
    plane = np.abs(_dot(p - a, n)) / np.sqrt(np.where(nn > 0, nn, 1.0))
    return np.where(inside, np.minimum(plane, edge), edge)


def seg_seg(p0, p1, q0, q1):
    """Distance between segments p0-p1 and q0-q1: the closest pair of their lines where it lies on both, else the
    nearest of the four end-to-segment distances (a convex quadratic on a square is least on its edge otherwise)."""
    d1, d2, r = p1 - p0, q1 - q0, p0 - q0
    a, e, b, c, f = _dot(d1, d1), _dot(d2, d2), _dot(d1, d2), _dot(d1, r), _dot(d2, r)
    den = a * e - b * b
    ok = den > 1e-12 * a * e
    s = (b * f - c * e) / np.where(ok, den, 1.0)
    t = (a * f - b * c) / np.where(ok, den, 1.0)
    inner = ok & (s >= 0) & (s <= 1) & (t >= 0) & (t <= 1)
    di = np.linalg.norm(r + s[:, None] * d1 - t[:, None] * d2, axis=1)
    ends = np.minimum.reduce([pt_seg(p0, q0, q1), pt_seg(p1, q0, q1), pt_seg(q0, p0, p1), pt_seg(q1, p0, p1)])
    return np.where(inner, np.minimum(di, ends), ends)


def seg_hits_tri(p0, p1, a, b, c):
    """Whether the segment p0-p1 passes through the triangle (Moller-Trumbore; a segment in the triangle's plane is
    left to the distance terms, which then give 0 where it crosses an edge or has an end inside)."""
    d, e1, e2 = p1 - p0, b - a, c - a
    h = np.cross(d, e2)
    det = _dot(e1, h)
    ok = np.abs(det) > 1e-12 * np.linalg.norm(d, axis=1) * np.linalg.norm(e1, axis=1) * np.linalg.norm(e2, axis=1)
    inv = 1.0 / np.where(ok, det, 1.0)
    sv = p0 - a
    u = _dot(sv, h) * inv
    q = np.cross(sv, e1)
    v = _dot(d, q) * inv
    t = _dot(e2, q) * inv
    return ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t >= 0) & (t <= 1)


def tri_tri(A, B):
    """Exact distance between triangles A[k] and B[k] (n x 3 corners x 3): the least over the edges of each to the
    other triangle, where an edge's distance is 0 if it passes through, else the least of its ends to the triangle and
    the edge to the triangle's three edges (two triangles that meet have an edge of one through the other)."""
    out = np.full(len(A), np.inf)
    for X, Y in ((A, B), (B, A)):
        for i, j in ((0, 1), (1, 2), (2, 0)):
            p0, p1, a, b, c = X[:, i], X[:, j], Y[:, 0], Y[:, 1], Y[:, 2]
            d = np.minimum.reduce([pt_tri(p0, a, b, c), pt_tri(p1, a, b, c),
                                   seg_seg(p0, p1, a, b), seg_seg(p0, p1, b, c), seg_seg(p0, p1, c, a)])
            out = np.minimum(out, np.where(seg_hits_tri(p0, p1, a, b, c), 0.0, d))
    return out


def triangles(g):
    """The grower's two triangles in every valid cell, as in the area: corners (a, b, d) and (a, d, c)."""
    p, cell = g[0], g[2]
    a, b, c, d = p[:-1, :-1][cell], p[1:, :-1][cell], p[:-1, 1:][cell], p[1:, 1:][cell]
    return np.concatenate([np.stack([a, b, d], 1), np.stack([a, d, c], 1)])


def exact(x, y, upper):
    """The least distance between surfaces x and y as the grower's triangles. `upper` is the distance between their
    closest two corners, so the closest two triangles are among the pairs whose centres lie within upper plus each
    one's reach (the farthest of its corners from its centre); every such pair is measured exactly."""
    A, B = TRI[x], TRI[y]
    ca, cb = A.mean(1), B.mean(1)
    ra = np.linalg.norm(A - ca[:, None], axis=2).max(1)
    rb = np.linalg.norm(B - cb[:, None], axis=2).max(1)
    tb, best = cKDTree(cb), upper
    keep = np.nonzero(tb.query(ca, k=1)[0] <= upper + ra + rb.max())[0]
    for k in range(0, len(keep), 200):
        ks = keep[k:k + 200]
        near = tb.query_ball_point(ca[ks], upper + ra[ks] + rb.max())
        i = np.repeat(ks, [len(n) for n in near])
        j = np.fromiter(itertools.chain.from_iterable(near), dtype=np.int64, count=len(i))
        m = np.linalg.norm(ca[i] - cb[j], axis=1) <= upper + ra[i] + rb[j]
        if m.any():
            best = min(best, float(tri_tri(A[i[m]], B[j[m]]).min()))
    return best


print(f"\nThe least distance between every two surfaces, exact, on the grower's triangles; for those within {NEAR:g} "
      f"voxels, how much of each lies within {NEAR:g} voxels of the other (its triangles cut {K} by {K}):")
TRI = {s: triangles(G[s]) for s in NAMES}
EDGE = {s: max(np.linalg.norm(TRI[s][:, i] - TRI[s][:, j], axis=1).max() for i, j in ((0, 1), (1, 2), (2, 0)))
        for s in NAMES}                                   # the longest triangle edge on each surface
CORNERS = {s: np.unique(TRI[s].reshape(-1, 3), axis=0) for s in NAMES}
order = sorted((cKDTree(CORNERS[b]).query(CORNERS[a], k=1)[0].min(), a, b) for a, b in itertools.combinations(NAMES, 2))
touch, other, far = [], None, 0
for upper, a, b in order:
    # every point of a triangle lies within its longest edge of each of its corners, so no two points of these
    # surfaces are nearer than upper - EDGE[a] - EDGE[b]; a pair that cannot touch or beat the closest so far is skipped
    if upper - EDGE[a] - EDGE[b] > max(NEAR, other[0] if other else np.inf):
        far += 1
        continue
    d = exact(a, b, upper)
    if d <= NEAR:
        touch.append((a, b, d))
    elif other is None or d < other[0]:
        other = (d, a, b)
def within(x, y):
    """How much of surface x lies within NEAR voxels of surface y, in voxels squared: every triangle of x that could
    come that near is cut into K x K small triangles of equal area, and each counts when its centre lies within NEAR
    of one of y's triangles, measured exactly."""
    A, B = TRI[x], TRI[y]
    ca, cb = A.mean(1), B.mean(1)
    ra = np.linalg.norm(A - ca[:, None], axis=2).max(1)
    rb = np.linalg.norm(B - cb[:, None], axis=2).max(1)
    tb = cKDTree(cb)
    A = A[tb.query(ca, k=1)[0] <= NEAR + ra + rb.max()]
    i, j = np.meshgrid(np.arange(K), np.arange(K), indexing="ij")
    up, down = i + j <= K - 1, i + j <= K - 2          # the K x K small triangles: K(K+1)/2 upright, K(K-1)/2 inverted
    uv = np.concatenate([np.stack([i[up] + 1 / 3, j[up] + 1 / 3], 1), np.stack([i[down] + 2 / 3, j[down] + 2 / 3], 1)]) / K
    total = 0.0
    for k in range(0, len(A), 100):
        T_ = A[k:k + 100]
        pts = (T_[:, None, 0] + uv[None, :, :1] * (T_[:, None, 1] - T_[:, None, 0])
               + uv[None, :, 1:] * (T_[:, None, 2] - T_[:, None, 0])).reshape(-1, 3)
        w = np.repeat(0.5 * np.linalg.norm(np.cross(T_[:, 1] - T_[:, 0], T_[:, 2] - T_[:, 0]), axis=1) / K ** 2, K * K)
        near = tb.query_ball_point(pts, NEAR + rb.max())
        pi = np.repeat(np.arange(len(pts)), [len(n) for n in near])
        tj = np.fromiter(itertools.chain.from_iterable(near), dtype=np.int64, count=len(pi))
        m = np.linalg.norm(pts[pi] - cb[tj], axis=1) <= NEAR + rb[tj]
        pi, tj = pi[m], tj[m]
        hit = np.zeros(len(pts), bool)
        hit[pi[pt_tri(pts[pi], B[tj, 0], B[tj, 1], B[tj, 2]) <= NEAR]] = True
        total += w[hit].sum()
    return total


for a, b, dmin in sorted(touch):
    print(f"  {a} and {b}: {'they cross' if dmin == 0 else f'nearest {dmin:.2f} voxels'}; "
          f"{within(a, b) * VOXEL_MM ** 2:.2f} mm2 of {a} and {within(b, a) * VOXEL_MM ** 2:.2f} mm2 of {b} "
          f"lie within {NEAR:g} voxels of the other")
if other:
    print(f"  closest of the other pairs: {other[1]} and {other[2]}, {other[0]:.2f} voxels apart at their nearest")
print(f"  pairs measured exactly: {len(order) - far}; the other {far} are provably farther apart than that")
