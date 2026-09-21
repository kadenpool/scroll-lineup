# Sheet check: do the grown PHerc0846A surfaces stay on one papyrus sheet?

> **Correction, 14 Sep 2026.** The headline below is too strong. This check measured whether a bright papyrus band
> *exists near* the mesh, not whether the mesh *sits on* it. Measured properly on 14 Sep with axiosdevs' published
> seating test plus a depth-profile offset (`evidence_0914/SEATING_CHECK.md`), two of the windows cleared here are
> 168 um and 300 um off the nearest sheet centre, and roughly half of our meshes across the three scrolls are not
> well seated. What survives, and is now confirmed by two further instruments, is the other finding: over-firing
> tracks *good* mesh position rather than bad, so the response is not an artefact of bad surfaces.



Private check, 12 Sep 2026 (run 09:45-10:11 AEST; box A clock 23:54-00:10 UTC). Nothing public.
Question: the two ink models "fire everywhere" on 0846A (15-48 % ink on the surface, still 7-36 % when the inference
window is moved 40 voxels off the mesh; NINE_UM_CHECK.md). A mesh that crosses between sheets, or rides the gap between two
sheets, would show texture that looks like ink everywhere. This check measures where each mesh sits in the sheet stack.

## 1. Verdict in one paragraph

- **The 0846A grown surfaces are on a papyrus sheet, not in the gaps, and most of them track one sheet about as well as the
  published PHerc1203 segments made by the same grower.** No window is "off-sheet". 9 of 27 windows show a clear single band
  at one depth ("on one sheet"), 12 show a band that the mesh drifts through ("weak band"), 6 show no coherent band
  ("wandering": the mesh sits at random depths in the sheet stack, i.e. it passes through gaps and sheets).
- **Over-firing does NOT track bad mesh position — it tracks good mesh position.** The windows that fire most are the ones
  where the mesh sits cleanly on one sheet; the wandering windows are the low-ink ones. Rank correlation between ink share
  and the band-consistency score is +0.57 (27 windows), and between ink share and the share of tile-to-tile band jumps is
  -0.78. By class: "on one sheet" median ink 20 % (range 2-44), "weak band" 15 % (2-29), "wandering" 3 % (2-8).
- So sheet-crossing is ruled out as the cause of the 15-48 % ink shares. The "40 voxels off the sheet" result is explained
  by the sheet spacing: 40 voxels = 375 um is 1.5-2.5 sheets away (spacing 150-250 um here), so the off-sheet window is
  simply another sheet of the same scroll, and the models fire on that too.
- Remaining explanation for the over-firing (not tested here): the models respond to this scroll's papyrus texture itself
  (scan/contrast domain shift), not to where the mesh is.

## 2. Method

1. **Render.** For every window, 41 layers at one voxel spacing (9.362 um, so +/-20 layers = +/-187 um) around the mesh,
   with `vc_render_tifxyz --auto-crop --scale 1 -g 0 --num-slices 41 --slice-step 1 --tif-output ... --cache-gb 4`, streamed
   from the scroll's own official 9.362 um volume (0846A: 20250728152254; 0139: 20250728140407; 1203: 20250820131727).
   Layer 20 is the mesh. The task suggested 29 layers; 41 was used so that the neighbouring sheet is visible too.
   No `--flip-normals` (the earlier 9 um check used it; only the sign of "in front / behind" differs).
2. **Depth profile per tile.** In 32 x 32 px tiles (0.30 mm) the mean grey of rendered pixels in each layer gives a
   41-point depth profile (smoothed by 1 layer). Tiles with < 80 % rendered pixels (black frame, holes) are dropped.
3. **Why not "brightest layer".** The first version used the brightest layer per tile as the sheet centre. On the known-good
   PHerc0139 control this hopped between the mesh's own sheet and its neighbour (the +/-187 um stack contains both), giving
   40-layer "jumps" even for a perfect mesh. So the metrics were rebuilt around the LOCAL cycle and its consistency:
   - **phase** (per tile): where the mesh layer sits in the local sheet/gap cycle within +/-8 layers: 1 = at the sheet
     centre, 0 = in the gap. Evaluated at the window's typical band position (a constant mesh-to-band offset is not
     wandering; the published 0139 mesh rides 2-3 layers in front of its band centre everywhere).
   - **band** (per window; the headline number): average all the tiles' normalised profiles, remove a linear trend, and take
     the prominence of the bump nearest the mesh layer, divided by the typical tile-level modulation. 1 would mean every
     tile has its band at exactly the same depth; 0 means the band sits at a different depth in every tile, so averaging
     washes it out. A gradient without a bump scores 0 (this caught two windows the first version had mis-scored).
   - **band jumps**: share of neighbouring tile pairs whose nearest bright band (found by walking uphill from the mesh
     layer) differs by more than 6 layers (56 um) — the nearest sheet switches between neighbours.
   - **gap tiles**: share of tiles with phase < 0.3 (mesh layer in the dark part of the cycle).
