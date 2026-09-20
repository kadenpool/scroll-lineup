# Validation and reproduction

Every run this tool has been through, the machines and library sets
they ran on, what each cost, and what failed. The README carries the
results; this file carries the evidence and the commands.

## 1. What has been run

| round | pairs | outputs | what it establishes |
|---|---|---|---|
| validation, 12-13 Sep 2026 | 12 official pairs on 7 objects | `results/`, table in `results/table.md` | the graded result against the challenge's own transforms, under a rule fixed in advance (`PREREG.md`) |
| worked example, 11-15 Sep 2026 | PHerc1203, for which no official transform exists | `examples/pherc1203/` | five runs over four days, three of them from a clean clone into an empty environment; all five byte-identical |
| robustness, 15 Sep 2026 | the 9 remaining official pairs in the catalogue | `robustness/`, table in `robustness/table.md` | every publishable official pair now has a graded result, including three the tool gets wrong |
| coverage, 15-16 Sep 2026 | the last 5, on PHerc0343P and PHercParis4 | `coverage/`, table in `coverage/table.md` | all 26 official transforms are now graded, with nothing excluded. Machine D, section 3 |
| landmark audit, 16 Sep 2026 | all 26 official transforms, no scan data read | `audit/`, output in `audit/results.txt` | whether each published transform fits the landmarks published with it. 4 of the 25 that carry landmarks do not |
| copy comparison, 19 Sep 2026 | all 26 catalogue transforms against their per-volume `transform.json` | `audit/compare_copies.py`, output in `audit/copies.txt` | 18 per-volume copies exist; 17 match the catalogue; PHercParis4 45.532 -> 7.91 does not, 518.3 um RMS against 35.1. About 20 s, one small fetch per volume |
| depth curve, 13 Sep 2026 | PHerc0139 w016, 9 depth windows on known text | `depth/`, data in `depth/ctl_curve.json` | how far the ink model's window can move before it stops reading. The basis of the 50 um alignment budget |
| render-path decomposition, 20 Sep 2026 | the same PHerc0139 w016 surface, five renders differing in one thing each | `downstream/results.json`, arms `aligned_nopool`, `theirmesh`, `official_bicubic` | why the challenge's own input reads 0.912 where this folder's render of the same transform reads 0.857: depth averaging worth nothing (0.916 without it), smooth interpolation worth 0.019 and not significant block by block, and the mesh's grid step worth 0.040, which is 72 % of the gap |
| reading test, 19 Sep 2026 | PHerc0139 w016 carried by three transforms through one render path, plus the challenge's own aligned input | `downstream/`, data in `downstream/results.json` | whether a better alignment gives a better reading: official 0.857, v6_0139c 0.812, v2_0139a 0.790, and 0.912 through the challenge's own pipeline. The order holds; the gap between the first two is inside the block-to-block noise |

**The two rounds added on 16 Sep, and their costs.** The landmark audit reads only
`metadata.json` and does one matrix multiply per landmark: **4 seconds**, no scan data, no GPU, on
machine B. The depth curve was produced on 13 Sep on a Kaggle T4 with the released 9 um checkpoint
`seed43_step060000` (138,360,231 bytes), nine inference runs over one 101-layer render, each scored
against the published labels for that segment. Neither is a scan-alignment run, so neither has a
transform, a verdict or a place in the tables above; both are evidence the README leans on and are
therefore recorded here.

**The reading test, 19 Sep, and its costs.** Run on an 8-core arm64 Mac with 8 GiB, in its own Python
3.12 environment with torch 2.14.0 for the ink model, which the tool itself does not need. Each arm is 12
tiles of 384 px rendered with `vc_render_tifxyz` straight from the public bucket, 87 to 248 s a tile, then
nine windows scored both ways on CPU, 20 to 31 minutes an arm. At the ink model's default batch of 8 with
2 workers the scoring passed 4.9 GB and was stopped; batch 2 with no workers holds about 1.7 GB, and at
batch 2 the aligned input re-scored at 0.9123 against 0.912 at batch 8 on another machine. Two render
settings cost a full re-render before they were understood, and `downstream/README.md` states both:
`--slice-step` counts voxels of the level being read, and the region has to be located on a canvas that
the affine rescales.

**One blemish in the coverage round, stated rather than tidied away.** `coverage/x5_Paris4` has a
zero-byte `datacheck_landmarks.txt` and no corresponding json, so the last column of its row in
`coverage/table.md` is blank. The other four runs have both. That step produced no output and left
no error behind, so the cause is not recorded and I will not invent one: the run was on a shared
machine at low priority and the most likely explanation is that it was interrupted. Nothing else in
that row depends on it, and the pair's graded verdict comes from `validation.json`, which is
present and complete.

