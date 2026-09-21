# Pre-registration: the depth-window sweep ("are we reading the wrong 0.2 mm?")

Written 13 Sep 2026, 13:05 AEST (from `date`), BEFORE any sweep data was cut, rendered or scored. Nothing below may be
changed after a number is seen; deviations go in a dated section at the bottom of the result file, as in Plan A.

## 1. The question

Every 9 um run so far (the 9 um check, Plan A, Plan B on PHerc0813, Plan B fallback on PHerc0211, Plan C) read **one fixed
21-slice window** out of a 101-slice render: layers [40,61), the nominal sheet centre, with off-sheet nulls at [0,21) and
[80,101). The models were given 0.2 mm of a 0.95 mm render and asked "is there ink here".

If a mesh does not sit exactly on the sheet's mid-plane, or its normals point the other way, the real ink layer is somewhere
else in those 101 slices and every run so far has been reading the wrong 0.2 mm. Two observations make this worth testing
rather than assuming:

1. On PHerc0813 and PHerc0211 most meshes answered more strongly in the REVERSE depth order, and on 0211 all nine w020
   meshes did. Real text in the control answers 2.6x more strongly FORWARD. A flipped or mis-centred window looks like that.
2. Nobody has published a depth sweep on these scrolls, so "the model cannot read this scroll" and "the model was not shown
   the right layer" have never been separated.

## 2. What is run

**Stage 1, calibration on known text (must pass before any scroll data is judged; lesson L51).**
The control is the same one every run has used: PHerc0139 segment w016 rendered from the official 9.362 um volume with the
9 um check recipe (101 slices, `--flip-normals`), with the challenge's own published ink labels on that render. Already on
box A (`p0813/ctl/ctl/ctl_w016.zarr`, 101 x 1309 x 2884), so nothing is re-rendered.

Cut nine 21-slice windows at starts 0, 10, 20, 30, 40, 50, 60, 70, 80 and run the ink_9um checkpoint
`hybrid_3d2d-seed43/step-060000` (the best-transfer checkpoint, the one used in every run above) on each, in both depth
orders. Measure, per window: pixel AUC against the published labels, ink share (p > 0.5) on labelled ink and on labelled
background, and the on/off ratio using the two extreme positions as the off-sheet null.

**Stage 2, the sweep on scroll data (only if stage 1 passes G0).**
The same nine window positions on: the six PHerc0846A candidate regions, the ten Plan A held-out ordinary 0846A windows
(the within-scroll null), and the strongest meshes of PHerc0813 (z11904_w020, z13088_w040) and PHerc0211 (z7920_w020,
z9120_w020) plus four ordinary meshes of each as their own nulls. Re-rendered on box A with the recipe already used
(the 101-slice renders themselves were deleted after cutting; the render scripts and mesh lists are kept).

## 3. Gates, set now

**G0 (calibration, decides whether the test has any power at all).** On the known-text control:
- the best depth position must reach pixel AUC >= 0.85 forward, AND
- at least one position must fall to AUC <= 0.65 forward, AND
- the response must be depth-localised: the AUC curve over the nine positions must have a single peak, and positions more
  than two steps (20 layers, 0.19 mm) from the peak must be at least 0.10 AUC below it.

If G0 fails, the sweep cannot tell a right depth from a wrong one on data where we know the answer, so it cannot tell us
anything about the scrolls. Then: report the calibration honestly, stop, and do not run stage 2.

**G1 (a hit on scroll data).** For a scroll window or mesh, a hit is a depth position where all three hold:
- ink share on-sheet >= 2 % (the Plan A G3 bar), AND
- on/off ratio >= 3 with the 0.5 % floor (the Plan A G3 bar), AND
- forward-dominant (forward ink share >= reverse).

**G2 (depth-localised, the shape test).** A hit must fall away with depth the way the control does: at least 0.10 AUC
equivalent, measured as the hit's ink share dropping by half or more at two steps away on both sides where both sides exist.
A response that is flat across all nine positions is the papyrus texture again, not a layer of ink.

**G3 (the multiple-comparison control, the one that matters).** Sweeping nine positions gives nine chances to look good, so
the null must be swept identically and compared max to max:
- the same window's own off-sheet nulls, swept over all nine positions, take their maximum; and
- the scroll's ordinary windows (the within-scroll null), swept over all nine positions, take their maximum.
A hit counts only if its best-over-depth value exceeds the best-over-depth of BOTH nulls by the G1 margins. A hit that only
beats the fixed-depth null is not a hit.

**Verdict rule.** PASS = at least one scroll window passes G1 and G2 and G3. Anything else is a FAIL, and a FAIL is reported
as what it is: at every depth in the rendered 0.95 mm, these models see the scroll's papyrus texture and not ink.

## 4. What a PASS would and would not mean

A PASS would mean the earlier runs read the wrong layer and there is a depth where the model answers like it answers on real
text. It would NOT by itself be evidence of letters: the same by-eye and shape tests would still have to be passed, on the
eligible 9.362 um volume, before anything is claimed. A FAIL closes the "we were reading the wrong 0.2 mm" explanation and
makes the three-scroll negative substantially stronger, which is itself worth reporting in the honest method report.

## 5. Honest caveats, written before the run

- The nine positions overlap (21-slice windows at 10-layer steps), so neighbouring results are correlated. That is why G2
  is about the shape of the curve and G3 compares maxima, not any single position.
- The models were trained on windows centred on the sheet. At extreme positions the input is mostly air or the neighbouring
  sheet, which can itself produce a response; the control calibration is what tells us what that looks like.
- A flipped normal is not the same as a shifted window, and this test cannot separate the two. Both are "the model was shown
  the wrong 0.2 mm", which is the question being asked.
- The control is one segment of one scroll. If its AUC curve is sharp, that is evidence the method has power on that data,
  not proof it has power on every scroll.

## 6. Deviation log (appended after stage 1, each entry dated and before the data it affects)

1. **13 Sep 2026, 13:35 AEST.** Stage 2 moves from nine depth positions at 10-layer steps to seventeen at 5-layer steps.
   Reason: the stage-1 control curve (`PLAN_D_STAGE1_CONTROL.md`) shows the response peak is about as wide as a 10-layer
   step (0.877 at the centre, 0.571 and 0.537 at +/-10), so a peak could fall between grid points. Decided from control
   data only, before any scroll window was cut or scored. Gates G1, G2 and G3 unchanged; G2's "two steps" is read as
   20 layers, not as two grid positions. On the finer grid the off-sheet null of G3 is every
   position whose 21-layer window lies mostly outside the sheet band (starts 0, 5, 75, 80), which is the same physical
   region the pre-registration named ([0,21) and [80,101)), not a new or weaker null.
2. **13 Sep 2026, 13:20 AEST.** Motivation 1 in section 1 (reverse-dominance as a sign of a mis-centred window) was
   refuted by prior work before our first scroll window ran: flummoxjr's 17 Aug sweep found the forward-reverse relation
   flat at every offset within +/-6 voxels, and our own control confirms the reverse direction never rises at any depth.
   The test continues for motivation 2 (nothing published beyond +/-6 voxels). Recorded so the result file cannot claim
   a motivation that was already dead. See `PLAN_D_PRIOR_ART.md`.
