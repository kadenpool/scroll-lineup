# Does a better alignment give a better reading?

Everything else in this repository stops at a matrix. This folder carries a surface through a transform,
runs the challenge's ink model on what comes out, and scores it against the challenge's own labels.

**On one segment, through one render path, the reading follows the alignment, and how the input is made
matters about as much as the transform does.** PHerc0139 w016, scored against its published ink labels:

| surface carried to the 2.4 um scan by | rendered by | AUC, forward | AUC, reversed | labelled ink called ink | background called ink |
|---|---|---|---|---|---|
| the official transform | the challenge (its own aligned input) | **0.912** | 0.520 | 70.8 % | 7.2 % |
| the official transform | this folder | **0.857** | 0.603 | 54.4 % | 8.2 % |
| v6_0139c, graded 18 / 31 / 38 um | this folder | **0.812** | 0.628 | 57.0 % | 13.3 % |
| v2_0139a, graded 43 / 107 / 152 um | this folder | **0.790** | 0.627 | 29.9 % | 5.5 % |

All four are the centre 21-layer window, the model's own threshold of 0.5 for "called ink", and the
same held-out validation region, 178,146 pixels on the label grid. For comparison, the same mesh in its
own 9.362 um scan, with no transform at all, reads 0.877 (`depth/`).

Read the middle three rows together: same render path, same model, same labels, only the matrix changes.
The official transform reads best, this tool's better transform next, its worse one last, which is the
order of their graded error. The first two rows differ only in how the image is rendered, and that
costs 0.055, about what this tool's transforms cost against the official one: 0.045 and 0.067. Part of
that may be home advantage: the model was trained on the challenge's own kind of input, including on
this segment (below).

## How big the differences are, and how sure

Not very sure. Scored block by block on the label grid, each arm carried back through its own
registration, this tool's v6_0139c reads worse than the official transform in **16 of 27 blocks** of
64 px (sign test p = 0.22), by a mean of 0.048 AUC with a 95 % block-bootstrap interval of **-0.013 to
+0.115**. With 96 px blocks it is 12 of 17 (p = 0.07), +0.087, interval +0.006 to +0.175. The
whole-region numbers reproduce on the label grid (0.856, 0.813, 0.790), so the order is not an artefact
of the frames, but at this sample size it is a direction on one segment, not a measured cost.

The clearest single difference is in the last column but one. The worse transform, v2_0139a, finds
**about half as much of the labelled ink** at the model's threshold as v6_0139c does, 29.9 % against
57.0 %, while its AUC is only 0.022 lower. AUC ranks pixels; the share is what a person looking at the
ink map sees.

## What was run

- **Surface**: the official PHerc0139 w016 mesh (public segment `20250108000004-w029`), which has
  published ink labels.
- **Arms**: the mesh carried from the 9.362 um scan to a 2.4 um scan by one of three matrices, all in
  `transforms/`: the official one for the 2.399 um scan, inverted; this tool's `v6_0139c` for the same
  scan; and this tool's `v2_0139a` for the 2.403 um scan `20250820105138`, the pair that bends (see
  `docs/seating-check.md`).
- **Render**, identical for all three: `vc_render_tifxyz` at level 2 of the finer scan, `--scale 1
  --slice-step 1 --flip-normals --num-slices 101`, the `--affine` from `transforms/`, over the labelled
  region in 384 px tiles. At level 2 that is 9.596 um per pixel and per layer. `--slice-step` counts
  voxels of the level being read, so at level 2 it has to be 1; 4 gives layers 38 um apart.
- **Model and scoring**: `ink_9um`, `hybrid_3d2d-seed43/step-060000`, nine 21-layer windows, both depth
  orders, AUC over the validation mask (`sweep.py`).
- **Registration** (`register.py`): each render is matched to the label grid by scale and shift against
  the aligned input's centre slice, the same method used for the 9.362 um control. Every arm lands within
  1 px in all six sub-windows checked.
- **The aligned input** was re-scored on the same machine as the three arms and gave 0.9123, against 0.912
  measured on another machine earlier, so the machine and library versions do not move the number.

## What the registration takes out, and what is left

Registering each render to the labels in 2D removes any sideways error in the transform before
scoring. **So this measures what the ink model is sensitive to, the depth at which the surface sits and
the image there, and not whether a transform puts a label in the right place on the page.** For carrying
a segment or a label between scans the sideways error matters too, and this does not test it.

What is left can be measured directly. Each 128 px block's best match to the official render's surface
layer shows where this tool's transform put the surface in depth (`depth_maps.json`). v6_0139c shares
the official render's scan, so its match is tight; v2_0139a's render comes from another scan, so its
match is looser and its nine unmatched blocks, all at the right-hand edge, are left out rather than guessed.

| transform | blocks matched | median depth offset | range | 90 % of blocks within |
|---|---|---|---|---|
| v6_0139c | 108 of 108 | +2.8 um | -21 to +13 um | 14 um |
| v2_0139a | 99 of 108 | -12.7 um | -27 to +26 um | 21 um |

v6_0139c's surface is tilted against the official one, by up to about three layers (34 um) from one end
of the 22 mm region to the other; v2_0139a's sits about a layer to the other side and wanders further.
Both are inside the model's depth tolerance of about six layers, and both still read, with the peak in
the right window. The difference shows up less in AUC than in how much ink crosses the threshold.

## What this changes in the rest of the repository

The alignment budget in the main README treats the whole transform error as if it were depth error.
This says that is conservative for reading: once the sideways part is registered away, a transform
graded WEAK at 107 um at the 95th percentile still reads, and its error in depth is about a fifth of
that. It is not conservative for carrying labels or segments between scans, where all of the error counts.

## What this does not show

- **One segment, one model, one checkpoint.** A different segment could order the arms differently.
- **The differences between transforms are small against the block-to-block noise**, as above.
- **The render path is not the challenge's.** The official transform through this folder reads 0.857,
  through the challenge's own pipeline 0.912. The images agree closely (NCC 0.857 against the aligned
  input's centre slice), so the gap is in how the layers are formed, not where they are. Which step of
  the challenge's pipeline makes the difference is not measured here. nerln measured the same kind of
  gap first, on PHerc0139 w035 (villa #1648): an input rendered at level 2 read 0.949 and 0.955 against
  0.979 for the published volume.
- **The aligned input has a home advantage.** w016 is one of the segments this checkpoint was trained on,
  in exactly the aligned input's form (villa `aligned21_hybrid_3d2d.json`). The pixels scored here are its
  held-out validation region, which shares no pixel with the trained region, but the model has seen the
  rest of this segment in that form. So part of the 0.912 against 0.857 gap may be the model preferring
  its training input rather than the other render being worse. The three arms rendered here share one
  form, so their order is not affected.
- **v6_0139c is graded WEAK by one micron** (31 um at the 95th percentile against a 30 um bar). There is no
  PASS-graded transform for this scan pair to compare.

## Files

| file | what |
|---|---|
| `results.json` | every arm: the nine-window curve, the peak, the registration, the depth match, the grade |
| `per_block.json` | block-by-block AUC on the label grid, and the paired tests above |
| `depth_maps.json` | per-block depth offset of each of this tool's surfaces against the official one |
| `transforms/` | the three 9.362 um to 2.4 um matrices used, each the inverse of a committed transform |
| `register.py`, `sweep.py`, `per_block.py` | registration, the nine-window sweep and scoring, the block comparison |

Reproducing the renders takes about 100 s per tile on a laptop CPU, 12 tiles per arm, streaming from the
public bucket; the renders themselves are not committed. The scoring, once rendered, took 20 to 31 minutes
per arm on CPU.
