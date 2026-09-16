# How far the ink model's depth window can move before it stops reading

The alignment budget in the main README says a transform needs to land inside about 50 um. This is
the measurement that number comes from. It used to be cited to a repository that does not exist yet,
which made it the one claim in this package a reader could not check. The data is now here.

## What was measured

PHerc0139 segment w016, where the text is known and the challenge publishes ink labels. The released
9 um model was run on the same rendered stack nine times, moving its 21-layer window ten layers at a
time, and each run was scored against the held-out validation labels. Every run also went in reverse
depth order, which is the null: a real reading should collapse when the layers are fed backwards.

`ctl_curve.json` is the whole result, nine rows. `ctl_curve.png` is the plot.
`plot_ctl_curve.py` redraws it from the json, and needs matplotlib, which the tool does not.

**One wrinkle in the committed picture:** its caption calls the peak "the window everyone uses".
That was written before we checked, and it is not right. The peak here is layers 40 to 61, and the
tool's own published documentation recommends a different one. The text below is correct and the
caption is stale; the numbers in the figure are the numbers in the json.

## The curve

| window (layers) | AUC forward | AUC reversed |
|---|---|---|
| 0 to 21 | 0.539 | 0.552 |
| 10 to 31 | 0.525 | 0.490 |
| 20 to 41 | 0.557 | 0.529 |
| 30 to 51 | **0.571** | 0.464 |
| **40 to 61** | **0.877** | 0.525 |
| 50 to 71 | **0.537** | 0.469 |
| 60 to 81 | 0.422 | 0.456 |
| 70 to 91 | 0.385 | 0.501 |
| 80 to 101 | 0.465 | 0.530 |

**One window reads and no other comes close.** At the peak the model reaches 0.877 against the
labels and marks 57 % of labelled ink. One ten-layer step in either direction takes it to 0.571 and
0.537, which is not reading. Reversed depth order never rises above 0.552 anywhere.

Be precise about the rest, because "at chance" would be too tidy: the off-peak forward windows run
0.385 to 0.571, which is a **wider** spread than the reversed arm's 0.456 to 0.552. Two of them sit
outside the null band rather than inside it. The peak is the finding; the floor is noisy, this is one
segment of one scroll with no repeats, and there are no error bars on any of it.

Ten layers of a 9.362 um scan is 94 um. So the usable window is narrower than 94 um, and this
measurement puts no bound tighter than that on its own.

## Where the 50 um budget comes from

flummoxjr measured the inside of the same curve on 17 August 2026, at one-voxel steps from minus 6 to
plus 5, and found a gentle decay across that range. That is the fine structure this measurement
cannot see, and the reason is the step size rather than the render: this run moves ten layers at a
time, so everything between the steps is invisible to it. **That figure is not in this repository.**
It is the one external number the 50 um budget leans on.

Put together: **fine within about 6 layers, gone by 10.** Six layers of a 9.362 um scan is 56 um, so
a transform landing inside about 50 um leaves the model on the readable part of the curve. That is
the budget, and it is why a 123 um error in a published transform (see `audit/`) is worth reporting.

**What this measurement alone can support**, without flummoxjr's finer one: the window is narrower
than 94 um, because ten layers away is already gone. It cannot get you to 50 on its own. Anyone
relying on the tighter figure is relying on his work as well as this.

## The gate that ships inside the data file

`ctl_curve.json` carries a `G0` block: `best_ge_0.85`, `worst_le_0.65`, `single_peak`,
`far_all_0.10_below`, and `G0_PASS: true`. It is the pass rule this control had to clear before the
sweep it belongs to was allowed to mean anything, and it is recorded here because a gate that only
appears in a data file is a hidden bar.

Two things about it are worth saying rather than leaving to be found. **The peak clears the 0.85 bar
by 0.027**, which is not a wide margin. And the bar was set for a different purpose, as the entry
condition for a depth sweep on unread scrolls, not as a test of this curve. Read the numbers, not the
`true`.

## What this does not show

- It is one segment of one scroll with one model. A different model or a different scan could have a
  different tolerance.
- It measures where the window sits, not whether the surface underneath it is seated correctly.
  Those are different failures and this says nothing about the second.
- The peak window, 40 to 61, is not the window the tool's own documentation recommends. That
  discrepancy was reported upstream separately.
