# Fifth independent review: are review 4's findings fixed? (24 Sep 2026, before day 3's publication and run)

Reviewer: a separate Claude Code agent, read-only, asked to check each of review 4's findings and whether amendment 1
now matches the code. Verdict and findings as returned (lightly shortened, private paths removed); the response is
in PREREG.md's amendment 1.

READY WITH FIXES

Review 4's findings:
1. FIXED. The PHerc0139 sham arm is in the job and the rules: day-1 sham i, its own k, the same swap and mask, and it
   must read 0.40 to 0.60 at every strength.
2. FIXED. The rules match the surface QC. The close pair is disclosed; recomputed from the surface grids: 2.1 voxels at
   the windows, 10.2 at the cores. No other pair across surfaces comes within 19 voxels.
3. PARTLY. The list of changes since the first draft misses two: the intact-papyrus rule moved from the sheet layer
   to layer 14, and the rewrite deleted "Any region they mark is shown with the floor beside it".
4. PARTLY. The quoted profiles now match the records (65.4, 108.6 at layer 12, 73.4; 100.0 to 134.4; 0.5 to 5.7;
   peaks at layers 0 to 27; every day-1 core passes the sheet rule, the weakest at 7.12). But the rules said our
   renders use the team's `num_slices` 28; they use 31.
5. FIXED ("a core that fails is skipped").
6. FIXED. Four hashes pinned, all equal to the local files; each core's profile checked.
7. FIXED. The smoke run is stated as the first model output on this scroll.
8. FIXED. The control's direction and the intact rule's layer are stated.
9. FIXED. The scored results are saved before the whole-surface maps, which sit in a try block; the pinned villa code
   runs jobs in sorted order, so the whole-surface jobs run last.

New problems:
- A. SHOULD. "No floor is reported for this scroll" if a check fails, but the code decides per checkpoint. Write
  "for that checkpoint".
- B. SHOULD. The text fixes for 3 and 4 (render settings; put back the deleted sentence; list the intact-layer change).
- C. NOTE. villa's renderer centres its stack at (n - 1)/2 (vc_render_tifxyz.cpp, buildOffsetList): a 28-plane
  render puts the surface between planes 13 and 14, ours on 14, so "surface at layer 14, as in PHerc0139" may be half
  a voxel out. Say so.
- D. NOTE. "25 cores examined, one skipped": candidates whose windows overlap a taken one are passed over without
  being logged. Write "25 measured".
- E. NOTE. "10 voxels apart" is measured between grid points 20 voxels apart, so it is an upper bound.
- F. NOTE. Day 3 runs no transplant, and neither sham arm gets a depth shift. Say so.

Dry run of v2 (it arrived during the review): done, no errors, self-test passed; all four input hashes equal the pinned
values and all 24 profile checks passed; 133 jobs (6 references, 12 clean, 36 planted, 36 of each sham arm, 7 whole
surfaces); k 0.556 to 1.294, PHerc0846B sham k 0.689 to 1.851, PHerc0139 sham k 0.605 to 1.119; clipping at most
1.44 %. The five reader tests all agree. Three s01 core profiles recomputed from the local render match exactly.
