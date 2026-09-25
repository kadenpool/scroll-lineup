# An ink detection floor for the public 9 um ink models (pre-registered; days 1 and 3 done, day 2 pending)

When the public 9 um ink models find nothing on an unread scroll, is that "no ink", or "no ink recovered yet"? The
challenge's 2026 Open Problems page asks exactly this for June 2027. This folder measures it directly: real ink from
PHerc0139, where the text is read, is planted into papyrus at graded strength, the same public models are run, and
the weakest ink they still recover is found. Every claim is limited to ink like PHerc0139's.

**Day 1 result (24 Sep, run after publication): GO, for the swap plant with both checkpoints.** The models read the
donor letters in place at AUC 0.754 and 0.782. The same letters swapped into blank papyrus read like the same letters
moved whole (planted minus transplant +0.033 and +0.024), shams of the same shape read like nothing (0.50 to 0.57),
and the planted letters read at 0.81 and 0.79 at full strength. The additive plant failed (it reads 0.09 to 0.11
below the transplant), so the swap is carried forward. Every number is in `RESULTS_DAY1.md`, generated from the run's
own output (`day1/run/`), and `read_day1.py` recomputes every gate from it apart from the Kaggle job's own code.
Before it, a smoke run on one target checked the pipeline end to end on the published code; its numbers are not used.
A caveat that the eligible-scroll atlas (`rodriguescarson/eligible-scroll-atlas`) stated before day 1 was published,
added here on 25 Sep: one of the four target segments, w042, lies between windings the models were trained on (w041
and w043). Here w042 serves only as blank papyrus for plants and shams, never as known ink. Its two clean windows read
0.599 and 0.442 with `seed42_step010000` (the other targets 0.36 to 0.56) and 0.605 and 0.505 with
`seed43_step060000` (0.36 to 0.61). Leaving its two windows out changes no day-1 result: with their 28 jobs removed from
`day1/run/results.json`, `read_day1.py` gives the same pass or fail on every gate, for both plants and both checkpoints
(the swap's letters at full strength then read 0.805 and 0.780).

**Day 3 result (24 Sep, run after publication): on PHerc0846B, one checkpoint gives a floor and the other fails
its checks.** PHerc0846B is an unread First Letters scroll scanned at the same voxel size and energy as PHerc0139.
The same donor letters were swapped into its papyrus at three strengths, in windows on the seven surfaces we grew on
it (s01 to s07 in `../pherc0846b-surfaces/`; the targets fall on six of them), with two kinds of sham (its own papyrus, and
PHerc0139's).

- `seed42_step010000`: every check passed. The planted letters read at median AUC 0.506, 0.559 and 0.750 at
  strengths 0.25, 0.5 and 1, so the **detection floor (median 0.70) is 0.87** of the full strength of PHerc0139's
  ink, and the clear floor (0.80) is above 1: not reached even at full strength. Window by window the spread is wide:
  at full strength 0.50 to 0.89, and 4 of the 12 stay below 0.70.
- `seed43_step060000`: **no floor**, as the rules say. Its sham of PHerc0139 papyrus read 0.332 at full strength,
  below the 0.40 to 0.60 the rules allow: it reads plain PHerc0139 papyrus, swapped into this scroll, as less
  ink-like than its surroundings, so it responds to the foreign texture itself. The check is two-sided; review 4
  added this sham for the opposite case, foreign texture that reads as ink (`REVIEW4.md`).
- On both checkpoints the six reference windows reproduced day 1 exactly, and the job's readout is recomputed apart
  from its own code by `read_day3.py` (AGREE). Every number, target by target and in both directions, with each
  target's texture scale and clipping, is in `RESULTS_DAY3.md`, generated from the run's own output (`day3/run/`).
- Not pre-registered comparisons, for context only. On PHerc0139 (day 1) the same checkpoint read the same letters
  at 0.814 at full strength, against 0.750 here; but day 3 also places the letters differently (on the surface
  layer, with no depth matching) and scales them to a quieter papyrus (median texture scale 0.88, against 1.21 on
  day 1). The four lowest windows at full strength are those on s05, s06 and s07; the s05 and s06 windows are also
  the only two with donor 1.
- The models' own output on the seven whole surfaces is in `day3/whole_surfaces.png`, beside each surface's CT and
  labelled with each checkpoint's floor, and the raw maps are published as a data release,
  [ink-floor-day3-maps](https://github.com/kadenpool/scroll-lineup/releases/tag/ink-floor-day3-maps). We claim no
  letters from them; read them with the floor above in mind. The bright frame near the edge of every map follows the
  edge of the rendered surface (on it for `seed42_step010000`, up to 0.4 mm inside it for `seed43_step060000`): an
  edge effect, not ink.
- Before the run, a smoke run on one target checked the pipeline on the published code; its numbers are not used.
  Its whole-surface maps are byte-identical to the full run's.

The windows were chosen before any model ran on this scroll (`prep_day3.py`, `day3/windows_day3.json`), and the job
(`floor_day3.py`) is the day-1 job with only the day-3 parts replaced. Two more independent reviews found problems,
which were fixed before publication (`REVIEW4.md`, `REVIEW5.md`), and a sixth checked these results before they were
published (`REVIEW6.md`). `PREREG.md` now also carries two errata to
amendment 1, both about figures for the surfaces; no rule changes.

**A blind check by eye (25 Sep).** Kaden looked at 36 of `seed43_step060000`'s day-3 output maps, shuffled: letters
planted at full strength, at half strength, and shams of the same shape, twelve of each. He said "letters" for 8, 5
and 6 of them: by eye, the planted letters were not told apart from the shams (one-sided Fisher exact p = 0.34 and
0.79). This fits day 3's readout for the same checkpoint, which failed its checks on PHerc0846B. The design was fixed
before day 3's full run was fetched (`BLIND1_DESIGN.md`; a one-window smoke run, holding the maps behind 3 of the 36
pictures, had been read, and was not shown to Kaden); the pictures, the key, the answers and a guide to taking the test yourself are
in `blind1/`.

**Day 2 (pre-registered 25 Sep, amendment 2 in `PREREG.md`; run pending): the day-1 test with a third model,**
`hecate` 9.6 um, released by the team on 15 Sep. Every day-1 job is resampled to 9.6 um and read by the model card's
own code, pinned by revision and sha256 (`floor_day2.py`, generated from the day-1 job by `make_day2.py`, only the
model changed). How far these segments are held out from hecate's training is stated as far as it can be known,
with the dataset listings behind it (`day2/`). Two more independent reviews found problems, fixed or stated before
publication (`REVIEW7.md`, `REVIEW8.md`), and a ninth checked the files staged for this publication (`REVIEW9.md`). Two smoke runs checked and timed the job before publication; their scores were not
opened.

**Status: days 1 and 3 done; day 2 pre-registered, its run pending.** The rules, the windows and the code below were published before any result was seen, and each
result sits beside them, with any change to the rules as a dated amendment in `PREREG.md`. The rules were revised before publication, after three independent reviews and a dry run; `PREREG.md`
says what changed and why, and the second and third reviews are here as returned (`REVIEW2.md`, `REVIEW3.md`).
`PREREG.md` also states one mistake: a smoke run of an earlier version of the code was started by accident before
publication; its output has not been opened and is not used.

| file | what it is |
|---|---|
| `PREREG.md` | the rules: data, models, windows, the two plants and their shams, the readout, the gates |
| `prep_day1.py` | chooses every day-1 window by those rules, on segments the models were not trained on |
| `day1/windows.json`, `day1/masks.npz` | the chosen windows, their sheet profiles and registrations, and the letter masks |
| `floor_kernel.py` | the Kaggle job for day 1, byte for byte what runs |
| `read_day1.py` | reads a finished run and recomputes every gate apart from the Kaggle job's own code |
| `REVIEW2.md`, `REVIEW3.md` | the second and third independent reviews, before publication, as returned |
| `RESULTS_DAY1.md` | day 1's results, generated from the run's own output |
| `day1/run/results.json`, `day1/run/summary.md` | the run's own output (every job's AUC in both directions; the gates) |
| `prep_day3.py`, `day3/windows_day3.json`, `day3/prep_day3.log` | day 3's window choice on PHerc0846B, and its log |
| `floor_day3.py`, `read_day3.py` | the day-3 Kaggle job, and a reader that recomputes its readout apart from it |
| `REVIEW4.md`, `REVIEW5.md` | the fourth and fifth independent reviews, of day 3 before publication, as returned |
| `day1/plant_check.png` | one dry-run target: the letters in place, the clean target, both plants, the transplant and both shams at s = 1 |
| `RESULTS_DAY3.md` | day 3's results, generated from the run's own output |
| `day3/run/results.json`, `day3/run/summary.md` | the day-3 run's own output (every job's AUC in both directions; the readout) |
| `day3/whole_surfaces.png` | the models' own output on the seven whole surfaces, beside each surface's CT |
| `REVIEW6.md` | the sixth independent review, of the day-3 results before their publication, as returned, with what was done |
| `floor_day2.py`, `make_day2.py` | the day-2 Kaggle job (hecate), and the script that generates it from the day-1 job |
| `REVIEW7.md`, `REVIEW8.md` | the seventh and eighth independent reviews, of day 2 before publication, as returned, with what was done |
| `REVIEW9.md` | the ninth independent review, of the files staged for this publication before they went out (day 2's rules, the w042 caveat, and surface releases that follow separately), as returned, with a re-check and what was done |
| `BLIND1_DESIGN.md`, `BLIND1_RESULT.md`, `blind1/` | a blind check by eye of 36 day-3 maps: the design (fixed before day 3's full run was fetched), the result, the pictures, the key and the answers |
| `blind1_build.py`, `blind1_score.py`, `blind1_page.html` | build the pictures and the key from the day-3 run's window maps, score answers against the key, and the page template the pictures were shown on (in the claude.ai app, which saved each answer) |
| `day2/ink_bucket_*.json` | the ink dataset's PHerc0139 folder listings (25 Sep), and our seven segments' own folders, behind day 2's held-out statement |
| `results_md.py`, `results_day3_md.py`, `whole_figure_day3.py` | write the two results pages and the figure from the runs' own output: `python3 results_day3_md.py day3/run day1/run/results.json <out>` rebuilds `RESULTS_DAY3.md` byte for byte; the day-1 page's letters-only lines also need that run's kept maps (not published); `python3 whole_figure_day3.py <folder with the data release's maps> ../pherc0846b-surfaces day3/run/results.json <out>` rebuilds the figure |

Day 1 asks only whether the method works: do planted letters read at full strength, and read like the same letters
moved whole into the same papyrus, through the same model, while shams of the same shape read like nothing? Nothing is claimed about any other scroll unless the
day-1 gates pass.

*Written with Claude Code under my direction.*
