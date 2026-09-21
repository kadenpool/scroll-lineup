# The official "looks like letters" scorer: can it tell writing from our ink-map blobs?

Written Sat 12 Sep 2026 by a sub-agent (started 01:03 AEST, finished 05:31 AEST, both from `date`). Private: nothing
posted, pushed or shared, no Kaggle. All compute ran on box B (CPU) in `<work-dir>/scorer32/`. Box A was only read.

Pictures in this folder:
- `scorer_overlays.png`: what the scorer marks on known pages.
- `scorer_calibration_dots.png`: every window's score, by type, including ours.

## 1. Short answer

**Verdict: NO for our maps. It tells writing from blobs only on big pages, and our maps are too small for it.**

1. **On whole pages it works as a writing detector.** We used the challenge's own PHerc0139 ink maps: three whole
   segments, about 6 x 7 cm each. It marked 25% of a typical known-text window and 0% of every blank window. When the
   same ink was rearranged, its score fell hard:
   - blobs shuffled: -65% (the original scored higher in 31 of the 33 windows whose score changed)
   - page turned 90 degrees: -96% (33 of 34)
2. **On a 7.5 mm window, the size of our maps, it can't tell text from shuffled blobs.** We cut the same windows out
   and scored them alone. 38% of known-text windows then scored exactly 0. Known text beat shuffled blobs only at
   AUC 0.60, where 0.5 is a coin flip. So a score for one of our maps is not evidence either way. As the brief says,
   we stop there.
3. **Our maps (for the record only, not evidence).** They were scored in the same batch. 233 of 252 windows scored 0,
   19 scored above 0, and the highest was 0.22. At the same size, 62% of known-text windows and 52% of shuffled-blob
   windows scored above 0, so these numbers say nothing either way about writing.
4. **What the scorer really is: a "row of letters" detector.** It paints a band over each row of letter-sized ink
   blobs. It ignores speckle and dense clutter, and gives almost nothing to a page turned sideways.
5. **It has a blind spot.** All 6 known-text windows of segment w026 scored 0, although their published ink share is
   12-25%. It can't see faint or speckled writing, so a 0 never proves "no writing".
6. **"32um" is not the resolution it needs.** It only fires properly when letters are small in pixels.
   - On PHerc Paris 4, its own training scroll, it marked 58% of text at 63 um per pixel but only 17% at 32 um.
   - PHerc0139 writing is smaller (lines 4.6 mm apart, against 6.7 mm on Paris 4) and worked best at 44 um.
   - The tool's own layout settings expect lines 80-120 pixels apart. Paris 4 only fits that at about 63 um per pixel.

## 2. Calibration table (PHerc0139, 44 um per pixel)

Score = the share of a 7.5 mm window the scorer calls ink (its own measure: three models averaged, probability >= 0.5).

| Window type | n | Scored inside its whole segment (normal use): median | Same window cut out alone (like our maps): median |
|---|---|---|---|
| Known text (published ink share 10-60%) | 42 | 0.25 | 0.05 |
| Blank (published ink share under 0.5%) | 12 | 0.00 (all 12) | 0.00 (all 12) |
| Same text, ink blobs shuffled | 42 | 0.00 | 0.00 |
| Same text, page turned 90 degrees | 42 | 0.00 | 0.00 |
| Known text vs blank: AUC (1 = perfect, 0.5 = coin flip) | | 0.89 | 0.81 |
| Known text vs shuffled blobs: AUC | | 0.74 | **0.60** |
| same, pairs where the text window scored higher | | 31 of 33 that differ | 22 of 30 |
| Known text vs turned page: AUC | | 0.86 | 0.74 |
| same, pairs where the text window scored higher | | 33 of 34 | 24 of 28 |
| Windows scoring exactly 0: known text / shuffled / turned / blank | | 21% / 50% / 83% / 100% | 38% / 48% / 74% / 100% |

Notes:
1. **By segment (whole-segment scoring):** w040 0.41, w029 0.17, w026 0.00. Leaving out the blind w026, text beats
   shuffled at AUC 0.87 (w029) and 0.79 (w040), and turned at 0.92 and 0.96.
2. **Cut-out scores are noisy.** The same window scored in two random placements agreed only at rank correlation 0.55.
3. **Positive control:** PHerc Paris 4 Grand Prize segment 20231031143852 at 63 um per pixel (70 text windows; the
   segment has no blank windows).
   - text: 0.58
   - shuffled: 0.39 (text higher in 60 of 70)
   - turned: 0.00 (text higher in 70 of 70)

