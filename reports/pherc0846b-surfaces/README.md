# First surfaces on PHerc0846B

PHerc0846B is one of the scrolls eligible for the First Letters prize, and the open-data catalogue lists no surfaces
for it (checked 24 Sep 2026, catalogue ETag `7b86f3272d4ffa1085fafb4e3e6383bf`), and neither pscamillo's published meshes for eight other eligible scrolls
(`pscamillo/vesuvius-eligible-meshes`) nor the atlas built on them (`rodriguescarson/eligible-scroll-atlas`) covers it (checked 25 Sep). These are twelve surfaces grown on
it, 97.30 cm2 in all by the grower's own figures, of which about 1.1 to 1.2 cm2 is covered twice where surfaces meet
(below). Its eligible volume, `20250804142305`, was scanned at 9.362 um and 113 keV: the voxel size and energy of
PHerc0139's native scan, part of the data the public `ink_9um` models were trained on.

| surface | seed (x, y, z) | area cm2 | VC3D build |
|---|---|---|---|
| s01 | 3240, 3763, 7407 | 7.62 | d285029 (22 Sep) |
| s02 | 4231, 4731, 7422 | 7.87 | 78877ea (23 Sep) |
| s03 | 2647, 4752, 6832 | 8.04 | 78877ea (23 Sep) |
| s04 | 4207, 3214, 8143 | 8.60 | 78877ea (23 Sep) |
| s05 | 4336, 3439, 6640 | 7.65 | 78877ea (23 Sep) |
| s06 | 3719, 4324, 8504 | 8.38 | 78877ea (23 Sep) |
| s07 | 2998, 3154, 8630 | 8.89 | 78877ea (23 Sep) |
| s08 | 3952, 4718, 6128 | 7.76 | 6bbe6e2 (24 Sep) |
| s09 | 1586, 4563, 6128 | 7.94 | 6bbe6e2 (24 Sep) |
| s10 | 2939, 3837, 5962 | 7.67 | 6bbe6e2 (24 Sep) |
| s11 | 1968, 3794, 5104 | 8.05 | 6bbe6e2 (24 Sep) |
| s12 | 1633, 5203, 9874 | 8.84 | 6bbe6e2 (24 Sep) |

Each folder holds the surface in the challenge's tifxyz format (`x.tif`, `y.tif`, `z.tif`, `meta.json`): a grid of
152 by 152 points, one per 20 voxels, of which 21,904 are valid on every surface. Each has its own segment id,
`PHerc0846B_s01` to `PHerc0846B_s12`, so VC3D loads all twelve side by side. It also holds a preview: plane 15, the
middle one, where the surface lies, of the 31 rendered along the surface normal, shrunk to a third and stretched on
its own (1st to 99.5th percentile), so brightness cannot be compared between previews. `index.json` has the table
with every figure unrounded, written from each `meta.json` and the run's own record (`render_covered` is the share of
the render canvas holding scan data, as the render step recorded it; it reads 0.923 when the render holds scan data
wherever the grid reaches).
`python3 trace_numbers.py` re-derives the numbers here from the files (it needs numpy, scipy and Pillow).

## How they were made

- Grown with villa's `vc_grow_seg_from_seed` from the Linux AppImage, on the team's published m7 surface prediction
  for this volume (model 20260413222639, level 0, threshold 0.2) with its published normal grids, step 20, a limit
  of 75 generations, on free Kaggle CPU sessions: the growing step of the route the challenge's own guide describes
  (Create Segment, GrowPatch), run headless. The guide's route goes on to refine by hand and flatten; these surfaces
  had neither.
- Seeds: a picker that looks for a thin sheet inside the scroll, away from its edge and near mid-height, run over
  every place at least 12 mm from the others. The survey that gave s01 to s07 (24 Sep) was not kept; a kept one
  (25 Sep, 00:10 AEST) found 32 places, accepted 13, and its first seven are exactly s01 to s07. Of the other six,
  the five at least 12 mm from every earlier seed are s08 to s12; the sixth, (3662, 3726, 4912), lies 11.98 mm from
  s10 and was not grown. The seeds are at least 11.8 mm apart. None was chosen by looking at ink.