The open-data `metadata.json` carries **26 official transforms**, and
**all 26 now have a graded result here**, with nothing excluded. An
earlier version of this file said five were "on two objects this
repository does not discuss". That was an unexplained exclusion in a
package whose whole claim is that nothing is hidden, so the five were
run. They are in `coverage/`, listed in `pairs_coverage.txt`, and
section 2.7 says what they cost and what they showed.

Three of those five take their fixed volume from a **second access
root** that the metadata names, `data.aws.ash2txt.org`, rather than
from the S3 bucket. Anyone enumerating the catalogue on the assumption
that it lives in one bucket will silently miss them and will most
likely conclude the data is broken.

## 2. The robustness round

### 2.1 What was run, and why those pairs

All nine of the remaining publishable pairs were run, rather than a
chosen subset, so there is no question of picking the ones that work.
The pair list is `pairs_robustness.txt` and the command is the same
one the twelve used:

```
bash run_validation.sh pairs_robustness.txt
```

Between them the nine add: two objects the tool had never seen; two
voxel sizes it had never seen (0.55 and 3.24 um) and a third on the
fixed side (9.366 um); two pairs at the same resolution on both sides,
where the scale ratio is exactly 1; a 73 degree turn with an 8.6
degree tilt; the first pair whose official transform is a **mirror** (section 2.7 found three more);
a pair whose official transform publishes **no landmarks at all**; a
**blosc-compressed** volume, which the five-package install cannot
open; and a 0.55 um field of view 5.9 mm across looking into a 62 mm
scan.

### 2.2 What each one stresses, and how it came out

| pair | moving -> fixed (um) | what it stresses that the twelve did not | confidence | verdict |
|---|---|---|---|---|
| `r1_0841` | PHerc0841 2.403 -> 9.366 | a new object, and a fixed voxel size not seen before | HIGH | PASS |
| `r2_0172` | PHerc0172 7.91 -> 7.91 | a new object; the same resolution on both sides, so the scale ratio is exactly 1; an official transform with **no landmarks**; a **blosc-compressed** fixed volume that the five-package install cannot open | HIGH | PASS |
| `r3_0500hi` | PHerc0500P2 0.55 -> 2.215 | 0.55 um, four times finer than anything tried before; a 73 degree turn with an 8.6 degree tilt; one of the four official transforms in the catalogue that are **mirrors**; a 5.9 mm field of view inside a 62 mm scan | **CHECK** | **FAIL** |
| `r4_0332c` | PHerc0332 3.24 -> 3.24 | a new voxel size; same resolution both sides; two scans of one object at different energies | HIGH | PASS |
| `r5_0332b` | PHerc0332 3.24 -> 7.91 | a new moving resolution onto the 2023 7.91 um scan | HIGH | WEAK |
| `r6_1667roi` | PHerc1667 1.129 -> 2.399 | a partial-view tile on an object whose other pair passed | HIGH | **FAIL**, see below |
| `r7_1667b` | PHerc1667 3.24 -> 7.91 | the 3.24 um to 7.91 um step on a second object | **CHECK** | **FAIL** |
| `r8_0139d` | PHerc0139 2.403 -> 9.362 | a third 2.403 um scan of an object already in the twelve, so a direct test of run-to-run consistency on one geometry | HIGH | PASS |
| `r9_0139e` | PHerc0139 2.403 -> 9.362 | a fourth, same | HIGH | WEAK |

### 2.3 The generated table

`robustness/table.md` is produced by the repository's own
`summarize.py`, the same code that produces `results/table.md`, so
these rows are built exactly like the committed twelve:

```
python summarize.py robustness/r1_0841 robustness/r2_0172 ... > robustness/table.md
```

