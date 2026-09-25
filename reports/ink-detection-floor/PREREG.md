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

### Amendment 1 (24 Sep 2026): day 3, the floor on PHerc0846B

Written after day 1 passed (its results are in `RESULTS_DAY1.md`) and before any ink model had run on PHerc0846B. A
first draft was committed before the day-1 run. Since then, and before any model output on this scroll was seen, these
rules changed: the day-1 sheet rule was dropped, plants go surface to surface with no depth shift, and the
intact-papyrus rule is measured on the surface layer rather than a sheet layer (all three because of PHerc0846B's
depth profiles, below); targets and shams come from one pooled order over all seven surfaces, with an even split if
fewer than 24 pass; the draft's rule for surfaces covering the same papyrus was replaced by the measured touches,
below; the six day-1 references are run again as a control; and, after two more independent reviews (`REVIEW4.md`,
`REVIEW5.md`), a second sham arm of PHerc0139 papyrus was added and the inputs were pinned. The windows
(`day3/windows_day3.json`) were chosen by `prep_day3.py` before this was published; the job is `floor_day3.py`, built
from the day-1 job by replacing only the day-3 parts.

#### Why this scroll

PHerc0846B is a First Letters-eligible scroll with no public surfaces. Its eligible volume `20250804142305` was
scanned at 9.362 um and 113 keV, the voxel size and energy of PHerc0139's native scan, where the `ink_9um` models and
the day-1 donors come from. So a floor measured here needs no resampling and no change of energy.

#### Data

- Surfaces: our seven PHerc0846B surfaces (s01 to s07), each grown with villa's `vc_grow_seg_from_seed` on the team's
  published m7 surface prediction and its normal grids, step 20, 75 generations, from seeds (x, y, z) 3240, 3763, 7407
  (s01); 4231, 4731, 7422; 2647, 4752, 6832; 4207, 3214, 8143; 4336, 3439, 6640; 3719, 4324, 8504; 2998, 3154, 8630
  (s02 to s07); 7.62 to 8.89 cm2 each, 57.05 cm2 in all. They barely touch: of about 21,900 grid points each (one per
  20 voxels), 17 points of s04 lie within 4 voxels of s07 (nearest 0.8), 5 of s01 within 4 of s05 and 2 of s01 within
  4 of s04. The surfaces' files are published with the day-3 results.
- Renders: villa's `vc_render_tifxyz`, 31 planes, `--flip-normals`, `slice_step` 1.0 on the level-0 scan; we keep
  planes [1, 29), 28 layers, like the team's PHerc0139 volumes. villa's renderer centres its stack at (n - 1)/2, so
  our surface lies on layer 14, while in a 28-plane render it lies between layers 13 and 14: the two layouts may
  differ by half a voxel (4.7 um). We do not correct for it.
- The seeds came from a picker that looks for a thin sheet on the prediction inside the scroll, away from its edge;
  s01 was grown first, and s02 to s07 after the first draft of these rules, with seeds from the same picker at least
  12 mm apart. Nothing about them was chosen by looking at ink.
- Nothing else about the scroll is used: no ink map exists for it.

#### Windows (fixed rules; numpy seed 20260924)

- Cores 512 x 512 px inside 1024 x 1024 px windows, as on day 1, on a 64 px grid where the surface layer (layer 14) is
  non-zero on at least 99 % of the core; whole windows on the same surface do not overlap.
- Intact papyrus, as on day 1 but measured on the surface layer (layer 14) rather than a sheet layer: at most 3 % of
  it textureless. The day-1 sheet rule does not apply here (see below).
- All candidate cores of all seven surfaces are pooled and put in one order by the seed; a candidate whose window
  overlaps one already taken is passed over, a core that fails is skipped, and the first 24 that pass are taken. The
  first n are the targets and the next n the shams, n = 12, or half of those taken if fewer than 24 pass; target i has
  sham i and uses day-1 donor i mod 6. If n is under 6, day 3 is not run, and that is reported. (A 3040 px canvas
  holds at most 4 whole 1024 px windows that do not overlap, so 7 surfaces hold at most 28.)
- With no ink map, "blank" cannot be checked: a target may hold real ink. The clean readout measures that, target by
  target.
