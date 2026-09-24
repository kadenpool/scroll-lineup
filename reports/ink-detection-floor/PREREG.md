# Pre-registration: an ink detection floor for the public 9 um ink models ("plant and recover")

Kaden Pool, with Claude Code under his direction. Written 22 Sep 2026 and revised before publication after three
independent reviews (their findings, and what changed, are listed at the end). No result had been seen when it was
published; one smoke run was started by mistake before publication, and its output has not been opened (see the
end). Rules below are fixed; any change after a result is seen goes in a dated amendment at the end, with the reason,
and the original rule stays visible.

## 1. The question

When the public 9 um ink models find nothing on an unread scroll, is that "no ink" or "no ink recovered yet"? The 2026
Open Problems page asks exactly this for June 2027. We measure it directly: take real ink from PHerc0139, where the
text is read, plant it into papyrus at graded strength, run the same models, and find the weakest ink they still
recover. Every claim is limited to **ink like PHerc0139's at 113 keV**; an unread scroll may carry different ink.

Day 1 answers only whether the method works: **do planted letters read at full strength, and read like the same
letters moved whole into the same papyrus, through the same model, while shams of the same shape read like
nothing?** Nothing is claimed about any other scroll until the day-1 gates pass.

## 2. Data (all public, vesuvius-challenge-open-data)

- PHerc0139 native scan `20250728140407` (9.362 um, 113 keV). Each segment's surface volume
  `surface-volumes/9.362um-1.2m-113keV-volume-20250728140407.zarr/0` is 28 layers (ZYX, uint8); the surface is meant to
  sit at plane 14, and each window's own sheet position is measured (below).
- **Only segments the models were not trained on.** villa's shipped training config for these checkpoints
  (`ink_detection/configs/aligned21_hybrid_3d2d.json`) lists, for PHerc0139, w016, w017, w028, w029, w035, w039, w040,
  w041 and w043 (2.4 um data aligned to 9 um) and w035, w039, w040, w041 and w044 (native 9.362 um); the `ink_9um`
  dataset card lists the same native set. None of these is used. Donors: w025, w026, w027. Targets: w036, w042, w045,
  w046. Shams: blank papyrus of w025, w026, w027.
