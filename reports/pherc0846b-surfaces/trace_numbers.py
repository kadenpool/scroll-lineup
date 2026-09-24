"""Re-derive every number in this folder's README from the surface files themselves.

  python3 trace_numbers.py        (needs numpy, scipy and Pillow, as scroll-lineup does; a minute or two)

A tifxyz grid stores the x, y and z of each point in voxels of the scan, one point per 20 voxels along the surface;
a point the grower did not reach is -1. Between grid points the surface is the bilinear blend of the four corners of
its cell. For each surface this prints its grid, its segment id, and its area measured from the grid the way the
grower measures it (each cell as two triangles, split along the diagonal from its first corner to its opposite one).
Then how much of each preview shows no scan data (the air outside the scroll is 0 in the masked scan), and every
place where two surfaces come within 4 voxels of each other: first at the grid points alone, then with each cell
near the other surface sampled 6 by 6.
"""
import itertools, json, os
import numpy as np
from PIL import Image
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
VOXEL_MM = 9.362e-3                                   # 9.362 um, the scan's voxel size
STEP, NEAR, K = 20, 4.0, 6
NAMES = sorted(d for d in os.listdir(HERE) if d.startswith("s0") and os.path.isdir(os.path.join(HERE, d)))
INDEX = {r["surface"]: r for r in json.load(open(os.path.join(HERE, "index.json")))}


def grid(s):
    x, y, z = (np.asarray(Image.open(os.path.join(HERE, s, f"{a}.tif")), dtype=np.float64) for a in "xyz")
    ok = (x > 0) & (y > 0) & (z > 0) & np.isfinite(x) & np.isfinite(y) & np.isfinite(z)
    p = np.stack([x, y, z], -1)
    a, b, c, d = p[:-1, :-1], p[1:, :-1], p[:-1, 1:], p[1:, 1:]
    cell = ok[:-1, :-1] & ok[1:, :-1] & ok[:-1, 1:] & ok[1:, 1:]
    area = np.where(cell, 0.5 * np.linalg.norm(np.cross(b - a, d - a), axis=-1)
                    + 0.5 * np.linalg.norm(np.cross(d - a, c - a), axis=-1), 0.0)
    diag = np.maximum(np.linalg.norm(d - a, axis=-1), np.linalg.norm(c - b, axis=-1))
    return p, ok, cell, area, np.where(cell, diag, 0.0)


def fine(g, cells):
    """K x K samples inside each chosen cell (bilinear), with the share of the cell's area each one stands for."""
    p, _, _, area, _ = g
    i, j = np.nonzero(cells)
    u = (np.arange(K) + 0.5) / K
    s, t = np.meshgrid(u, u, indexing="ij")
    w = np.stack([(1 - s) * (1 - t), s * (1 - t), (1 - s) * t, s * t], -1).reshape(-1, 4)
    corners = np.stack([p[i, j], p[i + 1, j], p[i, j + 1], p[i + 1, j + 1]], 1)       # cells x 4 x 3
    pts = np.einsum("kc,ncx->nkx", w, corners).reshape(-1, 3)
    return pts, np.repeat(area[i, j] / K ** 2, K * K)


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
print(f"\nSampled {K} by {K} in every cell that could come within {NEAR:g} voxels of the other surface:")
closest, apart = [], 0
for a, b in itertools.combinations(NAMES, 2):
    reach = NEAR + G[a][4].max() + G[b][4].max()     # a cell with every corner farther than this cannot come within NEAR
    near = {}
    for x, y in ((a, b), (b, a)):
        p, ok, cell = G[x][0], G[x][1], G[x][2]
        dc, _ = T[y].query(p.reshape(-1, 3), k=1, distance_upper_bound=reach)
        dc = dc.reshape(ok.shape)
        corner = np.minimum.reduce([dc[:-1, :-1], dc[1:, :-1], dc[:-1, 1:], dc[1:, 1:]])
        near[x] = cell & np.isfinite(corner)
    if not near[a].any() or not near[b].any():
        apart += 1
        continue
    pa, wa = fine(G[a], near[a])
    pb, wb = fine(G[b], near[b])
    d, _ = cKDTree(pb).query(pa, k=1)
    d2, _ = cKDTree(pa).query(pb, k=1)
    closest.append((d.min(), a, b))
    if d.min() <= NEAR:
        print(f"  {a} and {b}: nearest {d.min():.2f} voxels; {wa[d <= NEAR].sum() * VOXEL_MM ** 2:.1f} mm2 of {a} and "
              f"{wb[d2 <= NEAR].sum() * VOXEL_MM ** 2:.1f} mm2 of {b} lie within {NEAR:g} voxels of the other")
rest = sorted(c for c in closest if c[0] > NEAR)
if rest:
    print(f"  closest of the other pairs: {rest[0][1]} and {rest[0][2]}, {rest[0][0]:.1f} voxels apart")
print(f"  pairs with no cell in reach of each other: {apart}")