| run | scroll: moving -> fixed (um) | official geometry | G2 score: winner / runner-up | confidence | error vs official: median / p95 / max um | verdict | at official landmarks: ours / official RMS um | held-out image blocks must move: ours / official (median um) | image blocks at the official landmarks must move: ours / official (median um) | tool | min | MB |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| r1_0841 | PHerc0841: 2.403 -> 9.366 | rot -0, tilt 0.0 | 0.85 / 0.15 | HIGH | 13 / 23 / 28 | PASS | 19 / 14 (n=7) | 10 / 19 (n=38) | 9 / 5 (n=7) | 0.2.1 | 3.2 | 958 |
| r2_0172 | PHerc0172: 7.91 -> 7.91 | rot 0, tilt 0.0 | 0.37 / 0.17 | HIGH | 0 / 1 / 1 | PASS | - | 0 / 0 (n=13) | - | 0.2.1 | 7.2 | 867 |
| r3_0500hi | PHerc0500P2: 0.55 -> 2.215 | rot 73, tilt 8.6, mirror | 0.18 / 0.18 | CHECK | 22521 / 25762 / 26989 | FAIL | 22431 / 9 (n=7) | n=0 | n=0 | 0.2.1 | 17.2 | 201 |
| r4_0332c | PHerc0332: 3.24 -> 3.24 | rot 0, tilt 0.0 | 0.89 / 0.38 | HIGH | 4 / 5 / 7 | PASS | 4 / 2 (n=6) | 3 / 5 (n=39) | 4 / 4 (n=6) | 0.2.1 | 1.2 | 531 |
| r5_0332b | PHerc0332: 3.24 -> 7.91 | rot -0, tilt 0.0 | 0.78 / 0.35 | HIGH | 16 / 40 / 53 | WEAK | 18 / 9 (n=8) | 6 / 19 (n=42) | 7 / 10 (n=7) | 0.2.1 | 1.0 | 694 |
| r6_1667roi | PHerc1667: 1.129 -> 2.399 | rot 0, tilt 0.4 | 0.81 / 0.29 | HIGH | 162 / 417 / 566 | FAIL | 6 / 123 (n=6) | 6 / 103 (n=23) | 4 / 61 (n=5) | 0.2.1 | 2.8 | 1030 |
| r7_1667b | PHerc1667: 3.24 -> 7.91 | rot 0, tilt 0.4 | 0.65 / 0.32 | CHECK | 6398 / 12361 / 14272 | FAIL | 10357 / 13 (n=5) | n=0 | n=0 | 0.2.1 | 1.9 | 770 |
| r8_0139d | PHerc0139: 2.403 -> 9.362 | rot -0, tilt 0.2 | 0.91 / 0.25 | HIGH | 13 / 24 / 35 | PASS | 16 / 9 (n=7) | 9 / 17 (n=41) | 8 / 6 (n=7) | 0.2.1 | 3.2 | 1093 |
| r9_0139e | PHerc0139: 2.403 -> 9.362 | rot 0, tilt 0.1 | 0.86 / 0.25 | HIGH | 41 / 103 / 147 | WEAK | 60 / 25 (n=8) | 22 / 41 (n=42) | 21 / 21 (n=8) | 0.2.1 | 3.8 | 1162 |

### 2.4 What each one cost

Wall clock and peak resident memory from `/usr/bin/time` around every
invocation; megabytes from each run's own `report.json`. One machine,
one software stack, 8 cores.

| pair | scroll, moving -> fixed um | scroll-lineup wall s | peak RSS GiB | MB read | whole pair wall s | peak RSS GiB, whole pair |
|---|---|---|---|---|---|---|
| r1_0841 | PHerc0841: 2.403 -> 9.366 | 194 | 2.67 | 958 | 320 | 2.67 |
| r2_0172 | PHerc0172: 7.91 -> 7.91 | 435 | 3.47 | 867 | 519 | 3.47 |
| r3_0500hi | PHerc0500P2: 0.55 -> 2.215 | 1032 | 8.18 | 201 | 1101 | 8.18 |
| r4_0332c | PHerc0332: 3.24 -> 3.24 | 70 | 1.05 | 531 | 147 | 1.34 |
| r5_0332b | PHerc0332: 3.24 -> 7.91 | 60 | 1.00 | 694 | 91 | 1.00 |
| r6_1667roi | PHerc1667: 1.129 -> 2.399 | 166 | 2.69 | 1030 | 308 | 2.69 |
| r7_1667b | PHerc1667: 3.24 -> 7.91 | 117 | 1.13 | 770 | 156 | 1.13 |
| r8_0139d | PHerc0139: 2.403 -> 9.362 | 194 | 2.54 | 1093 | 322 | 2.54 |
| r9_0139e | PHerc0139: 2.403 -> 9.362 | 227 | 2.51 | 1162 | 366 | 2.51 |

Totals for the nine: 55 minutes of wall clock for the whole pairs, 7.3 GB read, one non-zero
exit (the `datacheck.py` bug in 2.6). Peak resident memory is 1.0 to
3.5 GiB on eight of the nine and **8.2 GiB on the 0.55 um pair**,
which is the one that needs the slow 2D search and also the one that
fails. Across all twenty-one pairs the per-pair range is 1 to 17
minutes and 0.2 to 2.1 GB, and the whole set is 2.3 hours of compute
and 21.7 GB read. The two totals are on different bases: 55 minutes is whole-pair wall clock, 2.3 hours is scroll-lineup time only.

### 2.5 The failures, stated plainly

Four PASS, two WEAK, three FAIL.