- The pick (`day3/prep_day3.log`): 25 cores measured, 24 taken, one failing the intact rule (s06, 7.8 % textureless).
  Two shams on different surfaces come close: sham 5 (s07) and sham 6 (s04) lie within 10 voxels of each other at
  their cores and within 2 at their windows (measured between grid points 20 voxels apart, so these are upper bounds);
  they are kept, as the rules say, and this is stated here.

#### Why the day-1 sheet rule is dropped here

On PHerc0139 the team's surface volumes show a papyrus sheet with air on both sides: day-1 target00's recorded profile
(`day1/windows.json`) runs from 65.4 up to 108.6 at layer 12 and back to 73.4, and every day-1 core peaked at layer 10
to 17 by at least 7 grey levels. On PHerc0846B none of the 25 day-3 cores measured would pass that rule: their
recorded profiles (`day3/windows_day3.json`) are nearly flat, between 100.0 and 134.4, standing 0.5 to 5.7 levels
above their own median, with peaks anywhere from layer 0 to 27. Densely packed papyrus would give flat profiles; so
could a surface that crosses from one sheet to another, which parts of these surfaces do (their previews show swirls
there); we do not claim which. Kept as it was, the rule would stop day 3 on this scroll.

#### Plants, strengths, checks, readout

- The six day-1 donors (PHerc0139), unchanged, and the swap plant, carried forward from day 1, with the day-1 rules
  for background, residual, texture scale and edges.
- Depth: surface to surface. No depth shift for the donor or for either sham: each residual goes in at the same
  layers, since both layouts put the surface at layer 14 of 28 (to within the half voxel above). Day 3 runs no
  transplant.
- Strengths 0.25, 0.5, 1 as on day 1; s = 0 is the untouched target.
- Two shams per strength, both through the same swap and mask: one of PHerc0846B papyrus (sham i, with its own k), and
  one of PHerc0139 papyrus (day-1 sham i, blank and on a held-out segment, with its own k), because the planted
  letters bring PHerc0139 texture into this scroll and a model that reacts to foreign texture would otherwise lower
  the floor unseen.
- Direction: each checkpoint's primary direction from day 1 (forward for both). Both directions are kept.
- Control: the six day-1 references are run again; if any of a checkpoint's reference AUCs, in its primary direction,
  differs from day 1's by more than 0.01 (section 9), that checkpoint's day-3 run is not read.
- Checks before any floor is read, per checkpoint: the median clean AUC, the median PHerc0846B sham AUC at every
  strength and the median PHerc0139 sham AUC at every strength all lie in [0.40, 0.60]. If any fails, no floor is
  reported for that checkpoint, and the reason is.
- The floor, as section 8: the detection floor is the smallest s whose median planted AUC reaches 0.70, the clear
  floor 0.80 (linear between grid points; "above 1" if never), always reported with the curve.
- Inputs pinned: the job stops unless `windows.json`, `masks.npz`, `day3/windows_day3.json` and day 1's `results.json`
  have the sha256 values written into it (c3e90e83..., f87c5cf9..., 278eae90..., 61f6af77...), and unless every
  target's and sham's 28-layer profile in the render matches the one the pick recorded.

#### The models' own output on the whole surfaces

Both checkpoints are also run over the seven whole rendered surfaces, both directions, and the raw maps are published
as they are. We claim no letters from them. Any region they mark is shown with the floor beside it; a reading of
letters is left to people who read Greek papyri. As on day 1, one smoke run on one target checks the pipeline first;
it also runs the whole surfaces, so it is the first model output on this scroll. Its numbers are not used; the readout
and the published maps come from the full run.

#### Erratum to amendment 1 (24 Sep 2026, published with the day-3 results; no rule changes)

Two figures under "Data" were wrong or coarse. An independent review of the surfaces' own release found them before
that release was published (`reports/pherc0846b-surfaces/REVIEW.md` in this repository). No rule uses either.

