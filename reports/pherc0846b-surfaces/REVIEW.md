# Independent review of this release (24 Sep 2026, before publication)

Reviewer: a separate Claude Code agent, read-only, asked to check every claim in the README against the run records,
run `trace_numbers.py`, and look at every preview. Verdict and findings as returned (lightly shortened, private paths
removed), each followed by what was done.

READY WITH FIXES

1. BLOCKER. The README said the area measured from the stored grid was 55.72 cm2, 0.4 to 6.0 % less than the
   grower's, as if the grower over-reported. But every `meta.json` area equals the stored grid's area with each cell
   split into two triangles, to 1e-15; `trace_numbers.py` took each cell's flat area, a lower bound that ignores folds.
   **Done:** `trace_numbers.py` now measures the grid as the grower does and gets the same seven figures; the claim is
   gone.
2. BLOCKER. All seven `meta.json` had the segment id `probe_recipe`. VC3D skips a segment whose id it has already
   loaded (`VolumePkg.cpp`, "Duplicate segment id ... skipping"), so the seven would load as one. **Done:** each has
   its own id, `PHerc0846B_s01` to `PHerc0846B_s07`, the only change from the grower's output; `trace_numbers.py`
   checks the ids differ.
3. SHOULD. The overlap counts are grid points 20 voxels apart, so they are floors and the nearest distances ceilings.
   Sampled 6 by 6 per cell: s04 and s07 meet at 0.16 voxels over about 11 mm2, s01 and s05 at 0.12 over about 3 mm2,
   s01 and s04 at 0.34 over about 0.5 mm2; "barely touch" and "no other pair" still hold (the next closest pair is 38
   voxels apart). **Done:** `trace_numbers.py` samples every cell that could come within 4 voxels 6 by 6, and the
   README gives both measures.
4. SHOULD. "Seeds at least 12 mm apart" is false: s02 and s06, and s04 and s06, are 11.84 mm apart; the 12 mm rule
   applied to candidates, and the 7 of 14 include s01's seed, found again. **Done:** reworded as such.
5. SHOULD. All seven are the same grid of valid points, which would be 7.58 cm2 lying flat; the extra area is stretch
   and fold, and the largest, s07, is the worst surface. **Done:** said.
6. SHOULD. Each preview is stretched to its own 1st to 99.5th percentile, so brightness cannot be compared. **Done:**
   said.
7. SHOULD. No licence or credit: the catalogue lists the volume as CC BY-NC 4.0, and the previews are renders of it.
   **Done:** one line, the same licence.
8. First look: s01, s03 and s07 fair. s02 looks darker because of the stretch, set by a very bright fleck at the right
   edge; name the fleck. s04: crossed fibres cover the lower half, not two thirds. s06: the fibres are a tilted band
   through the middle. s05: add the swirls down the lower right edge and a small no-data patch at the top. **Done:**
   all four rows changed.
9. NOTE. The Kaggle working paths in `meta.json` are not private; keep them so the files match the run output.
   **Kept.**
10. NOTE. The published day-3 amendment repeats the grid-point touch figures and a total of 57.05 cm2. **Done:** an
    erratum with the day-3 results (the total is 57.06; the finer measure is given beside the grid-point one).
11. NOTE. The guide's route also refines by hand and flattens; these surfaces had neither. **Done:** said.

Checked and right: the catalogue ETag, and no PHerc0846B segments in it; the volume's eligibility; 9.362 um and
113 keV, and what the `ink_9um` models were trained on; builds, the 404 fallbacks, sha256 values, the 75-generation
limit and the render flags; every published file byte-identical to its run output; no long dashes, private paths
or lesson numbers; the disclosure line.
