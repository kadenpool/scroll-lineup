# Second independent review: all twelve surfaces (25 Sep 2026, before the five new ones were published)

Reviewer: a separate Claude Code agent, read-only, asked to check every claim in three draft surface releases (the
PHerc0490B, PHerc0483B and this 12-surface PHerc0846B one) against the run records, run `trace_numbers.py`, and look
at every preview at full size. Verdict for the three together: READY WITH FIXES. The findings that concern this
release, as returned (lightly shortened), each followed by what was done. The first review, of s01 to s07, is in
`REVIEW.md`.

1. BLOCKER. "At most 0.3 % black ... except s11 (2.35 %)" undersold s11: its upper left, and the gap along its crack,
   are dark with no papyrus texture, 7 to 17 % of the preview depending on the threshold, where every other surface
   is under 1 %; the 2.35 % counts only the no-data pockets inside that area. **Done:** said in that bullet and in
   s11's first-look row.
2. SHOULD. The README pointed to `REVIEW.md`, which the folder did not hold. **Done:** it holds the first review, and
   this one.
3. SHOULD. "The closest other pair, s01 and s07, stays 38 voxels apart": their grid points are 37.2 voxels apart; the
   script's closest-pair line used only samples inside cells (the same flaw was in the published seven-surface
   README). **Done:** the script now takes the grid points too, and the text says 37.
4. SHOULD. First look: s08 also has swirls and gaps along the top and down the right side; on s10 the swirls and
   streaks cover the left third, not just the edge. **Done.**
5. NOTE. The sixth seed, not grown, (3662, 3726, 4912), lies 11.98 mm from s10; say so, and give the survey's time
   zone (it ran at 24 Sep 14:10 UTC). **Done.**
6. NOTE. Two things the published README had were dropped: the grid-point counts beside the finer measure, and "a
   surface grown there lies on no papyrus". **Done:** both restored.
7. NOTE. The DRAFT line at the top is removed at publication.

Checked and right: every area and the total; the seeds (11.84 mm apart at the closest); the builds; the survey counts; all
eleven pairs that meet, with s10 and s01 the largest, and about 1.1 cm2 covered twice in all; the black shares; the
licence and eligibility; every surface byte-identical to its run output, each `meta.json` different only in its
segment id, the ids unique; s01 to s07 identical to the published files; everything the published README says kept
or correctly updated; no long dashes, private paths or lesson numbers; the disclosure line.

## Later (25 Sep): the distances and areas, measured exactly

A review of the files staged for publication (its re-check, in `../ink-detection-floor/REVIEW9.md`) found the
closest-pair distances still too high on PHerc0846B: `trace_numbers.py` sampled each cell 6 by 6 and added the grid
points, but never the cell edges between them, and s07's grid point (101, 149) lies 36.33 voxels from s01's cell edge
between grid points (2, 120) and (2, 121), not 37.2. **Done:** `trace_numbers.py` now measures the least distance
between every two surfaces exactly, on the grower's triangles, and skips only pairs it can prove are farther apart.
It gives s01 and s07 36.33 voxels at their nearest; the seven overlapping pairs, and s09 and s10, cross each
other; s01 and s09, s05 and s10, and s05 and s09 are 1.73, 1.67 and 3.18 voxels apart at their nearest.

A further independent review checked this with its own code (its own triangles, and exact fraction arithmetic for the
crossings): the geometry, the pruning and the skip rule are safe, and every distance above holds. It found the areas
within 4 voxels still sampled, 6 by 6 in each cell, which read the seven larger overlaps about 4 to 12 % low and the
four smallest further off, mostly low (s05 and s09 share 0.07 mm2, not "under 0.05"). **Done:** they are measured on
the same triangles, each cut 12 by 12 (cutting 24 by 24 changes none by more than 0.01 mm2): s10 and s01 about 67
mm2, s03 and s08 22 to 26, s04 and s07 12 to 15, and 1.1 to 1.2 cm2 covered twice in all. The README gives these. A
last independent review checked the new areas with its own code, bounding each one from both sides: every figure
holds.
