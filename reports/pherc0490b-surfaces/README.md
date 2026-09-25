# First surfaces on PHerc0490B

PHerc0490B is one of the scrolls eligible for the First Letters prize (villa's `prizeEligibility.json`), and the
open-data catalogue lists no surfaces for it (checked 24 Sep 2026, catalogue ETag
`7b86f3272d4ffa1085fafb4e3e6383bf`), and neither pscamillo's published meshes for eight other eligible scrolls
(`pscamillo/vesuvius-eligible-meshes`) nor the atlas built on them (`rodriguescarson/eligible-scroll-atlas`) covers it (checked 25 Sep). These are three surfaces grown on it, 23.42 cm2 in all, which do not touch one
another (below). Its eligible volume, `20250521151215`, was scanned at 8.64 um and 116 keV.

| surface | seed (x, y, z) | area cm2 | VC3D build |
|---|---|---|---|
| s01 | 2981, 5226, 5330 | 7.68 | 24ca51b (24 Sep) |
| s02 | 4716, 5233, 7342 | 7.71 | 24ca51b (24 Sep) |
| s03 | 2096, 3256, 6672 | 8.03 | 24ca51b (24 Sep) |

Each folder holds the surface in the challenge's tifxyz format (`x.tif`, `y.tif`, `z.tif`, `meta.json`): a grid of
152 by 152 points, one per 20 voxels, of which 21,904 are valid on every surface, with a segment id of its own
(`PHerc0490B_s01` to `PHerc0490B_s03`) so VC3D loads all three side by side. It also holds a preview: plane 15, the
middle one, where the surface lies, of the 31 rendered along the surface normal, shrunk to a third and stretched on
its own (1st to 99.5th percentile), so brightness cannot be compared between previews. `index.json` has the table
with every figure unrounded, written from each `meta.json` and the run's own record (`render_covered` is the share of
the render canvas holding scan data, as the render step recorded it; it reads 0.923 when the render holds scan data
wherever the grid reaches). `python3 trace_numbers.py` re-derives the numbers here from the files (it needs numpy,
scipy and Pillow).

## How they were made

- The same recipe as the PHerc0846B surfaces (`../pherc0846b-surfaces/`): villa's `vc_grow_seg_from_seed` from the
  Linux AppImage, on the team's published m7 surface prediction for this volume (model 20260413222639, level 0,
  threshold 0.2) with its published normal grids, step 20, a limit of 75 generations, on free Kaggle CPU sessions,
  run headless; no hand refinement or flattening. The pinned d285029 AppImage is no longer on GitHub, so all three
  used the release then called "latest", build 24ca51b, dated 24 Sep; each run logged the fallback, and
  `index.json` records each AppImage's sha256.
- Seeds: the recipe's own picker (a thin sheet inside the scroll, away from its edge and near mid-height), run over
  every place at least 12 mm from the others: 32 places, of which only 3 pass its thin-sheet test, against 13 of 32
  on PHerc0846B and 6 of 33 on PHerc0483B. Why is not measured: the team's m7 prediction marks 21 to 35 % of each
  128-voxel box as sheet here, against 18 to 32 % on PHerc0846B and 22 to 40 % on PHerc0483B, so density alone does
  not explain it. The three seeds are about 22 mm apart at the closest. None was chosen by looking at ink.
- Rendered with villa's `vc_render_tifxyz` at full resolution: 31 planes, one per voxel, `--flip-normals`.
- Areas are the grower's own, and `trace_numbers.py` gets the same figures from the grid. All three are the same grid
  of valid points, which would cover 6.45 cm2 lying flat; the rest of each area is stretch and fold, so a larger
  area does not mean more good surface.
- Overlap: none. No two surfaces come within 4 voxels of each other anywhere (measured exactly on the grower's
  triangles).
- On the scan, not in the air (villa issue #1875): at most 0.24 % of each preview is black (no scan data, or the
  darkest papyrus after the stretch), except s03, where a corner patch with no data brings it to 0.88 %.

## Limits

- A preview shows crossed papyrus fibres where a surface follows one sheet, and swirls where it crosses from one
  sheet to another. On this scroll the swirls cover more than on PHerc0846B. A first look at each preview, by
  Claude Code (not a measurement):

  | surface | first look |
  |---|---|
  | s01 | mostly swirls; crossed fibres in patches through the middle |
  | s02 | crossed fibres over the middle and lower right; swirls at the top and lower left; dark gaps at the bottom |
  | s03 | mostly streaks radiating from the centre; a no-data patch with a bright block at the lower right corner |

- These are grown patches, not a full unwrapping: 23 cm2 is a small part of the scroll.
- No ink has been read from them.

The scan, and the team's surface prediction these were grown on, are the Vesuvius Challenge's open data; the
catalogue lists the volume under CC BY-NC 4.0, and these surfaces and previews, made from it, are shared under the
same licence.

An independent review checked this release before publication; its findings, and what was done about each, are in
`REVIEW.md`, with a later check of the distances.

*Grown and written with Claude Code under my direction.*
