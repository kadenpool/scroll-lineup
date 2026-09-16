# Do the published transforms fit their own published landmarks?

Some official transforms in the challenge's `metadata.json` ship the landmark pairs they were built
from, as `from_landmarks` and `to_landmarks`. Applying the matrix to the from-points should land on
the to-points. This measures how far it actually lands, for every transform in the catalogue that
publishes landmarks.

```
python audit/audit_landmarks.py            # about 4 s, reads only the public metadata
python audit/audit_landmarks.py local.json # or point it at a local copy
```

It needs numpy and fsspec, both of which the tool already requires. It uses nothing else from this
repository, so it can be lifted out and run on its own.

## What it reports today

`results.txt` is the output of the run committed here. Of the 26 official transforms, **25 publish
landmarks and 4 of those miss their own by more than 30 um**:

| object | moving to fixed (um) | landmarks | RMS um | worst point um |
|---|---|---|---|---|
| PHerc1667 | 1.129 to 2.399 | 6 | **123.3** | 212.5 |
| PHerc0332 | 2.399 to 7.91 | 6 | **103.1** | 133.9 |
| PHerc1667 | 2.399 to 7.91 | 12 | **53.6** | 117.8 |
| PHercParis4 | 45.532 to 7.91 | 8 | **35.1** | 63.4 |

The other 21 sit between 0.0 and 25.3 um, and fourteen are under 10. So the four are separated from
the rest by a clear gap rather than by where a threshold was drawn.

## Why 30 um

The released ink models are documented as sensitive to depth offset, and flummoxjr published a
measurement on 17 August 2026 of how the response decays inside plus or minus 6 voxels. Six layers of
a 9.362 um scan is about 56 um, so 30 um is a little over half of the window that public
measurement covers. Half would be 28; 30 is a round number near it and nothing turns on the
difference, since the four flagged sit at 35 and above while the next is 25.3.

It is a deliberately conservative line drawn from a public number, not a derived constant. **Which
rows appear obviously does depend on where it sits**: at 40 um the table has three rows, at 25 um it
has six. What does not depend on it is the gap, since the flagged four start at 35.1 and the next
value down is 25.3.

## What this is not

- **Not a claim the matrices are wrong for what they were fitted for.** A transform can be a good
  global fit and still miss individual clicked points, and landmark placement has its own error.
- **Not a claim this tool does better. It is mostly worse.** Measured the same way against official
  landmarks, this tool beats the official transform on **1 of the 21 pairs that publish them** and is
  worse on 19, with one pair publishing none. On PHerc0332 ours sits 104 um from the same six points
  the official matrix misses by 103. The one win is PHerc1667 1.129 to 2.399, at 6.3 um against
  123.3, and one pair is not a generalisation.
- **And the comparison is not like for like, in the reference's favour.** This table measures each
  official matrix against the points it was *fitted to*, which is an in-sample residual and the
  easiest test a fit can be given. This tool's errors are measured out of sample, on points it never
  saw. A fit that cannot hit its own fitted points is the finding here; it does not follow that
  anything else fits them better.

## One trap, since it cost us a wrong number

Take the voxel size from the volume's `long_id`, not from `data.origins`. A volume can carry several
origins and the last may be a prediction store whose path has no voxel size in it, which silently
yields `None`. A `None` scale then leaves the answer in voxels rather than microns, and voxels look
like a plausible number rather than an error. The first run of this script reported 51.4 instead of
123.3 for exactly that reason.
