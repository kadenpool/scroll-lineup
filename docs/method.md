# Method, in full

The README has the four-line version. This is the same thing with the
sizes, the search spaces and the reasons.

## G1: whole-scroll search, about 300 um (finer for small objects)

The taller scan is read whole at a coarse pyramid level. Five
cross-sections of the shorter scan are read at about 75 um.

Each cross-section becomes a polar signature around its material
centroid: the outline, plus band-passed inner detail. One FFT along
the angle axis then scores all 360 rotations at once. Mirror images
and upside-down placements are scored in the same pass, so a scan that
was loaded into the beamline the other way up is found rather than
missed.

The five heights must match five heights of the other scan at the
right spacing, which is what pins the height: a single cross-section
matches in many places, five at a fixed spacing do not.

A full 2D search is added in two cases: when the best answer does not
stand clearly above the next one, and when the shorter scan sees only
part of the cross-section. In practice the first case is the common
one: of the seven runs that took the 2D search, only two were triggered
by a partial field of view, and two of the 1.129 um tiles never took
it at all. That search is every 5 degrees, both mirror images, every height,
and it is the slow path. Measured on the five runs that took it, it
cost 4.2 to 13.0 minutes.

## G2: re-score the best answers, about 150 um

Full 2D image matching of the inner detail at the five heights,
refining rotation to 0.25 degrees, plus height and height scale.

The winner's score and its margin over the runner-up are both written
to `report.json` as `g2.results` and `g2.margin`. A small margin is
one of the things that raises `CHECK`.

The five refined placements give a first 3D transform. The drift in x
and y with height gives the tilt.

## B: 3D block matching, about 75, 37 and 19 um

Dozens of cubes of the shorter scan, spread over height and area and
inside material, are matched in the other scan by masked normalised
cross-correlation with a sub-voxel peak fit.

One cube is taken per storage chunk, so a cube costs one chunk read.
The exception is the coarsest of the three block levels, where two are
taken per chunk and axis, because a small scan has very few chunks at
that level. That was half of the 0.2.0 fix; the widening search box
below was the other half.

Each match is a landmark pair. A 12-parameter affine is fitted to them
with outlier rejection, two rounds per resolution, each round starting
from the previous one.

When too few cubes match, the search box widens by 2x and then 4x.
That was added in v0.2.0 after a 14 degree tilt left only 6 or 7 blocks
matching and the edges 1 to 2 mm out.

The block centres that survive the fit are written into
`transform.json` as `moving_landmarks` and `fixed_landmarks`, so the
fit can be checked or redone by anyone.

## Confidence

`HIGH`, or `CHECK` with the reasons attached: a small G2 margin, too
few blocks, or a block residual over 30 um.

The flag is cautious in one direction: one pair in the twelve
validation runs is flagged `CHECK` and is right.

In the other direction it is good but not perfect. Of the nine
robustness pairs, it flagged both genuine failures and named the
reason each time, and it reported `HIGH` on a third pair the
pre-registered rule grades FAIL. On that pair the tool's own block
residual is 4.6 um RMS at correlation 0.99, and at the official
transform's own landmarks the tool's answer sits 6.3 um off while the
official matrix sits 123 um off its own landmarks. `HIGH` is a
statement about the fit, not about the reference.

**One outright miss is known.** In the coverage round,
`coverage/x3_Paris4` is graded FAIL at 215 um p95 and reported `HIGH`
with no reasons at all. There the reference is better than the tool,
though not clean: it hits its own landmarks at 35 um RMS, one of the
four misses in `audit/`, where the tool manages 57. It is a 45.532 um
overview scan matched onto a 7.91 um scan, a scale jump of nearly six,
well outside anything else attempted. Nothing in the confidence
machinery notices that regime. Read `confidence` next to `blocks[-1]`,
never alone, and treat a large scale ratio as unverified.

## The half-voxel convention

Pyramid levels are 2x2x2 means, so level-L voxel `i` is centred on
level-0 coordinate `2^L i + (2^L - 1)/2`. The tool uses that
everywhere.

That is checked against the data rather than assumed. On a 128-cubed
block of the PHerc1203 9.362 um scan, level 1 equals the 2x2x2 mean of
level 0 to within 8-bit rounding: largest difference 0.50 grey levels,
mean difference 0.25, r = 0.99995.

Getting this offset wrong costs half a level-0 voxel, 4.7 um on a
9.362 um scan. That is the size of the block residuals the tool
reports, so it would be invisible in the residuals and wrong in the
answer.
