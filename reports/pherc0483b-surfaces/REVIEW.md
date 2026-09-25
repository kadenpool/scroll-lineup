# Independent review of this release (25 Sep 2026, before publication)

Reviewer: a separate Claude Code agent, read-only, asked to check every claim in three draft surface releases (the
PHerc0490B, PHerc0483B and 12-surface PHerc0846B ones) against the run records, run `trace_numbers.py`,
and look at every preview at full size. Verdict for the three together: READY WITH FIXES. The findings that concern
this release, as returned (lightly shortened), each followed by what was done:

1. BLOCKER (PHerc0483B). The build table and the text said all five used 24ca51b; the run records show s01 used 24ca51b and s02 to s05 used 6bbe6e2 (sha256 9100dfe0...), released later the same day. **Done:** table and text corrected.
2. SHOULD. The seeds are 12.998 mm apart at the closest, not "at least 13". **Done:** "about 13 mm".
3. SHOULD. "The closest pair, s03 and s05, stays 60 voxels apart": their grid points are 58.2 voxels apart; the script's closest-pair line used only samples inside cells. **Done:** the script now takes the grid points too, and the text says 58.
4. SHOULD. First look: s02 has crossed fibres only in a central block, about half, with swirls down the left side, the right edge and the bottom; s04 also has swirls at the lower left. **Done.**
5. SHOULD. The flat-area caveat the PHerc0846B review asked for was missing: each grid would cover 6.45 cm2 lying flat,
  and the other 6 to 12 % of each area is stretch and fold (the review said 6 to 25 %, for both scrolls together
  and against the flat area). **Done.**
6. NOTE. "Session" should be plural; `render_covered` in `index.json` was not explained; a review line was needed.
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
Here it gives s03 and s05 58.24 voxels at their nearest (58.2 in the README; the 58 of item 3 holds). A further
independent review, with its own code, confirmed the method and the 58.24.