**How the pixel size changes the score** (median score of known-text windows, scored inside the whole segment):

| Page | 32 um/px (the name) | 44 um/px | 63 um/px | 90 um/px |
|---|---|---|---|---|
| Paris 4, 70 text windows | 0.17 | 0.49 | 0.58 | 0.56 |
| PHerc0139 w040, 23 windows | 0.26 | 0.41 | 0.30 | not run |
| PHerc0139 w029, 13 windows | 0.10 | 0.17 | 0.06 | not run |
| PHerc0139 w026, 6 windows | 0.00 | 0.00 | 0.00 | not run |

## 3. Our maps (NOT evidence: the scorer failed calibration at this size)

1. There are 252 windows: 244 maps, with the four 15 mm "big" maps cut into 7.5 mm tiles. They were scored at 44 um
   per pixel in the same two random mosaics as the calibration windows.
   - PHerc0846A: 11 of 100 windows above 0, highest 0.22.
   - PHerc1203: 8 of 152 above 0, highest 0.10.
2. Highest-scoring windows:
   - s0846a_rr0 r110_c105: D 0.22, C 0.21. This is the only region where both depth orders scored clearly above 0.
   - s0846a2_b0 r65_c25 C: 0.11
   - big2 r22_c106 D, top-right tile (challenge orientation): 0.10
   - s0846a2_b0 r105_c105 C: 0.10
3. C and D of the same region hardly agree (rank correlation 0.16).
4. Cut-out scores jump around, so read the top list loosely.
   - At 63 um per pixel, s0846a_rr0 r110_c105 was near the top again (D 0.31, C 0.29).
   - But the top window there was survey_b0 r42_c126 D at 0.58, which had scored 0.06 at 44 um.
   - s0846a_rr0 r110_c105 is the one region that fires in both depth orders at both pixel sizes. That makes it worth a
     look by eye, and nothing more.
5. Even our inkiest windows rarely fire. Of the 61 with canonical ink share of 10% or more, 15% scored above 0. Shuffled
   blobs of known text, which have the same ink amount, scored above 0 in 52%. So to this model our blobs rarely look
   like letters in a row. But that could just be a different writing size or style on these scrolls. It is not a
   verdict on writing.

## 4. What it means

1. **Don't quote this scorer's number for a 7.5 mm map as evidence, for or against writing.** At that size it can't
   tell known text from the same ink shuffled, and it gives 0 to more than a third of known text.
2. **It is a useful writing detector on big renders.** That means many lines and several centimetres wide, at a pixel
   size where the letters are about as big as Paris 4 letters at 63 um per pixel.
3. **The honest way to use it is a before/after on a big render.** Score the page, then the same page with its ink
   shuffled, and turned 90 degrees. Writing drops a lot, and texture should not. That fits the project rule: a real
   failure, proven with before/after.
4. **Because of the blind spot, a scorer that doesn't fire is weak evidence.** Only a line-shaped response that
   collapses when the page is shuffled or turned would count.

## 5. What the scorer is (from the code and the model files)

1. **Model:** `scrollprize/ink-coverage-32um` on Hugging Face (checkpoints checked against the published sha256).
   - It is a 2D nnU-Net made of three models ("folds"), trained 250 epochs.
   - Its training data was 21 renders of PHerc Paris 4 only, each about 1,900-2,070 by 3,000-6,300 pixels.
   - Held-out quality is about 0.6 pseudo-Dice.
2. **Input:** one grey image of an ink-probability render, where bright = ink. The official pipeline has two steps:
   - `render_ink.py` takes the brightest of 5 layers through the scroll's ink-prediction volume. It divides the image
     by its own 95th percentile and saves a JPEG.
   - `get_ink_metrics.py` hands that to nnU-Net. nnU-Net crops the black border, rescales the image by its own mean
     and spread, and reads it in overlapping 768 x 2048 tiles. Each tile is read four ways (flipped), and the three
     models are averaged.
3. **Output:** a probability per pixel of "clearly identifiable ink".
   - The tool reports the ink area (probability >= 0.5), a line score and a column score.
   - In practice the ink it marks is whole bands along text lines.