**PHerc0500P2 0.55 -> 2.215 um, FAIL, flagged `CHECK`.** A 5.9 mm
field of view looking into a 62 mm scan, at a resolution four times
finer than anything tried before, with a 73 degree turn, an 8.6 degree
tilt and a mirror. Neither search stage can separate its candidates.
The whole-scroll stage scores its top four at 4.5348, 4.5253, 4.5247
and 4.5217, and the refinement stage at 0.1827, 0.1807, 0.1806 and
0.1796, a margin of 0.002. It is the refinement scores that the tool
quotes in its CHECK reason. Block matching then produced no fit at any of its six
rounds ("too few good blocks; transform unchanged", 0 of 25 used at a
median correlation of 0.099), so the answer is the coarse G2 estimate
and it is 22.5 mm out. The tool reported `CHECK` and named both
reasons. This is also the only pair whose official transform is a
mirror, and the tool's answer is a mirror too, so the branch fires;
nothing here shows it producing a correct transform.

**PHerc1667 3.24 -> 7.91 um, FAIL, flagged `CHECK`.** Block matching
again produced no fit; the answer is 6.4 mm out and its landmark RMS
is 10,357 um against the official transform's own 13.4 um. `CHECK`,
with the reason.

**PHerc1667 1.129 -> 2.399 um, FAIL, reported `HIGH`, and the
reference is the thing at fault.** Graded FAIL at 162 / 417 / 566 um.
Three instruments disagree with the grade:

| instrument | ours | the official transform |
|---|---|---|
| block residual of the fit (25 blocks, ncc 0.99) | 4.6 um RMS | not applicable |
| the official transform's own 6 hand-placed landmarks | 6.3 um RMS (3 to 10 um apiece) | **123 um RMS (42 to 213 um apiece)** |
| 23 held-out image cubes, how far they must move | 6.0 um median | 103 um median |
| 5 image cubes at the official landmarks | 3.9 um median | 61 um median |

The landmark row is the one that matters, because it is independent of
this tool's method entirely: those are the points a person clicked,
published alongside the official matrix, and that matrix does not fit
them. Two committed files and six subtractions reproduce it
(`robustness/r6_1667roi/official_transform.json` and `transform.json`).

The verdict stays FAIL. The rule measures distance from the official
transform, and `PREREG.md` says a noisy reference is reported beside
the verdict and never used to excuse it.

**The honest reading of `CHECK` after this round.** It caught both
failures where the tool really did fail, and named the reason each
time. It reported `HIGH` on a pair the rule grades FAIL, and on the
evidence above it was right to. `confidence` is a statement about the
fit; it says nothing about the reference. Read it next to
`blocks[-1]`.

### 2.6 A bug in one of the checkers

`PHerc0172 7.91 -> 7.91` is the only pair in the catalogue whose
official transform publishes no landmarks: `moving_landmarks` and
`fixed_landmarks` are both `[]`. Until 15 Sep 2026 `datacheck.py
--at-landmarks official` indexed that empty array and raised
`IndexError`. It now exits with a message naming the missing field
and pointing at the held-out mode, verified by running it on this
pair (exit 0, no traceback). The guard sits in front of the array
access, so no other code path and no committed result changed. The
column stays blank in `robustness/table.md` because this reference
genuinely has no landmarks to check against.

`scroll_lineup.py` and `validate.py` handle the pair normally, and so
does `datacheck.py` in its held-out mode, so only the third check is
affected. `robustness/r2_0172/` therefore has no
`datacheck_landmarks.json` and that column of its row is blank.

The fix is one guard, and it is **not** in 0.2.1: the version in this
repository is the one all twenty-one runs were made with, and changing
the code would invalidate them. `CHANGELOG.md` records it as a known
issue.

### 2.7 The coverage round: the last five, 15-16 Sep 2026

Run so that no official transform is left ungraded. Same command, same
pre-registered rule, on an ARM Linux machine (machine D below):

```
bash run_validation.sh pairs_coverage.txt
```

| run | scroll: moving -> fixed (um) | official geometry | confidence | error: median / p95 / max um | verdict |
|---|---|---|---|---|---|
| `x1_0343P` | PHerc0343P 8.64 -> 2.215 | rot -0, tilt 0.0 | **CHECK** | 16 / 26 / 33 | PASS |
| `x2_Paris4` | PHercParis4 1.129 -> 2.4 | rot -1, tilt 0.1 | HIGH | 5 / 9 / 11 | PASS |
| `x3_Paris4` | PHercParis4 45.532 -> 7.91 | rot -141, tilt 0.8, **mirror** | HIGH | 97 / 215 / 259 | **FAIL** |
| `x4_Paris4` | PHercParis4 2.4 -> 7.91 | rot -141, tilt 0.8, **mirror** | HIGH | 17 / 26 / 33 | PASS |
| `x5_Paris4` | PHercParis4 2.4 -> 7.91 | rot -140, tilt 0.9, **mirror** | HIGH | 11 / 24 / 30 | PASS |

The full generated row for each is in `coverage/table.md`.

**Four PASS, one FAIL.** Two things came out of this round that change
what the rest of this file says.

