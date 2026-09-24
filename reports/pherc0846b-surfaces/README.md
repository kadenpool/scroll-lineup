# First surfaces on PHerc0846B

PHerc0846B is one of the scrolls eligible for the First Letters prize, and the open-data catalogue lists no surfaces
for it (checked 24 Sep 2026, catalogue ETag `7b86f3272d4ffa1085fafb4e3e6383bf`). These are seven surfaces grown on
it, 57.06 cm2 in all, which barely touch one another (below). Its eligible volume, `20250804142305`, was scanned at
9.362 um and 113 keV: the voxel size and energy of PHerc0139's native scan, part of the data the public `ink_9um`
models were trained on.

| surface | seed (x, y, z) | area cm2 | VC3D build |
|---|---|---|---|
| s01 | 3240, 3763, 7407 | 7.62 | d285029 (22 Sep) |
| s02 | 4231, 4731, 7422 | 7.87 | 78877ea (23 Sep) |
| s03 | 2647, 4752, 6832 | 8.04 | 78877ea (23 Sep) |
| s04 | 4207, 3214, 8143 | 8.60 | 78877ea (23 Sep) |
| s05 | 4336, 3439, 6640 | 7.65 | 78877ea (23 Sep) |
| s06 | 3719, 4324, 8504 | 8.38 | 78877ea (23 Sep) |
| s07 | 2998, 3154, 8630 | 8.89 | 78877ea (23 Sep) |

Each folder holds the surface in the challenge's tifxyz format (`x.tif`, `y.tif`, `z.tif`, `meta.json`): a grid of
152 by 152 points, one per 20 voxels, of which 21,904 are valid on every surface. Each has its own segment id,
`PHerc0846B_s01` to `PHerc0846B_s07`, so VC3D loads all seven side by side. It also holds a preview: plane 15, the
middle one, where the surface lies, of the 31 rendered along the surface normal, shrunk to a third and stretched on
its own (1st to 99.5th percentile), so brightness cannot be compared between previews. `index.json` has the table
with every figure unrounded, written from each `meta.json` and the run's own record.
`python3 trace_numbers.py` re-derives the numbers here from the files (it needs numpy, scipy and Pillow).

## How they were made

- Grown with villa's `vc_grow_seg_from_seed` from the Linux AppImage, on the team's published m7 surface prediction
  for this volume (model 20260413222639, level 0, threshold 0.2) with its published normal grids, step 20, a limit
  of 75 generations, on a free Kaggle CPU session: the growing step of the route the challenge's own guide describes
  (Create Segment, GrowPatch), run headless. The guide's route goes on to refine by hand and flatten; these surfaces
  had neither.
- Seeds: a picker that looks for a thin sheet inside the scroll, away from its edge and near mid-height. Run over 14
  candidate places at least 12 mm apart, it accepted 7: s01's seed, found again, and the six others. The seeds it
  settled on are at least 11.8 mm apart. None was chosen by looking at ink.
- Rendered with villa's `vc_render_tifxyz` at full resolution: 31 planes, one per voxel, `--flip-normals`.
- Areas are the grower's own, and `trace_numbers.py` gets the same figures from the grid. All seven are the same
  grid of valid points, which would cover 7.58 cm2 lying flat; the rest of each area is stretch and fold, so a
  larger area does not mean more good surface (s07, the largest, is the most swirled).
- Overlap: the surfaces barely touch. At the grid points, 17 points of s04 lie within 4 voxels of s07, 5 of s01
  within 4 of s05, and 2 of s01 within 4 of s04. Sampled 6 by 6 in each cell, s04 and s07 meet within 0.16 voxels
  and share about 11 to 13 mm2 (within 4 voxels of each other), s01 and s05 meet within 0.12 voxels over about
  3.5 mm2, and s01 and s04 within 0.34 voxels over less than 1 mm2. That is about 0.3 % of the total. The closest other
  pair, s01 and s07, stays 38 voxels apart.
- On the scan, not in the air: villa issue #1875 reports that the m7 prediction marks sheet in the air around every
  First Letters scroll, and that a surface grown there lies on no papyrus. These lie on the scan: at most 0.3 % of
  each preview is black (no scan data, or the darkest papyrus after the stretch), except s05, where a patch with no
  data at the top brings it to 1.0 %.
- The pinned d285029 AppImage was no longer on GitHub (HTTP 404) when s02 to s07 were grown, so they used the
  release then called "latest", build 78877ea, dated 23 Sep. Each run logged the fallback, and `index.json` records
  each AppImage's sha256.

## Limits

- A preview shows crossed papyrus fibres where a surface follows one sheet, and swirls where it crosses from one
  sheet to another. The swirled parts are not good surface, and how much of each surface they cover differs a lot.
  A first look at each preview, by Claude Code (not a measurement):

  | surface | first look |
  |---|---|
  | s01 | crossed fibres over most of it; swirls along the top and left edges |
  | s02 | crossed fibres over most of it, crossed by two long cracks; swirls at the top and lower right; a very bright fleck at the right edge, which also makes this preview look darker |
  | s03 | crossed fibres over most of it; a dark band down the left side; swirls at the lower right |
  | s04 | crossed fibres over the lower half; swirls and gaps across the upper half |
  | s05 | crossed fibres almost everywhere; swirls in the top right corner and along the lower right edge; a small patch with no data at the top |
  | s06 | crossed fibres in a tilted band through the middle; swirls and dark gaps above and below it |
  | s07 | mostly swirls and streaks; little clear crossed-fibre texture |

- These are grown patches, not a full unwrapping: 57 cm2 is a small part of the scroll.
- No ink is read from them here. The ink detection floor was measured on them, and the public ink models' own
  output on each whole surface is published with it (`../ink-detection-floor/`, day 3); no letters are claimed
  from that output.

The scan, and the team's surface prediction these were grown on, are the Vesuvius Challenge's open data; the
catalogue lists the volume under CC BY-NC 4.0, and these surfaces and previews, made from it, are shared under the
same licence.

An independent review checked this release before publication; its findings, and what was done about each, are in
`REVIEW.md`.

*Grown and written with Claude Code under my direction.*
