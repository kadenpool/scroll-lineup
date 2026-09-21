# Plan C: the adapted 9 um model over every PHerc0846A survey window ("keep 0846A warm")

Status: COMPLETE 13 Sep 04:57 AEST (kernel finished 04:41 AEST; every number below is from `plan_c_files/results.json`,
tables printed by `plan_c_files/plan_c_report.py` into `plan_c_files/report_tables.md`). Running log at the bottom.
Private: nothing public, no spending; box A renders + squiffymccat private dataset/kernel only.

## 1. Question and rule (fixed before any result was seen)

Plan A's run (ii) checkpoint (`a0846_full_final.pth`: ink_9um seed42 step-010000 fine-tuned with 0846A papyrus labelled "no ink")
calls almost nothing "ink" on 0846A: on the ten held-out ordinary windows it gave 0.0-2.2 % on-sheet and about 0 off-sheet, and
none of the six candidate regions reached Plan A's G3 gate (>= 2 % on-sheet with on/off > 3). Plan C runs that checkpoint,
and the original checkpoint, over EVERY 0846A survey window rendered at 9.362 um, and asks: does any window anywhere on the
grown surfaces stand out the way a candidate would have to? Flag rule (Plan A's G3, applied window by window): adapted
on-sheet ink share >= 2 % AND on / max(off, 0.5 %) >= 3, measured on the eroded valid mask (rendered pixels eroded 8 px).

## 2. Recipe (what was actually run)

- Windows: all 105 survey windows of the grown 0846A surfaces (18 of pass 1 + 87 of pass 2, including the 57 "rest" windows
  the 2 um survey is still running tonight), plus Plan A's 4 new held-out windows and its 6 candidate zoom regions (the
  T2/T3 consistency check): 115 renders. Of the survey windows, 14 were Plan A training negatives (flagged in the tables).
- Render: the 9 um check's recipe unchanged (`n9/render_one.sh`: eligible volume
  `20250728152254-9.362um-1.2m-113keV-masked.zarr`, `vc_render_tifxyz --auto-crop --scale 1 -g 0 --num-slices 101 --slice-step 1
  --flip-normals`), cut with Plan A's `cut_slabs.py` into on-sheet layers [40,61), off-sheet A [0,21), off-sheet B [80,101).
  Hand test first (L44): window 072318733_r95_c10 re-rendered and cut reproduces Plan A's `cut_info.json` digit for digit
  (valid fraction 0.9002479734289691; slab means 96.55 / 98.40 / 92.49), so the renders are the same data Plan A saw.
- Inference: Plan A's harness code verbatim (villa 777cb16 flat inference, overlap 0.5, hann blending, both depth
  directions, T4 x2, batch 16) inside `plan_c_files/c0846.py`; the adapted checkpoint is checked by md5 against the kernel
  output (`40d7e0f0b4af24a44b294760a206dabe`) and both checkpoints must load with 0 missing / 0 unexpected keys.
  Hand test of the harness (box A CPU, `dry_run.sh`, same code path): on the T2 window 072318733_r95_c10 it gives adapted
  on-sheet 2.22 % (fwd 4.43 / rev 0.00), off 0.00 %, original on-sheet 20.63 %, off 15.26 %; Plan A's Kaggle numbers were
  2.21 / 4.43 / 0.00 / 0.00 and 20.62 / 15.25 (worst difference 0.0001 over 8 values). So the render, the cut, the
  inference and the scoring all reproduce Plan A before the whole-scroll run was launched.
- Measures per window and checkpoint: ink share (p > 0.5) on the eroded valid mask for on / offA / offB in both directions;
  on = mean of the two directions, off = mean of the four off-sheet values, ratio = on / max(off, 0.005). The same numbers on
  Plan A's plain valid mask are kept for the consistency check (Plan A's T2/T3 numbers must reproduce within fp16 noise).
