# Plan A result: teaching ink_9um that PHerc0846A papyrus is "no ink"

Pre-registration: `PLAN_A_PREREG.md` (written 16:29 AEST, before any data was built). Everything below was produced
after it; deviations are listed in section 6. Status line and gate verdict: see section 5.

## 1. What was done (recipe, in plain words)

- The model: the challenge's 9 um ink detector, checkpoint `hybrid_3d2d-seed42/step-010000` (the best-transfer
  checkpoint of the August benchmark; the one that scored AUC 0.85 on known text in our 9 um check).
- The idea: keep training it on its own public labelled data (real ink, four scrolls) PLUS windows of PHerc0846A papyrus
  labelled "no ink anywhere", so it learns that 0846A's texture is not ink while keeping its ability to read real ink.
- Training code: villa's own `vesuvius.ink_detection` (commit 777cb16), driven by our Kaggle harness
  (`plan_a_files/a0846.py`, built from `scratch_ft343/ft343.py`). Same optimiser and loss as the checkpoint's own recipe
  (SGD momentum 0.99 nesterov, cosine warm-up, BCE with label smoothing 0.5 + Dice 0.25, fp16, batch 32, uniform patch
  sampling). Two configurations: (i) head-only = only the last 1-channel layers train (50 of 34.5 M parameters),
  LR 1e-3, 1.5 h on one T4; (ii) full fine-tune, LR 1e-4, 2 h.
- Known-text data (`squiffymccat/a0846-text9um`, private): ink_9um's own published labels (HF bucket
  `scrollprize/datasets/ink_9um`), with the 21-slice inputs rebuilt exactly as ink_9um's `prepare_9um_isotropic_input`
  does (public 2.399 um surface volume, pyramid level 2, centred 84 planes averaged 4-to-1). Twelve training crops of
  2048 x 2048 px (one per segment: PHerc0139 w017 w029 w040 w043, PHerc1667 w013 w018 w028 w031, PHercParis4 w01 w03
  w06 w09), placed where each segment has the most ink. Three validation crops around the published validation masks
  (pherc0139-w016, pherc0814-46527, pherc1667-w029), never trained on.
- 0846A data (`squiffymccat/a0846-neg9um`, private): 7.5 mm survey-style windows of the grown 0846A surfaces, rendered
  from the eligible 9.362 um volume with the 9 um check's exact recipe (101 slices, `--flip-normals`), cut into the
  same 21-slice windows: on-sheet layers [40,61), off-sheet [0,21) and [80,101) (40 voxels = 0.37 mm either side).
  - training pool: 24 windows on the 8 surfaces that hold no candidate (17 never-picked survey windows + 7 new ones cut
    by a blind rule); inside the kernel the 20 with the lowest baseline on-sheet response are kept, 4 dropped;
  - held-out ordinary windows (T2): 10, never trained on (6 unscored survey-2 windows on two surfaces the model never
    sees in training + 4 new windows on training surfaces at other positions);
  - candidate regions (T3): the six 15 mm zoom regions, never trained on;
  - excluded from training everywhere: the six candidate surfaces and every window ever picked as a strong 2 um spot.
- Tests, computed by the same code before (original checkpoint) and after (fine-tuned final checkpoint):
  T1 pixel AUC on the validation crops (forward order); T2 ink share > 0.5 on-sheet and off-sheet on the 10 held-out
  windows; T3 the same plus the on/off ratio on the six candidates. Gates: G1 median T1 AUC >= 0.83; G2 median
  off-sheet share after/before < 1/3; G3 one candidate with on-sheet share >= 2 % and on/off > 3.

## 2. Data actually built (from `plan_a_files/data_meta/`)

Known text (crop = the part fed to the model; "supervised" = pixels with a published label; ink = share of those):

