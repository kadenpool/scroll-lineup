# Where the other people's numbers come from

`trace_numbers.py` re-derives every number that is **ours** from committed evidence. It cannot check
a number published by someone else. This file is the equivalent for those: what we quote, who
published it, where, and the exact wording.

Every entry below was fetched from the live repository on **16 September 2026** and checked against
the shipped data rather than the prose where the repository ships data. The entries in the last
section were added on **19 September 2026** and say so. Where our earlier notes had a
figure or an attribution wrong, the correction is recorded rather than quietly fixed.

## FrankTheRope, `scrollrank`

`docs/submission/september_2026.md`, HEAD `3c7612b`, 12 Sep 2026. Renamed from ScrollScout in commit
`3b7a8b5` the same day; the document self-titles under the old name and cites the old URL at tag
`progress-2026-09b`, which redirects.

| what we quote | verbatim |
|---|---|
| Known-text control | "public ink_9um ... reaches pixel AUC 0.886 against the official labels ... and with the same slices in reversed depth order it falls to 0.689" |
| What it draws | "ink_9um draws blobs where the letters are, not glyphs" |
| The conclusion we adopt | "So the eligible-scroll negatives cannot be read as 'there is no ink'." |

Scale, confirmed from the repository: 22 PHerc1203 meshes at 9.362 um, three depths, two seeds, two
directions = 264 predictions in 2 h 20 min, and "Over 550 predictions, about 100 000 window
scorings" across the whole submission. Covers PHerc1447, PHerc1203 and PHerc0800. **None of our three
scrolls were run by him**; PHerc0813 and PHerc0211 appear only as catalogue entries.

## Jinhojeong, `vesuvius-crossscroll-ink-diagnostic`

Single commit `c04f15b`, 14 Jul 2026.

> "Running it across 71 S2/S3 segments, no automated 'letterness' score I tried ranks the Scroll 1
> positive control near the top, which means there is no working positive control for letterness on
> the unreadable scrolls."

**The model is the 2023 grand-prize TimeSformer**, not the released 9 um models: the repository says
so twice and the checkpoint path confirms it
(`timesformer_wild15_20230702185753_0_fr_i3depoch=12.ckpt`). No 9 um model appears anywhere in it.
That difference is the basis of our claim to be measuring something else.

**A correction to our own earlier note.** We had recorded that he tested and rejected both CycleGAN
and entropy-minimisation test-time adaptation "on measured grounds". Only the latter is true. CycleGAN
was rejected without being run, and he says why: "Any letters that come out are unverifiable. I did
not run it as a letter finder for that reason." There is no CycleGAN code in the repository. The
entropy-minimisation result is measured: Scroll 5 baseline AUC 0.53, robustness check 0.96, and "the
adaptation slightly hurt, because entropy minimization optimizes confidence, not correctness".

## TAUIL-Abd-Elilah, `eligible-mesh-alignment`

HEAD `b48b2b0`, 13 Sep 2026. Numbers recomputed from the shipped `data/mesh_alignment.json` and they
reproduce exactly.

| scroll | meshes | median angle | within 30 deg |
|---|---|---|---|
| PHerc0211 | 88 | 7.8 deg | 85 / 88 |
| PHerc0813 | 75 | 9.0 deg | 71 / 75 |
| whole corpus | 338 of 340 | 7.9 deg | mean 10.6 |

**A correction to our own earlier note, and it matters.** We had recorded this as measured against
the team's surface prediction. It is not. The mesh normal comes from the tifxyz grid tangents; the
sheet normal comes from "the leading eigenvector of the local structure tensor of a 96 cubed CT cube"
of the raw masked CT volume. The two share no input, which is the point: agreement between them
cannot arise by construction. The surface prediction is a separate second gate he applies only to
PHerc1447 and three controls. Citing the 7.9 degree figure as a prediction comparison would
misattribute the instrument.

The 30 degree threshold: random axial directions in 3D average 60 degrees, so 60 is the null, and
under 30 is the "follows the sheets" regime.

His asymmetry, which we carry with the numbers: **"a low, tight reading is evidence. A high,
scattered reading is not evidence of anything."**

**PHerc0846A is not in this corpus.** The corpus is eight scrolls: PHerc0358, 0800, 0211, 0826, 0257,
0125, 0813, 0268. A search for "0846" returns one coincidental substring inside a vertex count. So
two of our three scrolls have this clearance and the third has none.

## TAUIL-Abd-Elilah, `pherc1447-ink-survey`

HEAD `041c240`, 13 Sep 2026, commit titled "Correction: the surfaces under this negative do not
follow the sheets".

> "Median 61.2 deg, range 42.2 to 81.5 deg, 0 of 14 within 30 deg of the local sheet normal, where a
> random-orientation null is 60 deg."

