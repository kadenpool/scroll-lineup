# Plan A pre-registration: teach ink_9um that PHerc0846A papyrus is "no ink" (negative-only domain adaptation)

Written 2026-09-12 16:29 AEST, before any render, download or inference for this experiment was made.
Private experiment (Kaden approved "A: teach a model 0846A", 12 Sep 16:12). Nothing public. Kaggle kernels
private, account squiffymccat, kernel names `vesuvius-a0846-head` and `vesuvius-a0846-full`.

## 1. Question

Both official 9 um ink checkpoints call 15-48 % of PHerc0846A's surface "ink" and still 7-36 % when the surface is
moved 40 voxels off the sheet (NINE_UM_CHECK.md Table 3). There is no known text on 0846A, so there are no positive
labels. The untried public idea (flummoxjr) is negative-only adaptation: keep training the model on its own public
labelled data (real ink, four scrolls) PLUS windows of 0846A papyrus labelled "no ink", so it learns that 0846A's
texture is not ink while keeping its ability to read real ink. Does that remove the over-firing without losing
real-ink detection, and does any candidate region then stand out from its own off-sheet control?

## 2. Base model and code (fixed)

- Checkpoint: `scrollprize/ink_9um` `hybrid_3d2d-seed42/step-010000.pth` (leverckpts/seed42_step010000.pth`,
  138,360,039 bytes). Chosen in the brief; it was the better transfer checkpoint in the August benchmark and our own ranking.
  Its baseline on known text in the 9 um check: pixel AUC 0.849 (forward) on the pherc0139-w016 validation region.
- Training and inference code: villa `vesuvius.ink_detection` at commit `777cb16cf9208b35897b231843174f2440d9f1f1`
  (the commit the ft343 harness pins), run through our harness `scratch_ft343/ft343.py` adapted as
  `evidence_0912/plan_a_files/a0846.py`. Kept from ft343 unchanged: environment build (uv, Python 3.14 venv, torch
  2.14 cu126), checkpoint download and strict-load pre-check, init file with the exact inference weights (EMA off),
  training config built from the checkpoint's embedded recipe, SGD momentum 0.99 nesterov, cosine warm-up, grad clip 1,
  fp16, batch 32, `sampling_strategy: uniform`, calibration run then a time-budgeted run, head-only wrapper, package flat
  inference. Changed: the data stage (loads two pre-built Kaggle datasets instead of downloading PHerc0343P) and the
  metrics (T1/T2/T3 below instead of teacher correlation).
- Known pitfalls carried over (lessons L36-L44, ft343 README): labels must be 21 planes deep (create_label_zarrs writes 65),
  EMA is copied before the checkpoint loads so it stays off, `dataloader_workers` >= 1, the head-only wrapper needs a
  `__main__` guard for spawn workers, `bce_label_smoothing 0.5` leaves little loss headroom at low ink fractions (see 6).

## 3. Data (fixed before any of it is built)

### 3a. Real ink (positives + ordinary papyrus of the training scrolls)

Labels: HF bucket `scrollprize/datasets/ink_9um/labels/aligned-scrollprizeorg-21slices/` (public, no token: verified with
plain HTTPS at 16:20). Inputs: rebuilt exactly as ink_9um's `prepare_9um_isotropic_input` does (public 2.399 um surface
volume, pyramid level 2, centred 84 of the Z planes, mean of 4 -> 21 slices, uint8), using our
`nine_um_files/build_aligned_generic.py` rule, so input and label share one grid.

- Training segments (12, never the validation ones): PHerc0139 w017, w029, w040, w043; PHerc1667 w013, w018, w028, w031;
  PHercParis4 w01, w03, w06, w09. One crop of 2048 x 2048 label pixels per segment (16 x 16 chunks of 128), placed by a
  fixed rule: the chunk-aligned 2048^2 window with the most ink pixels (inklabels > 0) in the segment, searched on the
  chunk grid. Labels and supervision masks as published, cropped. Reason for crops: 12 whole segments would be > 10 GB.
- Validation segments (T1, never trained on): pherc0139-w016, pherc0814-46527, pherc1667-w029 = the three segments that
  ship `_validation_mask.zarr` (the README calls them the online-validation cases of the released checkpoints). Crop:
  the chunk-aligned bounding box of the validation mask plus one chunk of margin, capped at 3072 x 3072 (if the mask is
  larger, the 3072^2 window holding the most validation pixels). These crops also serve as the package's online
  validation set during training (validation_mask = the published one), so "best validation" checkpoints are optimistic
  and the FINAL checkpoint is the headline, as in ft343.

### 3b. PHerc0846A negatives (label = all zero) and held-out windows

Render recipe = the 9 um check's, unchanged: `vc_render_tifxyz` from the eligible 9.362 um volume
`PHerc0846A/volumes/20250728152254-9.362um-1.2m-113keV-masked.zarr/`, `--auto-crop --scale 1 -g 0 --num-slices 101
--slice-step 1 --flip-normals`, i.e. `nine_um_files/render_one.sh` (box A, one render at a time per worker, deleted after
its 21-slice cut-outs are written). Cut-outs: on-sheet = render layers [40, 61); off-sheet A = [0, 21); off-sheet B =
[80, 101) (= 40 voxels = 0.37 mm each side, the 9 um check's "nm40/np40"). The model centre-crops 17 of the 21, so it sees
layers 42-58 on-sheet, exactly as before.

Windows are the survey's 40 x 40-cell (7.5 mm) windows on the grown 0846A surfaces (`p0846a_survey/`, `p0846a_survey2/`)
plus new windows cut by the same rule. EXCLUDED everywhere (never rendered for training): the six zoom regions and every
window on the six candidate surfaces 025619069, 063746464, 030142380, 063530412, 040822053, 024106908. Also excluded from
training: any window that was ever "picked" as a strong 2 um spot (7 windows: 025522741_r65_c75, 024106966_r70_c75,
032347463_r85_c65, 032347463_r110_c105, 034621782_r40_c85, 061936267_r40_c15, 061936267_r20_c55), because they might be
the faint ink we are looking for.

- Training pool (25): the 17 never-picked survey windows on the 8 eligible surfaces (024106966 r35_c10 r75_c35;
  025522741 r75_c35 r105_c100; 032347463 r105_c10; 034621782 r50_c45 r100_c85; 061936267 r80_c95; 065120760 r65_c65
  r90_c105 r110_c65; 065428392 r10_c60 r55_c20 r95_c5; 071903158 r90_c50 r95_c105 r105_c10) + 8 NEW windows, one per
  eligible surface. Selection inside the pool, made in the kernel from the BASELINE run before training: keep the 20
  windows with the lowest baseline on-sheet ink share (seed42 step-010000, max of forward and reverse); the 5 highest are
  dropped and used nowhere. (The survey responses already known for the 17: 2 um shares 1-22 %, 9 um on-sheet shares
  9-50 %; the pool is what exists, so "lowest" is a mild filter, not a strong one.)
- Held-out ordinary windows for T2 (10, fixed now, never trained on): the 6 survey-2 windows on the two surfaces that
  were never scored (072318733 r55_c85 r95_c10 r100_c95; 073911423 r60_c45 r65_c85 r105_c85) + 4 NEW windows, one each
  on 025522741, 034621782, 065120760, 071903158. None chosen by response.
- NEW-window rule (deterministic, blind to any model response): on the surface's cell grid, candidate origins (r0, c0) on
  a 5-cell lattice; a candidate needs >= 1440 of its 1600 cells inside the survey band (x != -1 and 1904 < z < 5709) and
  must not overlap any existing survey window or an already placed new window (|dr| >= 40 or |dc| >= 40); take the
  candidate with the most band cells, ties to the smaller (r0, c0). The first placed window on a surface is the training
  window; on the four designated surfaces the second is the held-out window.
- Candidate regions for T3 (6, never trained on): the six 15 mm zoom regions in `p0846a_zoom/` (r35_c65, r30_c105,
  r105_c25, r50_c70, r75_c45, r50_c40), re-rendered with the same recipe.
- Negative labels: inklabels = 0 everywhere; supervision mask = rendered pixels (max over the 21 slices > 0) eroded by
  8 px, replicated through the 21 planes (the ft343 writer). Only the ON-SHEET cut-out is used for training; off-sheet
  slabs are test inputs only, so T2's off-sheet numbers are not something the model was trained on directly.

### 3c. Caveat, stated up front: "negatives" may contain ink

There is no proof that any 0846A window is blank. If a training window holds faint real ink, the model is taught to call
exactly that "no ink". Direction of the bias: it makes G2 (less off-sheet firing) easier and G3 (a candidate standing
out) harder, and it can make a real-ink region look like papyrus after training. So a PASS here means "the over-firing
is a texture effect the model can unlearn without losing known text"; a FAIL on G3 alone does NOT show the candidates are
blank, because the same texture that was trained away might carry the ink. Mitigations: candidates and their surfaces
are excluded, picked windows are excluded, the lowest-response windows are used, and the held-out and candidate regions
are never trained on. The mitigation is partial and is reported as such.

## 4. Held-out tests (fixed now; baselines measured first with the same code as the after-numbers)

Inference for every test: the package's flat inference on the 21-slice input, overlap 0.5, hann blending, both directions
(forward = as rendered, reverse = flipped depth order), on the T4, batch 32. Ink share = fraction of valid pixels with
p > 0.5, valid = pixels rendered on the ON-SHEET cut-out (max over slices > 0), the same pixel set for the two off-sheet
slabs of that window. Every number is computed for the original checkpoint (before) and the fine-tuned final checkpoint
(after) by the same function in the same run.

- T1 known text: pixel AUC (rank-based, Mann-Whitney) of the forward map against inklabels > 0 over the validation-mask
  pixels of each of the 3 validation crops (pixels with a zero input at the middle slice removed). Also reported, not
  gated: the reverse-order AUC, the ink share on labelled ink pixels (recall at 0.5) and on labelled non-ink pixels.
  Reference: the 9 um check's 0.849 on w016 came from a native 9.362 um render, a different input path; the number to
  compare with is this run's own baseline.
- T2 over-firing on 10 held-out ordinary 0846A windows: on-sheet share (mean of forward and reverse) and off-sheet share
  (mean of the 4 values: slabs A and B x forward and reverse), per window, before and after. Reference baseline from
  NINE_UM_CHECK.md: 15-48 % on, 7-36 % off (measured there on the candidates).
- T3 candidate regions: the same on-sheet and off-sheet shares on the 6 zoom regions, plus the ratio
  on / max(off, 0.005) (0.5 % floor so an all-zero map cannot pass by division), before and after.

## 5. Gates (pre-registered; PASS needs all three)

- G1: median over the 3 validation crops of T1 forward AUC (final checkpoint) >= 0.83.
- G2: median over the 10 held-out windows of (off-sheet share after / off-sheet share before) < 1/3.
- G3: at least one of the 6 candidate regions has, after, on-sheet share >= 2 % AND on / max(off, 0.005) > 3.
FAIL otherwise. Both the numbers and the verdict are reported; a gate that cannot be computed (missing input, crashed
stage) is reported as NOT RUN, not as a pass. If the harness blocks (data format, quota), stop and report.

Configurations (two at most today), run in order:
- (i) head-only: `FREEZE=head` (the ft343 wrapper: only the 1-channel output convolutions train; on this model that is
  the ink task head plus the depth-attention logits, 50 of 34.5 M parameters), LR 1e-3, warm-up 200, cosine,
  bce_label_smoothing 0.5 (the checkpoint's own recipe, kept so the > 0.5 threshold means the same before and after),
  batch 32, 1.5 h of training on one T4. Expected: cannot collapse T1 (AUC is rank-based and a head this small mostly
  recalibrates); may or may not move G2; passing G3 through recalibration alone would be surprising.
- (ii) full fine-tune: all parameters, LR 1e-4 (a hundredth of the pretraining peak), warm-up 200, cosine,
  bce_label_smoothing 0.5, batch 32, 2 h on one T4. Run only if (i) leaves T1 median AUC >= 0.83.
Same datasets, same seed (42), same evaluation code for both.

## 6. Sanity checks that must be seen in the logs before a number is believed (L38, L44, L41)

- Data: per-segment table of shape, valid fraction, supervised fraction, ink fraction (text crops 10-40 % of supervised
  pixels expected; negatives exactly 0). The kernel refuses to train if any negative has an ink pixel or any text crop
  has none.
- Loss headroom with smoothing 0.5: perfect predictor 0.562 nats; best constant at overall ink fraction f: 0.593 (f 6 %),
  0.611 (10 %), 0.619 (12 %), 0.631 (15 %). The kernel prints f and both numbers, and the train loss must drop below
  the constant's value within the first 500 steps; if it sits at the constant, the run is reported as collapsed.
- Checkpoint: strict load 0 missing / 0 unexpected keys; the before-maps of the original checkpoint must reproduce the
  9 um check's w016 behaviour qualitatively (forward AUC well above reverse).
- Fallbacks are counted and printed; a stage that fell back on every input is a failure.

## 7. Outputs

- `evidence_0912/PLAN_A_RESULT.md`: recipe, baselines, before/after table per test, gate verdict, caveats.
- Pictures `evidence_0912/plan_a_*.png`: before/after maps on candidates r105_c25 and r30_c105 (the two that stood out
  most in the 9 um check) and on the w016 validation crop.
- Checkpoints: Kaggle output `a0846_head_final.pth` / `a0846_full_final.pth`, copied to leverckpts/`
  under the same names. Datasets `squiffymccat/a0846-text9um` and `squiffymccat/a0846-neg9um` (private).
- Everything in this file is fixed; anything changed after data was seen is listed in PLAN_A_RESULT.md under
  "deviations from the pre-registration" with the reason.