| segment | role | crop (px) | supervised % of crop | ink % of supervised | validation px |
|---|---|---|---|---|---|
| pherc0139-w016 | validation | 896 x 2432 | 23.0 | 23.3 | 178,146 (23.2 % ink) |
| pherc0814-46527 | validation | 722 x 896 | 29.3 | 35.4 | 160,899 (37.3 % ink) |
| pherc1667-w029 | validation | 2432 x 2688 | 2.3 | 36.9 | 382,351 (23.0 % ink) |
| pherc0139-w017 | train | 2048 x 2048 | 18.1 | 31.1 | |
| pherc0139-w029 | train | 2048 x 2048 | 8.0 | 26.7 | |
| pherc0139-w040 | train | 2048 x 2048 | 13.2 | 47.3 | |
| pherc0139-w043 | train | 2048 x 2048 | 6.2 | 43.7 | |
| pherc1667-w013 | train | 2048 x 2048 | 29.4 | 31.5 | |
| pherc1667-w018 | train | 2048 x 2048 | 38.6 | 25.7 | |
| pherc1667-w028 | train | 2048 x 2048 | 9.4 | 26.6 | |
| pherc1667-w031 | train | 2048 x 2048 | 28.1 | 22.9 | |
| phercparis4-w01 | train | 2048 x 2048 | 39.8 | 24.7 | |
| phercparis4-w03 | train | 2048 x 2048 | 29.4 | 36.7 | |
| phercparis4-w06 | train | 2048 x 2048 | 37.1 | 32.0 | |
| phercparis4-w09 | train | 2048 x 2048 | 32.6 | 32.8 | |

The w016 validation region has exactly the 178,146 pixels the 9 um check used, so T1 on w016 is the same test as before,
on the aligned input instead of a native 9.362 um render.

