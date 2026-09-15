# The seating check, in full

The README has the result and the table. This is the reasoning behind
them and the one change made to somebody else's instrument.

## Why a second instrument is needed at all

Agreement with another transform, or a small block residual, shows the
fit is self-consistent. It says nothing about whether a surface
carried through the transform still lies on a sheet of papyrus rather
than cutting across the windings. Those are different questions and
they need different measurements.

## The test is axiosdevs'

`seat_mesh.sheet_contrast` in
[herculaneum-scroll-tools](https://github.com/axiosdevs/herculaneum-scroll-tools)
scores how strongly the brightness profile through a surface peaks at
the surface itself.

They published it after their own cross-scan transfer passed a 0.86
slice correlation and still failed the seating test, and they withdrew
the ink maps that had come from it. Their formula is used here
unchanged; it is the `at-mesh` column.

## The one change: how the curve is read

Their readout takes the global argmax of the contrast curve. Over a
deep stack that is unstable, because a papyrus profile is periodic:
the global argmax answers "which sheet is brightest", which is a
different question from "is this surface on a sheet".

So `pct` is the share of the whole +/- 750 um contrast curve lying
below the value at the surface. That has an exact null. A surface
placed at random scores 0.50 by construction, so the number can be
read without calibrating anything.

## The arrangement

Two of this tool's own transforms from the validation table, with a
PHerc0139 control surface that carries known text. Mesh, window and
renderer are held fixed, and only the transform changes.

- **Own scan**: the surface rendered directly in the 9.362 um scan,
  with no transform at all.
- **Through**: the same surface rendered from the 2.403 um scan
  through the transform.

The two arms therefore read physically different scans, taken at
different energies, of the same object.

## The result

| transform used | its graded error (median / 95th / max um) | at-mesh, own scan | at-mesh, through | pct, own scan | pct, through | depth-profile correlation |
|---|---|---|---|---|---|---|
| PHerc0139 2.399 to 9.362, inverted | 18 / 31 / 38 | +8.58 | +6.26 | 0.94 | 0.94 | 0.994 |
| PHerc0139 2.403 to 9.362, inverted (the bending pair) | 43 / 107 / 152 | +8.58 | +0.18 | 0.94 | 0.60 | 0.718 |

The test breaks a seated surface when the transform is poor and leaves
it seated when the transform is good. This tool's own error numbers
predicted which was which, before the seating test was run.

## What it means in practice

At tens of microns, a transferred surface stays on its sheet. Past
100 um, on a pair where the two scans bend, it comes off, and one
affine is the wrong model there however well it is fitted.

Run this test on any transform before trusting a surface carried
through it, including one of this tool's.

## Where this number comes from

The seating table was measured outside this repository, with a
renderer and a control surface that are not part of it. Reproducing it
needs axiosdevs' `sheet_contrast` and a mesh. The two transforms it
grades **are** in this repository, at `results/v6_0139c/` and
`results/v2_0139a/`, so the half of the table that is this tool's
output is checkable here.
