# Eleventh independent review: day 4's rules, windows and job (26 Sep 2026, before the rules' publication)

Reviewer: a separate Claude Code agent, read-only, asked whether amendment 3 says exactly what the day-4 job does,
whether the resampling to 8.64 um is right, whether the generator, the reader and the made-up test cases work, whether
the windows follow the stated rules, and whether anything would make the result unreadable or misleading. No model of
ours had run on PHerc0483B. Verdict and findings as returned (lightly shortened, private paths removed), each followed by
what was done.

READY WITH FIXES

1. SHOULD. "The plane means differ by under 0.001 grey levels": both records keep plane means to two decimals, so the
   match shows only a difference under 0.01, which is the limit itself. **Done:** "the same to the two decimals both
   records keep".
2. SHOULD. The difference between arms is given only when the checks also pass in both arms (the job, the reader and
   the made-up "onearm" case agree), not whenever an arm is read; seed 43 failed a check on day 3. **Done:** "for each
   checkpoint whose control holds and whose checks pass in both arms".
3. SHOULD. The kept maps are 554 x 554 in arm B and for the scale references (amendment 2 stated day 2's 499); arm B's
   masks are not kept; and the scale references' kept crop leaves out one row and one column of the carried mask.
   **Done:** all three stated, with where the masks come back from (`masks.npz`, through the job's resampler).
4. SHOULD. With n = 8, donors 0 and 1 are used twice and donors 2 to 5 once (day 3 used each twice), and the PHerc0139
   shams come from w025 and w026 only; day 3's AUCs at full strength varied largely by donor. **Done:** checked here
   against the windows, and stated in the limits: a difference from day 3's floor may partly reflect this mix.
5. SHOULD. Commit now to the fragility check that day 2 needed after its result: every check, floor and difference
   with its margin, and whether leaving out any one target changes it. **Done:** in the amendment, and
   `read_day4.py` prints the margins and the leave-one-target-out results for every arm and checkpoint.
6. SHOULD. 64 of the 81 cores examined failed the textureless rule (1 of 25 on day 3), so the floor describes the most
   intact fifth of the papyrus examined. **Done:** stated in the limits.
7. NOTE. The control dropped "in its primary direction". **Done.**
8. NOTE. `read_day4.py` checked neither job counts nor strengths: deleting one sham job, or running seven targets,
   still gave AGREE, and a two-strength run crashed. **Done:** it now checks the strengths, the ten jobs of every
   target in each arm, eight targets (one in a smoke run), six references, six scale references and the whole
   surfaces, and prints DIFFER otherwise; a made-up case with one sham job missing is added, and the reader refuses it.
9. NOTE. "The scale the models were trained at": the card lists 24 pooled segments at about 9.6 um and 5 native at
   9.362 um. **Done:** "the voxel size of the models' native training scans (most of their training data was pooled
   to about 9.6 um)".
10. NOTE. "(as day 3)" after the 3.0 to 6.6 % stretch read as if day 3 had the same figures, and the draft did not
    name its reviews, as amendments 1 and 2 do. **Done:** "on average", "(as day 3)" dropped, and this review named.

Checked and right, as returned: `make_day4.py --check` matches byte for byte, and `floor_day4.py` is the file the dry
run ran and the three notebooks hold; arm A matches day 3 line by line; arm B uses sigma 52 for the target and its
sham, computes k on the resampled residual, and makes the PHerc0139 residual at 9.362 um before resampling it; the
resampler matches the amendment's formula to within 2e-6, and the masks exactly; everything maps inside the donor core
and window; the made-up cases pass, and ten more of the reviewer's own (a missing reference, a missing scale
reference, a move in the reverse direction only, arm A failing its checks, ties at 0.40 and 0.70, a missing score)
behave safely; the windows' counts (5,780, 81, 17, 64), n = 8, the carries, the boxes, the absence of overlaps in
either arm, the correlations 0.986 to 0.996 and the sha256 recompute; the seed was committed before the pick ran;
the renders share one build; the dry run's 182 jobs, k 0.828 to 0.963 and 0.863 to 0.989, and clipping at most
0.229 %; villa's inference code accepts the 1109 and 2806 px inputs; no dashes; every script parses on Python 3.9.

## Staging check (a separate reviewer, 26 Sep, of the exact files staged for publication)

READY WITH FIXES, all done: the write-up called the difference between arms "the effect of the step in scale itself",
which amendment 3's limits contradict (now "measured with resampled stand-ins"); the amendment said `read_day4.py`
prints all of the reported figures, but the run's `results.json` holds every figure they come from and the reader prints the nearest check's
margin and the leave-one-target-out results (now said so, and "its margins" in the write-up); the write-up's "native
training scans" gained the amendment's note on pooled training data; `make_day4.py` pointed at an unpublished plan
(now amendment 3); `fake_day4.py`'s usage line lacked the `missing` case. Checked and right, as returned: every "Done"
above; the PREREG diff only adds lines at the end; every figure in amendment 3 matches its record; `make_day4.py
--check` on both Pythons; `floor_day4.py` equals the dry run's copy; the made-up cases 8 of 8; `windows_day4.json`'s
sha256 on both picks, in the job and in the amendment; the staged `prep_day4.py` is the one Kaggle ran on 26 Sep;
plain ASCII, no private paths, links resolve, Python 3.9 parses everything.

Final check (a third reviewer, 26 Sep, of the staging fixes only): READY WITH FIXES, three wording fixes, all done:
`make_day4.py`'s docstring said one change was not named by amendment 3, though the amendment names the profile
check (now: one detail of it differs from day 3's); "results.json holds all of it" became "every figure these come
from" (the margins are computed by the reader); and the texts now say two reviews, whose findings were fixed or stated.

*Edited 26 Sep 2026 (AEST): "no model had run on PHerc0483B" now says "no model of ours" (see the erratum to amendment 3).*
