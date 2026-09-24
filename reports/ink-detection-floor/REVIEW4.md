# Fourth independent review: day 3 on PHerc0846B (24 Sep 2026, before its publication and run)

Reviewer: a separate Claude Code agent, read-only, given a written brief. Verdict and findings as returned (lightly
shortened, private paths removed); the response to each is in PREREG.md's amendment 1.

NOT READY

1. BLOCKER: the shams cannot see the texture the plants carry in. Plants bring PHerc0139 texture (a sheet with air)
   into dense PHerc0846B; shams bring PHerc0846B texture. A model reacting to foreign texture would lower the floor
   unnoticed (day 1's same-scroll shams already reached 0.566 at s = 1 with seed 42). So "the sham and clean checks
   still guard against the model reacting to texture" overclaims. Fix: add a sham arm from day 1's 12 PHerc0139 blank
   sham cores, same swap and k, and require its median in [0.40, 0.60] too.
2. SHOULD: "no point of one lies within 4 voxels of another" is false: s04 and s07 come within 0.8 voxels (17 points
   within 4), s01 and s05 2.6 (5), s01 and s04 2.2 (2); the QC printed "none" below 0.5 %. The window pick checks
   overlap within a surface only; shams 5 (s07) and 6 (s04) are about 2 voxels apart at their windows, 10 at their
   cores. Fix: correct it; add a 3D check and pick again, or disclose the pair.
3. SHOULD: the amendment names only the sheet rule as changed since the first draft; the depth shift, the pooling of
   targets and shams across surfaces, the cross-surface overlap rule and the reference control changed too. List each.
4. SHOULD: the "why" numbers are not the rule's measure and cannot be checked: day-1 target00's quoted profile is not
   its recorded one (65, 64, 62 ... 109 ... 73); the PHerc0846B one is a single row; the 0-of-40 draw has no script
   or log. The recorded day-3 profiles are nearly flat, as surfaces crossing sheets also give, so "this is the scroll,
   not the rendering" overclaims. Fix: quote recorded profiles and the selection log (0 of 25 cores pass; prominence
   0.5 to 5.7); claim only that the render settings match.
5. SHOULD: "taken in that order while they pass" says the pick stops at the first failure; the code skips. One core
   failed (s06, 7.8 % textureless). Fix: "a core that fails is skipped".
6. SHOULD: the inputs are not pinned: Kaggle attaches each kernel's latest output, and the job recorded render shapes
   only. Fix: check the four sha256 values from the dry run; check each core's profile against the window file.
7. NOTE: the smoke run also runs all seven whole surfaces, so it is the first model output on this scroll, not "one
   target". Say so or skip them.
8. NOTE: the control reads the primary direction only; the intact rule, called "unchanged", uses layer 14, not a
   sheet layer. Say both.
9. NOTE: the whole-surface jobs cannot change the scored ones (villa runs each job alone with per-patch
   normalisation, and "whole_" sorts last, so the split across GPUs is unchanged).

Checked and right: coverage on the surface layer, the grid, the boxes, no overlap within a surface (all 24), one
pooled seeded order, the 12 and 12 split, donor i mod 6. Dry run: done, no errors, 97 jobs, all four input hashes equal
to the local files, donors identical to day 1, k 0.556 to 1.294, clipping at most 1.4 %. The job's readout, run on
made-up AUCs, behaves as written (floors, "above 1", three "not read" cases). No dashes or private paths. Dropping the
depth shift keeps the donors' sheets (layers 11 to 14) where the model reads; no bias seen from it.