- Results are written to results.json after every batch of 20 windows; the raw maps (uint8, six per window and checkpoint)
  are saved so any picture or re-scored metric is a local recompute (L60).

## 3. Results (115 windows, both checkpoints, kernel status ok, 2.48 h on 2x T4)

**Short answer: no window stands out. The adapted model's response over the whole surveyed scroll is a smooth tail, not a
cluster: median 0.13 % on-sheet over the 109 ordinary windows, 90th percentile 2.35 %, maximum 7.8 %. Eleven windows (10 %)
pass the Plan A G3-style flag (>= 2 % on-sheet, on/off >= 3), so that rule is a top-decile cut on ordinary papyrus, not a
"candidate stands out" test. None of the six candidate zoom regions passes (best 1.9 %); thirteen ordinary survey windows
sit above them. The maps in every flagged window are rounded blobs in one depth direction, not strokes or rows.**

Numbers first:

- Windows: 115 = 105 survey (18 pass 1 + 87 pass 2) + 4 Plan A new held-out + 6 zoom regions; all 115 rendered (valid
  fraction 0.80-0.95), all 115 scored by both checkpoints; 0 fallbacks, 0 dropped.
- Adapted checkpoint, on-sheet share (eroded mask) over the 109 ordinary windows: median 0.13 %, p90 2.35 %, max 7.8 %,
  13 windows >= 2 %. Leaving out the 14 windows it was trained on (95 left): median 0.26 %, p90 2.53 %, max 7.8 %.
  The 14 trained-on windows: median 0.01 %, max 0.60 % (as expected: it was taught they are blank).
- Original checkpoint over the same ordinary windows: median 24.0 %, p90 34.5 %, range 9.1-44.6 % (the known over-firing).
- The six zoom candidates, adapted on-sheet: r105_c25 1.87 %, r75_c45 1.82 %, r50_c70 1.11 %, r35_c65 0.74 %, r30_c105 0.04 %,
  r50_c40 0.00 % (ranks 15, 16, 25, 30, 79, 89 of 115). None >= 2 %.