**1. The mirror claim was wrong, in our own favour and against it.**
Section 2.2 called PHerc0500P2 "the only official transform in the
catalogue that is a mirror", and the README said no pair had shown the
tool producing a correct mirrored transform. Neither is true. Taking
the determinant of all 26 official matrices, **four are mirrors**: one
on PHerc0500P2 and three on PHercParis4. The tool recovers the flip on
all four, matching the sign of the determinant every time, and two of
the four now pass outright. So the mirror path is exercised and works,
which the package previously declared as an untested weakness.

**2. A genuine confidence miss, the first one.** `x3_Paris4` is graded
FAIL at 215 um p95 and the tool reported `HIGH` with no reasons. This
is not the PHerc1667 situation where the reference is at fault: here
the official transform hits its own landmarks at 35 um RMS and ours at
57, so ours is simply the worse of the two. It is a 45.532 um overview
scan onto a 7.91 um scan, a scale jump of nearly six, which is further
than anything else attempted. **The confidence signal does not cover
that regime, and says nothing to warn you.** That is now the clearest
known limitation of the tool.

## 3. Machines, Python versions and library sets

| | machine A | machine B | machine C | machine D |
|---|---|---|---|---|
| operating system | Ubuntu 24.04.4 LTS | macOS 26.0.1 | macOS 26.0.1 | Ubuntu 24.04.4 LTS |
| architecture | x86-64 | arm64 | arm64 | **aarch64** |
| cores / RAM | 8 / 23 GiB | 8 / 8 GiB | 8 / 8 GiB | 8 / 46 GiB |
| Python | 3.12.3 | 3.9.6 | 3.14.7 | 3.12.3 |
| numpy | 2.5.3 | 2.0.2 | 2.5.3 | 2.5.3 |
| scipy | 1.18.1 | 1.13.1 | 1.18.1 | 1.18.1 |
| fsspec / s3fs | 2026.7.0 | 2025.10.0 | 2026.7.0 | 2026.7.0 |
| pillow | 12.3.0 | 11.3.0 | 12.3.0 | 12.3.0 |
| numcodecs | 0.16.5 | 0.12.1 | not installed | not installed |
| what it ran | all 9 robustness pairs, and the clean-clone reproduction | 7 pairs as a second opinion, and every CI command | the offline suite, 36 checks, all passed | all 5 coverage pairs (section 2.7) |

Machine D is **ARM Linux**, a third architecture. The five pairs it
graded went through the same pre-registered rule as every other pair
and came out consistent with the rest.

Each set is what a plain `pip install numpy scipy fsspec s3fs Pillow`
resolved to on that interpreter. Nothing was pinned. Machines A and B
were measured on 15 Sep 2026, machine C later the same day.

Machine C is the oldest and the newest interpreter question answered
from the other end: 3.14 is one version beyond the newest in the CI
matrix at the time, and the five packages installed on it without
complaint and gave the same answers. That is the reason 3.14 was then
added to the matrix. What machine C has **not** done is a live pair
against the open data, so treat it as evidence about portability of the
code, not as a third independent reproduction of the results.

## 4. Does the answer move across library versions?

The committed example reproduces byte for byte, five times over four
days. Every one of those runs resolved to the same package versions,
so byte-identity is a statement about one software stack. This is the
test that was missing.

Seven pairs were run on both machines. For each, the two transforms
were applied to the eight corners of the moving volume and the largest
disagreement measured in fixed micrometres.
| pair | md5 equal? | largest disagreement over the moving volume | median error vs official, A / B | p95, A / B |
|---|---|---|---|---|
| v9_MANBp | no | 0.000118 um | 6.219120 / 6.219146 | 13.010421 / 13.010422 |
| r1_0841 | no | 0.000022 um | 12.577754 / 12.577757 | 23.343845 / 23.343847 |
| r4_0332c | no | 0.000012 um | 3.558476 / 3.558479 | 5.394179 / 5.394181 |
| r5_0332b | no | 0.000020 um | 15.786112 / 15.786114 | 39.679895 / 39.679898 |
| r7_1667b | no | 0.000259 um | 6398.397023 / 6398.397135 | 12360.528365 / 12360.528423 |
| r8_0139d | no | 0.000031 um | 12.779028 / 12.779028 | 24.284073 / 24.284076 |
| r9_0139e | no | 0.000033 um | 41.242640 / 41.242642 | 103.482018 / 103.482026 |

**Reading.** Byte-identity holds within a stack. Across stacks the
md5 changes and the physical answer does not: the largest disagreement
is about one ten-thousandth of a micrometre, on pairs whose voxels are
one to three micrometres, and every published figure for those rows is
unchanged to six decimal places.

The transforms from machine B are committed under
`robustness/second_stack/<pair>/transform.json`, so the comparison can
be redone from this repository with no network and no scan data;
`tests/test_offline.py` does exactly that on every run.

## 5. The clean-clone reproduction

