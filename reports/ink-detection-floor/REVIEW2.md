# Second independent review of the ink detection floor, day 1 (24 Sep 2026, before publication)

Reviewer: a separate Claude Code agent, read-only, given a written brief. Verdict and findings as returned; the
response to each is in PREREG.md's "Revisions" section.

READY WITH FIXES

1. BLOCKER: G1 still compares planted letters against letters in a different setting at the core edge
   (floor_kernel.py 341-359, 473-474). The donor's letter mask is cut at the core boundary; the plant puts those
   cut letters into near-blank papyrus, while the reference sees the same letters continuing into more text.
   41 to 76 % of each donor's letter pixels lie within 64 px of the core edge; 70 to 100 % within 128 px (one model
   patch). Outside the core the published map shows 12 to 42 % ink in donor windows, 1 to 10 % in target windows.
   Two effects pull opposite ways and could cancel. Fix: one "transplant" job per target (the donor's whole core
   swapped in); G1 = planted minus transplant; report transplant minus reference as the context gap.
2. SHOULD: PREREG's "its errors do not favour either" is false: ink the map misses (or misplaces by more than
   3 px) counts as a negative in place but is never copied into a plant, so mask errors lower only the reference.
3. SHOULD: the 16 px border is not "wider than any registration shift": only donors were registered. The 2.399 um
   canvases are 3.885 to 3.894 times the 9.362 um canvases, not 3.9025, so shifts grow with position; a fit on the
   donors predicts 17.8 and 19.2 px for target03 and target05 on w042. Every target and sham still stays under
   0.5 % ink at its predicted shift +/- 3 px, so no window changes. Fix: register every window, or reword.
4. SHOULD: the swap smooths the letters at s below 1 (a blend of two textures with weights 1 - s and s):
   0.81x at s = 0.25 and 0.77x at s = 0.5 in the dry-run jobs; its sham 0.64x to 0.78x. Fix: weights that keep
   texture level. PREREG's "0.83x to 1.34x" is out of date.
5. SHOULD: s = 1 still clips: additive s = 1 pushes 1 to 9 % of letter voxels to 0 in the model's layers and 0.8
   to 2.3 % to 255 near the sheet. Fix: log the clipped share per job and state it.
6. SHOULD: results.json cannot prove what ran: no hash of windows.json or masks.npz; checkpoints from Hugging
   Face's `resolve/main`, which can change. Fix: log input hashes, checkpoint sha256 or revision. villa's shipped
   config lists the training segments, so PREREG's "may be" can become a checked statement.
7. NOTE: the intact-papyrus measure is relative and checks one layer; shams sit near the limit (median 1.8 %,
   max 3.0 %), donors at 0.8 % (max 1.6 %); plant/sham texture ratio at s = 1 runs 0.66 to 1.59, no direction.
8. NOTE: G3 passes on a flat curve ("dose-response" overclaims); G0 is tested in the direction it just picked;
   a median sham near 0.5 can hide shams split high and low.
9. NOTE: the donor letters barely show at 9 um (mean under letters -0.12 to +0.21 texture SD). G0 failing is a
   real risk.
10. NOTE: registration is right (synthetic shifts recovered within 0.35 px; the flipped sign gives correlation
    near 0; map image sizes equal the level-3 shapes on all 7 segments). "within 0.02 px" overstates.
11. NOTE: the Kaggle side is sound (preds file names, uint8, full size; matches sweep_kernel v7, which ran 476
    smaller jobs in 2 h 44 min on 2 T4).

First review's findings: 1 FIXED, 2 FIXED, 3 FIXED, 4 FIXED (numbers stale), 5 PARTLY (see 1 and 2), 6 FIXED,
7 PARTLY (s = 1 clips), 8 FIXED, 9 FIXED, 10 FIXED.