- "57.05 cm2 in all" should read 57.06 cm2: 57.05 is the sum of the rounded figures.
- The touch figures count grid points 20 voxels apart, so the counts are floors and the nearest distances ceilings.
  Sampled 6 by 6 in each cell (the release's `trace_numbers.py`), s04 and s07 meet within 0.16 voxels and share about
  11 to 13 mm2 within 4 voxels of each other; s01 and s05 meet within 0.12 voxels over about 3.5 mm2; s01 and s04
  within 0.34 voxels over less than 1 mm2; the closest other pair stays 38 voxels apart.

### Amendment 2 (25 Sep 2026, before any day-2 result was read): day 2, hecate 9.6 um

Section 3 fixed day 2 in one sentence: `hecate` 9.6 um is added under the same rules, on its own jobs, each finished
28-layer volume resampled from 9.362 to 9.6 um in all three directions, `hecate.py` reading its central 16 planes,
forward and with `--reverse`, and the masks carried to that grid by nearest neighbour. This amendment fixes what that
sentence left open. Nothing in the day-1 rules changes. A seventh independent review, of the job and of an earlier
draft of this text, found problems (`REVIEW7.md`): each is fixed here or, for a few harmless leftovers, stated in that
review; an eighth (`REVIEW8.md`) checked the fixes, and a ninth (`REVIEW9.md`) the files staged for this publication.

**What had been run before this was published.** Two smoke runs of the day-2 job, on one target each, ran on
Kaggle before publication: the first (version 1 of the job, since changed) to check the pipeline, the second
(version 2, the job below) to check it again and to time it. Their outputs were downloaded but their scores (AUCs,
means, gates) were not opened: only their status, errors, job counts, map shapes and timings were read, by a script
that prints no score. The watcher's own logs of the two runs also hold the summary table; they were not opened either,
and are kept out of the repository until this is public. Both smoke runs also score the six day-1 reference windows, which the full run's G0 reads; that
is why their scores stay closed until this amendment is public.

#### The model and its code, pinned

- `scrollprize/hecate` on Hugging Face at revision `9cb86e500e944b11a06a7020403cde5dffb5bcb2` (15 Sep 2026):
  `hecate_9.6um.pth`, 522,576,086 bytes, sha256 `809f4f10f7cb7afa19b4bee0f7d2ab31edd7e11b664f9f210cc9c17f22fcfe5d`;
  `hecate.py`, sha256 `c232c18a1a86cfb91257a00db13288202bb8ae33732ba26f7291a9b8adb8da59`. The job stops unless both
  match, and unless its inputs are day 1's (`windows.json` `c3e90e83...`, `masks.npz` `f87c5cf9...`).
- The job calls the card's own `hecate.load_model` and `hecate.predict` (what its command line runs), once per job
  and direction, in float32 (the card's default; Kaggle's T4 GPUs have no native bfloat16), 32 patches per batch,
  the card's default XY stride (half a patch).

#### The jobs

- Every day-1 job, built by day 1's own code from the same inputs: references, clean targets, both plants at three
  strengths with their shams, and the transplants.
- Each job's finished 28-layer volume is resampled to exactly 9.6 um in all three directions, by linear
  interpolation (`scipy.ndimage.affine_transform`: output voxel i sits at input voxel i x 9.6 / 9.362), onto a grid
  of 27 x 998 x 998 that lies wholly inside the input. `hecate.py` then reads the central 16 of the 27 planes:
  planes 5 to 20 forward, and planes 6 to 21 in reverse order with `--reverse`. In the planted and transplant jobs
  the letters sit on the target's measured sheet, layers 10 to 13 (median 12), which this grid carries to planes
  9.8 to 12.7 (median 11.7): about 1 plane from the middle of the forward window (12.5) and 2 from the reversed one's
  (13.5), inside both; the references' donor sheets lie at layers 11 to 14. This follows from section 3's wording
  and the card's own window; it is stated, not changed. The clipped share and the recorded `layers` stay day 1's
  [4, 25), which hold every layer that hecate's two windows reach (5 to 22).
- Each job's letter mask and background mask are carried to the 998 x 998 grid by the same map, nearest neighbour,
  and scored by day 1's pixel AUC. The kept core maps are 499 x 499 (section 3 says 512 for day 1), and each job's
  core masks on that grid are kept beside them, so a reader can score them without resampling again.

#### Held out, as far as can be known

Section 2 uses only segments a model was not trained on. For `hecate` this can be checked only in part:

- Its model card says development used the Scroll Prize ink dataset and scans from the Vesuvius Challenge open-data
  collection. In that dataset (Hugging Face bucket `scrollprize/datasets`, folder `ink`, listings of 25 Sep saved as
  `day2/ink_bucket_0139_20260925.json`, `day2/ink_bucket_unused_0139_20260925.json` and, one level down for our
  seven segments, `day2/ink_bucket_segments_0139_20260925.json`), the PHerc0139 folder holds
  11 segments (w016, w017, w028,
  w029, w030, w035, w039, w040, w041, w043, w044), none of ours; all seven day-1 segments (w025, w026, w027, w036,
  w042, w045, w046) are in the folder `ink/unused/0139`, where each segment's folder holds its render and a `preds` folder
  of model predictions, but no ink labels (a labelled folder, such as w041's, holds `inklabels` and
  `supervision_mask` files).
- The 9.6 um model learned from its 2.4 um sibling's outputs, not from labels, including on renders of native coarse
  scans supervised by the fine scan's predictions "where both scans were available"; PHerc0139 has both scans, and
  the card does not list which segments were used.
  If ours were among them, the model may have learned its teacher's reading of these very letters. And our letter
  masks come from the team's 2.4 um ink map (the `ink_canonical_2um` family, `hecate`'s base model), so the masks and
  the model share an ancestor; that could raise `hecate`'s scores on the references and the transplants. Neither can
  be ruled out; both are stated beside every day-2 result.

