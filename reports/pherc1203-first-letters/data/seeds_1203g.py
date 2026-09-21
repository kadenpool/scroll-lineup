"""Seed points for growing PHerc0846A surfaces inside its sharp-scan band (coarse L0 z 1864..5749, image-verified).
Sample the published surface prediction (m7-L0) at a coarse level, keep positive voxels inside the band (with a 150-slice
margin so patches can grow up and down), pick 60 spread-out seeds (>= 3 mm apart). Writes p0846a/seeds.json (x y z, L0)."""
import json, os, numpy as np, zarr, fsspec
B = "vesuvius-challenge-open-data"; V = f"{B}/PHerc1203/representations/predictions/surfaces/20250820131727-surface-20260413222639-surface-m7-L0-th0.2.zarr"
fs = fsspec.filesystem("s3", anon=True)
print("levels:", [x.rsplit("/", 1)[-1] for x in fs.ls(V, detail=False)])
L = 3; Z = zarr.open(fsspec.get_mapper(f"s3://{V}/{L}", anon=True), mode="r"); s = 2 ** L
print("level", L, Z.shape, Z.dtype, Z.chunks)
z0, z1 = (10040 + 150) // s, (11829 - 150) // s
pts = []
rng = np.random.default_rng(0)
for zc in range(z0, z1, max(1, (z1 - z0) // 40)):
    sl = np.asarray(Z[zc]); yy, xx = np.nonzero(sl > (sl.max() / 2 if sl.max() > 1 else 0))
    if len(yy) == 0: continue
    for i in rng.choice(len(yy), size=min(30, len(yy)), replace=False): pts.append((int(xx[i]) * s, int(yy[i]) * s, zc * s))
rng.shuffle(pts); seeds = []
for p in pts:
    if all(np.hypot(p[0] - q[0], p[1] - q[1]) * 9.362e-3 > 3 or abs(p[2] - q[2]) * 9.362e-3 > 3 for q in seeds): seeds.append(p)
    if len(seeds) == 60: break
os.makedirs("<run-dir>/p1203g", exist_ok=True)
json.dump([{"x": x, "y": y, "z": z} for x, y, z in seeds], open("<run-dir>/p1203g/seeds.json", "w"), indent=0)
print(len(pts), "candidate points ->", len(seeds), "seeds; z range", min(p[2] for p in seeds), max(p[2] for p in seeds))
