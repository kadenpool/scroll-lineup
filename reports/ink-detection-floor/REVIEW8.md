# Eighth independent review: are review 7's findings fixed? (25 Sep 2026, before amendment 2's publication)

Reviewer: a separate Claude Code agent, read-only, asked to check each of review 7's findings in the day-2 job and
the draft, and whether the draft matches the code. It read the two smoke runs only through a script that prints no
score, and opened none. Verdict and findings as returned (lightly shortened, private paths removed), each followed by
what was done.

READY WITH FIXES

Review 7's findings:
1. PARTLY. The draft states the blind rule and the check script prints no score, but the watcher still printed each
   smoke's summary table into its own log, and those logs were not kept out of the repository. **Done:** they are
   git-ignored, the watcher has a `BLIND=1` mode that prints no summary, and the draft says the logs hold the table,
   unopened.
2. FIXED. Float32, batch 32. Smoke 2: 49.6 minutes for 10 jobs a GPU, 4.96 minutes a job; the full run about 7.4
   hours with job building, so "about 7.5 hours" holds; smoke 1 took 8.29 minutes a job.
3. FIXED. Samples land at i x 1.025422 (exactly 9.6 um); the furthest samples are inside the input; the kept core is
   rows and columns 250 to 748 (499 px); image and masks differ only on letter edges; no zero edges.
4. PARTLY. The plane windows match `predict`, but "median 11" pooled the shams, which carry no letters: in the 84
   planted and transplant jobs the letters sit at layers 10 to 13, median 12 (plane 11.7), about 1 plane off the
   forward middle and 2 off the reversed. **Done:** the draft says so.
5. FIXED. The held-out caveat.
6. FIXED. The kept core masks; `read_day1.py` gives byte-identical output on day 1 and the expected lines on a fake
   day-2 run.
7. FIXED. The input pins equal day 1's files and smoke 2's record.
8. PARTLY. The push folders are fixed, but the other leftovers were only in REVIEW7 while the draft said "all fixed
   here". **Done:** the draft says the clipped share and `layers` stay day 1's [4, 25), which hold every layer hecate's
   windows reach (5 to 22).

New:
- SHOULD. The card's sentence goes on "and scans from the Vesuvius Challenge open-data collection", and the 9.6 um
  model trained on native coarse-scan renders supervised by fine-scan predictions "where both scans were available";
  PHerc0139 has both. **Done:** both in the held-out caveat.
- NOTE. The bucket listings behind the held-out evidence were not saved. **Done:** saved with their date.
- NOTE. `make_day2.py` said it prints every changed line; it prints a count. **Done:** corrected.

Checked and right: `make_day2.py` rebuilds `floor_day2.py` byte for byte; smoke 2 ran exactly this file; the pins;
both smokes healthy (done, self-test passed, no errors, 20 jobs, 40 finite AUCs, 80 kept arrays of 499 px, none
constant); the gate code unchanged; the day-1 results page rebuilds identical.