#### Cost

The review counted about 426 GFLOP a patch, 1,922 patches a job and 174 jobs. The timed smoke run (version 2, one
target, 20 jobs) took 49.6 minutes of inference on two T4s, about 5.0 minutes a job on each GPU (the first version,
in emulated bfloat16, took 8.3), so the full run takes about 7.5 hours in one session, inside Kaggle's 12-hour
limit; it is not split.

#### Readout

Day 1's gates, unchanged, for `hecate_9.6um` as the one checkpoint: G0 to G3 per plant, the primary direction the
one with the higher median reference AUC. The smoke runs' numbers are not used.

### Second erratum to amendment 1 (25 Sep 2026, published with the surfaces' update; no rule changes)

More figures about the surfaces were wrong, in amendment 1's "Data" and in the first erratum. No rule uses any of
them.

- The seeds of s01 to s07 are not all at least 12 mm apart: s02 and s06, and s04 and s06, are 11.84 mm apart. The
  surfaces' own release says so (at least 11.8 mm).
- In the first erratum, the closest other pair among s01 to s07, s01 and s07, is 36.3 voxels apart at its nearest,
  not 38. That figure came from samples, which can only overstate a least distance; the surfaces' `trace_numbers.py`
  now measures it exactly, on the grower's triangles. The first erratum's nearest distances for the pairs that meet
  are upper bounds and still hold; measured exactly, s04 and s07, s01 and s05, and s01 and s04 cross each other. Its
  areas came from samples too, which read them low: on the triangles, s04 and s07 share 12 to 15 mm2 within 4 voxels
  of each other (not 11 to 13), s01 and s05 3.7 to 3.8 mm2 (not about 3.5), and s01 and s04 under 1 mm2, as it says.

### Amendment 3 (26 Sep 2026, before any model has run on PHerc0483B): day 4, the floor on PHerc0483B

Written after day 3's results were published (`RESULTS_DAY3.md`) and before any ink model had run on PHerc0483B. The
renders and the windows below were made before this was published, by private CPU jobs that run no model; the job is
`floor_day4.py`, generated from the day-3 job by `make_day4.py` through exact-match replacements, so everything not
named below is day 3's. Two independent reviews of this amendment, the windows and the job found problems, each fixed
or stated here (`REVIEW11.md`).

**What had been run before this was published.** The ten render jobs and the window pick described below, and one dry
run of the day-4 job on Kaggle's CPUs with no model: it built all 182 jobs (80 in each arm, the six references, the
six scale references and the ten whole surfaces) without an error, its self-tests passed (the resampler's among
them), k came to 0.83 to 0.96 in arm A and 0.86 to 0.99 in arm B, and at most 0.23 % of the changed voxels were
clipped. No model has run on PHerc0483B.

#### Why this scroll

PHerc0483B is a First Letters-eligible scroll whose only surfaces are our five, published on 25 Sep. Its one volume,
`20251124083638`, was scanned at 8.64 um and 116 keV: a voxel about 8 % smaller than PHerc0139's 9.362 um, where the
donors and the models' native training data come from. It has no finer scan, so models made for ~9 um scans are the
ones that can read it, and villa's code would read it at 8.64 um: it never rescales by voxel size. Day 4 measures the
floor one step away in voxel size, with and without resampling.

#### Data