4. **Controls, rendered the same way.** (a) The public PHerc0139 segment 20250108000004-w029 (known text, the "known text
   w016" region of the 9 um check), its official 9.362 um mesh already on box A, three 7.5 mm crops. (b) Four 7.5 mm windows
   of published PHerc1203 raw segments (auto_grown_20251005230830031, ...221856743, ...20250930104534929: same grower as our
   0846A surfaces, same 9.362 um scan family, and the same packing/contrast as 0846A, which 0139 does not have — 0139 has
   dark air gaps between sheets, 0846A and 1203 have sheets packed with grey, not black, between them).
5. **Verdict thresholds, fixed from the controls.** Published windows score band 0.07-0.33 (0139: 0.25-0.33; 1203: 0.07,
   0.13, 0.15, 0.20). "On one sheet" = band >= 0.10 (at or above the published median); "weak band" = 0.05-0.10 (the
   weakest published 1203 window is in this class too); "wandering" = below 0.05, i.e. weaker than every published window;
   "off-sheet" = median phase < 0.35 or > 50 % gap tiles (no window); "can't tell" = < 150 usable tiles (no window).
6. **Coverage.** The six 15 mm zoom regions (also scored on their central 7.5 mm quarter, column "band (centre 7.5 mm)"), the
   ten survey windows with the highest 2 um-model ink share and the eleven lowest (papyrus share >= 0.5), plus 7 control
   windows: 34 renders, 18-35 s each for 7.5 mm, 60-130 s for 15 mm. Renders were deleted right after measuring; box A
   never went below 11.1 GB free; 11 MB of results/logs/scripts remain in box A:sc/ (mine).
   The two 101-layer zoom renders and the 101-layer 0139 render left on box B from the 9 um check were re-scored with the
   same code and agree with the fresh renders (band 0.08 vs 0.08 for r105_c25, 0.07 vs 0.09 for r75_c45).

Ink % C / D in the tables = frac_gt_0.5 of models C (rendered order) and D (reversed) from the survey runs
(kag_out/s0846a_b*, s0846a2_b*, z0846a_b*); "band depth" = layers from the mesh to the band centre (+ = behind, along the
render normal); "tile modulation" = typical (max-min)/mean of a tile's profile (how much sheet/gap structure the scan shows).

## 3. Results

### Controls: published PHerc0139 w029 mesh (three 7.5 mm crops)

| window | ink % C / D | band | band (centre 7.5 mm) | band depth (layers) | tile modulation | phase (median) | gap tiles % | band jumps % | tiles | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| 0139 w029 crop0 | - / - | 0.33 | - | +3 | 0.84 | 0.74 | 16 | 10 | 625 | on one sheet |
| 0139 w029 crop1 | - / - | 0.33 | - | +2 | 0.83 | 0.68 | 21 | 9 | 625 | on one sheet |
| 0139 w029 crop2 | - / - | 0.25 | - | +3 | 0.83 | 0.57 | 25 | 10 | 625 | on one sheet |

### Controls: published PHerc1203 segments (7.5 mm windows)

| window | ink % C / D | band | band (centre 7.5 mm) | band depth (layers) | tile modulation | phase (median) | gap tiles % | band jumps % | tiles | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| 1203 20251005230830031 r82_c82 | - / - | 0.13 | - | +0 | 0.20 | 0.67 | 19 | 13 | 529 | on one sheet |
| 1203 20251005230830031 r122_c42 | - / - | 0.15 | - | +0 | 0.19 | 0.66 | 21 | 14 | 526 | on one sheet |
| 1203 20251005221856743 r180_c64 | - / - | 0.07 | - | -1 | 0.25 | 0.57 | 27 | 21 | 474 | weak band |
| 1203 20250930104534929 r42_c126 | - / - | 0.20 | - | +1 | 0.18 | 0.66 | 23 | 17 | 460 | on one sheet |

### PHerc0846A: the six 15 mm zoom regions

| window | ink % C / D | band | band (centre 7.5 mm) | band depth (layers) | tile modulation | phase (median) | gap tiles % | band jumps % | tiles | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| 040822053 Z r50_c70 | 22 / 16 | 0.21 | 0.35 | -1 | 0.37 | 0.67 | 21 | 15 | 2304 | on one sheet |
| 025619069 Z r105_c25 | 25 / 12 | 0.08 | 0.08 | -3 | 0.36 | 0.68 | 20 | 14 | 1824 | weak band |
| 063530412 Z r30_c105 | 24 / 6 | 0.10 | 0.09 | -3 | 0.20 | 0.61 | 25 | 16 | 1823 | on one sheet |
| 063746464 Z r75_c45 | 2 / 23 | 0.09 | 0.03 | +3 | 0.39 | 0.57 | 31 | 23 | 2300 | weak band |
| 030142380 Z r35_c65 | 4 / 13 | 0.03 | 0.03 | +2 | 0.25 | 0.51 | 32 | 30 | 2251 | wandering |
| 024106908 Z r50_c40 | 5 / 3 | 0.06 | 0.10 | +5 | 0.15 | 0.54 | 31 | 23 | 2271 | weak band |

### PHerc0846A: the ten highest-ink 7.5 mm survey windows

| window | ink % C / D | band | band (centre 7.5 mm) | band depth (layers) | tile modulation | phase (median) | gap tiles % | band jumps % | tiles | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| 061936267_r20_c55 | 40 / 47 | 0.15 | - | +0 | 0.22 | 0.65 | 20 | 10 | 529 | on one sheet |
| 061936267_r40_c15 | 24 / 44 | 0.10 | - | +4 | 0.40 | 0.61 | 28 | 21 | 529 | on one sheet |
| 040822053_r65_c25 | 27 / 31 | 0.07 | - | -1 | 0.35 | 0.63 | 26 | 15 | 529 | weak band |
| 034621782_r40_c85 | 33 / 24 | 0.29 | - | -4 | 0.73 | 0.75 | 13 | 14 | 529 | on one sheet |
| 061936267_r80_c95 | 18 / 37 | 0.10 | - | +4 | 0.35 | 0.59 | 27 | 15 | 529 | weak band |
| 032347463_r110_c105 | 21 / 28 | 0.07 | - | +4 | 0.19 | 0.58 | 24 | 11 | 529 | weak band |
| 040822053_r105_c105 | 28 / 18 | 0.07 | - | -3 | 0.40 | 0.58 | 27 | 20 | 529 | weak band |
| 034621782_r50_c45 | 18 / 26 | 0.15 | - | -2 | 0.79 | 0.87 | 7 | 7 | 529 | on one sheet |
| 063530412_r30_c105 | 33 / 7 | 0.19 | - | -4 | 0.19 | 0.58 | 24 | 16 | 529 | on one sheet |
| 030142380_r35_c65 | 4 / 35 | 0.06 | - | +1 | 0.28 | 0.57 | 26 | 17 | 529 | weak band |

### PHerc0846A: the eleven lowest-ink 7.5 mm survey windows

| window | ink % C / D | band | band (centre 7.5 mm) | band depth (layers) | tile modulation | phase (median) | gap tiles % | band jumps % | tiles | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| 071903158_r105_c10 | 2 / 1 | 0.01 | - | -4 | 0.26 | 0.51 | 34 | 33 | 515 | wandering |
| 024106966_r75_c35 | 3 / 1 | 0.00 | - | +2 | 0.28 | 0.50 | 34 | 31 | 529 | wandering |
| 065428392_r10_c60 | 3 / 1 | 0.18 | - | +0 | 0.41 | 0.68 | 21 | 24 | 528 | on one sheet |
| 025522741_r75_c35 | 3 / 1 | 0.05 | - | -1 | 0.19 | 0.55 | 28 | 28 | 518 | weak band |
| 024106966_r35_c10 | 3 / 2 | 0.05 | - | -5 | 0.14 | 0.55 | 29 | 19 | 522 | weak band |
| 071903158_r95_c105 | 2 / 3 | 0.06 | - | +3 | 0.26 | 0.53 | 30 | 24 | 529 | weak band |
| 065120760_r65_c65 | 4 / 2 | 0.04 | - | -3 | 0.30 | 0.53 | 33 | 35 | 515 | wandering |
| 065120760_r110_c65 | 5 / 2 | 0.04 | - | +1 | 0.23 | 0.55 | 30 | 28 | 526 | wandering |
| 024106908_r70_c80 | 3 / 4 | 0.04 | - | -6 | 0.18 | 0.52 | 31 | 24 | 520 | wandering |
| 065428392_r55_c20 | 7 / 2 | 0.20 | - | -1 | 0.46 | 0.72 | 18 | 18 | 529 | on one sheet |
| 065428392_r95_c5 | 5 / 4 | 0.10 | - | -6 | 0.22 | 0.50 | 34 | 26 | 474 | weak band |

### Does over-firing track sheet position? (27 0846A windows)

| what is compared with ink share (mean of C and D) | rank correlation | n |
|---|---|---|
| band (sheet consistency) | +0.57 | 27 |
| band jumps (nearest sheet switches between tiles) | -0.78 | 27 |
| gap tiles | -0.55 | 27 |
| phase (median) | +0.57 | 27 |
| tile modulation (scan contrast) | +0.30 | 27 |
| papyrus share of the window (from windows.json) | +0.68 | 21 |
| 7.5 mm survey windows only: band | +0.59 | 21 |

Reading: the more consistently the mesh sits on one sheet, the MORE the models fire. Windows with no coherent band are the
2-8 % ink windows. Part of this is that the lowest-ink windows sit near the edges of their surfaces (papyrus share 0.5-0.7,
ragged geometry), which is also where the grower wanders; either way the direction is opposite to the hypothesis.

### The six zoom regions: sheet verdict next to the 9 um "40 voxels off" result

Ink share (%) of the 9 um model s43-60k, rendered / reversed order, from NINE_UM_CHECK.md Table 3.

| region | on the mesh | window 40 voxels in front | 40 voxels behind | sheet verdict (band, centre-quarter band) |
|---|---|---|---|---|
| r50_c70 | 47 / 48 | 36 / 34 | 35 / 34 | on one sheet (0.21, 0.35 — the best 0846A window) |
| r30_c105 | 28 / 35 | 22 / 23 | 25 / 27 | on one sheet (0.10, 0.09) |
| r105_c25 | 15 / 30 | 7 / 12 | 11 / 17 | weak band (0.08, 0.08) |
| r75_c45 | 42 / 31 | 24 / 22 | 23 / 19 | weak band (0.09, 0.03) |
| r50_c40 | 26 / 30 | 18 / 22 | 20 / 23 | weak band (0.06, 0.10) |
| r35_c65 | 28 / 24 | 24 / 20 | 21 / 19 | wandering (0.03, 0.03) |
| known text 0139 w016 | 13 / 6 | 5 / 4 | 4 / 3 | on one sheet (0.25-0.33) |

The region that fires most (r50_c70, 47 %) is the one most cleanly on a single sheet, and it still fires 35 % when the
window is 375 um away — which, at a sheet spacing of 150-250 um, is one or two sheets over. The off-mesh response is the
model liking other sheets of this scroll, not the mesh being off its sheet.

## 4. What the pictures show

- `sheet_check.png`: per window, the layer the mesh sits on (left) and the phase map (right; green = mesh at the sheet
  centre, red = in the gap). Bottom: the window-mean depth profiles — the 0139 control has a strong band 20-30 um behind the
  mesh, the 1203 controls a small bump exactly at the mesh, the 0846A high-ink windows small bumps at the mesh or a few
  layers in front, the wandering windows nothing.
- `sheet_check_offsets.png`: the same layout with the nearest-band offset map instead (blue = band in front, red = behind).
- The phase maps are speckled even for the 0139 control (16-25 % "gap" tiles on a known-good mesh): at 0.3 mm the
  published meshes also wobble through their sheet. Read the window-mean profile and the band score, not single tiles.

## 5. Caveats

- Only four published 1203 windows and one 0139 mesh as controls; the class boundaries (0.05 / 0.10) are set from them and
  are a graded scale, not a pass/fail line. A published 1203 window falls in "weak band".
- "Wandering" means the mesh's depth relative to the local sheet is inconsistent across the window; with sheets 150-250 um
  apart and grey (not empty) gaps, the code cannot say whether it stays inside one thick sheet or steps to the next.
  Either way those windows are the low-ink ones, so it does not matter for the question asked.
- The 0139 control is a different scan with dark air gaps; its band scores are naturally higher. The 1203 controls are the
  like-for-like comparison (same grower, same scanner settings, same packing).
- Ink shares in the tables come from the 2 um-scan survey models (C/D); the 9 um numbers in the zoom table come from the
  9 um check. Both agree on which regions fire most.

## 6. Files

- Scripts: `evidence_0912/sheet_check_files/` — `render_win.sh` (render, disk guard, lock), `sheet_depth.py` (tile
  profiles, run on box A), `run_queue.sh` (render -> profile -> delete, one window at a time), `make_list.py` +
  `rank_windows.py` (window selection; `sc_list.txt`, `selection.json`, `_json/ranked.json`), `sheet_metrics.py` (phase /
  band / jump metrics from the saved profiles; `metrics_41.json`), `sheet_report.py` (verdicts, `tables.md`, both
  PNGs), `confound.py` (correlations), `period.py` (sheet spacing from the 101-layer stacks), `run_fork101.sh`.
- Data kept: `results/*.npz` (per-tile profiles, centre layer 2x down) and `results_fork101/`; render logs in
  `logs_boxA/`. Nothing was left on box A exceptsc/` (11 MB) and on box B `<work-dir>/sc/` (small).
