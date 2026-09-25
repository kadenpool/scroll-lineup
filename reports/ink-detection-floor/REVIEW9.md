# Ninth independent review: this publication's exact files (25 Sep 2026, before they went out)

Reviewer: a separate Claude Code agent, read-only, asked to check the exact files staged for this push: the three
surface releases (PHerc0846B grown from seven surfaces to twelve; PHerc0490B and PHerc0483B new; later held back, see
the end), the w042 caveat on day 1, and day 2's rules with their files. It re-derived the surfaces' numbers, rebuilt the published outputs, and
read the day-2 smoke runs only through a script that prints no score. Verdict and findings as returned (lightly
shortened, private paths removed), each followed by what was done.

NOT READY

1. BLOCKER. `whole_figure_day3.py` found the surfaces with `startswith("s0")`, which now also picks up s08 and s09,
   so the documented command stops with `KeyError: 'whole_s08__forward is not a file in the archive'`. **Done:** the
   script now takes the surfaces the run's maps hold (a fix made in our working copy at 00:59 on 25 Sep and not
   carried to this repository until now); from the twelve-surface folder, and from the seven-surface folder published
   here, it rebuilds the published figure byte for byte (sha256 `40ef82fc...`).
2. BLOCKER. "A caveat noted later (25 Sep) by the eligible-scroll atlas" is false: the atlas's README already said
   "w042 sits between training windings" on 22 Sep (a copy we saved then), before day 1 was published on 24 Sep.
   **Done:** the caveat says the atlas stated it before day 1 was published, and that it was added here on 25 Sep.
3. SHOULD. `PREREG.md`: "the references' donor sheets lie at layers 10 to 14", but the six donors sit at 14, 11, 11,
   13, 11 and 11, so 11 to 14 (10 to 14 is all windows pooled). **Done.**
4. SHOULD. `PREREG.md`: "all fixed here (`REVIEW7.md`)", while review 8's item 8 says some leftovers were only
   stated, and `REVIEW8.md` is not cited. **Done:** "each is fixed here or, for a few harmless leftovers, stated in
   that review", with reviews 8 and 9 cited.
5. SHOULD. The erratum to amendment 1, already public, says the closest other pair among s01 to s07 is 38 voxels
   apart; the corrected `trace_numbers.py` gives 37.2. **Done at first** as a second erratum to amendment 1; the
   re-check below found 37.2 still too high, so the erratum is held back, to go out with the surfaces.
6. NOTE. The PHerc0846B README should name the atlas, and explain `render_covered`, which its `index.json` now has,
   as the other two READMEs do. **Done** in the surface releases (held back, below): both, and the atlas is named in
   all three READMEs.
7. NOTE. The PHerc0490B and PHerc0483B reviews say "the other 6 to 25 % of each area"; as a share of the area it is
   6 to 20 %, and 25 % is the excess over the flat 6.45 cm2. **Done** in the surface releases (held back, below):
   each gives its own scroll's share (16 to 20 %, and 6 to 12 %) and says what the review had said.
8. NOTE. `REVIEW8.md` named a script that is not published. **Done:** it now says what the script does instead.
9. NOTE. `PREREG.md` said the unused folder holds our segments' 2.4 um renders and model predictions, but the saved
   listings show its top-level folders only. **Done:** each of the seven segments' folders was listed one level down
   and saved (`day2/ink_bucket_segments_0139_20260925.json`): each holds its render and a `preds` folder of model
   predictions, and no ink labels (the labelled w041 folder, listed beside them, holds four label files). The text now
   says only that; "2.4 um" is dropped, since the listing does not show the resolution.
10. NOTE (optional). Leaving out w042's windows changes no day-1 gate: the swap still passes and the additive still
    fails, on both checkpoints. **Done:** checked again here, with `read_day1.py` on the run's results with w042's
    28 jobs removed (the same pass or fail on every gate; the full-strength swap reads 0.805 and 0.780), and added
    to the caveat.

Checked and right, as returned: every figure in the three surface READMEs matches `trace_numbers.py`, `index.json`
and each `meta.json`; s01 to s07 are byte-identical to the published files; each review matches its README; the w042
AUCs are right, and w041 and w043 are training segments in section 2; `PREREG.md` equals our working copy;
`make_day2.py` rebuilds `floor_day2.py` byte for byte, and that file is the job smoke 2 ran; the pins, the 27 x 998 x
998 grid, planes 5 to 20 and 6 to 21, float32 and the held-out folder lists are right; smoke 2's timing holds (49.6
minutes for 20 jobs); `read_day1.py` ends in AGREE; `RESULTS_DAY1.md` matches apart from the letters-only lines (which
match too with the kept day-1 maps); `RESULTS_DAY3.md` rebuilds byte-identical; links resolve; no long dashes,
private paths or draft markers, and every disclosure line is present.

## Re-check (a separate reviewer, 25 Sep, of the files after the fixes above)

READY WITH FIXES

- BLOCKER (surfaces). The closest-pair distances are still sampled, not measured: the fixed `trace_numbers.py` adds
  the grid points but never samples the cell edges between them. s07's grid point (101, 149) is 36.33 voxels from
  s01's cell edge between grid points (2, 120) and (2, 121), so s01 and s07 do not stay 37.2 (or 37) voxels apart;
  for the same reason s10 and s01 come within 0.02 voxels (not 0.07), and the four pairs that touch at a point within
  0.2 to 3.3 voxels (not 0.8 to 3.5). PHerc0483B's 58 holds. **Done:** the 36.33 was checked again here; the three
  surface releases and the second erratum are held back from this publication until `trace_numbers.py` measures
  these distances exactly, on the surfaces' own triangles, and a review has checked it (the other figures in this
  finding are the reviewer's own estimates; the exact ones go out with the surfaces).
- SHOULD. Amendment 1, already public, says the seeds are at least 12 mm apart; s02 and s06 are 11.84 mm apart.
  **Held back:** it goes into the same erratum, with the surfaces.
- Checked and right: the figure rebuilds byte-identical from the release's maps, which match the release by sha256;
  the atlas's note was saved on 22 Sep, before day 1's publication; with w042's 28 jobs removed, every gate keeps its
  pass or fail, the reader still agrees with the job, and the full-strength swap reads 0.805 and 0.780; the
  donors' sheets are at layers 11 to 14; `PREREG.md` equals our working copy and only adds lines; the held-out
  listings, `REVIEW8.md`, the links, dashes, private paths and the file table.

What went out in this publication: day 2's rules (amendment 2) and files, the w042 caveat, the day-3 figure script
and these reviews. The surface releases follow once their distances are exact.