- Surfaces s01 to s05 as published: villa's `vc_grow_seg_from_seed` on the team's m7 prediction (model 20260413222639,
  level 0, threshold 0.2) and its normal grids, step 20, 75 generations, from seeds (x, y, z) 4881, 3280, 6384 (s01);
  1975, 3900, 6392; 6424, 3971, 7042; 3664, 5875, 4624; 5808, 3247, 8208 (s02 to s05); 6.84 to 7.33 cm2 each, 35.42
  in all. No two come within 4 voxels (the closest, s03 and s05, 58.2 voxels apart, measured on the triangles).
- Renders: villa's `vc_render_tifxyz` on level 0, 31 planes, `--flip-normals`, planes [1, 29) kept as 28 layers with the
  surface on layer 14 (amendment 1's half-voxel note applies), two per surface: arm A with `--scale 0.92288
  --slice-step 1.0835648`, 9.362 um per pixel and per plane (2806 px canvas); arm B with `--scale 1 --slice-step 1`,
  8.64 um (3040 px), the settings the surfaces were first rendered with. All ten were made on 25 Sep with one VC3D
  build, 75c79ac (AppImage sha256 `19bc7e18df269bc68b19b8c637aa9124d87ff30c3f1997bd50295489f03bf805`); each render's
  own metadata gives its pixel size (9.362 or 8.64 on every axis), and each arm-B render repeats the 31 plane means its
  grow run recorded (the same to the two decimals both records keep; the limit is 0.01).
- Nothing else about the scroll is used: no ink map exists for it.

#### Two arms, one set of windows

- Arm A (primary): day 3's jobs on the arm-A renders, with the donors, masks and PHerc0139 shams as they are: the floor
  at 9.362 um, the voxel size of the models' native training scans (most of their training data was pooled to about
  9.6 um).
- Arm B (secondary): the scan at its own 8.64 um, with every length the rules give in pixels kept at its physical size.
  The donor-frame arrays are resampled to 8.64 um in all three directions (the donor residual, the PHerc0139 sham
  residual and M_soft linearly; M and N by nearest neighbour): voxel (z, y, x) of a 28 x 554 x 554 arm-B core takes the
  value at (14 + (z - 14) r, 255.5 + (y - 276.5) r, 255.5 + (x - 276.5) r) of the donor's 28 x 512 x 512 core,
  r = 8.64 / 9.362, always inside it. The PHerc0139 sham is resampled like the letters, so it controls for the
  resampling too. Target and sham backgrounds use sigma 52 px (section 5's 0.45 mm). k is day 3's formula, computed on
  the resampled residual.
- Scale references (arm B): the six day-1 donor windows resampled whole the same way (1109 px), masks carried, read in
  place. Reported beside arm B; not a gate.
- The difference: for each checkpoint whose control holds and whose checks pass in both arms, the median over targets
  of (arm A minus arm B) AUC at s = 0, 0.25, 0.5 and 1, with every target's value. Descriptive; no threshold.
- The kept core maps are 512 x 512 in arm A and 554 x 554 in arm B and for the scale references; arm B's masks are not
  kept, and are rebuilt from `masks.npz` by the job's own resampler (`to_b`). For the scale references the kept 554 px
  crop leaves out one row and one column of the carried mask, so scores recomputed from their kept maps can differ
  slightly from the job's.

#### Windows (fixed rules; numpy seed 20260926)

- One pick, on the arm-A renders, by day 3's rules unchanged: 512 px cores in 1024 px windows on a 64 px grid; layer 14
  non-zero on at least 99 % of the core; whole windows on one surface do not overlap; at most 3 % of layer 14
  textureless. All candidates of the five surfaces are pooled in one seeded order; one overlapping a taken window is
  passed over, one that fails is skipped, and at most 24 that pass are taken; n is 12, or half of those taken if fewer
  pass; target i has sham i and donor i mod 6. Under 6 targets, day 4 is not run, and that is reported.
- Each window is carried to arm B about its core's centre, times 9.362 / 8.64: a 554 px core in a 1109 px window,
  clamped to the canvas, again at least 99 % covered. The pick records each core's 28-layer profile in both arms, and
  the correlation of layer 14 between them (arm B resampled onto arm A's grid); it stops if any is under 0.5.
- The pick (`prep_day4.py`, run on 25 Sep, and again on 26 Sep after a comment in it was changed, with a
  byte-identical result; `day4/windows_day4.json`, sha256
  `6d19cf5b871b3ed455f396d8d7ea9facdc71a60eeaf91c394b81d93818e9ac5e`, and its log): 5,780 candidate cores, 81 examined in
  the seeded order, 17 passed (64 failed the textureless rule), so n = 8 targets and 8 shams, on all five surfaces. The
  layer-14 correlation between arms is 0.986 to 0.996 on all 16. The seed is a date, as on days 1 and 3.

#### Plants, shams, checks, readout

- As day 3 in both arms: the six day-1 donors and the swap plant, surface to surface with no depth shift; s = 0.25, 0.5
  and 1, s = 0 untouched; two shams per strength (PHerc0483B sham i and day-1 PHerc0139 sham i, each with its own k);
  both directions kept, each checkpoint's primary direction from day 1 (forward). No transplant.
- Control: the six day-1 references run once, for both arms; if any of a checkpoint's reference AUCs, in its primary
  direction, moves more than 0.01 from day 1's (section 9), that checkpoint's day-4 run is not read, in either arm.
- Each arm is read for a checkpoint only when every one of its jobs, and the control, is scored in both directions; a
  missing score in one arm does not stop the other. The scale references are read when all of theirs are.
- Checks, per checkpoint and arm: the median clean AUC, the median PHerc0483B sham AUC at every strength and the median
  PHerc0139 sham AUC at every strength lie in [0.40, 0.60]. If any fails, that arm gives no floor for that checkpoint,
  and the reason is reported.
- Floors, per checkpoint and arm, as section 8. Arm A's are day 4's floors for PHerc0483B; arm B's are reported as the
  floors at the scan's own voxel size.
- Reported beside them: every target's AUCs, k and clipped share; each donor's ink contrast after resampling (arm B);
  the scale references; the difference between arms; and, for every check, floor and difference, its margin against
  its limit and whether leaving out any one target (its clean, planted and sham jobs) changes whether a check passes,
  whether a floor is found, or the sign of the difference (the run's `results.json` holds every figure these come from; `read_day4.py`
  prints the nearest check's margin and the leave-one-target-out results, the difference's at s = 1).
- Inputs pinned: windows.json, masks.npz and day 1's results.json as on day 3, and `day4/windows_day4.json`; every
  target's and sham's profile in both arms is checked against the pick's record.

#### The models' own output on the whole surfaces

Both checkpoints run over the five whole renders of each arm, both directions; the raw maps are published as they are,
with the floor beside any region they mark, and no letters are claimed. One smoke run (one target per arm, one whole
surface per arm) checks the pipeline first; it is the first model output on this scroll, and its numbers are not used.

#### Limits, stated now

- Pixel sizes are nominal: a pixel is a grid unit, and these grids' points lie on average 3.0 to 6.6 % farther apart
  than the 20-voxel step.
- Neither arm is a native scan at the other size: arm A's papyrus and arm B's letters are resampled, so the difference
  between arms is the effect of reading at 9.362 or at 8.64 um with these stand-ins.
- In arm B the model's 21 layers span 173 um instead of 187 um; n is 8, so medians are noisier than day 3's (n = 12).
- With n = 8, donors 0 and 1 are used twice and donors 2 to 5 once (day 3 used each twice), and the PHerc0139 shams
  come from w025 and w026 only. Day 3's AUCs at full strength varied largely by donor, so a difference from day 3's
  floor may partly reflect this mix.
- 64 of the 81 cores examined failed the textureless rule (1 of 25 on day 3), so the floor describes the most intact
  fifth of the papyrus examined, not the scroll's surfaces as a whole.
- k matches the donor to the target's texture level, not its character; the scan's 116 keV differs from PHerc0139's 113.
- PHerc0483B is in no `ink_9um` training set (the card lists PHerc0139, Scroll 1667, PHerc. Paris 4 and PHerc0814).

### Erratum to amendment 3 (26 Sep 2026, before day 4's full run was read; no rule changes)

Amendment 3 says that no model has run on PHerc0483B, that our five surfaces are its only ones, and that day 4's
smoke run is the first model output on this scroll. Each is true only of our own work. On 11 Sep 2026, gmDevi's
`vc-windows-tools` (commit 4206088) published an ink-model screen of PHerc0483B: a tracks-only spiral fit, with every
fifth winding rendered in both layer directions and scored (36 renders of 18 windings), all negative. It published
the renders and their scores, not the surfaces; ours remain the first published surfaces on this scroll. Nothing in
the rules changes.