> "The negative reported here is therefore much weaker evidence than it appeared: it shows no ink was
> recovered from these surfaces, not that PHerc1447 lacks ink in those regions. The
> pipeline-validation half of this repo ... is unaffected and still stands. The scroll-level
> conclusion is withdrawn."

## axiosdevs, `herculaneum-scroll-tools`

HEAD `c836a52`, 14 Sep 2026, the newest item cited here.

The seating test, from one README passage:

> "`seat_mesh.sheet_contrast` measures how much brighter the middle of a rendered stack is than
> plus or minus 25 layers out; correctly seated surfaces give +30.0 (PHerc0139) and +38.7
> (PHercMANBp), a surface known to cut across the windings gives -0.1, and this registration gives
> -0.2."

Threshold 15. **Two different cross-cut references exist in that repository** and must not be merged:
-0.1 for the known cross-cut surface, and 8.5 in a PHerc0009B native-trace context.

The counterweight we quote in section 9, recomputed from the shipped `ink/calib_depth.json`:
sheet contrast is anti-correlated with ink readability at **r = minus 0.900** across 20 depth-window
settings scored against the published PHerc0139 ink map. Leave the geometry alone: contrast +11.17,
r +0.877. Maximise sheet contrast: +36.18, r +0.594.

> "A 14.4 um wobble costs only 0.877 -> 0.737 ... a silent detector over such a surface is not
> explained by its looseness."

**One discrepancy inside that repository**, noted so nobody quotes the wrong one: the docstring of
`calib_depth.py` says "+0.877 -> +0.620"; the shipped JSON gives **+0.594**. We quote the JSON.

## The phantom-fraction figure for PHerc0846A

**58.2 %** at voxel level in the published m7 surface predictions, against a 42.1 % grand-prize
average, with PHerc0813 at 43.4 % and PHerc0211 at 43.3 %. Carried into section 9 because 0846A is
the one of our three with no independent geometric clearance, so its confounds should be stated
rather than left implicit.

## Checked again on 19 September 2026: what was newer, and what we missed

The 16 Sep check said nothing newer bore on this report. That was wrong on 19 Sep, and one item was
already missed on 16 Sep: gmDevi's PHerc0846A batch is dated 11 Sep. Each item below was read from
the live repository on 19 Sep.

**TAUIL-Abd-Elilah, `corpus-ink-survey`.** First commit `6e7c66b`, 14 Sep 2026 11:53 UTC; HEAD
`297c4d9`, 18 Sep. The README says 324 meshes and 1,518.2 cm2 across all eight eligible scrolls,
PHerc0211 82 meshes and 397.8 cm2, PHerc0813 71 meshes and 341.0 cm2, scored with 4 `ink_9um`
checkpoints and `hecate` against the known-ink control PHerc0139 w043. (The repository's one-line
description still says 237 cm2; the README is newer and is what we quote.) It names two candidate
locations: PHerc0813 `z12496_w060`, forward, with `z13088_w040` ranked second and called "its own
neighbour"; and PHerc0211's inner wrap `z6112_w020` to `z9120_w020`, in reverse. His status line:
"Both are published as candidate locations, not discoveries." Section 5 of the report reads both
through our numbers, which `trace_numbers.py` re-derives from our own result files. Our windows
were committed on 13 Sep (`bc0660d`, 13:09 AEST) and scored that day, before his first commit.

**rodriguescarson, `eligible-scroll-atlas`.** Created 15 Sep 2026; HEAD `2afcd00`, 16 Sep. All 340
meshes on the eight eligible scrolls rendered into the team's layout and uploaded, 0 failures;
screening under a pre-registered recipe with two dated amendments; per-mesh scores "follow when it
finishes", so no ink result is quoted from it.

**gmDevi, `vc-windows-tools`.** Commit `4206088`, 11 Sep 2026, whose message names five other
scrolls, added `results/p0846A_batch/`. `batch.log` says 18 windings; 12 have a summary, and "best
letter-like blobs" is 0 on 11 of them and 1 on `w056`. Neither the README nor `report/REPORT.md`
mentions PHerc0846A, so the folder is quoted as published data, not as his conclusion.

**pscamillo, `vesuvius-eligible-meshes`**, at `0c966f8` (9 Sep): the source of our PHerc0813 and
PHerc0211 meshes, 32 of 75 and 30 of 90 (`data/evidence_0912/PLAN_B_0813_PREP.md` and
`PLAN_B_0211_PREP.md`). The same corpus both surveys above start from.

**tarikcankorkmaz00, `ink9um-z-window-selection`**, HEAD `e6138a3`, 18 Sep: 1,211 tiles at 11
offsets across plus or minus 47.98 um. Of the 160 tiles in his main result, 50, which is 31.2 %,
put their best window on the edge of that range. Paraphrased, not quoted, in section 6.
