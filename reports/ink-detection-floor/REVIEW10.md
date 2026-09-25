# Tenth independent review: day 2's results before their publication (25 Sep 2026)

Reviewer: a separate Claude Code agent, read-only, asked whether the run followed amendment 2, whether every number
and claim in the write-up holds against the run's own output and day 1's, and whether the held-out caveats sit beside
every day-2 result. Verdict and findings as returned (lightly shortened, private paths removed), each followed by
what was done.

NOT READY

1. BLOCKER. The GO rests on G1 passing by 0.002 (planted minus transplant -0.048 against the 0.05 limit), and it fails
   the w042 check the write-up publishes for day 1: with w042's 28 jobs removed, `read_day1.py` gives -0.056, so G1
   fails and there is no GO; dropping any one of 6 of the 12 windows flips it too. w042's neighbours, w041 and w043,
   are in the dataset hecate's card names, so day 1's caveat applies here. **Done:** checked again here, with the same
   numbers (-0.056 without w042; -0.053 without any one of six windows, -0.043 without any of the other six); the
   write-up now calls the result a narrow GO and states both, as checks made after the result.
2. BLOCKER. The index sentence "passes the same checks on PHerc0139 (day 2)" had no held-out caveat, and "the same
   checks" pointed back to day 3's. **Done:** it now says the model passes day 1's gates with the swap plant only
   narrowly, and that whether its training saw these segments cannot be ruled out.
3. SHOULD. The write-up's caveat dropped amendment 2's "the card does not list which segments were used". **Done:**
   restored.
4. NOTE. The held-out note called all 11 dataset segments "labelled", but the saved listings show label files only in
   w041's folder. **Done:** "the 11 PHerc0139 segments in the main folder"; the note also now says that w042 lies
   between two of them.
5. NOTE. `results_md.py`'s docstring still said "the day-1 results page". **Done.**
6. NOTE. G2 also passes near its limit: the swap sham reads 0.414 at s = 1 (quartiles 0.38 to 0.52). **Done:** the
   write-up says the shams sit near the lower limit.
7. NOTE. `read_day1.py` needs numpy, so on a bare Python it stops before printing AGREE (true before this change).
   **Not changed:** numpy is in the repository's requirements.

Checked and right, as returned: the pins (the model's revision, the checkpoint's size and sha256, hecate.py's sha256,
the inputs) equal amendment 2's; the Kaggle notebook held exactly the published `floor_day2.py`, and `make_day2.py`
regenerates it byte for byte; amendment 2 was pushed at 06:56 UTC and the run started at 07:01 UTC; all 174 jobs carry
day 1's metadata, all 348 AUCs recompute exactly from the kept maps, and there were no errors; the reviewer's own gate
code picks the forward direction (0.8619 against 0.5363) and reproduces every gate and number; `read_day1.py
day2/run` ends in AGREE; every cited number matches the run's output and day 1's; `results_md.py` gives day 1's page
unchanged, and the documented day-2 command rebuilds `RESULTS_DAY2.md` apart from its four letters-only lines; the
held-out text matches the saved listings and the model card; links, dashes, private paths, disclosure lines and
parsing on Python 3.9.

## Re-check (a separate reviewer, 25 to 26 Sep, of the rewritten files)

NOT READY

- BLOCKER. "None of our seven segments is among the PHerc0139 segments of the ink dataset hecate's card names" was
  false: the card links the whole `ink` tree, and all seven sit in its `unused` folder. **Done:** "among the 11
  PHerc0139 segments in the main folder ... (all seven are in its `unused` folder, without ink labels)".
- SHOULD. The index sentence carried only one of amendment 2's two caveats. **Done:** both.
- SHOULD. "Every number is in RESULTS_DAY2.md" was untrue for -0.053 and -0.056, and "that gap -0.053" could be
  confused with the page's "context gap". **Done:** "every number from the run"; "planted minus transplant -0.053".
- NOTE. "a limit of 0.05" is two-sided. **Done:** "+/-0.05".
- NOTE. "the team's" had no antecedent in the index. **Done:** "the Vesuvius Challenge team's".
- NOTE. The page and `results_md.py` said everything comes from the run's output, though a hand-written note now
  sits below the title. **Done:** when a note is given, the page says so (day 1's page is unchanged).
- Checked and right, as returned: every cited number, recomputed from the runs with the reviewer's own gate code (the
  six windows that flip the gate are both w042 windows, all three w045 windows and target10_w046); all 348 AUCs from
  the kept maps; both results pages' rebuilds; dashes, paths, links, Python 3.9; every "Done" above it.

Final check (a third reviewer, 26 Sep, of the changes above only): READY, with three notes, all done: the page gives
each job's AUC in the primary direction only (said); w042's neighbours are named as two of the 11 segments in the
main folder; `results_md.py`'s docstring says the note is not from the run.
