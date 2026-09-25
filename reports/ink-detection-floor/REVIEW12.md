# Twelfth independent review: day 4's results before their publication (26 Sep 2026)

Reviewer: a separate Claude Code agent, read-only, asked whether the run followed amendment 3, whether every number and
claim in the write-up, the index, the results page and the data release's notes holds against the run's own output and
day 3's, and whether the limits amendment 3 states are kept beside the result. Verdict and findings as returned
(lightly shortened, private paths removed), each followed by what was done.

READY WITH FIXES

1. SHOULD. None of amendment 3's limits appeared next to the result, and day 3's 0.87 was cited without the donor-mix
   caveat, which matters: day 3's own windows drawn with day 4's donor mix give a full-strength median of 0.668 to
   0.776, below 0.70 in 4 of 16 draws. **Done:** checked again here (the same numbers; day 3's own median 0.750), and
   the write-up now states n = 8, the donor mix and what it does on day 3's windows, the resampled stand-ins and the
   textureless share (17 of 81 cores passed) beside the result; the index names the mix too.
2. SHOULD. "-0.008 to +0.025" is the median over targets; single targets span -0.062 to +0.066. **Done:** "the median
   of arm A minus arm B", with the single-target span.
3. SHOULD. "Every number from the run is in RESULTS_DAY4.md" was false: each donor's ink contrast after resampling,
   which amendment 3 reports, was only in `results.json`. **Done:** the page now has a table of each donor's contrast
   at 9.362 and at 8.64 um, and the write-up says which figures are on the page and that the rest are in
   `day4/run/results.json`.
4. SHOULD. The write-up and amendment 3 are dated 26 Sep (Australian time), but the page says the run started at
   16:31 UTC on 25 Sep, which reads as a run before its rules. **Done:** the write-up gives both times in UTC (rules
   pushed 16:08, run started 16:31).
5. SHOULD. The release notes lacked day 3's warning about the bright band near the edge of the maps (34 of 40 maps show
   one, 62 to 86 px inside the edge). **Done:** the same sentence as day 3's release.
6. NOTE. The smoke run was not mentioned. **Done.**
7. NOTE. "Every job was read twice" (every window), "the 0.661 holds" (it stays at 0.660 to 0.662), "about 0.95" (0.954
   to 0.961). **Done:** all three as the reviewer gives them.
8. NOTE. At s = 0.25 the median difference changes sign when any one of four targets is left out; only s = 1 was
   reported that way. **Not changed:** the write-up gives the range of the median at every strength and the single
   targets' span, and says no clear difference; the reader's full output on the page shows the rest.
9. NOTE. The release notes said both arms' results were fragile to one window, but arm A's miss is not, only its
   check. **Done:** reworded.
10. NOTE. The PHerc0483B surfaces page would say "no ink has been read from them" and that day 4 "runs" on them.
    **Done:** it names day 4's result.

Checked and right, as returned: `read_day4.py` ends in AGREE, and its output equals the block on the page; the
reviewer's own recompute from `results.json` (182 jobs, no errors, every part complete, pins equal to `floor_day4.py`'s,
the control equal to day 1's in both directions) matches every median, check, floor, interquartile range, difference
and leave-one-target-out result, and every number the write-up and index cite; `RESULTS_DAY4.md` rebuilds byte for
byte; `results.json`, `summary.md` and `floor_day4.py` equal the private copies, and the job is unchanged since its
rules were published; the release's 40 maps match the recorded means, with the array names and shapes the notes
give; links resolve; no dashes or private paths; every script parses on Python 3.9, and `fake_day4.py` passes.

Final check (a second reviewer, 26 Sep, of the changes above only): READY WITH FIXES, all done: "every job's AUC"
became "every target window's AUC" (the references' reverse AUCs are only in `results.json`); the release is created
after the push, so its tag holds the results; "among amendment 3's limits"; the PHerc0483B page says neither
checkpoint reaches a floor; the index names PHerc0846B as day 3; "02:08 AEST"; the release notes rewrapped.