- Rendered with villa's `vc_render_tifxyz` at full resolution: 31 planes, one per voxel, `--flip-normals`.
- Areas are the grower's own, and `trace_numbers.py` gets the same figures from the grid. All twelve are the same
  grid of valid points, which would cover 7.58 cm2 lying flat; the rest of each area is stretch and fold, so a
  larger area does not mean more good surface (s07 and s12, the largest, are the most swirled).
- Overlap: seeds about 12 mm apart do not stop two surfaces from growing onto the same sheet. At the grid points
  (one per 20 voxels), 200 points of s10 lie within 4 voxels of s01, 81 of s08 within 4 of s03, 17 of s04 within 4
  of s07, 7 of s03 within 4 of s09, 5 of s01 within 4 of s05, and 2 each for s01 and s04, and s02 and s08. Measured
  on the grower's triangles, s10 and s01 share about 67 mm2 (lying within 4 voxels of each other), s03 and s08 about
  22 to 26 mm2, s04 and s07 12 to 15 mm2, and s01 and s05, s02 and s08, s03 and s09, s01 and s04 under 5 mm2 each;
  each of these seven pairs crosses, the two surfaces passing through each other. Four more pairs come within 4
  voxels over less than 0.1 mm2 each: s09 and s10 cross, and s01 and s09, s05 and s10, and s05 and s09 are 1.7,
  1.7 and 3.2 voxels apart at their nearest. No other pair comes within 4 voxels; the closest, s01 and s07, are 36.3 voxels apart at
  their nearest.
- On the scan, not in the air (villa issue #1875 reports that the m7 prediction marks sheet in the air around every
  First Letters scroll, and that a surface grown there lies on no papyrus): at most 0.3 % of each preview is black
  (no scan data, or the darkest papyrus after the stretch), except s05 (1.0 %, a patch at the top) and s11 (2.35 %).
  s11 is the exception in kind too: its upper left, and the gap along its crack, are dark with no papyrus texture,
  a far larger share of it than on any other surface; its 2.35 % counts only the no-data pockets inside them.
- The pinned d285029 AppImage was no longer on GitHub when s02 to s12 were grown, so each used the release then
  called "latest": 78877ea (23 Sep) for s02 to s07, 6bbe6e2 (24 Sep) for s08 to s12. Each run logged the fallback,
  and `index.json` records each AppImage's sha256.

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
  | s08 | crossed fibres over most of it, with a few cracks; swirls and gaps along the top and down the right side |
  | s09 | crossed fibres over most of it; swirls at the lower left |
  | s10 | crossed fibres over the right two thirds; swirls and streaks over the left third |
  | s11 | crossed fibres in bands; its upper left and a gap along a crack are dark, with no papyrus texture |
  | s12 | mostly swirls |

- These are grown patches, not a full unwrapping: 97 cm2 is a small part of the scroll.
- No ink is read from them here. The ink detection floor was measured on s01 to s07, and the public ink models' own
  output on each of those whole surfaces is published with it (`../ink-detection-floor/`, day 3); no letters are
  claimed from that output.

The scan, and the team's surface prediction these were grown on, are the Vesuvius Challenge's open data; the
catalogue lists the volume under CC BY-NC 4.0, and these surfaces and previews, made from it, are shared under the
same licence.

Two independent reviews checked these before publication: the first seven in `REVIEW.md`, all twelve in
`REVIEW2.md`, each with its findings and what was done about each. `REVIEW2.md` also records a later finding that
the closest distances were still too high and the areas within 4 voxels read low, and the exact measurement that
replaced them.

*Grown and written with Claude Code under my direction.*