- Flag rule (adapted on >= 2 % AND on / max(off, 0.5 %) >= 3, eroded mask): **11 of 115 pass**: 034621782_r50_c45 (7.8 %, ratio
  15.6), 101354117_r65_c45 (6.5 %, 13.0), 061936267_r40_c15 (5.9 %, 11.8; a "picked" 2 um spot), 080147148_r100_c100 (5.3 %, 10.5;
  the window the 2 um textlike scorer put at the top tonight), 040822053_r105_c105 (5.3 %, 9.8), 034621782_r40_c85 (3.8 %, 5.4;
  picked), 075517838_r5_c95 (3.5 %, 5.2), 113803923_r35_c20 (2.6 %, 5.1), 040822053_r50_c70 (2.5 %, 5.1), 072318733_r95_c10
  (2.3 %, 4.6; Plan A's 2.2 % held-out window), 034621782_r5_c45 (2.0 %, 4.0; Plan A held-out). Two more windows are above 2 %
  but fail the ratio because their off-sheet slabs also fire (094059720_r90_c75 3.2 %, 101729488_r105_c105 2.5 %).
- Every flagged window is one-sided: the weaker depth direction carries 0-42 % of the stronger one (e.g. #1 2.4 % forward /
  13.2 % reverse, #3 11.5 / 0.2). Real ink is often one-sided, but so was a third of blank-papyrus windows in the 12 Sep
  calibration (L51), so this is not a discriminator on its own.
- Agreement with the 2 um survey (56 windows have a 2 um result): rank correlation 0.5 between the 2 um ink share and the
  adapted 9 um share; 4 of the 11 windows with a 2 um share >= 30 % are >= 2 % here, against 3 of 45 below 30 %. Of the seven
  windows ever "picked" as strong 2 um spots, two are in the flagged eleven (ranks 3 and 6); the other five rank 22-88.
- The adapted response is still partly the original's texture response scaled down: correlation 0.55 between the two
  checkpoints' on-sheet shares over the 115 windows; the top original responders (061936267_r40_c15 44.6 %, 040822053_r105_c105
  44.5 %, 075517838_r5_c95 42.0 %, 034621782_r50_c45 39.6 %) are four of the top seven adapted ones.
- Surfaces: the eleven flags sit on eight surfaces; 034621782 has three (of its four windows) and 040822053 two (of three).
- Eroded versus plain valid mask: adapted on-sheet shares differ by at most 0.27 % (points), so the mask choice changes nothing.

### Ranked table: top 20 by adapted on-sheet ink share (percent; eroded mask; on and off = mean of the two depth directions; 2 um C/D = the 2 um survey's ink share in rendered / reversed order where it exists; "PICKED" = ever picked as a strong 2 um spot)

| # | window | source | Plan A role | 2 um C/D | adapted on (fwd/rev) | adapted offA | adapted offB | adapted on/off | flag | original on | original offA | original offB | original on/off |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 034621782_r50_c45 | survey2 | pool, dropped (never trained on) | 18/26 | 7.8 (2.4/13.2) | 0.0 | 0.0 | 15.6 | YES | 39.6 | 16.4 | 20.2 | 2.2 |
| 2 | 101354117_r65_c45 | survey2 | none | - | 6.5 (10.6/2.4) | 0.1 | 0.7 | 13.0 | YES | 38.2 | 16.8 | 17.4 | 2.2 |
| 3 | 061936267_r40_c15 | survey2 | none, PICKED | 24/44 | 5.9 (11.5/0.2) | 0.4 | 0.5 | 11.8 | YES | 44.6 | 19.4 | 24.6 | 2.0 |
| 4 | 080147148_r100_c100 | survey2 | none | 40/25 | 5.3 (1.8/8.8) | 0.0 | 0.2 | 10.5 | YES | 34.0 | 11.2 | 11.3 | 3.0 |
| 5 | 040822053_r105_c105 | survey2 | none | 28/18 | 5.3 (3.1/7.4) | 0.2 | 0.9 | 9.8 | YES | 44.5 | 19.0 | 25.0 | 2.0 |
| 6 | 034621782_r40_c85 | survey2 | none, PICKED | 33/24 | 3.8 (1.5/6.2) | 1.2 | 0.2 | 5.4 | YES | 34.4 | 20.4 | 18.0 | 1.8 |
| 7 | 075517838_r5_c95 | survey2 | none | - | 3.5 (5.6/1.4) | 1.3 | 0.0 | 5.2 | YES | 42.0 | 29.7 | 27.3 | 1.5 |
| 8 | 094059720_r90_c75 | survey2 | none | - | 3.2 (5.9/0.4) | 2.6 | 0.8 | 1.8 | - | 33.0 | 28.0 | 20.0 | 1.4 |
| 9 | 113803923_r35_c20 | survey2 | none | - | 2.6 (4.5/0.7) | 0.0 | 0.8 | 5.1 | YES | 25.3 | 12.3 | 17.2 | 1.7 |
| 10 | 040822053_r50_c70 | survey2 | none | 28/9 | 2.5 (0.5/4.6) | 0.3 | 0.0 | 5.1 | YES | 31.3 | 34.2 | 27.8 | 1.0 |
| 11 | 101729488_r105_c105 | survey2 | none | - | 2.5 (0.0/5.1) | 1.7 | 6.3 | 0.6 | - | 28.0 | 13.2 | 19.7 | 1.7 |
| 12 | 072318733_r95_c10 | survey2 | held-out | 12/37 | 2.3 (4.6/0.0) | 0.0 | 0.0 | 4.6 | YES | 19.9 | 14.9 | 13.7 | 1.4 |
| 13 | 034621782_r5_c45 | Plan A new | held-out | - | 2.0 (0.4/3.6) | 0.4 | 0.0 | 4.0 | YES | 29.2 | 13.7 | 13.4 | 2.2 |
| 14 | 025619069_r105_c25 | survey1 | none (candidate surface) | 27/14 | 1.9 (0.0/3.9) | 0.3 | 0.0 | 3.9 | - | 31.2 | 17.5 | 19.4 | 1.7 |
| 15 | zoom_r105_c25 | zoom | candidate | - | 1.9 (0.1/3.7) | 0.2 | 0.1 | 3.7 | - | 27.7 | 15.3 | 15.9 | 1.8 |
| 16 | zoom_r75_c45 | zoom | candidate | - | 1.9 (3.7/0.0) | 0.4 | 0.3 | 3.7 | - | 25.6 | 16.7 | 16.7 | 1.5 |
| 17 | 091538569_r60_c105 | survey2 | none | - | 1.8 (0.5/3.2) | 0.1 | 0.0 | 3.7 | - | 24.0 | 15.9 | 16.6 | 1.5 |
| 18 | 101354117_r75_c5 | survey2 | none | - | 1.7 (2.3/1.2) | 1.9 | 3.3 | 0.7 | - | 39.5 | 25.1 | 33.6 | 1.3 |
| 19 | 110152015_r25_c30 | survey2 | none | - | 1.7 (3.3/0.1) | 0.8 | 0.6 | 2.5 | - | 31.8 | 16.5 | 17.6 | 1.9 |
| 20 | 094059720_r5_c50 | survey2 | none | - | 1.7 (3.0/0.3) | 0.8 | 0.7 | 2.2 | - | 34.5 | 31.9 | 31.2 | 1.1 |

The full 115-row ranking is `plan_c_files/plan_c_ranking.json`; per-window, per-slab, per-direction numbers on both masks are in
`plan_c_files/results.json` ("windows"); the raw maps are on box A (`kag_out/c0846_9um/c0846_maps/<window>__<checkpoint>.npz`).

## 4. Consistency check against Plan A

The 16 Plan A T2/T3 windows were re-rendered and re-scored inside this run and compared with Plan A's Kaggle numbers on
Plan A's own (plain) valid mask: 128 values (on / off / on-forward / on-reverse, both checkpoints, 16 windows), **worst
absolute difference 0.000005 (5e-6), tolerance 0.005: PASS.** Examples: 072318733_r95_c10 adapted on 2.21 % (Plan A 2.21),
original on 20.63 % (20.62); zoom_r105_c25 adapted on 1.83 % (1.83), original 28.12 % (28.12); zoom_r30_c105 original 32.03 %
(32.04). Rendered pixel counts match exactly (577,600 for every 801 x 801 window). The box A CPU dry run of the same harness
had already matched to 1e-4 (section 2), so the Kaggle numbers are the same computation Plan A made, extended to all windows.

## 5. Pictures (top 6 by adapted on-sheet share)

`plan_c_files/plan_c_rank01_034621782_r50_c45.png` ... `plan_c_rank06_034621782_r40_c85.png`. Each row: CT on-sheet
(render layer 50) | original on-sheet forward | original on-sheet reverse | original off-sheet A forward | adapted on-sheet
forward | adapted on-sheet reverse | adapted off-sheet A forward | adapted off-sheet B forward; maps shown with the model
card's display window (p 0.25 black to 0.75 white); the ink share of that panel is in its label. What they show: the original
maps are the familiar wall-to-wall blotch on and off the sheet; the adapted maps are a few rounded patches (0.3-1 mm) in one
depth direction with a dark off-sheet, and none of the six shows stroke-like shapes, rows or a text-like spacing. The kernel
also wrote rank 7-8 pictures (`kag_out/c0846_9um/plan_c_rank07_*.png`, `rank08_*.png` on box A).

## 6. Honest reading

The adapted checkpoint does what Plan A said it does: near-zero background everywhere on 0846A (median 0.1-0.3 % on-sheet,
essentially nothing off-sheet), with a thin tail of windows at 2-8 %. That tail is real in the sense that it reproduces
exactly and is one-sided in depth, and it overlaps the 2 um survey's stronger windows more than chance (rank correlation
0.5; 4 of 11 strong 2 um windows against 3 of 45 weak ones), so the two models are still seeing the same features of the
papyrus. But nothing separates: the six candidate regions fall inside the ordinary tail (best 1.9 %, below thirteen ordinary
windows), the flag rule passes 10 % of ordinary windows, the top responders are largely the original checkpoint's top
responders scaled down (correlation 0.55), and every top map is blobs, not letters. The right description is "the adapted
model's residual response to 0846A texture ranks the surveyed windows; the highest are 034621782_r50_c45, 101354117_r65_c45,
061936267_r40_c15, 080147148_r100_c100 and 040822053_r105_c105", not "five new candidates". What this cannot say: whether
faint ink hides inside that tail; a negative-only adaptation makes exactly this failure invisible (Plan A section 7). If
anything on 0846A deserves eyes next, it is the three windows where two independent models agree most (061936267_r40_c15,
034621782_r40_c85, 080147148_r100_c100), looked at as CT + both maps at full resolution, not as more ink-share numbers.

