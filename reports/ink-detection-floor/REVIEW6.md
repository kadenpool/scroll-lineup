# Sixth independent review: the day-3 results, before their publication (24 Sep 2026)

Reviewer: a separate Claude Code agent, read-only, asked to check every number and claim in the day-3 write-up
against the run's own output, whether the publication keeps amendment 1's promises, and whether the published files
rebuild the results page. Verdict and findings as returned (lightly shortened, private paths removed), each followed
by what was done.

READY WITH FIXES (no blockers)

1. SHOULD. "The bright frame lies exactly where the rendered surface ends" holds for seed42; for seed43 the frame
   peaks 20 to 40 px (0.2 to 0.4 mm) inside the edge. "Edge effect, not ink" still holds. **Done:** said so.
2. SHOULD. "The same ink reads weaker on this scroll" (0.750 against 0.814): day 3 also placed the letters
   differently (surface layer, no depth matching, no sheet rule), and the texture scale k was lower (median 0.88
   against about 1.2), so the planted ink was smaller in grey levels. **Done:** moved under "not pre-registered
   comparisons, for context only", with both differences stated.
3. SHOULD. seed43's PHerc0139 sham reads 0.332, below chance: the model reads those patches as less ink-like, while
   review 4 added this sham for the opposite risk. **Done:** the direction is stated, and that the check is
   two-sided.
4. SHOULD. Amendment 1 says any region the maps mark is shown with the floor beside it; the results page does this,
   the figure labels and the release notes did not. **Done:** both now carry each checkpoint's floor, seed43's
   failed checks, and the edge-frame note.
5. SHOULD. "Every number, target by target, is in RESULTS_DAY3.md" was not true of each target's k, clipping share
   or reverse-direction AUCs, which the rules say are reported. **Done:** the page now has all three.
6. SHOULD. The reports index has no disclosure line. **Done.**
7. NOTE. The targets are on six surfaces, not seven (s03 holds only shams). **Done:** said.
8. NOTE. The four lowest windows (s05, s06, s07) include the only two with donor 1. **Done:** said.
9. NOTE. The AUCs and "detects from 0.87" are medians over 12 windows; 4 of the 12 stay below 0.70 even at full
   strength. **Done:** "median", and the 4 of 12, in the README and the index.
10. NOTE. The release notes called the checkpoint revision villa's (it is Hugging Face's) and named a private Kaggle
    run; create the release only after pushing. **Done**, and the release follows the push.
11. NOTE. "detection floor 0.868" beside mean map values could be read as a map value. **Done:** "of full
    strength".
12. NOTE. Day 2 (`hecate`) was never mentioned. **Done:** the README says it has not been run.
13. NOTE. "With none in the open-data catalogue" should read "with no surfaces in". **Done.**
14. NOTE. The surfaces' "under 0.3 % no scan data" counts black preview pixels, most of them the darkest papyrus
    after the contrast stretch (s01's render has 0.003 % true zeros). **Done:** stated as an upper bound.

Checked and right: the floors (0.868, above 1), every AUC quoted, 0.332, 0.814, "0.50 to 0.89", which windows are the
four lowest; the reference windows equal day 1 exactly (AUCs and means, both directions, both checkpoints); the smoke
and full-run whole-surface maps have the same sha256; PREREG.md is byte-identical to the source and the erratum
matches the surfaces' own checker and changes no rule; the run output, the job and the Kaggle notebook are what ran,
and the day-3 code and windows are unchanged since the pre-registration, which was pushed before the smoke run
started; the figure and the release use the full run's maps; no dashes, private paths or lesson numbers. Ran:
`read_day3.py` (AGREE); `results_day3_md.py` and `whole_figure_day3.py` (byte-identical outputs); `results_md.py`
(differs only in the letters-only lines, as stated); the surfaces' `trace_numbers.py` (all numbers match).
