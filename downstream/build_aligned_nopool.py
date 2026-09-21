"""Does the challenge's depth averaging explain the render gap?

The aligned arm of the reading test (0.912) is the challenge's own input: the published 2.399 um
surface volume, 84 centred planes of 109, averaged in groups of four into 21 slices. Our own render
of the same surface through the same transform reads 0.857, and the difference has been sitting there
unexplained since 19 Sep.

Our render samples ONE plane per 9.596 um layer. Theirs averages FOUR planes 2.399 um apart into each
layer. This rebuilds their input with the averaging removed, taking the second plane of each group of
four instead of its mean, and changes nothing else: same volume, same 84 planes, same crop, same
everything downstream. If the score falls from 0.912 toward 0.857, the averaging is the gap.

Writes aligned_w016_nopool.zarr next to aligned_w016.zarr.
"""
import concurrent.futures as cf
import json
import urllib.request

import numpy as np
import zarr
from numcodecs import Blosc

VOL = ("https://vesuvius-challenge-open-data.s3.amazonaws.com/PHerc0139/segments/"
       "20250108000004-w029_2025010827/surface-volumes/2.399um-0.22m-78keV-volume-20260102150214.zarr/2/")
CY0, CY1, CX0, CX1 = 36, 44, 12, 32
PICK = 1                      # which plane of each group of four to take; 1 is the second, nearest the mean's centre

meta = json.loads(urllib.request.urlopen(VOL + ".zarray").read())
assert meta["compressor"] is None and meta["chunks"] == [109, 128, 128], meta
Z = 109
z0 = (Z - 84 + 1) // 2
assert z0 == 13
H, W = (CY1 - CY0 + 1) * 128, (CX1 - CX0 + 1) * 128
out = np.zeros((21, H, W), np.uint8)


def fetch(k):
    cy, cx = k
    for _ in range(4):
        try:
            raw = urllib.request.urlopen(f"{VOL}0/{cy}/{cx}", timeout=120).read()
            a = np.frombuffer(raw, np.uint8).reshape(109, 128, 128)
            block = a[z0:z0 + 84].reshape(21, 4, 128, 128)
            return k, block[:, PICK].copy()          # one plane per layer, no averaging
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return k, np.zeros((21, 128, 128), np.uint8)
        except Exception:
            pass
    raise SystemExit(f"chunk {k} failed")


keys = [(cy, cx) for cy in range(CY0, CY1 + 1) for cx in range(CX0, CX1 + 1)]
with cf.ThreadPoolExecutor(8) as ex:
    for (cy, cx), a in ex.map(fetch, keys):
        out[:, (cy - CY0) * 128:(cy - CY0 + 1) * 128, (cx - CX0) * 128:(cx - CX0 + 1) * 128] = a

g = zarr.open_group("aligned_w016_nopool.zarr", mode="w", zarr_format=2)
arr = g.create_array("0", shape=out.shape, chunks=(21, 128, 128), dtype="uint8",
                     compressors=Blosc(cname="zstd", clevel=5, shuffle=Blosc.BITSHUFFLE), fill_value=0)
arr[:] = out
g.attrs.update({"format": f"level2-plane{PICK}of4-21slice (the aligned input with the averaging removed)",
                "source": VOL, "crop_label_px_y0x0": [CY0 * 128, CX0 * 128], "shape": list(out.shape),
                "source_z_slice": [z0, z0 + 84]})
print("wrote aligned_w016_nopool.zarr", out.shape, "nonzero", float((out[10] > 0).mean()))
