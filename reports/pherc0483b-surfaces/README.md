# First published surfaces on PHerc0483B

PHerc0483B is one of the scrolls eligible for the First Letters prize (villa's `prizeEligibility.json`), and the
open-data catalogue lists no surfaces for it (checked 24 Sep 2026, catalogue ETag
`7b86f3272d4ffa1085fafb4e3e6383bf`), and neither pscamillo's published meshes for eight other eligible scrolls
(`pscamillo/vesuvius-eligible-meshes`) nor the atlas built on them (`rodriguescarson/eligible-scroll-atlas`) covers it (checked 25 Sep). gmDevi's `vc-windows-tools` had screened a spiral fit of it with an ink model on 11 Sep 2026
(commit 4206088: renders of 18 windings, all negative), publishing the renders but not the surfaces. These are five
surfaces grown on it, 35.42 cm2 in all, which do not touch one
another (below). Its eligible volume, `20251124083638`, was scanned at 8.64 um and 116 keV.

| surface | seed (x, y, z) | area cm2 | VC3D build |
|---|---|---|---|
| s01 | 4881, 3280, 6384 | 7.33 | 24ca51b (24 Sep) |
| s02 | 1975, 3900, 6392 | 6.99 | 6bbe6e2 (24 Sep) |
| s03 | 6424, 3971, 7042 | 7.24 | 6bbe6e2 (24 Sep) |
| s04 | 3664, 5875, 4624 | 6.84 | 6bbe6e2 (24 Sep) |
| s05 | 5808, 3247, 8208 | 7.01 | 6bbe6e2 (24 Sep) |

Each folder holds the surface in the challenge's tifxyz format (`x.tif`, `y.tif`, `z.tif`, `meta.json`): a grid of
152 by 152 points, one per 20 voxels, of which 21,904 are valid on every surface, with a segment id of its own
(`PHerc0483B_s01` to `PHerc0483B_s05`) so VC3D loads all five side by side. It also holds a preview: plane 15, the
middle one, where the surface lies, of the 31 rendered along the surface normal, shrunk to a third and stretched on
its own (1st to 99.5th percentile), so brightness cannot be compared between previews. `index.json` has the table
with every figure unrounded, written from each `meta.json` and the run's own record (`render_covered` is the share of
the render canvas holding scan data, as the render step recorded it; it reads 0.923 when the render holds scan data
wherever the grid reaches).
`python3 trace_numbers.py` re-derives the numbers here from the files (it needs numpy, scipy and Pillow).

## How they were made

- The same recipe as the PHerc0846B surfaces (`../pherc0846b-surfaces/`): villa's `vc_grow_seg_from_seed` from the
  Linux AppImage, on the team's published m7 surface prediction for this volume (model 20260413222639, level 0,
  threshold 0.2) with its published normal grids, step 20, a limit of 75 generations, on free Kaggle CPU sessions,
  run headless; no hand refinement or flattening. The pinned d285029 AppImage is no longer on GitHub, so each used
  the release then called "latest": build 24ca51b for s01, and 6bbe6e2, released later the same day, for s02 to
  s05. Each run logged the fallback, and `index.json` records each AppImage's sha256.
- Seeds: s01's came from the recipe's own picker (a thin sheet inside the scroll, away from its edge and near
  mid-height). The same picker, run over every place at least 12 mm from the others (33 places), passed 6; two of
  them lie within 12 mm of s01's seed (4.4 and 10.1 mm) and would mostly repeat it, so they were not grown. The five
  seeds are about 13 mm apart at the closest. None was chosen by looking at ink.
- Rendered with villa's `vc_render_tifxyz` at full resolution: 31 planes, one per voxel, `--flip-normals`.
- Areas are the grower's own, and `trace_numbers.py` gets the same figures from the grid. All five are the same grid
  of valid points, which would cover 6.45 cm2 lying flat; the rest of each area is stretch and fold, so a larger
  area does not mean more good surface.
- Overlap: none. No two surfaces come within 4 voxels of each other anywhere; the closest pair, s03 and s05, are
  58.2 voxels apart at their nearest (measured exactly on the grower's triangles).
- On the scan, not in the air (villa issue #1875): at most 0.30 % of each preview is black (no scan data, or the
  darkest papyrus after the stretch).

## Limits

- A preview shows crossed papyrus fibres where a surface follows one sheet, and swirls where it crosses from one
  sheet to another. A first look at each preview, by Claude Code (not a measurement):

  | surface | first look |
  |---|---|
  | s01 | crossed fibres over the upper-left half, coarse, with dark gaps; swirls below and to the right |
  | s02 | crossed fibres in a central block, about half of it; swirls down the left side, the right edge and the bottom |
  | s03 | mostly swirls; crossed fibres in a diagonal band through the middle |
  | s04 | crossed fibres over most of it; a smoother region at the upper right; swirls at the lower left |
  | s05 | crossed fibres over the left half; swirls on the right |

- These are grown patches, not a full unwrapping: 35 cm2 is a small part of the scroll.
- No ink is read from them here; see day 4 below.

The scan, and the team's surface prediction these were grown on, are the Vesuvius Challenge's open data; the
catalogue lists the volume under CC BY-NC 4.0, and these surfaces and previews, made from it, are shared under the
same licence.

An independent review checked this release before publication; its findings, and what was done about each, are in
`REVIEW.md`, with a later check of the distances.

Day 4 of the ink detection floor (`../ink-detection-floor/`, amendment 3 and `RESULTS_DAY4.md`) ran the two public 9 um
ink checkpoints on these five surfaces: neither reaches a floor (one does not detect PHerc0139 letters planted at full
strength, and the other fails its checks), and no letters are claimed from their output.

*Edited 26 Sep 2026: gmDevi's earlier ink-model screen of this scroll is credited, the title says "first
published surfaces", and day 4's result is named.*

*Grown and written with Claude Code under my direction.*
