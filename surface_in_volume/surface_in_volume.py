#!/usr/bin/env python3
"""Do published surfaces address voxels that exist in the volume they are aligned to?

A `<segment>-on-<volume>-<voxel>um.tifxyz` names, in its own filename, the volume whose frame its x/y/z
grids are in. Every valid grid point should therefore address a voxel that exists in that volume. This
checks the surface's OWN coordinates against that volume's shape, so a point outside is a published
coordinate that does not address published data (ScrollPrize/villa#1717).

Axis order: the volume's .zarray shape is (z, y, x) and the grids are named x/y/z, so z is compared
against shape[0]. Points are subsampled 4x on each grid axis; a missing point (-1 on all three grids) is
excluded before anything is measured.

  python3 surface_in_volume.py --count results_2026-09-08/*.jsonl   # re-count the published result
  python3 surface_in_volume.py --only SAMPLE SEGMENT VOLUME          # check one surface/volume pair
  python3 surface_in_volume.py [N] [--shard K --nshards M]           # the full survey (see README)

The full survey downloads every transformed surface's three grids, so it is slow; the 8 Sep run was
split into three shards. Needs numpy and Pillow; the catalogue and data are read anonymously.
"""
import argparse, gc, glob, gzip, io, json, os, re, ssl, sys, time, urllib.error, urllib.request
import numpy as np
from PIL import Image

S3 = "https://vesuvius-challenge-open-data.s3.amazonaws.com/"
AS_BASE = "https://data.aws.ash2txt.org/"
CATALOG_URL = S3 + "metadata.json"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "surface_in_volume.jsonl")
STRIDE = 4
ON_RE = re.compile(r"-on-(\d+)-([0-9.]+)um\.tifxyz/?$")
try:
    import certifi
    _SSL = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    _SSL = ssl.create_default_context()


def get(u, t=90, tries=4):
    """Fetch with backoff. A 404 is an answer, not a hiccup, so it is not retried."""
    last = None
    for i in range(tries):
        try:
            with urllib.request.urlopen(u, timeout=t, context=_SSL) as r:
                return r.read()
        except urllib.error.HTTPError:
            raise
        except Exception as e:
            last = e
            if i < tries - 1:
                time.sleep(2 ** i)
    raise last


def catalog():
    raw = get(CATALOG_URL, t=180)
    return json.loads(gzip.decompress(raw) if raw[:2] == b"\x1f\x8b" else raw)


def pairs(cat=None):
    """Every published transformed surface with the volume its own filename says it is aligned to."""
    cat = cat or catalog()
    out = []
    for sample, e in cat["samples"].items():
        vols = e.get("volumes") or {}
        vol_path = {}
        for vid, v in vols.items():
            p = next((o["origins"][0]["path"] for o in (v.get("data") or [])
                      if o.get("type") == "ome-zarr" and o.get("origins")), None)
            if p:
                vol_path[vid] = p
        for sid, seg in (e.get("segments") or {}).items():
            for d in (seg.get("data") or []):
                if d.get("type") != "tifxyz-transformed":
                    continue
                for o in (d.get("origins") or []):
                    m = ON_RE.search(o.get("path", ""))
                    if m:
                        out.append(dict(sample=sample, segment=sid, volume=m.group(1), voxel_um=float(m.group(2)),
                                        tif=o["path"], zarr=vol_path.get(m.group(1))))
    return out


_HOST = {}


def volume_base(zarr_path):
    """Which host serves this volume. Most sit on the S3 bucket; paths beginning `samples/` are served
    only by data.aws.ash2txt.org, so S3 is tried first and ash2txt second."""
    if zarr_path not in _HOST:
        _HOST[zarr_path] = None
        for base in (S3, AS_BASE):
            try:
                get(base + zarr_path + "0/.zarray", t=20)
                _HOST[zarr_path] = base
                break
            except Exception:
                continue
    return _HOST[zarr_path]


