# The pass/fail rule, fixed before any validation pair was run

Written 12 Sep 2026, 01:44 AEST (from `date`), against v0.1.0 of this tool as hand-tested on PHerc1203 only.
PHerc1203 has no official transform, so nothing in it could tune the tool towards the official answers.
The pairs listed below had not been run with the tool when this file was written.

## Pairs listed in advance (moving -> fixed, the same direction as the official metadata entry)

1. *(withheld: one pair on a scroll this repository does not discuss; the rule applied to it unchanged,
   and it came out PASS. It is withheld for reasons unrelated to the tool. 8 of the 9 pairs listed here
   are in the published table.)*
2. PHerc0139   20250820105138 (2.403 um) -> 20250728140407 (9.362 um)
3. PHerc0009B  20250521125136 (8.64 um)  -> 20250820154339 (2.401 um)   (official has ~2.8 deg tilt)
4. PHerc0814   20260309142202 (2.399 um) -> 20250804134230 (9.362 um)   (official: ~176 deg rotation)
5. PHerc0139   20250822062710 (2.403 um) -> 20250728140407 (9.362 um)
6. PHerc0139   20260102150214 (2.399 um) -> 20250728140407 (9.362 um)   (official: ~178 deg rotation)
7. PHerc0500P2 20250528085330 (4.317 um) -> 20250526151718 (2.215 um)
8. PHerc0500P2 20250526151718 (2.215 um) -> 20250820143440 (9.362 um)   (stress test: official ~14 deg tilt)
9. one 1.129 um -> 2.4 um pair (stress test: the 1.129 um scans are partial fields of view)

A pre-registration with a silently deleted row is not a pre-registration, so the withheld row is left in
place and numbered. Six further pairs were run in a second round **after** this file was written and after
the first round's results were known, under the same rule and with no change to it: PHerc1667 2.399 ->
7.91, PHerc0332 2.399 -> 7.91, PHerc0814 1.129 -> 2.399, PHerc0139 1.129 -> 2.399, and two more that are
withheld. Four of those six are in the published table. That second round was blind in the sense that none
of its pairs had been run by any version of the tool before; it was not covered by this file's list.

## Error measure

Distance between where ours and the official transform put the same point, for 4000 random points in
scroll material inside both scans, in micrometres. Also at 25 named points (5 heights x centre/4 sides)
and at the official's own landmarks (reported next to the official affine's own residual there).

## Verdict per pair

- **PASS**: 95th percentile error <= 30 um (about 3 voxels of a 9.4 um scan, 12 voxels of a 2.4 um scan).
- **WEAK**: 95th percentile <= 150 um (right place, not good enough to render a segment from the other scan).
- **FAIL**: anything else, or no answer.

If the official's own landmark residual is large, that is reported next to the verdict, not used to excuse it.