## 7. Files

- `plan_c_files/`: `results.json` + `kernel.log` (the run), `plan_c_ranking.json`, `report_tables.md`, `plan_c_rank01..06_*.png`,
  `plan_windows.json`; `plan_c_windows.py` (window plan), `render_c.sh` (box A render/cut/tar loop), `c0846.py` (Kaggle harness,
  assembled by `assemble.py` from Plan A's `a0846.py` + `c0846_new.py`), `dry_run.sh` (box A CPU hand test of the harness),
  `make_nb_c.py` / `push_kernel_c.sh` / `upload_ds_c.sh` / `poll_c.sh` / `kstat_c.py` (Kaggle plumbing, squiffymccat only),
  `plan_a_ref.json` (Plan A's per-window T2/T3 numbers), `plan_c_report.py` (tables from results.json).
- box A: `<run-dir>/c0846/` (plan_windows.json, kds/ tars, seg/ cut slabs, logs/).
- Kaggle (private): dataset `squiffymccat/c0846-9um`, kernel `squiffymccat/vesuvius-c0846-9um`.

## 8. Running log (AEST, from `date`)

- 01:01 started; read OVERNIGHT_0913, PLAN_A_RESULT/PREREG, NINE_UM_CHECK 1-3, HANDOFF tail, lessons L44-L69.
- 01:04 hand-test render of 072318733_r95_c10: identical to Plan A's cut_info (see section 2); full render of 115 windows
  launched on box A, 2 nice'd workers, 15 GB disk guard.
- 01:20 harness c0846.py assembled and compiled; box A CPU dry run of the harness (1 window, both checkpoints) launched.
  Trap found on the way: `<run-dir>/coverage.py` shadows the `coverage` module when python runs with that cwd on
  sys.path and executes a registration job at import time (lesson L70).
- 02:11 dataset ready (16:10Z) and kernel squiffymccat/vesuvius-c0846-9um v1 pushed (16:11Z); poller running on box A.
- 02:00 renders complete: 115/115, 0 failures, valid fraction 0.80-0.95, 4.1 GB of tars.
- 02:10 dataset squiffymccat/c0846-9um ready (Kaggle auto-extracted the tars to <name>/<name>/); 02:11 kernel
  squiffymccat/vesuvius-c0846-9um v1 pushed (2x T4); one poller, 5 min.
- 04:41 kernel complete (2.48 h: env 1.3 min, unpack 3 min, checkpoints 0.6 min, inference 144 min = 6 batches x 2
  checkpoints, report 8 s); 04:53 outputs fetched to box A kag_out/c0846_9um (266 files incl. 230 raw-map npz);
  tables + top-6 pictures made on box A (postproc_c.sh); copied to plan_c_files/.
- 04:57 this report written; files committed (no push).