0846A windows: 801 x 801 px at 9.362 um (7.5 mm), rendered fraction 0.82-0.90 (the mesh's own outline); zoom regions
1301-1601 px, rendered fraction 0.93-0.95. Two of the new windows rendered empty and were replaced (section 6).

## 3. Baseline of the original checkpoint (measured by the same code, Kaggle T4; kernel squiffymccat/vesuvius-a0846-head)

T1 pixel AUC (forward order): pherc0139-w016 0.893, pherc0814-46527 0.884, pherc1667-w029 0.845 (median 0.884).
T2 (10 held-out ordinary 0846A windows, ink share > 0.5): on-sheet 0.10-0.30, off-sheet 0.10-0.23 (the over-firing).
T3 (six candidate regions): on-sheet 0.22-0.32, off-sheet 0.15-0.29.

## 4. Before / after, run (i) head-only (50 parameters, LR 1e-3, 1.5 h)

| test | before | after (final checkpoint) |
|---|---|---|
| T1 AUC w016 / 0814 / 1667 | 0.893 / 0.884 / 0.845 | 0.894 / 0.882 / 0.851 (median 0.882) |
| T1 recall at 0.5 | 0.73 / 0.79 / 0.61 | 0.39 / 0.51 / 0.39 (the model became far more conservative) |
| T2 off-sheet share, ratio after/before | 1 | 0.09-0.21 on all 10 windows (median about 0.17) |
| T2 on-sheet share | 0.10-0.30 | 0.01-0.05 |
| T3 candidates, on / off after | | r35_c65 0.050 / 0.023 (2.2x); r30_c105 0.058 / 0.032 (1.8x); r105_c25 0.064 / 0.022 (2.9x); r50_c70 0.063 / 0.051 (1.2x); r75_c45 0.053 / 0.026 (2.0x); r50_c40 0.032 / 0.021 (1.5x) |

Reading: the head-only run recalibrated the model (it now calls far less "ink" everywhere, 0846A on-sheet and off-sheet alike,
and real text recall halves while AUC holds). No candidate separates from its own off-sheet null.

## 5. Gate verdict, run (i)

G1 PASS (median AUC 0.882 >= 0.83). G2 PASS (off-sheet ratio 0.17 < 1/3). G3 FAIL (best on/off ratio 2.9 on r105_c25, below 3;
on-sheet 6.4 % >= 2 %). **VERDICT: FAIL for run (i).** By the pre-registration, run (ii) (full fine-tune, LR 1e-4) is
launched because run (i) did not collapse T1: kernel squiffymccat/vesuvius-a0846-full, pushed 12 Sep 21:20 AEST. Its verdict
decides Plan A.

Harness note: the "after" stage's extra evaluation of the best-validation checkpoint hit a KeyError (t2 map key) after the
final-checkpoint numbers were computed; the gates used the final checkpoint. Status "partial" refers to that extra evaluation.
The agent that ran this was cut off by a session limit before writing sections 3-5; they were filled in by the main session
from kag_out/a0846_head/results.json and kernel.log.

## 6. Deviations from the pre-registration (all before any model was trained)

See `plan_a_files/DEVIATIONS.md` for the timed log. In short:

1. The blind new-window rule found fewer admissible spots than planned: the two missing held-out windows were filled on
   other eligible surfaces with the survey's own 75 % coverage threshold (both have 100 % coverage anyway). Pool 24, not 25.
2. Text crop placement uses the compressed label bytes from the bucket listing as the "most ink" measure (HF rate-limits
   per-chunk fetches); the exact ink pixel count of every chosen crop is in the table above.
3. Two new windows on surface 071903158 rendered empty (outside the masked volume). No non-empty admissible spot exists
   on that surface, so the replacements went to 024106966 (r110_c75, training pool) and 032347463 (r5_c85, held-out),
   by the same blind rule. The harness now refuses any window with < 50 % rendered pixels.
4. Kernel (i) v1 failed before touching the model (Kaggle auto-extracts uploaded tar files; the harness expected tars).
   Fixed; nothing about the experiment changed.

## 7. Honest caveats

- "Negatives" may hold faint real ink (prereg 3c). A PASS would mean the over-firing is a texture effect the model can
  unlearn; a FAIL on G3 alone does not prove the candidates are blank.
- The uniform patch sampler draws roughly four 0846A patches per known-text patch (published supervision covers only
  6-40 % of each text crop); per pixel the supervised ink fraction is about 13-16 %, which leaves only ~0.06 nats between
  a perfect model and a constant output under label smoothing 0.5 (the L38 trap). The kernel checks the train loss
  against that constant.
- Inference on Kaggle runs on the T4 in the package's default precision; the 9 um check ran CPU fp32. The before-numbers
  here are re-measured with the Kaggle setup, so before/after are comparable to each other, not bit-identical to the
  9 um check.
- Head-only (i) trains 50 parameters and can mostly recalibrate; (ii) is the substantive test.

## 8. Before / after, run (ii) full fine-tune (all 34.5 M parameters, LR 1e-4, 9000 iterations, 2 h 12 min on two T4s)

Kernel squiffymccat/vesuvius-a0846-full, complete 12 Sep 23:35 AEST. Files: `plan_a_files/run_ii/` (results.json, kernel.log,
pictures for w016, r105_c25, r30_c105). Same harness KeyError in the best-validation extra evaluation; gates use the final checkpoint.

| test | before | after (final checkpoint) |
|---|---|---|
| T1 AUC w016 / 0814 / 1667 | 0.893 / 0.884 / 0.845 | 0.908 / 0.876 / 0.837 (median 0.876) |
| T1 recall at 0.5 | 0.73 / 0.79 / 0.61 | 0.68 / 0.64 / 0.57 |
| T2 on-sheet share, 10 held-out ordinary windows | 0.10-0.30 | 0.000-0.022 (median 0.003) |
| T2 off-sheet share | 0.10-0.26 | 0.000-0.002 (ratio after/before about 0) |
| T3 candidates, on / off after | | r35_c65 0.007 / 0.000; r30_c105 0.000 / 0.000; r105_c25 0.018 / 0.002; r50_c70 0.011 / 0.004; r75_c45 0.018 / 0.003; r50_c40 0.000 / 0.000 |

Train loss ran below the constant-output floor (minimum 0.532 vs 0.634), so the model learned rather than collapsed (the L38 check).

## 9. Gate verdict, run (ii), and the Plan A verdict

G1 PASS (0.876 >= 0.83). G2 PASS (off-sheet share essentially zero). G3 FAIL: no candidate reaches 2 % on-sheet; the best two
(r105_c25, r75_c45) are at 1.8 %, and an ordinary held-out window (072318733_r95_c10) is at 2.2 %. **VERDICT: FAIL. Plan A is
closed by its pre-registration** (run (i) FAIL, run (ii) FAIL). Reading: once the model learns that 0846A papyrus is not ink, it
calls almost nothing ink on 0846A, and the candidate regions do not stand out from ordinary windows. This does not prove the
candidates are blank (section 7); it says this model, adapted this way, cannot find letters there.

What stays warm for 0846A: the adapted checkpoint is a cleaner survey tool (near-zero background); running it over every 0846A
9 um render and looking for any region at or above 2 % on-sheet with a clean off-sheet is cheap (inference only) and is the
next 0846A item if Plan B leaves GPU time. Next by Kaden's rule ("if A doesn't work then go to B"): PHerc0813.