4. **Resolution:** see point 6 of section 1.
   - The render defaults (`--scale 0.25` at `--group-idx 1`) give one pixel per 8 volume voxels. We don't know which
     ink volume they rendered. If it was on the 7.91 um Paris 4 grid, that is 63 um per pixel, which fits both the
     layout settings and the positive control. The "32um" in the name fits neither.
   - We area-averaged the 2.4 um maps to 32, 44, 63 and 90 um per pixel.

## 6. How it was run

1. **Maps:** the challenge's published canonical ink maps (`*new_canon*.tif`, 2.399 um per pixel), read from the open
   data bucket.
   - PHerc0139 segments w026, w029 and w040 (20250108000001-w026_2025010854, 20250108000004-w029_2025010827,
     20250831000000-w040_2025083102).
   - Paris 4 segment 20231031143852 (2.4 um) as the positive control.
   - Windows were 7.49 mm (3,120 px) squares on a grid, fully inside the segment (checked against each segment's mesh
     file).
2. **Whole-segment scoring:** each segment map was area-averaged to the scorer's pixel size and scaled and JPEG'd like
   `render_ink.py`. It was then scored exactly as `get_ink_metrics.py` does. Each window's score was read from the
   result.
3. **Cut-out scoring:** everything was pasted in random order into one big strip with 0.5 mm gaps and scored as one
   strip. That was all 42 text, 42 shuffled, 42 turned and 12 blank windows, plus our 252 windows. It was done twice
   with different random orders, and the two scores averaged.
4. **Shuffled control:**
   - Each ink blob (probability >= 0.25, with its soft edge) went to a random spot with a random quarter-turn.
   - Holes were filled with the window's own background.
   - Blobs cut by the window edge only slide along that edge.
   - Neighbouring letters are often merged into one blob, so the control keeps some of the line structure. That
     makes it a conservative test.
5. **Check:** our code gives bit-identical probabilities to nnU-Net's own file-based predictor, which is the call
   `get_ink_metrics.py` makes. Max difference was 0.0 on a 768 x 1670 test image.
6. **Our maps:** `canon_pred_asinput.png` from box A.
   - Turned to the challenge orientation (`[:, ::-1]`), as recorded in `canon_run_info.json`.
   - Pixels outside the surface (value 0) were left out of each score.

## 7. Caveats

1. **Input type:** the scorer was built for renders of a 3D ink volume, and we gave it 2D canonical maps. The Paris 4
   control shows it works well on those, so that is not why it fails on small windows.
2. **Orientation:** it needs text lines to run horizontally. We assumed our maps are in the challenge orientation, as
   the run files say. If they were sideways, even real text would score about 0.
3. **Window size:** a 7.5 mm window holds only about 1.6 PHerc0139 lines. That is exactly why the scorer struggles on it.
4. **Sample size:** only three PHerc0139 segments and one Paris 4 segment, with 42 known-text windows in all.
5. **Other scrolls:** the scorer has never seen PHerc0846A or PHerc1203 writing. Their letters may need a different
   pixel size. A different pixel size does not rescue small windows, though. We repeated the cut-out test at 63 um per
   pixel (one random order) and it was worse: 74% of known text scored 0, known text vs shuffled blobs gave AUC 0.49,
   and known text vs turned gave 0.57.

## 8. Files

1. **Scripts** on box B, in `<work-dir>/scorer32/`:
   - `inkcov.py` (scorer wrapper)
   - `prep_seg.py`, `prep_p4.py`
   - `scramble.py`
   - `run_W.py` (whole segment), `run_M.py` (cut-out mosaic)
   - `stats_W.py`, `analyze_all.py`, `analyze_ours.py`, `diag_M.py`, `diag_blobs.py`
   - `verify_official.py`, `make_figs.py`, `setup.sh`, `slim_ckpt.py`
   - the `*.sh` runners and `logs_*.txt` for what ran when
2. **Results** in `out/`:
   - `W_*.json` (per-window scores, whole segments)
   - `M_44um_merged.json` (cut-out scores, including ours)
   - `stats_W.json`, `summary_all.json`, `ours_44um_summary.json`
3. **Cleanup:** the scorer install (nnU-Net in `pylib/`, the three checkpoints in `model/`, about 1.2 GB) and all
   temporary data have been deleted. The folder is now 3 MB, and the shared venv was never changed. `setup.sh`
   rebuilds the install in a few minutes: it installs into `pylib/`, downloads the checkpoints, and checks their
   sha256. Then run the scripts with `PYTHONPATH=pylib`.