- Letter masks come from the team's published 2.4 um ink map of each segment (`ink-detection/downsampled/*2.399um*
  new_canon*`, 1/8 of the 2.399 um canvas), carried onto each 9.362 um window by the voxel ratio (9.362 / 2.399) from a
  shared origin plus a shift measured for that window by matching the two scans' own surface images (the 9.362 um
  plane 14 against the 2.399 um level-3 middle plane: a correlation search, refined below a pixel by a parabola
  through the peak). Every window, donor, target and sham, is registered this way, and one whose match scores below
  r = 0.3, or that lies too near the canvas edge to register, is not used. For a blank window the shift is used to
  check that it is blank where the map really is.
- Known limits, stated now: the map is a model output, not a human label, and its errors do not cancel. Ink it misses
  stays among the negatives of the letters in place and of the transplant (section 5) but is never planted, so it can
  make planted letters read better than real ones. G1 is decided by its AUC rule alone; beside it we report a
  letters-only comparison (the model's median output on M, planted at s = 1 against the transplant, from the kept
  maps), which ink the map misses cannot move. Masks are only as good as the map and the registration.

## 3. Models and inference (fixed)

- `ink_9um` checkpoints `hybrid_3d2d-seed42/step-010000.pth` and `hybrid_3d2d-seed43/step-060000.pth` (the pair used in
  the ink-negative-controls report), run through villa's `vesuvius.ink_detection.inference.infer` as that report's
  harness does (overlap 0.5, hann blending, batch 8, both directions), on 21-layer volumes cut as layers [4, 25).
- Readout uses the raw model maps (the models' no-ink output sits near 0.25; no rescaling). The raw maps, cropped to
  each 512 px core, are kept with the results, with the sha256 of `windows.json`, `masks.npz` and both checkpoint
  files.
- The checkpoints are pinned: Hugging Face revision `7109667e2607db1b90c37c8b09cb876ea7fe7bb1`, sha256
  `5d0896899092f312299c988de5861a5b6d3669112ee2a4976e2ecf44d4fe3664` (seed 42) and
  `bf229faf754da3f1fc3026a3f9a9649341aeb3feb7bc89099cad31c55525d270` (seed 43). The run stops if a downloaded file does
  not match.
- Direction: both are always reported. The primary direction, per checkpoint, is the one with the higher median AUC on
  the references (the donors' letters in place). The planted letters keep the donors' orientation, so it applies to them.
  Because it is the better of two, G0 is read in the direction chosen for it.
- `hecate` 9.6 um (`hecate_9.6um.pth`, run with the model card's own `hecate.py`) is added on day 2 under the same
  rules, on its own jobs: each finished 28-layer volume resampled from 9.362 to 9.6 um in all three directions, then
  `hecate.py` reads its central 16 planes, forward and with `--reverse`; masks carried to that grid by nearest neighbour.

## 4. Windows (fixed rules; the seed is fixed so the choice can be repeated)

- Cores are 512 x 512 px (4.8 mm), each inside a 1024 x 1024 px model window centred on it (clamped to the canvas);
  whole windows do not overlap. Drawn with numpy seed 20260922 from positions on a 64 px grid where plane 14 is non-zero
  on at least 99 % of the core.
- **A clear sheet:** every core's mean-intensity profile over its 28 layers (smoothed over 3) must peak at layer 10 to
  17 and stand at least 7 grey levels above its own median. (Set from intensity profiles of candidate cores on 22 Sep,
  not from any model output: most peak at 11 to 14 by 7 to 29 levels; a few peak at layer 0 or 6, on a neighbouring
  sheet.)
- **Intact papyrus:** at most 3 % of every core's sheet layer may be without papyrus texture (the local standard
  deviation over 9 px under a quarter of that layer's median). Such areas are air in a crack or gap, which the ink map
  calls blank: without this rule a sham or target could carry holes in letter shapes, and a donor's own score could
  gain easy negatives. (Set on 22 Sep from the first chosen cores, before any model run: 0.4 to 9.9 % on donors,
  0.1 to 11 % on shams, 0.1 to 8.8 % on targets.)
- **Donors (6):** 2 cores on each donor segment where the published map marks 15 to 45 % of the core as ink.
- **Targets (12):** 3 blank cores on each target segment: at the window's own measured shift, and at that shift
  moved 3 px either way, the published map marks under 0.5 % of the core, and of the core with a 16 px border round
  it, as ink. Target i uses donor i mod 6.
- **Shams (12):** blank cores on the donor segments (4 on each), same rules, one per target.
- **A segment that cannot supply its share** under these rules gives what it can, and the shortfall is drawn from the
  other segments of the same kind, in the order listed above. (On 24 Sep, before any run, w042 could supply only 2
  of its 3 targets under the registered blank rule; the record is `shortfall` in `day1/windows.json`.)
- The chosen windows, their sheet profiles and registrations, and the ETags of the catalogue and the published maps
  they were drawn from, are in `day1/windows.json`; the masks in `day1/masks.npz`. Both are made by `prep_day1.py` and
  published with this file before any run.

## 5. Plants

Let V be a 28-layer core (float). M is the donor's ink mask (published map above 0.5 on the donor core); N, its
negatives, is every core pixel outside M dilated by 3 px (the band at the letter edges is left out of everything).

- **Background:** for each layer, B = a normalised Gaussian smoothing of V (sigma 48 px, 0.45 mm, wider than a stroke)
  with weights 1 on N and 0 elsewhere. Target and sham cores use the same N shape in their own frame.
- **Residual:** R = V - B on all 28 layers (R_donor, R_target, R_sham).
- **Texture scale:** k = robust standard deviation (1.4826 x MAD) of the target core's residual (layers [4, 25), B with
  weights 1 everywhere) divided by that of R_donor on N. k_sham is the same with R_sham in place of R_donor. Values
  away from 1 are expected (targets differ); they are reported per target.
- **Depth:** R_donor is shifted in depth by (target sheet layer - donor sheet layer), and R_sham by (target sheet layer -
  sham sheet layer), so the planted sheet lies on the target's own sheet. The layers a shift empties get zero residual
  (the smoothed background only); on day 1 no shift is larger than 3 layers, so they all lie outside the 21 the model
  reads.
- **Mask edges:** M softened by a Gaussian of 2 px (M_soft); scoring always uses the binary M and N.
- **Additive plant:** V' = clip(V_target + s * k * R_donor * M_soft, 0, 255), rounded, placed on the target core.
- **Swap plant:** V' = clip(V_target + M_soft * ((sqrt(1 - s^2) - 1) * R_target + s * k * R_donor), 0, 255): the donor's
  residual goes in at amplitude s, and the target's own residual under the letters is scaled by sqrt(1 - s^2), so that
  the two, being unrelated, keep the texture level; at s = 1 the target's texture under the letters is replaced by the
  donor's. The additive plant raises the texture under the letters (the target's stays and the donor's is added). The
  shams at every strength control for both.
- **Clipping:** at s = 1 some voxels reach 0 or 255. The share of changed voxels that clip, in the 21 layers the
  model reads, is logged for every job and reported (in the dry run's target at s = 1: 4.7 % for the additive plant,
  1.3 % for the swap, 1.5 % for the transplant).
- **Transplant:** for each target, the donor's whole core swapped in (the swap at s = 1 with a mask of ones): the same
  letters with the papyrus between them, cut at the same core edge and sitting in the same surroundings as the plants.
  The letters in place continue past the core into more text; a planted target's surroundings are blank. The
  transplant takes that difference out of G1.
- **Strengths:** s = 0.25, 0.5 and 1, for both plants; s = 0 is the untouched target.
- **Shams:** at every strength and for both plants, the same plant with R_sham (blank papyrus) in place of R_donor,
  through the same M_soft, with k_sham. It carries papyrus texture in letter shapes, and no ink.
- **Each donor's ink contrast** (the mean of R_donor on M minus on N, per layer, in units of the donor's texture SD) is
  logged in full, and reported per donor.

## 6. Readout

- **Reference AUC:** each donor window read unmodified; pixel AUC of the raw map, positives M, negatives N.
- **Planted, sham, transplant and clean AUC:** the same, with the donor's M and N placed on the target core.
- **Context gap:** transplant AUC minus its donor's reference AUC, reported per target and as a median.
- Medians are over windows. A gate is read only if every job has a score in both directions for that checkpoint;
  otherwise the run is reported as incomplete and no gate is read.

## 7. Gates (per checkpoint and plant, in the primary direction)

- **G0 (the model reads these letters in place):** the median reference AUC is at least 0.70.
- **G1 (planted letters read like the same letters moved whole):** the median, over targets, of (planted AUC at s = 1
  minus that target's transplant AUC) lies within +/- 0.05. Reported beside it: planted minus the donor's reference in
  place, and the context gap.
- **G2 (shams read like nothing):** the median sham AUC lies in [0.40, 0.60] at every strength (two-sided: a sham that
  reads below 0.40 shows the model reacting to the shape too). The spread of sham AUCs (interquartile range) is
  reported beside the median, so shams split high and low cannot hide behind it.
- **G3 (a dose-response):** the clean median lies in [0.40, 0.60]; the median planted AUC does not fall by more than
  0.02 from one strength to the next (s = 0, 0.25, 0.5, 1); and at s = 1 it is at least 0.70, so the planted letters
  read. (Without this last part, letters lost in the moving would pass G1, since the transplant would lose them too:
  the third review showed G0 to G3 passing with plants and transplants at 0.53.)
- **Day-1 go:** G0 to G3 pass for at least one checkpoint with at least one plant. The plant carried forward is the
  swap if it passes, otherwise the additive. If neither passes: no-go, and the finding is published as it stands.
- **Before the full run,** one smoke run on one target (both checkpoints) checks the pipeline end to end; its numbers
  are not used and are reported as such.

## 8. The floor (used from day 3, only if day 1 passes)

For each scroll and model setting: the planted AUC curve over s; the **detection floor** is the smallest s whose
median planted AUC reaches 0.70, and the **clear floor** the smallest reaching 0.80 (linear interpolation between grid
points; "above 1" if never). Both are always reported with the curve.

## 9. What we will not do

No gate, threshold, window, strength or metric changes after seeing a planted result, except by a dated amendment
that says what was seen. On later days, a run whose reference AUCs differ from day 1's by more than 0.01 (same windows,
same checkpoint) is not read: a moving control means the run is not comparable.

## Revisions before publication, first round (22 Sep, from the first independent review; no run existed)

The first draft planted w035's labelled letters into w040 and w041 and compared them with those segments' own labelled
text. The review found, and we checked, that the `ink_9um` dataset card lists w035, w039, w040, w041 and w044 as native
9.362 um training labels "used as-is": the first draft's claim that the model never saw this scan was wrong. So every
window now sits on a held-out segment, and the letters are compared with themselves in place. Also from the review: the
sheet in several first-draft targets sat at layers 4 to 9 while the donor's ink sat at 11 to 13, so plants are now
depth-matched and cores need a clear central sheet; one sham core served all targets, so each target now has its own,
at every strength, with a two-sided gate; the swap does not keep texture level (the first draft said it did); gates no
longer use s = 2, where letter voxels clip; the raw maps are kept; a missing score now stops the gates; and only a 404
from the bucket counts as an unwritten chunk.

## Revisions before publication, second round (22 to 24 Sep; no result had been seen)

Three changes came from checking the data. The registration first used phase correlation, which put the sub-pixel part
of the shift the wrong way and missed a 5.4 px test shift; it is now a correlation search refined by a parabola, and
the second review, running an exact copy, recovered synthetic shifts within 0.35 px. Blank cores must also be blank
over a 16 px border. And every core must be intact papyrus (section 4): a dry-run render showed a sham pasting a hole
in the papyrus, air in a crack that the ink map calls blank, into letter shapes.

A second independent review then read the rules, the code and the chosen windows (`REVIEW2.md`). It found that G1
compared letters cut at the core edge and set in blank papyrus with the same letters continuing into more text, so
each target now also gets a transplant and G1 compares the plants with it. It found that the swap blended two textures
in a way that lowered the texture at s below 1, so the swap now keeps the level; that s = 1 still clips some voxels,
which is now logged; that the results could not prove which inputs and checkpoint files ran, which they now record;
and that two sentences overclaimed: that the map's errors favour neither side, and that the 16 px border was wider
than every shift. Only donors had been registered, and the shifts grow with position because the two scans' canvases
differ slightly in scale. Registering every target and sham after selection found shifts up to 19 px, one sham just
over the blank rule (0.53 % at its own shift) and six windows that could not be registered reliably, so every window
is now registered when it is chosen and checked at its own shift (section 4). The review also confirmed from villa's
shipped training config that none of our segments was trained on (section 2).

A third independent review (`REVIEW3.md`) found that, with the transplant, day 1 could pass with planted letters that
read at chance, since a transplant that loses the letters loses them too; G3 now also requires the planted letters to
read at s = 1 (section 7). It also found that the blank check at each shift tested the core with its border but not
the core alone, which the rules promise; that G1 needed a rule, not a caution; and that the checkpoints should be
fixed in advance. All are now in the rules. The targets and shams were then chosen again with every rule applied: w042
could supply only 2 targets, so the rule for a short segment was added (section 4). The donors, their registrations
and their masks did not change (`masks.npz` is byte for byte the same; the records agree to within 1e-13). Every
target and sham was registered again afterwards, apart from the pick, and all pass (r 0.33 to 0.87; the worst ink
share 0.49 %). On day 1 no depth shift exceeds 3 layers, so the shift never empties a layer the model reads.

One mistake: on 24 Sep, while checking how the notebook is built, a smoke run of an earlier version of the code (one
target, both checkpoints) was pushed to Kaggle by accident, before this file was published and before the second
review's changes. Its output holds the six references' AUCs, which are G0's numbers, so it will not be opened before
the full run has finished, and it is not used. The smoke run required by section 7 runs on the published code, after
publication.

## Amendments

(none)
