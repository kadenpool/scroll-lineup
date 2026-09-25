# Independent review of this release (25 Sep 2026, before publication)

Reviewer: a separate Claude Code agent, read-only, asked to check every claim in three draft surface releases (the
PHerc0490B, PHerc0483B and 12-surface PHerc0846B ones) against the run records, run `trace_numbers.py`,
and look at every preview at full size. Verdict for the three together: READY WITH FIXES. The findings that concern
this release, as returned (lightly shortened), each followed by what was done:

1. SHOULD (PHerc0490B). "The m7 prediction is dense on this scroll, so neighbouring sheets merge" is not shown by the figure given: PHerc0846B's boxes are 18 to 32 % sheet and pass 13 of 32 places, PHerc0483B's 22 to 40 % and pass 6 of 33. **Done:** the comparison is given and the cause is left unmeasured.
2. SHOULD. The seeds are 21.97 mm apart at the closest, not "at least 22". **Done:** "about 22 mm".
3. SHOULD. The first look at s02 missed the swirls at the lower left and the dark gaps at the bottom. **Done.**
4. SHOULD. The flat-area caveat the PHerc0846B review asked for was missing: each grid would cover 6.45 cm2 lying flat,
  and the other 16 to 20 % of each area is stretch and fold (the review said 6 to 25 %, for both scrolls together
  and against the flat area). **Done.**
5. NOTE. "Session" should be plural; `render_covered` in `index.json` was not explained; a review line was needed.
  **Done.**

Checked and right: every area and total (`trace_numbers.py` matches to 0.01); the seeds and the survey counts; the
licence (CC BY-NC 4.0 in the catalogue, and no segments for this volume); eligibility (villa's list); every surface
byte-identical to its run output, each `meta.json` different only in its segment id, and the ids unique; no long
dashes, private paths or lesson numbers; the disclosure line.

## Later (25 Sep): the distances, measured exactly

A review of the files staged for publication (its re-check, in `../ink-detection-floor/REVIEW9.md`) found the
closest-pair distances still too high on PHerc0846B: `trace_numbers.py` sampled each cell 6 by 6 and added the grid
points, but never the cell edges between them, and s07's grid point (101, 149) lies 36.33 voxels from s01's cell edge
between grid points (2, 120) and (2, 121), not 37.2. **Done:** `trace_numbers.py` now measures the least distance
between every two surfaces exactly, on the grower's triangles, and skips only pairs it can prove are farther apart.
Here it confirms that no two surfaces come within 4 voxels; the closest, s01 and s03, are 977.8 voxels apart. A
further independent review, with its own code, confirmed the method and the 977.82.