def one(p):
    base = dict(sample=p["sample"], segment=p["segment"], volume=p["volume"], voxel_um=p["voxel_um"])
    host = volume_base(p["zarr"])
    if host is None:
        return dict(**base, error="volume not served by either host")
    shape = json.loads(get(host + p["zarr"] + "0/.zarray"))["shape"]     # (z, y, x)
    g = {}
    for a in "xyz":
        buf = get(S3 + p["tif"] + f"{a}.tif")
        im = Image.open(io.BytesIO(buf))
        g[a] = np.asarray(im)[::STRIDE, ::STRIDE].astype(np.float64)
        im.close(); del im, buf; gc.collect()
    X, Y, Z = g["x"], g["y"], g["z"]
    v = (X != -1) & (Y != -1) & (Z != -1)
    if v.sum() < 50:
        return dict(**base, error="too few valid points")
    x, y, z = X[v], Y[v], Z[v]
    over = {"x": float((x >= shape[2]).mean()), "y": float((y >= shape[1]).mean()), "z": float((z >= shape[0]).mean())}
    under = float(((x < 0) | (y < 0) | (z < 0)).mean())
    inside = float(((x >= 0) & (x < shape[2]) & (y >= 0) & (y < shape[1]) & (z >= 0) & (z < shape[0])).mean())
    return dict(**base, n_valid=int(v.sum()), shape_zyx=shape, inside=round(inside, 5),
                over_x=round(over["x"], 5), over_y=round(over["y"], 5), over_z=round(over["z"], 5),
                under_zero=round(under, 5),
                max_xyz=[round(float(x.max()), 1), round(float(y.max()), 1), round(float(z.max()), 1)],
                excess_z=round(float(z.max()) - shape[0] + 1, 1))


def count(files):
    """The published figure: surfaces with more than 0.1 % of their points outside, over those measured."""
    recs = [json.loads(l) for f in files for l in open(f) if l.strip()]
    ok = [r for r in recs if "inside" in r]
    out = [r for r in ok if 1 - r["inside"] > 0.001]
    print("%d records, %d surfaces measured, %d not measured (errors); %d of the %d have more than 0.1 %% of "
          "their points outside the volume they name (%.0f %%)" % (len(recs), len(ok), len(recs) - len(ok),
                                                                   len(out), len(ok), 100.0 * len(out) / len(ok)))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("n", nargs="?", type=int, default=900)
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--nshards", type=int, default=1)
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--count", nargs="+", metavar="FILE")
    ap.add_argument("--only", nargs=3, metavar=("SAMPLE", "SEGMENT", "VOLUME"))
    a = ap.parse_args()
    if a.count:
        count(sorted(f for pat in a.count for f in glob.glob(pat)))
        sys.exit(0)
    ps = sorted([q for q in pairs() if q["zarr"]], key=lambda q: (q["sample"], q["segment"], q["volume"]))
    if a.only:
        ps = [q for q in ps if [q["sample"], q["segment"], q["volume"]] == a.only]
        print(json.dumps(one(ps[0]) if ps else {"error": "no such pair in today's catalogue"}))
        sys.exit(0)
    if a.nshards > 1:
        ps = ps[a.shard::a.nshards]
    done = set()
    if os.path.exists(a.out):
        for l in open(a.out):
            d = json.loads(l); done.add((d.get("sample"), d.get("segment"), d.get("volume")))
    todo = [q for q in ps if (q["sample"], q["segment"], q["volume"]) not in done][:a.n]
    print(f"{len(ps)} pairs in shard; {len(done)} done; running {len(todo)}", flush=True)
    with open(a.out, "a") as fh:
        for i, q in enumerate(todo):
            t = time.time()
            try:
                r = one(q)
            except Exception as e:
                r = dict(sample=q["sample"], segment=q["segment"], volume=q["volume"],
                         error=f"{type(e).__name__}: {str(e)[:60]}")
            fh.write(json.dumps(r) + "\n"); fh.flush()
            tag = (f"inside {r['inside']:.4f}" if "inside" in r else r.get("error", "?")[:56])
            print(f"  [{i+1}/{len(todo)}] {q['sample']:<12} {str(q['segment'])[:14]:<15} {time.time()-t:>5.1f}s  {tag}", flush=True)