Run on 15 Sep 2026 after every change below, in a directory created
for it on the Linux box and deleted afterwards. Nothing from the
author's working copy was on the path: the tree arrived by `tar`, its
206 files were checked byte-identical on arrival (one md5 over all the
md5s, matching), a new virtual environment was built inside it, and
only the five packages the README names were installed.

```
=== A clean clone. 2026-09-14 17:22:57 UTC          (the box runs UTC; 15 Sep local)
Python 3.12.3

$ python3 -m venv .venv
  (the stock-Ubuntu ensurepip wrinkle again; the README's apt note applies)
$ pip install numpy scipy fsspec s3fs Pillow
  7.71 s -> numpy 2.5.3  scipy 1.18.1  fsspec 2026.7.0  s3fs 2026.7.0  pillow 12.3.0
$ python scroll_lineup.py --version
scroll-lineup 0.2.1

=== the offline checks
all offline checks passed                            wall 1.33 s   peakRSS 71096 KiB

=== the documented example, end to end
$ PY=.venv/bin/python bash run_1203.sh
scroll-lineup exit 0
[  216.7s] CONFIDENCE: HIGH
[  217.2s] wrote out_1203/transform.json (1260 MB downloaded)
compare exit 0
7jycwjmbfn    vs scroll-lineup: median    3.5 um  p95    5.2  max    6.0
flummoxjr     vs scroll-lineup: median   29.3 um  p95   46.5  max   54.5
datacheck scroll-lineup: 45/48 blocks, must move median 4.6 um
datacheck 7jycwjmbfn   : 45/48 blocks, must move median 5.0 um
datacheck flummoxjr    : 46/48 blocks, must move median 33.1 um
        Elapsed (wall clock) time: 6:11.55
        Maximum resident set size: 2691208 kbytes  (2.57 GiB)

=== md5, fresh run against the committed example
  MATCH    e278bd0e692ba9b47f531d51d93e2cd6  transform.json
  MATCH    1751e7551fd456662dbd924f87f895bc  transform_inverse.json
  MATCH    532261b826fdc4627e42aeb90191d6d0  qc.png

=== summarize.py regenerates the tables from the committed results
  IDENTICAL to the committed results/table.md
  IDENTICAL to the committed robustness/table.md
=== END 2026-09-14 17:29:27 UTC
```

Every comparison figure is identical to the 14 and 15 Sep transcripts
to the last decimal place, and all three md5s match the committed
example, so nothing in tonight's work moved a number the tool
computes. `summarize.py` now regenerates **both** tables byte for
byte, when the run folders are passed in the order of their pairs
file; the plain `results/*/` glob gives the same rows in a different
order, which `CHANGELOG.md` notes.

## 6. Continuous integration

`.github/workflows/ci.yml` has two jobs.

- **`offline`** installs `requirements.txt` and runs
  `python tests/test_offline.py` on Python 3.9, 3.11, 3.12, 3.13 and 3.14.
  No network beyond pip, no scan data, a couple of seconds.
- **`public-pair`** registers `PHercMANBp 1.129 um -> 2.399 um` from
  the public bucket with the committed `run_validation.sh`, then runs
  `tests/compare_run.py` against the committed row. It uploads the
  fresh run as an artifact whether it passes or fails.

**Every command in that workflow was first run locally, exactly as
written, and passed.** For a time this section said the workflow had
never executed on GitHub, because the repository had never been pushed,
and that there was therefore no badge, since a badge for a workflow
nobody has run asserts something nobody has checked.

That is no longer the state. On the first push, 15 Sep 2026, the
workflow ran on GitHub and **all six jobs passed**: the offline suite on
Python 3.9, 3.11, 3.12, 3.13 and 3.14, and one public pair end to end.
The badge at the top of the README reports that run and every one after
it.

The two steps with no local equivalent are `actions/checkout@v4` and
`actions/setup-python@v5`; a fresh copy of the tree and a chosen
interpreter stand in for them. Everything else below is the workflow's
own text, in order.

```
$ pip install -r requirements.txt
$ pip list
$ python tests/test_offline.py
  ...
  all offline checks passed                                    (1.9 s)

$ grep '^v9_MANBp ' pairs.txt > onepair.txt
$ PY=python bash run_validation.sh onepair.txt
  === v9_MANBp 2026-09-15 02:27:13
  scroll-lineup exit 0 02:29:24
  [  129.4s] CONFIDENCE: HIGH
  [  130.0s] wrote runs/v9_MANBp/transform.json (482 MB downloaded)
  validate exit 0
    "median_um": 6.219145553734623
  landmarks: ours rms 11.2 um vs official's own rms 8.6 um (n=15)
  === BATCH DONE 2026-09-15 02:31:26

$ python tests/compare_run.py runs/v9_MANBp results/v9_MANBp
  transform.json md5   fresh fa4650fa86bdd6b4172898cf290b6266
                   committed 014dc12f9953d40d2c8a03ac49ab2188   DIFFERENT
  largest disagreement over the moving volume's corners: 0.000118 um
  confidence: fresh HIGH, committed HIGH
  error vs official, median_um: fresh 6.219146, committed 6.219120, moved 0.000025 um
  the fresh run reproduces the committed one for v9_MANBp
```

