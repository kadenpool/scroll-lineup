# 9 um check on PHerc0846A: does the official 9 um ink model see ink where our 2 um maps do?

**Update 12 Sep, 06:18 AEST (from `date`): the within-scroll null has been run - see section 10. Short version: ordinary never-picked 0846A
windows show the same 9 um / 2 um overlap, in proportion to how much the 2 um model fires; r75_c45 is ordinary; r105_c25
stays on top on seed43 only, so it is not a robust outlier.**

Written overnight Sat 12 Sep 2026 by agent D (started 01:06 AEST, finished 03:53 AEST, both from `date`). Private: nothing
was posted or pushed; no public Kaggle notebooks were used (all runs were on box A and box B CPUs).

Pictures: `evidence_0912/nine_um_check.png` (one row per place: surface | 2 um map | 9 um forward | 9 um reverse | 9 um
off-sheet) and `evidence_0912/nine_um_r105_zoom.png` (close-up of the best region; the window was CHOSEN as the one with the
strongest agreement, so it is a best case to look at, not a statistic).

## 1. Short answer

**Verdict: CAN'T TELL.** By eye there are no letters in any 9 um map. By the numbers the 9 um model does respond where
the 2 um model responds, at about the strength seen on known text, but this test is not yet calibrated against blank
papyrus, so that response cannot be called ink.

1. **The pipeline works on known text.** Our exact render + model finds held-out official ink on PHerc0139 at pixel AUC
   0.88 (seed43 step-060000) / 0.85 (seed42 step-010000). Wrong depth order: 0.53 / 0.56. 40 voxels off the sheet: about
   0.5, with 3-7% of pixels called ink (13% / 21% on the sheet). A second scroll (PHerc1667, pooled input): 0.92 / 0.84.
2. **On 0846A the 9 um model over-fires.** It calls 15-48% of the surface "ink" and still 7-36% 40 voxels off the sheet.
   The maps are blotchy texture with no letter shapes. So "ink share" means nothing on this scroll.
3. **But it fires in the same places, in the same depth order, as the 2 um model.** Pixel correlation (9 um vs 2 um map,
   matched depth order) is 0.13-0.38 (z 2.5-7.2 against random shifts) in the six regions with 15 mm 2 um maps; known text gives 0.30-0.31. Opposite
   depth order: -0.09 to 0.15 (known text -0.05 / -0.06). Off the sheet: <= 0.12 (known text <= 0.03).
   Best region **r105_c25**: 0.38 / 0.36, opposite about 0, off-sheet <= 0.04, and a sharp peak exactly at the mesh when
   the depth window is moved (0.38 at the mesh, <= 0.10 at 10-40 voxels off) - the same shape as known text.
   Next cleanest: r75_c45 (0.24 / 0.30, opposite 0.04 / 0.05, off-sheet about 0).
   Weakest: r50_c70 (0.13 / 0.14, heaviest over-firing) and r50_c40 (0.14 / 0.13, no better than the opposite order).
4. **What that proves and what it does not.** The 2 um blobs are real features of the eligible 9.362 um scan (an
   independent model on the independent scan sees them), not an artifact of the 2.4 um scan or our registration. It does
   not prove ink: both models could share a false-positive texture on a scroll neither has seen. The deciding test is the
   same measurement on blank papyrus of an unseen scroll (not done; section 7).

## 2. Why this check

