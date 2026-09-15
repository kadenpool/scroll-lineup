# How good does an alignment have to be for ink detection?

The README keeps the answer and the budget table. This is the
working behind them.

## The question

The grades this tool reports (PASS, WEAK, CHECK) are thresholds
picked in advance. On their own they say nothing about whether a
transform is good enough for what you want to do with it. For the
most common use, carrying a surface between scans so an ink model
can read it, there is a measured answer.

## The measurement

The challenge's 9.362 um ink models are shown a 21-layer window of
the rendered sheet. Slide that window and the model's reading of
known text falls away quickly.

Measured on PHerc0139 segment w016 against the challenge's own
published ink labels, the model reads the writing at the sheet
centre (pixel AUC 0.877, 57 % of labelled ink marked) and is at
chance one 10-layer step away: 0.571 at -10 layers, 0.537 at +10.

Nearer in, flummoxjr measured the same thing finely on 17 Aug 2026
in `measure-before-you-hunt` and found a gentle decay out to +/- 6
layers. (Layers, not voxels: one layer of the rendered surface, which
is what the depth window is counted in throughout this page.)

Put together: **the tolerance is about +/- 6 layers, and it is gone
by 10.**

## The budget

One layer of the 9.362 um scan is 9.362 um, so that converts
directly into an alignment budget.

| alignment error, 95th percentile | layers of the 9.362 um scan | what it means for ink detection |
|---|---|---|
| 30 um (this tool's PASS bar) | 3.2 | comfortably inside tolerance |
| 56 um | 6.0 | the edge of tolerance |
| 94 um | 10.0 | the model is reading noise |
| 150 um (this tool's WEAK bar) | 16.0 | past the point of no return for ink work |

**A transform whose 95th-percentile error is inside about 50 um is
usable for ink detection at 9.362 um. A transform at the WEAK bar
is unusable for it, even though it is in the right place and looks
right by eye.**

That is the number to check before trusting a map made through a
transform, and it is why this tool reports the whole error
distribution rather than a single score.

## A worked example of the size of error that matters

The hand-made PHerc1203 alignment that this tool replaced was 29 um
out, split about evenly between height (18 um) and across (21 um).
The height part is about 2 layers and the whole error about 3, so
against the 6-layer tolerance above it is roughly half the budget.
Real, worth catching, survivable.

The failure mode to fear is the other one: the transform that lands
150 um out while still passing a correlation check.

## Sources

- The depth measurement is in a companion write-up, measured on public
  data with the challenge's own labels. **That write-up is not
  published yet, so every ink detection figure on this page is
  currently uncheckable**: the three AUC values, and the share of
  labelled ink marked at the sheet centre. It is listed as exception 5
  in section 8 of `VALIDATION.md`. The 50 um budget above rests on
  them. When the write-up goes up it will be at
  github.com/kadenpool/ink-finding-checks.
- flummoxjr's finer curve is `hunt/depth_offset_plan.md` in
  `measure-before-you-hunt`, 17 Aug 2026.