Exit 0 throughout; 4 min 17 s end to end, of which 129 s is the
registration itself.

## 7. The offline checks, and proof they can fail

`tests/test_offline.py` is in nine parts.

- **Geometry.** `fit_similarity`, `fit_affine`, `inv`, `decompose`,
  `rot2`, `FFTCorr`, `masked_ncc_valid` and `nms` are each given a
  transform or a shift chosen in advance and have to recover it. The
  affine fit has to recover a sheared, anisotropic map the similarity
  fit cannot, and has to ignore a zero-weighted outlier moved 10 mm.
  The pre-registered verdict rule is checked at both boundaries.
- **The committed evidence**, for `results/` and `robustness/` alike.
  Every cell of each table that comes from a committed JSON file is
  re-derived from that file: the error triple, the verdict from the
  pre-registered rule, the confidence, the G2 winner and runner-up,
  `g2.margin` as winner minus runner-up, the landmark RMS pair
  recomputed from the two committed matrices and the committed
  landmarks, both held-out block columns, the version, the minutes and
  the megabytes. Block accounting is checked for every round of every
  run: `n_used <= n_matched <= n_tried`, the listed blocks equal
  `n_matched`, and the boolean mask sums to `n_used`.
- **The worked example**: `transform_inverse.json` has to be the
  actual inverse, and `report.json` has to carry the same matrix.
- **The second stack**: every committed machine-B transform has to
  agree with its machine-A counterpart to better than 0.01 um.
- **The command line**: `--version`, `--help`, and a bare invocation
  that must fail cleanly.
- **The landmark audit.** The flagged set, the count under 10 um, the
  range of the rest and the summary line are re-derived from
  `audit/results.txt`, and both READMEs must carry them. The
  best-affine column is checked the same way: every row must carry one,
  the file's own "already are the least-squares affine" count must equal
  what its rows give, exactly one matrix may differ from that fit, and
  both READMEs must state the split and the differing pair's two
  numbers. Ours against
  the official transform is counted from the `at official landmarks`
  column of all three tables, and the sentence that reports it must
  use that count and no other.
- **The depth curve.** Every row of `depth/ctl_curve.json` must appear
  in `depth/README.md` with both its AUCs, the off-peak range and the
  reverse maximum must be the real ones, and the gate shipped inside
  the json must be documented.
- **The two published copies.** The counts at the top of
  `audit/copies.txt` must match its own rows, a copy marked identical
  must fit exactly as the catalogue copy does, the catalogue column
  must equal the landmark audit row for row, and the differing pair's
  numbers must reach all three documents. No document may call a
  reference sound when the audit counts it as a miss; four committed
  runs use such a reference.
- **The reading test.** Each arm's peak is re-derived from its nine-window
  curve rather than read from the stored field; every row of the
  downstream table, each difference and ordering its prose states, the
  block tests and intervals, and the depth-offset table are re-derived
  from `downstream/`'s files; the three matrices in
  `downstream/transforms/` must be the inverses of committed transforms;
  and `docs/alignment-budget.md` must carry the same qualification of the
  budget as the README. The three arms added on 20 Sep are checked the same
  way: each must be in `results.json` with its own peak at the centre window
  and its registration within a pixel, the README must state each one's own
  AUC, the "72 % of the gap" must be the arithmetic of the file rather than a
  number in prose, and the two new block tests must carry their own intervals,
  with the finer mesh's excluding zero at 64 px and the interpolation's not.

A check that has never failed has not been tested. Four deliberate
corruptions were planted in a throwaway copy of the tree; all four
were caught and the run exited 1:

```
  planted: one digit changed in a table cell (a p95 of 24 -> 34)
  planted: one landmark moved 3 voxels in an official_transform.json
  planted: 1.0 added to the example's inverse matrix
  planted: n_used raised above n_tried in one report.json

  FAIL every cell of results/table.md is re-derived from the committed JSON
       n3_0814roi: block round at 18.064 um: used/matched/tried out of order
       n3_0814roi: block round at 18.064 um: 13 kept by the mask, n_used 37
       v5_0139b: error column '12 / 34 / 33' != validation.json
       v9_MANBp: landmark RMS in validation.json is not what the committed matrices give
       v9_MANBp: the official landmark RMS in validation.json is not what its own matrix gives
  FAIL the example's transform_inverse.json really is the inverse
       max round-trip error 1.00e+00 moving voxels
  exit 1
```

`tests/compare_run.py` was tested the same way: a transform shifted by
0.834 fixed voxels, and a changed confidence level, both caught.