1. The team ruled (#1739) that First Letters evidence must come entirely from the official 9.362 um volume (mesh + render).
2. Our 0846A candidate spots were found on the 2.4 um scan with the 2 um model.
3. So the question: run the official 9 um model (ink_9um) on the official 9.362 um volume at the same six 15 mm regions.
   Does it light up where the 2 um maps light up, more than a null, and how does that compare with KNOWN text run the same way?

## 3. What was done (method)

1. **Renders.** The six 15 mm tifxyz regions (`p0846a_zoom/<name>`, grown on the eligible scan's own surface prediction) were
   rendered from `PHerc0846A/volumes/20250728152254-9.362um-1.2m-113keV-masked.zarr` with `vc_render_tifxyz --flip-normals`,
   101 slices 1 voxel apart, `--auto-crop` (same crop as the zoom pipeline's 9 um render, e.g. 1601x1601 from (899,299)),
   `--timeout 120 --cache-gb 4`. No affine (the meshes are in this volume's voxels).
2. **Depth windows.** One render per region, three 21-slice windows cut with villa's `--layer-start/--layer-end` (end exclusive):
   surface = slices 40..60 (the model uses the centre 17, 42..58, centred on the mesh); off-sheet nulls = slices 0..20 and
   80..100 (centred 40 voxels = 0.37 mm either side). Same image, same crop, same tiling for every run.
3. **Model.** villa's own flat inference (`python -m vesuvius.ink_detection.inference.infer`, villa source at e3df5c6; the inference, model and normalisation code is identical to origin/main be09a85 of 11 Sep),
   checkpoints `hybrid_3d2d-seed43/step-060000` and `hybrid_3d2d-seed42/step-010000` (0 missing / 0 unexpected keys),
   `--direction both --overlap 0.5 --blend-mode hann --batch-size 8 --no-compile`, CPU fp32 on box B and box A. The same run on
   both machines gave byte-identical maps.
4. **Known-text control, same pipeline.** `pherc0139-w016` from the public ink_9um dataset = public segment
   `20250108000004-w029_2025010827`. Its held-out validation region (0.16 cm2, 23% ink) was never in ink_9um's training loss
   (it does not overlap the supervision mask). PHerc0139 has an official 9.362 um volume from the same scan session and
   settings as 0846A's (113 keV, 1.2 m), and this segment has an official 9.362 um mesh. I rendered that mesh with exactly the
   flags above (explicit crop 2884x1309 instead of auto-crop) and ran exactly the same inference. The official labels (drawn
   on the pooled 2.4 um grid) were carried onto my render by image registration of the surface slice: scale 1.028, shift
   (73, 61) px, match score 0.73 vs 0.09 for the next-best position, leftover error <= 1 px in 6 sub-windows.
5. **Second control (different scroll, not our pipeline).** `pherc1667-w029` held-out region (0.35 cm2, 23% ink). PHerc1667 has
   no 9.362 um scan, so only the dataset's own pooled input could be used (2.4 um level 2, 84 centred planes averaged 4 at a
   time into 21, the `prepare_9um_isotropic_input` rule, rebuilt for the crop). Same for a pooled copy of the w016 region.
6. **2 um maps.** The zoom pipeline's maps (`kag_out/z0846a_b*/<name>/{C,D}/canon_pred_asinput.png`, C = rendered order,
   D = reversed; D is the official depth order). Resampled onto the 9 um grid by geometry: a 2 um pixel xs and a 9 um pixel
   x9 of the same mesh point satisfy xs = (x9 + crop9) * 3.89596 - crop2 (crops from both render logs), box-averaged over
   ~4x4 2 um pixels. The same crop rule, sharp crop = floor((9 um crop + 1) * 3.89596), reproduces all six sharp-render crops
   exactly. No flip was needed: in every region the unflipped mapping beat every flipped/rotated one, and a search over
   shifts up to 24 px found the best match within 25 px (0.24 mm) of the geometric mapping, gaining at most 0.02 in r.
7. **Measures.** Ink share = share of valid surface pixels with p > 0.5. AUC = pixel AUC against the official labels inside
   the held-out region. Co-location = pixel correlation r between the 9 um map and the 2 um map on the 9 um grid, tested
   against 200 random shifts of the 2 um map (z) and against the off-sheet windows. "Matched" = the 9 um run in the same
   physical depth order as the 2 um map's stronger direction (the side these spots were picked on; 9 um forward = 2 um D).
   Checkpoint agreement = r between the two checkpoints' maps.

## 4. Results (every number below is printed by n9_tables.py from the result files)

### Table 1. Known text (controls)

| control | input | checkpoint | AUC held-out, forward | AUC held-out, reverse | ink share held-out fwd / rev | ink share whole crop fwd / rev | ink share 40 vx off (mean of 4) |
|---|---|---|---|---|---|---|---|
| PHerc0139 w016 held-out (0.16 cm2, 23% ink) | OUR pipeline: 9.362 um render, --flip-normals | s43-60k | **0.88** | 0.53 | 19% / 7% | 13% / 6% | 4% (AUC 0.46-0.55) |
| PHerc0139 w016 held-out (0.16 cm2, 23% ink) | OUR pipeline: 9.362 um render, --flip-normals | s42-10k | **0.85** | 0.56 | 36% / 23% | 21% / 13% | 6% (AUC 0.44-0.61) |
| same held-out region | dataset input (pooled 2.4 um) | s43-60k | 0.91 | 0.52 | 22% / 3% | 11% / 2% | not run |
| same held-out region | dataset input (pooled 2.4 um) | s42-10k | 0.89 | 0.53 | 27% / 6% | 15% / 5% | not run |
| PHerc1667 w029 held-out (0.35 cm2, 23% ink) | dataset input (pooled 2.4 um; no 9.362 um scan exists) | s43-60k | 0.92 | 0.63 | 24% / 6% | 21% / 7% | not run |
| PHerc1667 w029 held-out (0.35 cm2, 23% ink) | dataset input (pooled 2.4 um; no 9.362 um scan exists) | s42-10k | 0.84 | 0.62 | 24% / 11% | 28% / 14% | not run |

Published 2 um prediction on the same w016 held-out labels: AUC 0.83.

### Table 2. Does the 9 um map sit where the 2 um map is? (pixel r on the 9 um grid)

'Matched' = the 9 um run in the same physical depth order as the 2 um map's stronger direction (the side these spots were picked on). z = against 200 random shifts of the 2 um map.

| place | checkpoint | 2 um stronger dir (share) | r matched (z) | r 9 um opposite order | r 9 um 40 vx off (max of 4) | ckpt agreement r (matched dir) |
|---|---|---|---|---|---|---|
| KNOWN TEXT PHerc0139 w016 crop (vs published 2 um prediction) | s43-60k | official order | 0.31 (z 6.8) | -0.05 | 0.03 | 0.56 |
| KNOWN TEXT PHerc0139 w016 crop (vs published 2 um prediction) | s42-10k | official order | 0.30 (z 6.8) | -0.06 | 0.02 | 0.56 |
| 0846A r35_c65 | s43-60k | D (13% vs 4%) | 0.25 (z 3.3) | 0.12 | 0.07 | 0.47 |
| 0846A r35_c65 | s42-10k | D (13% vs 4%) | 0.30 (z 4.8) | 0.12 | 0.07 | 0.47 |
| 0846A r30_c105 | s43-60k | C (24% vs 6%) | 0.28 (z 4.4) | 0.08 | 0.08 | 0.39 |
| 0846A r30_c105 | s42-10k | C (24% vs 6%) | 0.36 (z 6.1) | 0.12 | 0.12 | 0.39 |
| 0846A r105_c25 | s43-60k | C (24% vs 11%) | 0.38 (z 6.0) | -0.01 | 0.04 | 0.51 |
| 0846A r105_c25 | s42-10k | C (24% vs 11%) | 0.36 (z 4.6) | -0.02 | 0.01 | 0.51 |
| 0846A r50_c70 | s43-60k | C (22% vs 16%) | 0.13 (z 2.5) | -0.09 | 0.05 | 0.33 |
| 0846A r50_c70 | s42-10k | C (22% vs 16%) | 0.14 (z 3.3) | -0.05 | 0.09 | 0.33 |
| 0846A r75_c45 | s43-60k | D (23% vs 2%) | 0.24 (z 5.0) | 0.04 | 0.01 | 0.38 |
| 0846A r75_c45 | s42-10k | D (23% vs 2%) | 0.30 (z 7.2) | 0.05 | -0.02 | 0.38 |
| 0846A r50_c40 | s43-60k | C (5% vs 3%) | 0.14 (z 2.7) | 0.09 | 0.05 | 0.41 |
| 0846A r50_c40 | s42-10k | C (5% vs 3%) | 0.13 (z 2.9) | 0.15 | 0.11 | 0.41 |

### Table 3. Ink share (p > 0.5) per run, 0846A regions (15 mm, 9.362 um)

| region | checkpoint | surface fwd | surface rev | 40 vx off side A fwd / rev | 40 vx off side B fwd / rev |
|---|---|---|---|---|---|
| r35_c65 | s43-60k | 28% | 24% | 24% / 20% | 21% / 19% |
| r35_c65 | s42-10k | 22% | 22% | 17% / 13% | 15% / 15% |
| r30_c105 | s43-60k | 28% | 35% | 22% / 23% | 25% / 27% |
| r30_c105 | s42-10k | 26% | 37% | 19% / 24% | 23% / 24% |
| r105_c25 | s43-60k | 15% | 30% | 7% / 12% | 11% / 17% |
| r105_c25 | s42-10k | 18% | 38% | 13% / 19% | 14% / 18% |
| r50_c70 | s43-60k | 47% | 48% | 36% / 34% | 35% / 34% |
| r50_c70 | s42-10k | 29% | 34% | 26% / 29% | 26% / 33% |
| r75_c45 | s43-60k | 42% | 31% | 24% / 22% | 23% / 19% |
| r75_c45 | s42-10k | 31% | 21% | 19% / 16% | 18% / 16% |
| r50_c40 | s43-60k | 26% | 30% | 18% / 22% | 20% / 23% |
| r50_c40 | s42-10k | 21% | 21% | 16% / 16% | 16% / 13% |
| KNOWN TEXT w016 crop | s43-60k | 13% | 6% | 5% / 4% | 4% / 3% |
| KNOWN TEXT w016 crop | s42-10k | 21% | 13% | 7% / 6% | 7% / 7% |

### Table 4. Cross-check with the earlier 7.5 mm 2 um windows (centre quarter of each region)

| region | 2 um window stronger dir (share) | 2 um depth window | checkpoint | r matched (z) | r opposite order | r off-sheet (max of 4) |
|---|---|---|---|---|---|---|
| r35_c65 | D (35% vs 4%) | layers 15-77 | s43-60k | 0.15 (z 1.8) | 0.13 | 0.08 |
| r35_c65 | D (35% vs 4%) | layers 15-77 | s42-10k | 0.42 (z 3.9) | 0.17 | 0.07 |
| r30_c105 | C (33% vs 7%) | layers 32-94 | s43-60k | 0.28 (z 4.1) | 0.18 | 0.08 |
| r30_c105 | C (33% vs 7%) | layers 32-94 | s42-10k | 0.36 (z 4.6) | 0.08 | 0.18 |
| r105_c25 | C (29% vs 10%) | layers 13-75 | s43-60k | 0.46 (z 6.2) | 0.07 | 0.13 |
| r105_c25 | C (29% vs 10%) | layers 13-75 | s42-10k | 0.37 (z 5.4) | 0.01 | 0.14 |
| r50_c70 | C (28% vs 9%) | layers 16-78 | s43-60k | 0.23 (z 3.4) | -0.23 | 0.23 |
| r50_c70 | C (28% vs 9%) | layers 16-78 | s42-10k | 0.31 (z 3.4) | -0.06 | 0.30 |
| r75_c45 | D (21% vs 3%) | layers 35-97 | s43-60k | 0.19 (z 3.1) | -0.03 | 0.10 |
| r75_c45 | D (21% vs 3%) | layers 35-97 | s42-10k | 0.22 (z 3.4) | -0.05 | 0.18 |
| r50_c40 | C (11% vs 2%) | layers 16-78 | s43-60k | 0.27 (z 2.9) | 0.19 | 0.23 |
| r50_c40 | C (11% vs 2%) | layers 16-78 | s42-10k | 0.20 (z 3.1) | 0.26 | 0.25 |

### Table 5. Scale split of the co-location (uncalibrated diagnostic; 15 mm maps)

fine = blobs about 0.06-0.56 mm (the scale of strokes and letter parts); coarse = structure larger than about 0.56 mm.

| place | checkpoint | fine: matched / opposite / off-sheet | coarse: matched / opposite / off-sheet |
|---|---|---|---|
| KNOWN TEXT w016 | s43-60k | 0.26 / -0.03 / 0.01 | 0.53 / -0.12 / 0.10 |
| KNOWN TEXT w016 | s42-10k | 0.27 / -0.03 / 0.02 | 0.47 / -0.12 / 0.00 |
| r35_c65 | s43-60k | 0.19 / 0.06 / -0.02 | 0.50 / 0.35 / 0.26 |
| r35_c65 | s42-10k | 0.23 / 0.03 / -0.07 | 0.63 / 0.49 / 0.41 |
| r30_c105 | s43-60k | 0.23 / 0.09 / 0.02 | 0.51 / 0.12 / 0.10 |
| r30_c105 | s42-10k | 0.26 / 0.10 / 0.05 | 0.73 / 0.26 / 0.32 |
| r105_c25 | s43-60k | 0.33 / 0.10 / 0.02 | 0.66 / -0.10 / 0.14 |
| r105_c25 | s42-10k | 0.29 / 0.04 / -0.03 | 0.64 / -0.08 / 0.06 |
| r50_c70 | s43-60k | 0.07 / 0.01 / -0.03 | 0.28 / -0.41 / 0.20 |
| r50_c70 | s42-10k | 0.11 / 0.04 / -0.03 | 0.18 / -0.31 / -0.01 |
| r75_c45 | s43-60k | 0.21 / 0.07 / 0.07 | 0.43 / -0.08 / -0.22 |
| r75_c45 | s42-10k | 0.26 / 0.07 / -0.02 | 0.54 / 0.08 / -0.25 |
| r50_c40 | s43-60k | 0.09 / -0.00 / 0.05 | 0.41 / 0.43 / 0.21 |
| r50_c40 | s42-10k | 0.05 / 0.06 / 0.06 | 0.46 / 0.53 / 0.41 |

### Table 6. Depth tuning (seed43 step-060000): response as the 21-slice window moves off the mesh

Offsets in voxels (9.362 um) from the mesh; ink share, and in brackets AUC (known text) or r with the 2 um map (0846A).

| place | order | -40 | -20 | -10 | 0 | 10 | 20 | 40 |
|---|---|---|---|---|---|---|---|---|
| KNOWN TEXT w016 | fwd | 5% (0.54) | 6% (0.56) | 9% (0.57) | 13% (0.88) | 6% (0.54) | 5% (0.42) | 4% (0.46) |
| KNOWN TEXT w016 | rev | 4% (0.55) | 4% (0.53) | 5% (0.46) | 6% (0.53) | 4% (0.47) | 5% (0.46) | 3% (0.53) |
| r35_c65 | fwd | 24% (0.03) | 21% (0.12) | 24% (0.14) | 28% (0.25) | 26% (0.15) | 25% (0.03) | 21% (0.02) |
| r35_c65 | rev | 20% (-0.00) | 20% (0.05) | 22% (0.15) | 24% (0.12) | 20% (0.11) | 20% (0.06) | 19% (0.07) |
| r30_c105 | fwd | 22% (-0.07) | 28% (0.11) | 23% (0.12) | 28% (0.08) | 28% (0.09) | 31% (0.07) | 25% (0.08) |
| r30_c105 | rev | 23% (0.04) | 33% (0.04) | 30% (0.18) | 35% (0.28) | 31% (0.19) | 31% (0.15) | 27% (0.06) |
| r105_c25 | fwd | 7% (-0.03) | 12% (0.04) | 11% (0.00) | 15% (-0.01) | 10% (0.06) | 12% (-0.01) | 11% (-0.03) |
| r105_c25 | rev | 12% (0.04) | 13% (0.08) | 16% (0.05) | 30% (0.38) | 14% (0.08) | 17% (0.10) | 17% (-0.00) |
| r50_c70 | fwd | 36% (0.05) |  |  | 47% (-0.09) |  |  | 35% (0.03) |
| r50_c70 | rev | 34% (0.01) |  |  | 48% (0.13) |  |  | 34% (0.05) |
| r75_c45 | fwd | 24% (0.01) |  |  | 42% (0.24) |  |  | 23% (-0.12) |
| r75_c45 | rev | 22% (-0.00) |  |  | 31% (0.04) |  |  | 19% (-0.06) |
| r50_c40 | fwd | 18% (0.05) |  |  | 26% (0.09) |  |  | 20% (0.03) |
| r50_c40 | rev | 22% (0.05) |  |  | 30% (0.14) |  |  | 23% (0.03) |

## 5. What it means

1. **The 9 um path works on known text** (Table 1). Our exact render + model finds held-out official ink at AUC 0.88
   (seed43) and 0.85 (seed42), only in the official depth order (reverse 0.53 / 0.56) and only on the mesh (40 voxels off:
   0.44-0.61; Table 6: already gone 10 voxels off). So the 9 um model on the eligible volume *can* show real ink, and a
   clean "no" from it would mean something.
2. **At our spots the 9 um model lights up where the 2 um model lights up** (Tables 2, 4, 5, 6): in the matched depth
   order, about as strongly as on known text, much less in the opposite order, and near zero off the sheet. So the 2 um
   blobs are not a quirk of the 2.4 um scan or of our 2.4-to-9 um registration: an independent model on the independent,
   eligible scan responds at the same places, in the same depth order, and only on this sheet.
3. **But it is not a reading, and on this scroll the 9 um model over-fires** (Table 3): 15-48% of the surface called
   "ink" and still 7-36% at 40 voxels off the sheet, against 13% / 21% and 3-7% on known text. The maps are blotchy texture
   with no letter shapes in any region (picture). Ink share is useless as an ink measure on 0846A.
4. **Why "can't tell" and not "ink-like".** The nulls used here (off-sheet, random shift, opposite depth order, depth
   sweep) rule out chance and misregistration. They cannot rule out a surface texture that BOTH models mistake for ink:
   both were trained on labels from the same four scrolls, and 0846A is new to both. A sharp depth peak does not settle it
   either, because the model only responds to what sits centred in its window, ink or not. Only a blank-papyrus control on
   an unseen scroll can separate the two, and none exists yet (L51: this co-location test is uncalibrated). The two models
   also agree on which depth order is stronger in 9 of 9 checkpoint-region cases that are not ties (3 near-ties within 1 point). That shows which way each mesh faces and
   would happen with or without ink.
5. **Region by region** (Table 2, 15 mm maps for all six). r105_c25 has the cleanest pattern (matched 0.38 / 0.36,
   opposite about 0, off-sheet <= 0.04, sharp depth peak, fine-scale 0.33 / 0.29), the same shape as known text.
   r75_c45 is next (0.24 / 0.30, opposite 0.04 / 0.05, off-sheet about 0). r30_c105 and r35_c65 are co-located but less
   specific (opposite order 0.08-0.12, depth peak with shoulders). r50_c70 is weak (0.13 / 0.14) with the heaviest
   over-firing (48% on the surface, 35% off it). r50_c40 is weak and not direction-specific (0.14 / 0.13 matched vs
   0.09 / 0.15 opposite).
6. **For the #1739 evidence path:** nothing here is evidence of letters. It supports keeping r105_c25 and r75_c45 (then
   r30_c105, r35_c65) as the places to look harder at 9 um, and it gives each mesh's depth order for future evidence renders:
   forward (as rendered with --flip-normals) for r35_c65 and r75_c45; reverse for r30_c105, r105_c25, r50_c70, r50_c40.

## 6. What failed or is weak

1. **Night-plan premise corrected.** PHerc1667 w028 (and w029) ARE in ink_9um's training list (shipped config). Only the
   three held-out validation regions are clean controls (w016, 46527, w029).
2. **PHerc1667 has no 9.362 um scan** (only 2.399 and 1.129 um), so the 1667 control could not go through our render
   pipeline; it used the dataset's pooled input and is marked as such.
3. **Controls sit on training scrolls.** The held-out regions were never in the loss, but the model knows 0139 and 1667
   papyrus. 0846A is new to it, so the controls overstate what to expect here.
4. **Different 2 um models.** Known-text co-location used the published 2 um prediction (new_canon_autoresearch_recipe);
   the 0846A maps are our runs of scrollprize/ink_canonical_2um. Close relatives, not identical.
5. **The "off-sheet" windows are other wraps, not air.** The grey level is flat through all 101 slices (tightly packed
   sheets), so the null is "a different sheet at a random depth", which is still the right comparison for "is the response
   tied to THIS sheet".
6. **The 7.5 mm cross-check disagrees in places** (Table 4): it used older 2 um runs with their own depth windows on the
   centre quarter only; r75_c45 looks weaker and r50_c70 / r50_c40 look less specific there. The 15 mm maps (Table 2) are
   the primary comparison.
7. **My own mistakes (caught, fixed, lessons L53-L54):** a Mac bash 3.2 loop rendered the wrong mesh into one region's
   file (caught by a byte-count check, redone); a shift-null loop that could not terminate on small windows (fixed, re-run).
8. CPU fp32 instead of the GPU fp16 the checkpoints were trained with: tiny numeric differences, not enough to matter.

## 7. Next steps (short)

1. **Blank calibration (decides the verdict):** run both models on known-blank papyrus of a scroll neither model trained on
   (or on 0846A windows the 2 um survey found empty) and measure the same matched / opposite / off-sheet co-location. If it
   is near zero there, the 0846A co-location becomes meaningful.
2. **Look harder at r105_c25:** the co-located blobs at 9 um across more checkpoints and small depth offsets, zoomed, by eye.

## 8. Files

- This report and the pictures: `evidence_0912/NINE_UM_CHECK.md`, `evidence_0912/nine_um_check.png`, `evidence_0912/nine_um_r105_zoom.png`.
- Numbers (JSON) and scripts: `evidence_0912/nine_um_files/` (copies of box B `<work-dir>/n9/results/*.json` and the
  `n9_*.py`, `run_infer*.sh`, `render_*.sh` scripts).
- box B `<work-dir>/n9/`: `preds/` (every probability map, uint8 TIFF), `results/` (JSON, figure, surface slices),
  `ctl/` (control render, pooled crops, labels), the 101-slice renders of r105_c25 and r75_c45 (`data/`; the other four were
  deleted to free box B disk and can be re-rendered in ~2 min each with `render_one.sh` on box A), villa source copy `src/`,
  extra Python packages `pydeps/` (kept out of the shared venv), checkpoints `ckpts/`, logs. box A `<run-dir>/n9/`:
  scripts, logs and small copies of the maps only (all renders deleted after copying; footprint about 0.1 GB).

## 9. Running log (appended as results landed; AEST)





Entries up to 01:56 carry the window between two `date` readings (01:07, 01:28, 01:56) because I did not read the clock for each one; from 02:12 on, each time is a `date` reading taken when the line was written.

- 01:07-01:27 villa inference code read: ink_9um = 3D stem + 2D U-Net, patch 17x128x128, robust normalisation, centre-crops 17 of the given slices. 34.5M params. Checkpoints load with 0 missing / 0 unexpected keys.
- 01:07-01:27 CORRECTION to the night plan: PHerc1667 w028 IS in ink_9um training (shipped config lists pherc1667-w028 and -w029). Only the three validation-mask regions were held out: pherc0139-w016, pherc0814-46527, pherc1667-w029 (dataset README).
- 01:07-01:27 PHerc1667 has no 9.362 um volume (only 2.399 and 1.129 um). PHerc0139 does (20250728140407, same 113 keV / 1.2 m settings as the 0846A scan 20250728152254). pherc0139-w016 = public segment 20250108000004-w029_2025010827, which has an official 9.362 um mesh. So the positive control can go through the exact same render + inference pipeline.
- 01:07-01:27 Region render (hand test, r35_c65): 1601x1601 crop from (899,299) = same crop as the zoom pipeline's coarse render; 101 slices at 1 voxel, --flip-normals; 99 s, 232 MB.
- 01:07-01:27 Inference hand test on box B CPU: 123 s per checkpoint for both directions; layers 42..58 (centred on the surface slice 50). r35_c65 seed43 step-060000: ink>0.5 = 27.9% forward, 24.2% reverse. Looks blotchy.
- Depth profile of r35_c65 (mean grey per slice) is flat (103..114): tightly packed sheets, so "40 voxels off" lands on other wraps, not air.
- 01:28-01:40 SELF-CAUGHT: my first batch loop (Mac bash 3.2, associative array) rendered the wrong mesh into region r30_c105's file; byte-count check caught it. Wrong files deleted on box A and box B, loop fixed (case lookup + segment-name check + lock), re-run. r35_c65 (hand test, rendered before the loop) is unaffected (its log names the right mesh). Lesson L53.
- 01:40-01:52 Control labels (pherc0139-w016, ink_9um dataset): labels are 0/1 at Z=10 of a 21x7020x7220 grid (9.596 um). Held-out validation region = 178,146 px (0.16 cm2, two patches at the two ends of the labelled strip), 23.2% of it is ink. It does not overlap the supervision (training) mask (overlap 0 px). Targeted chunk download cross-checked against a full download: identical.
- 01:40-01:52 Control render: official 9.362 um mesh of public segment 20250108000004-w029 on the PHerc0139 9.362 um volume, SAME flags as our regions (101 slices, step 1, --flip-normals, scale 1), crop 2884x1309 from (1510,4659); 182 s, 363 MB.
- 01:40-01:52 Label grid -> my render: registered surface slice (render slice 50) against the pooled 2.4 um input (slice 10): scale 1.028, shift (73,61) px, NCC 0.73 (next best peak 0.09); residual shift in 6 sub-windows <= 1 px. Labels can be carried onto the 9.362 um render to ~1 px (9 um).
- 01:40-01:52 Also rebuilt the dataset's own "aligned" input for the same crop (level 2, planes 13..96, rounded mean of 4 -> 21 slices; same rule as prepare_9um_isotropic_input) to run the same model on the training-style representation.
- before 01:56 CONTROL PASSES (gate). Held-out w016 validation region, our exact 9.362 um render + inference: pixel AUC vs official labels 0.877 (seed43 step-060000, forward) and 0.849 (seed42 step-010000, forward). Ink share (p>0.5): 18.9% of the validation region (labels say 23.2% is ink); 57% of labelled-ink pixels vs 7.4% of labelled-background pixels (seed43). Whole crop 12.9%. For reference the published 2 um canon prediction scores AUC 0.826 on the same held-out labels.
- before 01:56 Reproducible: the same control run on box B and on box A gives byte-identical maps (max difference 0).
- before 01:56 Co-location on KNOWN text: 9 um map vs the published 2 um prediction, pixel r = 0.31 over the control crop (0.43 inside the held-out region), shift-null mean -0.01 +- 0.05 (z 6.8).
- before 01:56 First 0846A region r35_c65: ink share 28.0% / 24.3% (seed43 fwd/rev) on the surface vs 20-24% at 40 voxels off (both sides); seed42 22% vs 13-17%. Checkpoint agreement r 0.47 on the surface vs 0.28-0.33 off-sheet. 9 um (forward) vs 2 um map (D = same physical depth order): r 0.25 (seed43) / 0.30 (seed42), shift null -0.02 +- 0.08 (z 3.3 / 4.8). Off-sheet 9 um maps vs 2 um: r -0.01..0.09. Orientation check: no flip needed (identity best, 0.25 vs next 0.15); best local shift (4,0) px changes r by 0.001.
- 02:12 (date) CONTROL COMPLETE (w016 held-out, our pipeline). Reverse depth order is blind: AUC 0.53 (s43) / 0.56 (s42). Off-sheet windows (40 voxels either side): AUC 0.44-0.61 (chance) and ink share 3-7% of the crop vs 13% (s43) / 21% (s42) on the surface. Dataset-style pooled 2.4 um input of the same region: AUC 0.91 (s43) / 0.89 (s42) forward, 0.52 / 0.53 reverse. So on known text: forward >> reverse, surface >> off-sheet.
- 02:12 Second 0846A region r30_c105: here the 2 um map's strong order is C (24% vs 6%), and the 9 um model's stronger order is the SAME physical order (reverse on the flipped render): 36% vs 28% (s43), 37% vs 26% (s42). Matched co-location r 0.28 (s43, z 4.4) / 0.36 (s42, z 6.1); opposite 9 um order 0.08 / 0.12; off-sheet <= 0.12. r35_c65: matched r 0.25 / 0.30, opposite 0.12 / 0.12, off-sheet <= 0.07.
- KEY CONTRAST: on 0846A the 9 um model calls 19-27% of pixels "ink" even 40 voxels OFF the sheet (s43); on known text it calls 3-5% off-sheet. So ink share is not a usable ink measure on 0846A; co-location and direction are.
- 02:21 (date) SECOND CONTROL: PHerc1667 w029 held-out region (0.35 cm2, 23% ink), dataset-style pooled 2.4 um input (PHerc1667 has no 9.362 um scan, so our render pipeline cannot be used on it). AUC forward 0.92 (s43) / 0.84 (s42); reverse 0.63 / 0.62. Ink share: 77% of labelled ink vs 8% of background (s43).
- 02:21 Scale split (uncalibrated): at the scale of writing (blobs 0.06-0.56 mm) the matched 9 um / 2 um co-location is 0.19-0.26 on 0846A (r35_c65, r30_c105) vs 0.26-0.27 on known text; opposite depth order 0.03-0.10 (known text -0.03); off-sheet -0.07..0.05 (known text 0.01-0.02). At large scale (> 0.56 mm) 0846A also co-locates OFF-sheet (0.10-0.41), known text does not (0.00-0.10).
- 02:21 r105_c25 (no 15 mm 2 um map yet): 9 um reverse 30% vs forward 15% (s43), 38% vs 18% (s42); off-sheet 7-17%; checkpoint agreement 0.51 (rev) vs 0.26 (fwd). Its 7.5 mm 2 um map was also stronger in C (29% vs 10%) = same physical order as 9 um reverse.
- NOTE: in all three regions so far the 9 um model's stronger depth order is the same physical order as the 2 um model's. This says which way each mesh faces; it is expected from sheet geometry whether or not there is ink.
- 02:37 (date) r75_c45 (no 15 mm 2 um map yet): 9 um forward 42% vs reverse 31% (s43), 31% vs 21% (s42); off-sheet 19-24% (s43). Its 7.5 mm 2 um map was stronger in D (21% vs 3%) = same physical order as 9 um forward. Direction agreement between the two models: 4 of 4 regions so far.
- 02:52 (date) 15 mm 2 um maps for r105_c25 and r50_c70 arrived (z0846a_b1). r105_c25: 2 um C 25% vs D 12%; matched 9 um (reverse) r 0.38 (s43, z 6.0) / 0.36 (s42, z 4.7); opposite order -0.01 / -0.02; off-sheet <= 0.04. Cleanest region: same pattern as known text. r50_c70: 2 um C 22% vs D 16%; matched r 0.14 / 0.14 (z 2.5 / 3.3); the 9 um model calls 48% of the surface "ink" in BOTH orders and 35% off-sheet (s43): over-firing, weak co-location.
- 02:52 r50_c40 (7.5 mm 2 um map only so far): 2 um C 11% vs D 2%; 9 um reverse 30% vs forward 26% (s43), 21% vs 21% (s42); off-sheet 18-23%. Direction agreement 5 of 5 decided cases (2 ties at s42).
- 02:52 Alignment check (+-24 px): best shift within 20 px (0.19 mm) of the geometric mapping in all 4 regions, gain <= 0.016 in r; r at 24 px shift is still 0.11-0.30, i.e. the shared structure is broad (blob scale), not fine.
- 02:52 r75_c45's zoom sharp crop (1947, 4285) matches the crop rule floor((crop9 + 1) * 3.89596) exactly (5 of 5 regions).
- 02:56 (date) Cross-check with the earlier 7.5 mm 2 um windows (centre quarter of each region, their own depth windows): matched r 0.15-0.46 (z 1.8-6.2). Clean pattern again in r105_c25 (0.46 / 0.37, opposite 0.07 / 0.01). NOT specific in r50_c40 (matched 0.27 / 0.20, opposite 0.19 / 0.26, off-sheet 0.23 / 0.25) and r50_c70 (off-sheet 0.23-0.30 as high as matched). r75_c45: matched 0.19 / 0.22, opposite -0.03 / -0.05, off-sheet 0.10 / 0.18.
- 02:56 SELF-CAUGHT BUG: my shift-null loop accepted a shift only if the overlap was >= 30% of the whole image; for a 7.5 mm window (25% of the image) that never happens, so the first cross-check hung for 17 min. Fixed (overlap >= 30% of the valid area) and the window is now shifted inside its own box. 15 mm results unaffected (valid area ~93% of the image); re-run anyway for consistency.
- 03:09 (date) Box A disk touched 8.0 GB free (the zoom pipeline's guard) while I copied one extra render there for depth runs; I cancelled that and deleted 430 MB of my renders within a minute (8.4 GB free after). My box A footprint stayed under 1.5 GB (peak ~1.1 GB).
- 03:09 Scale split for r105_c25: fine matched 0.33 / 0.29 (known text 0.26 / 0.27), opposite 0.10 / 0.04, off-sheet 0.02 / -0.03. r50_c70: fine matched only 0.07 / 0.11.
- 03:12 (date) Depth tuning (seed43): on known text the response is confined to the window centred on the mesh (forward AUC 0.54-0.57 at -10/-20/-40, 0.88 at 0, 0.42-0.54 at +10/+20/+40; co-location 0.31 at 0, <= 0.04 elsewhere). r105_c25 (matched order) has the same sharp peak: co-location 0.38 at 0 vs <= 0.10 at every other offset, ink share 30% at 0 vs 12-17%. r30_c105 (matched) peaks at 0 (0.28) with a broader shoulder (0.18-0.19 at +-10). Opposite orders are flat. A sharp peak is what the model does with anything it only sees centred, so it is consistent with ink but not proof.
- 03:35 (date) Depth tuning complete. r35_c65 (matched, forward): co-location 0.25 at the mesh, 0.14-0.15 at +-10, 0.12 at -20, <= 0.03 at +20/+-40 (peak with shoulders, like r30_c105). Known text and r105_c25: sharp peak, nothing at +-10.
- 03:50 (date) Zoom batch b2 landed (03:43): 15 mm 2 um maps for r75_c45 and r50_c40. r75_c45 (2 um D 23% vs C 2%): matched 9 um forward r 0.24 (z 5.0) / 0.30 (z 7.2), opposite 0.04 / 0.05, off-sheet <= 0.01 -> clean and specific (its 7.5 mm window had undersold it). r50_c40 (C 5% vs D 3%): matched 0.14 / 0.13 (z 2.7 / 2.9), opposite 0.09 / 0.15, off-sheet <= 0.11 -> weak, not direction-specific. Orientation: unflipped best in both. Alignment: r75_c45 best shift (4,4) gains 0.0005; r50_c40 best (-8,-24) gains 0.019 (weak map, flat optimum).

## 10. Within-scroll null (12 Sep)

Written by agent E (follow-up; started 03:55, finished 06:17 AEST, both from `date`). Private: nothing posted or pushed;
box A and box B CPUs only. Figure: `evidence_0912/nine_um_null.png`. Tables and number blocks are printed by
`nine_um_files/null/n9null_summary.py` (and `n9null_counts.py`) from the result files and copied here unedited
(`null/results/summary_final.txt`, `counts.txt`).

### 10.1 Short answer

**Verdict: THE OVERLAP IS MOSTLY COMMON TO ORDINARY 0846A PAPYRUS. r75_c45 does not stand out. r105_c25 is borderline:
it beats every ordinary window on one checkpoint (seed43) but not on the other (seed42), so by the rule fixed in advance
it is not a robust outlier.**

1. **The test.** The previous run's exact render + ink_9um + overlap pipeline, run on 25 PHerc0846A survey windows that
   were never picked as strong spots (the null), and re-run on the six candidate windows the same way. Two tilings, each
   applied to everything: each window rendered alone, and each window inside a 15 mm render (the previous run's own
   Table 4 rule; its numbers reproduced exactly).
2. **Ordinary windows overlap too.** Never-picked windows reach matched r 0.26-0.28 (seed43) and 0.54-0.56 (seed42).
   Under the previous run's own tiling, 14 of the 25 reach z >= 2.5 against random shifts on seed42 (6 on seed43), and
   5 reach z >= 4. So "z 2.5-7.2" is not special on this scroll.
3. **The overlap follows how much the 2 um model fires.** Among ordinary windows, overlap rises with 2 um ink share
   (Spearman 0.59-0.75). The candidates were picked for high 2 um share, and that explains most of their edge: as a group
   they sit above the null (Mann-Whitney p 0.001-0.02), but at the same share they sit on the null's trend line
   (exceptions, all on seed43: r105_c25 under both tilings, r50_c40 under the 15 mm rule).
4. **r75_c45 is ordinary.** 0.08 / 0.14 (window alone) and 0.19 / 0.22 (15 mm rule): 11-21 of 25 ordinary windows are below it.
5. **r105_c25 is the only spot that stays at the top, and only on seed43.** seed43: 0.38 and 0.46, above all 25 ordinary
   windows under both tilings, 2-3 null SDs above what the null predicts at its share. seed42: 0.33 and 0.37, which is
   about the null's 95th percentile (0.32 and 0.38; it passes under one tiling and misses by 0.01 under the other), and
   ordinary for its share (+0.4 SD). One never-picked window (063746464_r25_c45, same grown surface as r75_c45, 2 um share
   23-24%) is clearly higher on seed42: 0.54 / 0.56.
6. **Known blank papyrus gives no overlap.** On blank papyrus of the known-text control scroll (PHerc0139 w016 held-out
   region) the two models do not co-locate: r -0.03 / -0.08 at 10 px or more from labelled ink. Its text gives 0.14-0.48
   (mostly above 0.3) in windows of the same size. So on a known scroll the overlap needs ink; on 0846A it appears
   wherever the 2 um model fires. That fits a texture both models share on 0846A, or faint ink almost everywhere; this test cannot tell those
   apart. Either way the overlap cannot pick out letter spots.
7. **Side finding: the overlap number moves by up to about 0.1 with tiling alone.** The model normalises each tile's
   brightness including any black frame, so a window rendered alone gives a different map from the same window inside a
   larger render (the two maps correlate only 0.71-0.85). r75_c45: 0.08 alone, 0.19 inside 15 mm. Any future 9 um
   evidence must fix and state its tiling.

**What it means for the #1739 evidence path.** The 9 um / 2 um overlap is not evidence of letters on 0846A: ordinary
papyrus shows it too. r75_c45 drops out. r105_c25 is the one place where one checkpoint beats every ordinary window
under both tilings. That is worth a closer look by eye at 9 um, but only a letter-shape test could make it evidence;
more overlap numbers cannot.

### 10.2 What was done

1. **Windows.** All 42 PHerc0846A 7.5 mm survey windows that have 2 um maps. The 17 windows ever named as a pick in
   our working log (zoom regions, one-sided list, two-sided strongest, top-8 re-run, "new strong") were kept out of the
   null before any result. That leaves 25 ordinary windows: 15 from survey pass 2 (2 um maps with the corrected depth
   window) and 10 from pass 1 (2 um maps at the default depth window 24-86). Their 2 um ink share runs from 0% to 37%:
   20 of them are 0-10%; 5 are 22-37%, as high as the candidates. The 11 picked-but-not-zoomed windows were not run
   (dropped to make room for the second tiling).
2. **Same pipeline as the previous run.** Same volume, `render_one.sh` and flags (101 slices, `--flip-normals`,
   `--auto-crop`; each crop checked equal to the survey's own 9 um render), same checkpoints (seed43 step-060000, seed42
   step-010000) and inference flags, same depth windows (surface [40,61); off-sheet [0,21) and [80,101)), same matched /
   opposite / off-sheet logic, and the previous run's own `n9_regions.py` functions (resampling, pearson, random-shift z;
   min shift 100 px as in its 7.5 mm cross-check) imported unchanged.
3. **Two tilings, applied to candidates and null alike.**
   - **Direct:** each 7.5 mm window's own mesh rendered alone (it has a ~20 px black frame). All columns.
   - **Context:** the window read off a 15 mm render around it, built with `zoom_regions.py`'s exact code. This is the
     previous run's Table 4 rule. My mesh for r75_c45 is byte-identical to the previous run's, my render + inference gives
     byte-identical maps (md5 of all four maps), and my code reproduces all 12 of its Table 4 values to 4 decimals.
     Surface depth window only, so no off-sheet column.
4. **Rules fixed before any null number was seen** (running log 04:35). A candidate "stands out" if its matched r is
   above the null's empirical 95th percentile on BOTH checkpoints; the verdict counts as robust only if both tilings
   agree. Survey-1 windows join the null only if default vs corrected 2 um depth changes r by <= 0.05 on average (it
   changed it by -0.001, so they were pooled: n = 25).
5. **Second null.** Known-blank papyrus: label = no ink inside the held-out validation region of the known-text control
   (PHerc0139 w016, the previous run's render and labels), same statistic against the published 2 um prediction.
6. **Guards.** Orientation and a +-24 px alignment search on every window (the previous run's own checks): shifting
   gains at most 0.10 in any window (0.06 for candidates), so no ordinary window is low because of misregistration. r does
   not rise with the depth-correction confidence (NCC; Spearman -0.25 to -0.02). The orientation check picks a flipped
   map only in weak windows (r <= 0.12), as chance does at 1/8 resolution.

### 10.3 Results

#### Table N1. Direct rule: every 7.5 mm window rendered on its own (s43 / s42 in each cell)

2 um ink share = the stronger 2 um direction (other direction in brackets), on the 9 um grid. r = pixel correlation between the 9 um map and the window's own 2 um map. z = against 200 random shifts of the 2 um map.

| group | window | 2 um ink share | r matched | z (matched) | r opposite order | r off-sheet (max of 4) |
|---|---|---|---|---|---|---|
| zoom window (candidate) | 030142380_r35_c65 (= r35_c65) | D 36% (C 4%) | 0.16 / 0.33 | 1.7 / 3.2 | 0.22 / 0.03 | 0.08 / -0.01 |
| zoom window (candidate) | 063530412_r30_c105 (= r30_c105) | C 33% (D 7%) | 0.30 / 0.28 | 4.6 / 3.5 | 0.11 / 0.10 | 0.08 / 0.10 |
| zoom window (candidate) | 025619069_r105_c25 (= r105_c25) | C 29% (D 10%) | 0.38 / 0.33 | 5.2 / 4.2 | 0.10 / -0.01 | 0.07 / 0.07 |
| zoom window (candidate) | 040822053_r50_c70 (= r50_c70) | C 28% (D 9%) | 0.17 / 0.28 | 2.4 / 3.0 | -0.19 / -0.07 | 0.16 / 0.25 |
| zoom window (candidate) | 063746464_r75_c45 (= r75_c45) | D 21% (C 3%) | 0.08 / 0.14 | 0.8 / 2.0 | -0.15 / -0.17 | -0.04 / 0.13 |
| zoom window (candidate) | 024106908_r50_c40 (= r50_c40) | C 11% (D 2%) | 0.12 / 0.15 | 1.6 / 2.5 | 0.08 / 0.19 | 0.19 / 0.21 |
| NULL, survey 2 | 061936267_r80_c95 | D 37% (C 18%) | 0.16 / 0.12 | 2.3 / 1.9 | -0.10 / 0.02 | 0.06 / -0.06 |
| NULL, survey 2 | 040822053_r105_c105 | C 28% (D 18%) | 0.16 / 0.22 | 2.2 / 3.4 | 0.04 / -0.04 | 0.05 / 0.02 |
| NULL, survey 2 | 034621782_r50_c45 | D 26% (C 18%) | 0.26 / 0.32 | 3.2 / 4.0 | 0.12 / 0.03 | 0.13 / 0.01 |
| NULL, survey 2 | 063746464_r25_c45 | D 23% (C 10%) | 0.24 / 0.54 | 2.9 / 7.2 | 0.11 / 0.01 | 0.23 / 0.31 |
| NULL, survey 2 | 034621782_r100_c85 | C 22% (D 16%) | 0.10 / 0.14 | 1.8 / 2.3 | 0.04 / 0.03 | 0.14 / 0.07 |
| NULL, survey 2 | 063530412_r85_c40 | D 7% (C 3%) | 0.08 / 0.10 | 1.3 / 1.7 | 0.04 / 0.06 | 0.07 / 0.09 |
| NULL, survey 2 | 065428392_r55_c20 | C 7% (D 2%) | 0.09 / 0.14 | 1.1 / 2.3 | 0.14 / 0.12 | 0.15 / 0.18 |
| NULL, survey 2 | 065120760_r90_c105 | D 6% (C 4%) | -0.07 / 0.13 | -1.2 / 1.9 | -0.03 / 0.08 | 0.12 / 0.17 |
| NULL, survey 2 | 065428392_r95_c5 | C 5% (D 4%) | 0.07 / 0.06 | 1.3 / 1.2 | 0.05 / 0.02 | 0.06 / 0.14 |
| NULL, survey 2 | 065120760_r110_c65 | C 5% (D 2%) | 0.01 / 0.05 | 0.2 / 0.8 | -0.02 / -0.00 | 0.13 / 0.13 |
| NULL, survey 2 | 065120760_r65_c65 | C 4% (D 2%) | 0.02 / 0.13 | 0.3 / 1.6 | -0.13 / -0.05 | 0.11 / 0.04 |
| NULL, survey 2 | 071903158_r95_c105 | D 3% (C 2%) | 0.02 / 0.14 | 0.4 / 2.0 | 0.05 / 0.11 | 0.01 / 0.02 |
| NULL, survey 2 | 065428392_r10_c60 | C 3% (D 1%) | 0.16 / 0.23 | 2.6 / 3.9 | 0.09 / 0.12 | 0.09 / 0.10 |
| NULL, survey 2 | 071903158_r105_c10 | C 2% (D 1%) | 0.02 / -0.00 | 0.3 / -0.1 | -0.13 / 0.02 | 0.10 / 0.23 |
| NULL, survey 2 | 071903158_r90_c50 | C 2% (D 1%) | -0.13 / -0.05 | -1.5 / -0.8 | 0.18 / -0.04 | 0.04 / -0.13 |
| NULL, survey 1 (default 2 um depth) | 025619069_r60_c5 | D 10% (C 6%) | 0.15 / 0.20 | 1.9 / 3.0 | 0.08 / 0.06 | 0.07 / 0.11 |
| NULL, survey 1 (default 2 um depth) | 030142380_r5_c105 | C 9% (D 4%) | 0.26 / 0.31 | 2.1 / 3.3 | 0.17 / 0.29 | 0.24 / 0.05 |
| NULL, survey 1 (default 2 um depth) | 032347463_r105_c10 | D 9% (C 7%) | 0.06 / 0.16 | 0.6 / 2.8 | 0.09 / 0.05 | 0.06 / 0.10 |
| NULL, survey 1 (default 2 um depth) | 024106908_r65_c0 | C 8% (D 6%) | 0.15 / 0.31 | 1.6 / 5.3 | -0.01 / 0.10 | 0.07 / 0.13 |
| NULL, survey 1 (default 2 um depth) | 025522741_r105_c100 | D 6% (C 5%) | -0.02 / 0.05 | -0.2 / 0.5 | 0.12 / 0.00 | -0.02 / 0.02 |
| NULL, survey 1 (default 2 um depth) | 024106908_r70_c80 | D 4% (C 3%) | 0.10 / 0.15 | 1.7 / 2.7 | 0.00 / 0.08 | 0.05 / 0.02 |
| NULL, survey 1 (default 2 um depth) | 024106966_r75_c35 | C 3% (D 1%) | 0.04 / 0.22 | 0.5 / 2.8 | -0.03 / 0.10 | 0.08 / 0.07 |
| NULL, survey 1 (default 2 um depth) | 025522741_r75_c35 | C 3% (D 1%) | -0.00 / 0.07 | -0.0 / 1.1 | 0.05 / 0.04 | 0.01 / 0.02 |
| NULL, survey 1 (default 2 um depth) | 024106966_r35_c10 | C 3% (D 2%) | 0.19 / 0.11 | 2.8 / 1.5 | 0.07 / 0.09 | 0.06 / 0.11 |
| NULL, survey 1 (default 2 um depth) | 030142380_r70_c20 | C 0% (D 0%) | -0.12 / -0.15 | -1.2 / -1.8 | -0.08 / -0.16 | -0.06 / 0.04 |

#### Table N2. Context rule (the previous run's Table 4 rule): window evaluated inside a 15 mm render around it (s43 / s42)

| group | window | 2 um ink share | r matched | z (matched) | r opposite order | source of the 9 um maps |
|---|---|---|---|---|---|---|
| zoom window (candidate) | 030142380_r35_c65 (= r35_c65) | D 35% (C 4%) | 0.15 / 0.42 | 1.8 / 3.9 | 0.13 / 0.17 | previous run's 15 mm render (= its Table 4) |
| zoom window (candidate) | 063530412_r30_c105 (= r30_c105) | C 33% (D 7%) | 0.28 / 0.36 | 4.1 / 4.6 | 0.18 / 0.08 | previous run's 15 mm render (= its Table 4) |
| zoom window (candidate) | 025619069_r105_c25 (= r105_c25) | C 29% (D 10%) | 0.46 / 0.37 | 6.2 / 5.4 | 0.07 / 0.01 | previous run's 15 mm render (= its Table 4) |
| zoom window (candidate) | 040822053_r50_c70 (= r50_c70) | C 28% (D 9%) | 0.23 / 0.31 | 3.4 / 3.4 | -0.23 / -0.06 | previous run's 15 mm render (= its Table 4) |
| zoom window (candidate) | 063746464_r75_c45 (= r75_c45) | D 21% (C 3%) | 0.19 / 0.22 | 3.1 / 3.4 | -0.03 / -0.05 | previous run's 15 mm render (= its Table 4) |
| zoom window (candidate) | 024106908_r50_c40 (= r50_c40) | C 11% (D 2%) | 0.27 / 0.20 | 2.9 / 3.1 | 0.19 / 0.26 | previous run's 15 mm render (= its Table 4) |
| NULL, survey 2 | 061936267_r80_c95 | D 37% (C 18%) | 0.13 / 0.20 | 1.8 / 2.9 | -0.04 / 0.11 | zoom-rule render, this run |
| NULL, survey 2 | 040822053_r105_c105 | C 28% (D 18%) | 0.14 / 0.25 | 2.3 / 3.8 | 0.00 / 0.02 | zoom-rule render, this run |
| NULL, survey 2 | 034621782_r50_c45 | D 26% (C 18%) | 0.21 / 0.32 | 2.7 / 4.3 | 0.07 / 0.04 | zoom-rule render, this run |
| NULL, survey 2 | 063746464_r25_c45 | D 24% (C 10%) | 0.28 / 0.56 | 3.2 / 8.5 | 0.04 / -0.03 | zoom-rule render, this run |
| NULL, survey 2 | 034621782_r100_c85 | C 22% (D 15%) | 0.17 / 0.21 | 2.8 / 3.8 | 0.06 / 0.07 | zoom-rule render, this run |
| NULL, survey 2 | 063530412_r85_c40 | D 7% (C 3%) | 0.16 / 0.16 | 2.6 / 2.9 | 0.18 / 0.10 | zoom-rule render, this run |
| NULL, survey 2 | 065428392_r55_c20 | C 7% (D 2%) | 0.07 / 0.03 | 1.0 / 0.6 | 0.12 / 0.06 | zoom-rule render, this run |
| NULL, survey 2 | 065120760_r90_c105 | D 6% (C 4%) | 0.02 / 0.14 | 0.2 / 2.5 | 0.02 / 0.09 | zoom-rule render, this run |
| NULL, survey 2 | 065428392_r95_c5 | C 5% (D 4%) | 0.04 / 0.15 | 0.9 / 2.6 | 0.07 / 0.10 | zoom-rule render, this run |
| NULL, survey 2 | 065120760_r110_c65 | C 5% (D 2%) | 0.04 / 0.06 | 0.8 / 0.7 | -0.02 / 0.01 | zoom-rule render, this run |
| NULL, survey 2 | 065120760_r65_c65 | C 4% (D 2%) | 0.01 / 0.08 | 0.1 / 1.0 | -0.03 / -0.03 | zoom-rule render, this run |
| NULL, survey 2 | 071903158_r95_c105 | D 3% (C 2%) | 0.01 / 0.12 | 0.1 / 1.9 | -0.01 / 0.09 | zoom-rule render, this run |
| NULL, survey 2 | 065428392_r10_c60 | C 3% (D 1%) | 0.10 / 0.22 | 1.9 / 3.5 | 0.18 / 0.16 | zoom-rule render, this run |
| NULL, survey 2 | 071903158_r105_c10 | C 2% (D 1%) | 0.03 / 0.03 | 0.6 / 0.4 | -0.06 / 0.01 | zoom-rule render, this run |
| NULL, survey 2 | 071903158_r90_c50 | C 2% (D 1%) | -0.13 / 0.01 | -1.8 / 0.0 | 0.19 / 0.01 | zoom-rule render, this run |
| NULL, survey 1 (default 2 um depth) | 025619069_r60_c5 | D 10% (C 6%) | 0.20 / 0.24 | 3.3 / 4.8 | -0.07 / 0.04 | zoom-rule render, this run |
| NULL, survey 1 (default 2 um depth) | 030142380_r5_c105 | C 9% (D 4%) | 0.28 / 0.40 | 2.9 / 4.1 | 0.24 / 0.33 | zoom-rule render, this run |
| NULL, survey 1 (default 2 um depth) | 032347463_r105_c10 | D 9% (C 7%) | 0.04 / 0.24 | 0.3 / 3.8 | 0.10 / 0.07 | zoom-rule render, this run |
| NULL, survey 1 (default 2 um depth) | 024106908_r65_c0 | C 8% (D 6%) | 0.13 / 0.31 | 1.9 / 5.7 | 0.00 / 0.09 | zoom-rule render, this run |
| NULL, survey 1 (default 2 um depth) | 025522741_r105_c100 | D 6% (C 5%) | 0.00 / 0.23 | 0.0 / 2.6 | 0.10 / 0.06 | zoom-rule render, this run |
| NULL, survey 1 (default 2 um depth) | 024106908_r70_c80 | D 4% (C 3%) | 0.13 / 0.13 | 2.1 / 2.2 | 0.04 / 0.07 | zoom-rule render, this run |
| NULL, survey 1 (default 2 um depth) | 024106966_r75_c35 | C 3% (D 1%) | -0.03 / 0.20 | -0.3 / 2.6 | -0.07 / 0.14 | zoom-rule render, this run |
| NULL, survey 1 (default 2 um depth) | 025522741_r75_c35 | C 3% (D 1%) | 0.05 / 0.08 | 1.1 / 1.5 | 0.08 / 0.17 | zoom-rule render, this run |
| NULL, survey 1 (default 2 um depth) | 024106966_r35_c10 | C 3% (D 2%) | 0.08 / 0.13 | 1.5 / 2.0 | -0.06 / 0.06 | zoom-rule render, this run |
| NULL, survey 1 (default 2 um depth) | 030142380_r70_c20 | C 0% (D 0%) | -0.10 / -0.06 | -1.1 / -0.7 | -0.07 / -0.07 | zoom-rule render, this run |

Reproduction check 063746464_r75_c45|my_ctx_render: my zoom-rule render + inference vs the previous run's 15 mm maps, identical: {'seed43_step060000': True, 'seed42_step010000': True} (md5 check: all four maps identical.)

Pooling rule: 3 windows have both 2 um maps; matched r (default depth minus corrected) mean -0.001, mean |diff| 0.013 -> pooled A+B: True.

#### Candidates against the null, direct tiling (null = 25 never-picked windows)

| window | r matched s43 (null windows below) | s42 (below) | mean of 2 (below) | above null p95? s43 / s42 | stands out (both) | SDs above null mean (mean of 2) |
|---|---|---|---|---|---|---|
| 030142380_r35_c65 (= r35_c65) | 0.16 (18 of 25) | 0.33 (24 of 25) | 0.24 (22 of 25) | no / yes | no | 1.1 |
| 063530412_r30_c105 (= r30_c105) | 0.30 (25 of 25) | 0.28 (21 of 25) | 0.29 (23 of 25) | yes / no | no | 1.5 |
| 025619069_r105_c25 (= r105_c25) | 0.38 (25 of 25) | 0.33 (24 of 25) | 0.36 (24 of 25) | yes / yes | YES | 2.1 |
| 040822053_r50_c70 (= r50_c70) | 0.17 (21 of 25) | 0.28 (21 of 25) | 0.23 (21 of 25) | no / no | no | 1.0 |
| 063746464_r75_c45 (= r75_c45) | 0.08 (12 of 25) | 0.14 (12 of 25) | 0.11 (11 of 25) | no / no | no | -0.1 |
| 024106908_r50_c40 (= r50_c40) | 0.12 (16 of 25) | 0.15 (16 of 25) | 0.14 (16 of 25) | no / no | no | 0.2 |

#### Candidates against the null, context tiling (the previous run's Table 4 rule)

| window | r matched s43 (null windows below) | s42 (below) | mean of 2 (below) | above null p95? s43 / s42 | stands out (both) | SDs above null mean (mean of 2) |
|---|---|---|---|---|---|---|
| 030142380_r35_c65 (= r35_c65) | 0.15 (19 of 25) | 0.42 (24 of 25) | 0.28 (23 of 25) | no / yes | no | 1.4 |
| 063530412_r30_c105 (= r30_c105) | 0.28 (23 of 25) | 0.36 (23 of 25) | 0.32 (23 of 25) | yes / no | no | 1.7 |
| 025619069_r105_c25 (= r105_c25) | 0.46 (25 of 25) | 0.37 (23 of 25) | 0.42 (24 of 25) | yes / no | no | 2.6 |
| 040822053_r50_c70 (= r50_c70) | 0.23 (23 of 25) | 0.31 (21 of 25) | 0.27 (23 of 25) | no / no | no | 1.3 |
| 063746464_r75_c45 (= r75_c45) | 0.19 (21 of 25) | 0.22 (16 of 25) | 0.21 (20 of 25) | no / no | no | 0.7 |
| 024106908_r50_c40 (= r50_c40) | 0.27 (23 of 25) | 0.20 (14 of 25) | 0.24 (22 of 25) | yes / no | no | 0.9 |

#### Null distributions and group numbers (printed)

```
DIRECT tiling, never-picked null
r_matched: s43: mean 0.08 sd 0.11 median 0.08 p95 0.26 (normal 0.26) max 0.26 | s42: mean 0.15 sd 0.14 median 0.14 p95 0.32 (normal 0.37) max 0.54 | mean2: mean 0.11 sd 0.12 median 0.11 p95 0.29 (normal 0.30) max 0.39
r_opposite_9um_order: s43: mean 0.04 sd 0.09 median 0.05 p95 0.17 (normal 0.18) max 0.18 | s42: mean 0.05 sd 0.08 median 0.04 p95 0.12 (normal 0.18) max 0.29 | mean2: mean 0.04 sd 0.07 median 0.04 p95 0.13 (normal 0.16) max 0.23
r_offsheet_max: s43: mean 0.08 sd 0.07 median 0.07 p95 0.21 (normal 0.19) max 0.24 | s42: mean 0.08 sd 0.09 median 0.07 p95 0.22 (normal 0.23) max 0.31 | mean2: mean 0.08 sd 0.07 median 0.08 p95 0.17 (normal 0.19) max 0.27
z_matched: s43: mean 1.07 sd 1.32 median 1.30 p95 2.85 (normal 3.24) max 3.17 | s42: mean 2.18 sd 1.86 median 2.01 p95 5.02 (normal 5.24) max 7.23 | mean2: mean 1.62 sd 1.48 median 1.66 p95 3.55 (normal 4.06) max 5.05
group tests: {"s43": {"zoom6_vs_null_p_one_sided": 0.017737793043688485, "picked_other_vs_null_p_one_sided": null, "zoom6_median": 0.16231904178857803, "null_median": 0.07999072223901749, "picked_other_median": null}, "s42": {"zoom6_vs_null_p_one_sided": 0.015446548260786303, "picked_other_vs_null_p_one_sided": null, "zoom6_median": 0.2837081849575043, "null_median": 0.13671185076236725, "picked_other_median": null}, "mean2": {"zoom6_vs_null_p_one_sided": 0.017737793043688485, "picked_other_vs_null_p_one_sided": null, "zoom6_median": 0.23388398066163063, "null_median": 0.1144150160253048, "picked_other_median": null}}
Spearman(r matched, 2 um share): null {"s43": 0.5884615384615385, "s42": 0.5969230769230769} all windows {"s43": 0.6661290322580645, "s42": 0.6596774193548388}
null windows with 2 um share >= 15%: {"n": 5, "windows": ["061936267_r80_c95", "040822053_r105_c105", "034621782_r50_c45", "063746464_r25_c45", "034621782_r100_c85"], "r_matched": {"s43": [0.16, 0.162, 0.26, 0.239, 0.097], "s42": [0.12, 0.223, 0.322, 0.536, 0.145]}}
survey2_only: n 15 | s43 mean 0.08 p95 0.25 max 0.26 | s42 mean 0.15 p95 0.39 max 0.54
survey1_only: n 10 | s43 mean 0.08 p95 0.23 max 0.26 | s42 mean 0.14 p95 0.31 max 0.31
all_never_picked: n 25 | s43 mean 0.08 p95 0.26 max 0.26 | s42 mean 0.15 p95 0.32 max 0.54

CONTEXT tiling, never-picked null
r_matched: s43: mean 0.08 sd 0.10 median 0.07 p95 0.27 (normal 0.25) max 0.28 | s42: mean 0.18 sd 0.13 median 0.16 p95 0.38 (normal 0.40) max 0.56 | mean2: mean 0.13 sd 0.11 median 0.12 p95 0.32 (normal 0.31) max 0.42
r_opposite_9um_order: s43: mean 0.04 sd 0.09 median 0.04 p95 0.19 (normal 0.19) max 0.24 | s42: mean 0.07 sd 0.08 median 0.07 p95 0.17 (normal 0.20) max 0.33 | mean2: mean 0.06 sd 0.07 median 0.05 p95 0.17 (normal 0.18) max 0.29
z_matched: s43: mean 1.24 sd 1.36 median 1.07 p95 3.17 (normal 3.49) max 3.29 | s42: mean 2.72 sd 1.98 median 2.58 p95 5.55 (normal 5.98) max 8.48 | mean2: mean 1.98 sd 1.56 median 1.75 p95 4.00 (normal 4.55) max 5.85
group tests: {"s43": {"zoom6_vs_null_p_one_sided": 0.0008610842871132082, "picked_other_vs_null_p_one_sided": null, "zoom6_median": 0.24950861185789108, "null_median": 0.07151507586240768, "picked_other_median": null}, "s42": {"zoom6_vs_null_p_one_sided": 0.009951363677726303, "picked_other_vs_null_p_one_sided": null, "zoom6_median": 0.33619607985019684, "null_median": 0.16399411857128143, "picked_other_median": null}, "mean2": {"zoom6_vs_null_p_one_sided": 0.000676372200287662, "picked_other_vs_null_p_one_sided": null, "zoom6_median": 0.27737632766366005, "null_median": 0.11533821473130956, "picked_other_median": null}}
Spearman(r matched, 2 um share): null {"s43": 0.713076923076923, "s42": 0.7515384615384615} all windows {"s43": 0.7608870967741936, "s42": 0.780241935483871}
null windows with 2 um share >= 15%: {"n": 5, "windows": ["061936267_r80_c95", "040822053_r105_c105", "034621782_r50_c45", "063746464_r25_c45", "034621782_r100_c85"], "r_matched": {"s43": [0.129, 0.14, 0.207, 0.284, 0.166], "s42": [0.204, 0.254, 0.318, 0.562, 0.209]}}
survey2_only: n 15 | s43 mean 0.09 p95 0.23 max 0.28 | s42 mean 0.17 p95 0.39 max 0.56
survey1_only: n 10 | s43 mean 0.08 p95 0.24 max 0.28 | s42 mean 0.19 p95 0.36 max 0.40
all_never_picked: n 25 | s43 mean 0.08 p95 0.27 max 0.28 | s42 mean 0.18 p95 0.38 max 0.56

How many never-picked windows reach the levels the previous report cited (its six regions: z 2.5-7.2)
direct seed43 n 25 | z>=2.5: 4 | z>=4: 0 | r>=0.2: 3 | r>=0.3: 0
direct seed42 n 25 | z>=2.5: 10 | z>=4: 2 | r>=0.2: 8 | r>=0.3: 4
context seed43 n 25 | z>=2.5: 6 | z>=4: 0 | r>=0.2: 4 | r>=0.3: 0
context seed42 n 25 | z>=2.5: 14 | z>=4: 5 | r>=0.2: 11 | r>=0.3: 4
```

#### Exploratory checks (added after part of the null was seen; not used for the verdict)

```
Fine-scale (0.06-0.56 mm) matched r, direct rule, primary null: s43: mean 0.07 p95 0.21 max 0.23 | s42: mean 0.14 p95 0.30 max 0.40
  030142380_r35_c65 (= r35_c65): fine matched 0.20 (23 of 25 null below) / 0.35 (24 of 25 null below); fine opposite 0.23 / 0.05
  063530412_r30_c105 (= r30_c105): fine matched 0.20 (23 of 25 null below) / 0.20 (19 of 25 null below); fine opposite 0.17 / -0.04
  025619069_r105_c25 (= r105_c25): fine matched 0.32 (25 of 25 null below) / 0.29 (23 of 25 null below); fine opposite 0.10 / 0.02
  040822053_r50_c70 (= r50_c70): fine matched -0.03 (2 of 25 null below) / 0.16 (12 of 25 null below); fine opposite -0.02 / -0.06
  063746464_r75_c45 (= r75_c45): fine matched 0.05 (11 of 25 null below) / 0.18 (18 of 25 null below); fine opposite -0.04 / -0.03
  024106908_r50_c40 (= r50_c40): fine matched 0.13 (19 of 25 null below) / 0.12 (9 of 25 null below); fine opposite -0.07 / 0.03

EXPLORATORY specific overlap (matched minus max(opposite, off-sheet)), direct rule, primary null: s43: mean -0.02 p95 0.12 max 0.13 | s42: mean 0.04 p95 0.22 max 0.29
  030142380_r35_c65 (= r35_c65): -0.07 (6 of 25 null below) / 0.29 (25 of 25 null below)
  063530412_r30_c105 (= r30_c105): 0.19 (25 of 25 null below) / 0.18 (22 of 25 null below)
  025619069_r105_c25 (= r105_c25): 0.28 (25 of 25 null below) / 0.26 (24 of 25 null below)
  040822053_r50_c70 (= r50_c70): 0.01 (14 of 25 null below) / 0.03 (11 of 25 null below)
  063746464_r75_c45 (= r75_c45): 0.12 (24 of 25 null below) / 0.01 (9 of 25 null below)
  024106908_r50_c40 (= r50_c40): -0.06 (6 of 25 null below) / -0.05 (4 of 25 null below)

EXPLORATORY share-adjusted (direct rule): null line r = a + b * share; candidate residuals in null-residual SDs (null's own 95th pct in brackets)
  s43: a 0.019 b 0.639 per unit share, resid SD 0.090 (null resid p95 1.65 SD): r105_c25 0.38 vs 0.21 predicted -> +2.0; r50_c70 0.17 vs 0.20 predicted -> -0.3; r75_c45 0.08 vs 0.15 predicted -> -0.8; r50_c40 0.12 vs 0.09 predicted -> +0.4; r35_c65 0.16 vs 0.25 predicted -> -1.0; r30_c105 0.30 vs 0.23 predicted -> +0.7
  s42: a 0.085 b 0.682 per unit share, resid SD 0.121 (null resid p95 1.43 SD): r105_c25 0.33 vs 0.28 predicted -> +0.4; r50_c70 0.28 vs 0.28 predicted -> +0.1; r75_c45 0.14 vs 0.22 predicted -> -0.7; r50_c40 0.15 vs 0.16 predicted -> -0.0; r35_c65 0.33 vs 0.33 predicted -> +0.0; r30_c105 0.28 vs 0.31 predicted -> -0.2

EXPLORATORY share-adjusted (context rule): null line r = a + b * share; candidate residuals in null-residual SDs (null's own 95th pct in brackets)
  s43: a 0.025 b 0.625 per unit share, resid SD 0.084 (null resid p95 1.33 SD): r105_c25 0.46 vs 0.21 predicted -> +3.0; r75_c45 0.19 vs 0.15 predicted -> +0.5; r35_c65 0.15 vs 0.24 predicted -> -1.1; r30_c105 0.28 vs 0.23 predicted -> +0.5; r50_c70 0.23 vs 0.20 predicted -> +0.3; r50_c40 0.27 vs 0.09 predicted -> +2.1
  s42: a 0.106 b 0.771 per unit share, resid SD 0.113 (null resid p95 1.82 SD): r105_c25 0.37 vs 0.33 predicted -> +0.4; r75_c45 0.22 vs 0.27 predicted -> -0.4; r35_c65 0.42 vs 0.38 predicted -> +0.3; r30_c105 0.36 vs 0.36 predicted -> -0.0; r50_c70 0.31 vs 0.32 predicted -> -0.1; r50_c40 0.20 vs 0.19 predicted -> +0.1

Tiling check (direct 7.5 mm render vs the same window cut from the 15 mm render):
  025619069_r105_c25|seed43_step060000|fwd map r 0.71 (interior 0.77)
  025619069_r105_c25|seed43_step060000|rev map r 0.78 (interior 0.85) coloc direct 0.38 vs 15mm-cut 0.46
  025619069_r105_c25|seed42_step010000|fwd map r 0.74 (interior 0.86)
  025619069_r105_c25|seed42_step010000|rev map r 0.85 (interior 0.90) coloc direct 0.33 vs 15mm-cut 0.37
  063746464_r75_c45|seed43_step060000|fwd map r 0.71 (interior 0.78) coloc direct 0.08 vs 15mm-cut 0.19
  063746464_r75_c45|seed43_step060000|rev map r 0.73 (interior 0.82)
  063746464_r75_c45|seed42_step010000|fwd map r 0.78 (interior 0.89) coloc direct 0.14 vs 15mm-cut 0.22
  063746464_r75_c45|seed42_step010000|rev map r 0.75 (interior 0.84)

```

#### Table N3. Known-blank papyrus (held-out validation region of the known-text control, PHerc0139 w016)

| pixels | n px | 2 um share > 0.5 | r matched (official order) s43 / s42 | z | r opposite order | r off-sheet (max of 4) |
|---|---|---|---|---|---|---|
| whole validation region (23% ink) | 187915 | 8% | 0.43 / 0.33 | 4.0 / 3.2 | 0.09 / -0.07 | 0.05 / 0.03 |
| blank: label = no ink | 144375 | 2% | 0.11 / 0.05 | 1.2 / 0.5 | -0.02 / -0.16 | 0.09 / 0.05 |
| blank, >= 10 px (94 um) from ink | 125587 | 2% | -0.03 / -0.08 | -0.2 / -0.7 | -0.05 / -0.15 | 0.05 / 0.03 |
| blank, >= 20 px (187 um) from ink | 105530 | 2% | -0.05 / -0.14 | -0.5 / -1.0 | -0.06 / -0.13 | 0.03 / 0.03 |

Known text at the null's window size (18 overlapping 7.5 mm windows of the same control, context tiling):
matched r 0.27-0.48 (s43) / 0.14-0.48 (s42), opposite order -0.14 to 0.08 (`null/results/known_text_windows.json`).

### 10.4 What it means

1. **The overlap is real but not specific.** The 9 um model does respond where the 2 um model responds, on 0846A. But it
   does so on ordinary windows too, in proportion to how much the 2 um model fires. The previous report's "same places,
   same depth order" pattern is what ordinary 0846A windows show as well.
2. **Why the candidates looked good.** They were chosen for high one-sided 2 um ink share, and overlap grows with 2 um
   share. At the same share, ordinary windows overlap as much; the exceptions are all on seed43 (r105_c25 under both
   tilings, r50_c40 under the 15 mm rule), and none holds on seed42.
3. **r105_c25 is the only survivor, and a weak one.** It is the top window of all 31 on seed43 under both tilings, and its
   overlap is more specific than all 25 ordinary windows on seed43 and 24 of 25 on seed42 (exploratory: matched minus
   the larger of opposite-order and off-sheet r, 0.28 / 0.26 vs null 95th percentile 0.12 / 0.22). But the second checkpoint does not confirm it, and it was
   named "strongest" after the overlap was seen: the best of six picks beating all 25 ordinary windows on one checkpoint
   happens about 1 time in 5 by chance (6 of 31 equally likely ranks).
4. **Ink or texture is still open, but it no longer matters for the overlap test.** On blank papyrus of a known scroll the
   overlap is zero. On 0846A it is everywhere the 2 um model fires. Either both models share a false-positive texture on
   0846A, or 0846A carries faint ink nearly everywhere. Either way the overlap cannot single out letters.

### 10.5 What is weak

1. **The null is "never picked", not "known blank".** 0846A is a written scroll; ordinary windows may hold ink too.
2. **25 windows.** The 95th percentile sits near the second-highest value, so a verdict within 0.01 of the line (r105_c25
   on seed42 under both tilings) could flip with a few more windows.
3. **Tiling noise.** One window's overlap moves by up to about 0.1 between tilings. Both tilings were applied to
   everything, so comparisons are fair, but single-window rankings are noisy.
4. **Survey-1 null windows** used 2 um maps at the default depth window (pooled by the pre-set test: corrected vs default
   depth changed r by -0.001 on the 3 windows that have both).
5. **The context tiling** ran the surface depth window only (no off-sheet column).
6. **Exploratory measures** (fine scale, specific overlap, share-adjusted) were added after part of the null was seen.
7. **My own mistake (caught, fixed, lesson L56):** my first context-render loop wrote into a folder another worker had
   not yet created, so three 230 MB renders piled up on box A for 4 minutes. Loop stopped, fixed, re-run. Results are
   unaffected. Box A footprint peaked at about 0.7 GB; it never dropped below 13 GB free.

### 10.6 Files

- Figure: `evidence_0912/nine_um_null.png` (rows = tiling; left two panels = matched r per window per checkpoint with the
  null's 95th percentile; right = matched r against 2 um ink share).
- Scripts, lists and JSON results: `evidence_0912/nine_um_files/null/` (`results/summary_final.txt` = every table above,
  as printed; `results/null.json`, `null_ctx.json`, `null_summary.json`, `blank_null.json`, `orient.json`,
  `direct_vs_15mm.json`, `known_text_windows.json`, `counts.txt`).
- box B `<work-dir>/n9null/` (515 MB): every 9 um map (`preds/` direct, `preds_ctx/` context), 2 um map copies
  (`maps2um/`), surface slices, results. box A `<run-dir>/n9null/` (9 MB): scripts, logs, context meshes. All renders
  deleted after use.
- Not run: the 11 windows picked earlier but not zoomed (lists in `null/lists/`; they can be run with `worker_lever.sh`).

### 10.7 Next steps (short)

1. **r105_c25 by eye at 9 um** (15 mm, more checkpoints, small depth offsets), judged by letter shape, not overlap.
2. **Drop overlap as an ink test on 0846A.** If a number is needed, it has to be a letter-shape score calibrated on
   >= 8 known text and >= 4 known blank windows (L51), run against this same 25-window null.
3. **A true blank on 0846A** (outside the written area, if one can be identified) would separate "texture" from "faint ink
   everywhere".

### 10.8 Running log (AEST, from `date`)

- 04:19 Hand test (025619069 = r105_c25 window, direct 7.5 mm render): render 58 s, 57 MB, crop identical to the survey's 9 um render; matched r 0.38 (s43, z 5.2) / 0.33 (s42, z 4.2), opposite 0.10 / -0.01, off-sheet 0.07 / 0.07. The previous run's Table 4 gave 0.46 / 0.37 for the same window cut from the 15 mm render.
- 04:19 TILING SENSITIVITY FOUND: the same window's 9 um map, direct render vs cut from the 15 mm render, correlates only 0.71-0.85 (0.77-0.90 away from edges). Renders are identical where both have data (99.8% of pixels); the difference is tiling (the direct render has a black frame around the window, and the 15 mm render's tile grid sits 16 px off). Co-location for r105_c25 moves 0.38 -> 0.46 (s43) from tiling alone. So candidates and null must go through the identical per-window rule, which this design does.
- 04:19 Known-blank null (0139 w016 held-out region): r matched 0.11 / 0.05 on all label-0 pixels, -0.03 / -0.08 at >= 10 px from ink, -0.05 / -0.14 at >= 20 px; whole region (23% ink) 0.43 / 0.33. On blank papyrus of a known scroll the two models do not co-locate.
- 04:35 PRE-REGISTERED verdict rule (before any null number was looked at): a candidate 'stands out' if its matched r is above the primary null's empirical 95th percentile for BOTH checkpoints; the verdict is called robust only if the direct-render rule and the context rule (below) agree. Group test: the six zoom windows vs the null, one-sided Mann-Whitney.
- 04:35 FRAME EFFECT explained: villa's flat inference normalises each 17x128x128 tile by its own median/MAD, zeros included (normalize_robust, use_mask False). A direct 7.5 mm window render has a ~20 px black frame (the window mesh stops there), so every tile within ~190 px of the edge is normalised differently; r75_c45's co-location drops 0.19/0.22 (cut from the 15 mm render) -> 0.08/0.14 (direct). Added a CONTEXT RULE for the null: the 15 mm region around each null window built with zoom_regions.py's exact code (my mesh for r75_c45 is byte-identical to p0846a_zoom's), surface window only, evaluated on the window exactly as Table 4 (my code reproduces all 12 Table 4 matched values to 4 decimals). The 11 'picked earlier' windows were dropped from the direct batch to make room (skip markers; they can run later).
- 04:46 Added a SECONDARY measure (after seeing 4 of the 25 null windows, so not blind): the fine-scale (0.06-0.56 mm, stroke-sized) part of the matched co-location, n9_bands.py's split, judged by the same 95th-percentile rule. The previous report leaned on it for r105_c25 (0.33 / 0.29 vs known text 0.26 / 0.27). Known text at the null's window size (18 overlapping 7.5 mm windows of the w016 control, context rule): matched r 0.27-0.48 (s43) / 0.14-0.48 (s42), opposite -0.14..0.08.
- 04:57 EXPLORATORY measure added after seeing 10 of 25 null windows (so not blind; reported as exploratory only): 'specific overlap' = matched r minus the larger of opposite-order r and off-sheet r. Known text: 0.28 / 0.28. Guards so far: +-24 px alignment search gains <= 0.06 in every group (no misregistered null window); orientation identity-best except in weak windows (r <= 0.13), as expected from chance at 1/8 resolution.
- 05:38 DIRECT RULE COMPLETE (31 windows: 6 zoom, 15 survey-2 null, 10 survey-1 null). Pooling rule: default-depth vs corrected 2 um map changes matched r by -0.001 on average (|diff| 0.013, 3 windows) -> survey 1 pooled, primary null n = 25. Null matched r: mean 0.08 / 0.15, 95th pct 0.26 / 0.32, max 0.26 / 0.54 (063746464_r25_c45, never picked, same surface as r75_c45, z 7.2). r105_c25 0.38 / 0.33 = above the 95th pct on both (25 / 24 of 25 null windows below; s42 margin 0.01) -> 'stands out' by the pre-registered rule under this tiling. r75_c45 0.08 / 0.14 = mid-null (12 of 25 below). Six zoom windows as a group above the null (Mann-Whitney one-sided p 0.018 / 0.015), BUT overlap rises with 2 um ink share (Spearman 0.59 / 0.60 in the null) and the zoom windows were picked for high share; against the null's share trend (exploratory) the candidates sit on the line except r105_c25 on s43 (+2.0 SD; s42 +0.4). Guards: alignment search gains <= 0.10 (null) / 0.06 (zoom); r does not rise with depth-correction NCC (Spearman -0.17 / -0.02).
- 06:18 CONTEXT RULE COMPLETE (25 null windows + my byte-identical re-run of r75_c45). Null matched r: mean 0.08 / 0.18, 95th pct 0.27 / 0.38, max 0.28 / 0.56. r105_c25 0.46 / 0.37 = above on s43 (25 of 25 below), NOT on s42 (23 of 25 below; misses the 95th pct by 0.01). r75_c45 0.19 / 0.22 = inside the null (21 / 16 of 25 below). VERDICT by the pre-set rule: r105_c25 stands out under one tiling and not the other -> not robust; r75_c45 ordinary under both. Section 10 written; figure evidence_0912/nine_um_null.png; box A footprint 9 MB, box B 515 MB, all renders deleted, no processes left running.
