"""Mirror the PHerc0846A normal grids needed to grow surfaces inside its sharp-scan band: xz + yz in full, xy only for
z slices 1364..6249 (band 1864..5749 +-500). vc_grow_seg_from_seed reads normal_grid_path from disk (as for 343)."""
import fsspec, os, time, concurrent.futures as cf
fs = fsspec.filesystem("s3", anon=True)
SRC = "vesuvius-challenge-open-data/PHerc1203/representations/predictions/surfaces/20250820131727-surface-20260413222639-surface-m7-L0-th0.2.normal-grids"
DST = "<run-dir>/p1203g/n_grid"; t0 = time.time()
os.makedirs(DST, exist_ok=True); fs.get(SRC + "/metadata.json", DST + "/metadata.json")
jobs = []
for sub in ("xz", "yz", "xy"):
    os.makedirs(f"{DST}/{sub}", exist_ok=True)
    for f in fs.ls(f"{SRC}/{sub}", detail=False):
        name = f.rsplit("/", 1)[-1]
        if sub == "xy" and not (9540 <= int(name.split(".")[0]) < 12330): continue
        if not os.path.exists(f"{DST}/{sub}/{name}"): jobs.append((f, f"{DST}/{sub}/{name}"))
print(len(jobs), "files to fetch", flush=True)
def get(j):
    for a in range(4):
        try: fs.get(j[0], j[1]); return 1
        except Exception: time.sleep(3)
    return 0
done = 0
with cf.ThreadPoolExecutor(32) as ex:
    for i, ok in enumerate(ex.map(get, jobs)):
        done += ok
        if i % 2000 == 0: print(f"  {i}/{len(jobs)} ({time.time()-t0:.0f}s)", flush=True)
print(f"NGRID_DONE {done}/{len(jobs)} files in {time.time()-t0:.0f}s", flush=True)