The last three parts were tested the same way on 19 Sep 2026: 23
corruptions, one at a time, each in a fresh copy of the tree. 22 were
caught. The one that was not is the useful result. Changing "worse on
19 of the 21 pairs" to 17 in the README passed, because the check
accepted any "19 of the" anywhere in the file. Following that up found
the sentence itself was wrong: of those 21 pairs only 20 publish
landmarks, and the count left out the five coverage pairs. The
sentence now reads 24 of 25, counted over all 26, and the check is
bound to it; the same corruption and four others aimed at it are now
caught.

The render-path arms were added on 20 Sep 2026. Six corruptions, one at a time,
each in a fresh copy: the mesh arm's AUC changed in the prose, the 72 % claim
changed to 80, the block interval's bound moved, the ink share changed, the
mesh arm's AUC changed inside `results.json`, and the arm's peak window moved.
The first two attempts at these checks were too weak to catch two of them,
because they asked only whether a number appeared anywhere in the file; they
now bind to the arm's own table row and to the sentence that compares two arms,
and all six are caught. Writing them also caught two errors of mine before the
push: the interpolation arm is better in 10 of 22 blocks, not 6, and the
no-averaging arm finds 69.4 % of the labelled ink, not 71.4.

The best-affine column was added on 20 Sep 2026, after
[villa#1843](https://github.com/ScrollPrize/villa/issues/1843) showed that a
large residual and a matrix that could be better are not the same thing.
Four corruptions, one at a time, each in a fresh copy of the tree: the
summary count changed from 24 to 23, the differing pair's best-affine
figure changed from 2.2 to 20.2 um, the README's count changed, and the
column removed from the table header. All four were caught, and the run
exited 1 each time.

Part I was tested the same way on 19 Sep: ten corruptions, nine caught.
The miss changed an arm's AUC in its curve, and the check read the
stored peak instead of the curve, so it could not see it. The check now
derives the peak from the curve, and the same corruption fails three
checks.

Two checks were added on 20 Sep 2026, after a read-through found the
README and `docs/method.md` vouching for the `x3_Paris4` reference,
which the audit counts among its four misses, and found the budget page
without the qualification the README gives it. Six corruptions, one at
a time, each in a fresh copy of the tree: all six caught. Before that,
the first run of the new check looked at nothing, because it read the
landmark fit from the wrong level of `validation.json`. A companion
check, that there is at least one run to look at, failed on that run,
and the check now covers the four runs whose reference is flagged.

## 8. Where the numbers come from

Every number in the README traces to a file in this repository, with
six exceptions.

1. **The seating table** was measured outside this repository, with a
   renderer and a control surface that are not part of it.
   Reproducing it needs axiosdevs' `sheet_contrast` and a mesh. The
   two transforms it grades **are** here (`results/v6_0139c/`,
   `results/v2_0139a/`), so the half that is this tool's output is
   checkable. `docs/seating-check.md` has the detail.
2. **"About 19,000 block matches"** is a property of 7jycwjmbfn-eng's
   own published file. `run_1203.sh` downloads it; its `P` and `D`
   arrays are both (19116, 3).
3. **The pyramid check** (0.50 grey levels, r = 0.99995) is a live
   computation on the public PHerc1203 volume rather than a stored
   result. It is a dozen lines and reads one 128-cubed block.
4. **Timings, memory and download sizes** come from the runs described
   in this file, except the per-pair minutes and megabytes in
   `results/table.md` and `robustness/table.md`, which come from each
   run's own `report.json`.
5. **The author's own hand-made PHerc1203 alignment**, quoted in the
   README as 29 um from this tool's answer and needing 27 um on the
   same held-out cubes. That transform predates the tool and is not
   committed here, so `compare1203.py` cannot reproduce those two
   numbers from this repository alone. It is the one comparison in
   the README that rests only on the author's word.
6. **"The tolerance is about +/- 6 layers"**, which the alignment
   budget leans on. This repository's own depth curve moves ten
   layers at a time (`depth/ctl_curve.json`, nine windows at 0, 10,
   20 ... 80), so nothing at +/- 6 was ever rendered here; the finer
   figure is flummoxjr's, measured on 17 Aug 2026.
   `depth/README.md` says so, but this list did not, and the README
   said there were five exceptions when this was a sixth.

Everything else, every row of both tables, every PHerc1203 figure,
every residual, is in `results/`, `robustness/`, `examples/` or
`PREREG.md`.

## 9. A note on the committed logs

Each run folder's `log.txt` and `report.json` say the run was written
to `runs/<pair>`, because that is where `run_validation.sh` puts it.
The folders were copied to `results/` and `robustness/` afterwards and
the files were left exactly as the tool wrote them. Anyone re-running
the batch will see `runs/<pair>` too.
