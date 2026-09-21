# Seating check: does axiosdevs' sheet-seating test undercut our three-scroll conclusion?

PRIVATE. Nothing posted, nothing pushed, nothing filed. Run 14 Sep 2026, 13:43-15:20 AEST
(box A clock 03:43-05:20 UTC, both from `date`). Their repo was cloned read-only into a scratch
directory, never into `<project>`. Their code was copied to box A **unmodified** (md5 checked)
and imported, not reimplemented.

Trigger: `submissions/DUPLICATE_CHECK_0914.md` item 8 — axiosdevs/herculaneum-scroll-tools
publishes a seating test whose author concluded that ink maps from a badly seated surface
"carry no information". If our meshes were badly seated, our three-scroll negative
(`evidence_0913/PLAN_D_RESULT.md`, `evidence_0912/PLAN_B_0813_RESULT.md`,
`PLAN_B_0211_RESULT.md`, `PLAN_A_RESULT.md`) would be an artefact of the surfaces, not a
finding about the models.

---

## 1. The verdict, in one line

**Six of our windows are provably sitting on a papyrus sheet — measured on the very renders the
ink model consumes, to within 56 µm of the sheet centre — and their median response is 1.20× their
own scroll's null, where real text under the identical pipeline gives 8-24×. Bad seating is
therefore not the explanation for our negative, and the three scroll conclusions stand.**

---

## 2. What the tool actually measures

The duplicate check described one test. There are **two**, on different scales, and conflating
them would have produced a wrong verdict.

| | `seat_mesh.seating_score` | `seat_mesh.sheet_contrast` |
|---|---|---|
| input | a tifxyz mesh **+ a volume** | an **already-rendered** layer stack |
| what it does | samples 500 surface points, takes the grid normal at each, reads the volume at 0 and at ±`gap` along that normal | takes the mean intensity profile across layers over pixels valid in every layer |
| the number | `mean(centre − ½(before+after))` over points with `centre > 40`, **times coverage** (the fraction above 40); returns −1.0 if coverage < 0.25 | `profile[mid] − ½(profile[mid−span] + profile[mid+span])`, default span 25 layers |
| how ±gap is chosen | **measured, not assumed**: `probe_gap` walks the mean profile outward in 2-voxel steps and takes the first minimum | fixed at ±25 layers |
| their calibration | correctly seated **19-35** (PHerc0139 21.3, PHercMANBp 24.0, PHerc1667 24.2); a surface visibly cutting across the windings **8.5**; threshold **15** | correctly seated **+30.0** (PHerc0139), **+38.7** (PHercMANBp); a surface known to cut across the windings **−0.1**; their own bad cross-scan registration **−0.2** |

The idea is the right one and is stated plainly in their source: *not* "are these points inside
material" — a cut across the windings is inside material too — but "does the sheet run along us".
On a seated sheet the centre sits in papyrus and both sides fall into the gaps.

Their own validation is real and self-critical. The test independently picks out the volume named
in a PHerc0139 mesh's filename and rejects the other six; and the author **withdrew their own
PHerc0009B ink maps** after the test rejected the surface those maps were rendered from
(`git log`: *"withdraw the PHerc0009B maps — rendered from a surface the seating test rejects"*).
`fit_seating.py` then optimises the seating score directly and still tops out at 6.2 against the
threshold of 15, from which they conclude the coarse-to-fine map on that scroll class is not rigid.

**The duplicate check's description was accurate but incomplete**: the numbers it quoted
(+30.0 / +38.7 / −0.1 / −0.2) are `sheet_contrast`, while the threshold of 15 it also quoted is
`seating_score`. They are different scales and cannot be compared to each other.

### The calibration trap, and why it decides this whole check

Every number in both calibrations was measured on **1.1-2.4 µm** scans. All of our work is at
**9.362 µm** — PHerc0813 volume `20250821151723`, PHerc0211 `20250821151803`, PHerc0846A
`20250728152254`, control PHerc0139 `20250728140407`.

Their own published `ink/seating.json` already shows the scale collapsing with resolution: the
same PHerc0139 segment scores **21.3** in its 2.4 µm volume and **12.85** in the 9.362 µm one —
below their own threshold of 15. Applying "threshold 15" to our 9.362 µm meshes would have
condemned every known-good official mesh at that resolution too. That is the uncalibrated-ranking
error L51 warns about, and it nearly produced the wrong answer here.

---

## 3. Calibration: reproduced, in both bands

Hand-test first (L44), on one input with a published expected value — their PHerc0139 w025 mesh
built natively on the 9.362 µm volume, scored in that volume:

| | score | coverage |
|---|---|---|
| their published row | 12.85 | 0.965 |
| this run | **13.98** | **0.966** |

Coverage matches to 0.001; the score differs by 1.13 because their survey samples 600 points and
`seat_audit.py`'s convention (used here) samples 500. PASS.

**Band A — reproducing their published "seats" values (2.4 µm).** Their code, their meshes, their
volumes, their `SCALES` tuple and level 2:

| scroll | volume | this run | theirs | delta |
|---|---|---|---|---|
| PHerc0139 | 20260102150214-2.399um | **19.21** | 21.33 | −2.12 |
| PHerc1667 | 20251217075048-2.399um | **25.83** | 24.21 | +1.62 |
| PHercMANBp | 20251216152116-2.399um | **29.70** | 23.96 | +5.74 |

All three land at or above their threshold of 15 and inside/above their stated 19-35 band. The
harness is faithful.

**Band B — the 9.362 µm band, which is the one our work lives in.** Published official segments
whose mesh is named `on-<9.362 µm volume id>`, i.e. built natively in the volume they are scored
against, so known-good by construction:

| scroll | segment | score | coverage |
|---|---|---|---|
| PHerc0139 | w025 | 13.98 | 0.966 |
| PHerc0139 | w028 | 12.73 | 0.952 |
| PHerc0139 | w027 | 12.18 | 0.942 |
| PHerc0139 | **w016 — our own control, the known-text mesh used in every run** | **11.38** | 0.928 |
| PHerc0139 | w026 | 11.19 | 0.940 |

**The 9.362 µm known-good band is 11.19 - 13.98, median 12.18 (n = 5).** That, not 15, is the bar.

Two necessary negatives found on the way, both checkable in one command:

- **PHerc0846A, PHerc0813 and PHerc0211 have no published segments at all** — the S3 `segments/`
  prefix is empty for each. There is no within-scroll positive control for any of our scrolls.
- **PHerc0139 is the only scroll with a natively-seated 9.362 µm published segment.** The same
  search over PHerc1203, PHercParis4, PHerc0172 and PHerc1667 returns none.

---

## 4. Our meshes on their published instrument — and why it cannot be trusted alone here

Their unmodified `seating_score`, level 2, best over scales (1.0, 2.0, 4.0, 0.5), 500 points —
`seat_audit.py`'s own protocol. The one adaptation: mesh directories are local paths rather than
S3 segment prefixes, because our meshes are not published. Volumes are the official S3 zarrs the
renders used. **79 meshes, 0 failures.**

| scroll | n | median | range | at or above the 9.362 µm floor (11.19) |
|---|---|---|---|---|
| PHerc0846A (grown by us) | 16 | 4.28 | −0.05 .. 19.99 | 2 of 14 |
| PHerc0813 (pscamillo) | 32 | 5.07 | −0.74 .. 18.49 | 1 of 32 |
| PHerc0211 (pscamillo) | 30 | 2.34 | −0.55 .. 34.88 | 1 of 29 |
| PHerc0139 control | 1 | 11.38 | — | reference |

Three meshes returned zero coverage at every scale (`zoom_r35_c65` and `032347463_r5_c45` on
0846A, `z6720_w020` on 0211): no sampled point reads above 40 anywhere. Counted, excluded from the
medians, named here rather than hidden.

Taken alone that table says our meshes are badly seated. **It should not be taken alone.** Checked
against a direct measurement of where each mesh actually sits (section 5), `seating_score` at
9.362 µm produces errors in **both** directions:

- **False negative.** `z7920_w020` (PHerc0211) scores **2.76** — below their cross-cut reference of
  8.5 — yet its sheet peak is **2 layers (19 µm)** from the mesh with a profile range of 28.1. It
  is one of the best-seated surfaces we have.
- **False positive.** `z6112_w080` (PHerc0211) scores **34.88**, the highest number in the whole
  check, above anything in their published corpus — yet its sheet peak is **14 layers (131 µm)**
  away, its contrast *at the mesh* is **−4.59**, and its profile range is only 9.6. It is not
  seated.

The cause is `probe_gap`. At level 2 of a 9.362 µm volume one voxel is 37.45 µm and the smallest
half-gap the walk can return is 4 voxels = 150 µm, against a sheet spacing on these scrolls of
150-250 µm. On our control it chose 374.5 µm — one and a half windings out. Dropping to level 1
sharpens it (the control rises 11.38 → **14.84** and its margin over an in-plane null rises
+3.37 → **+12.01**), but the probe is still coarse. Agreement between their two instruments across
our 26 scored windows is only **rho = +0.35 to +0.51**.

**So no per-mesh verdict from `seating_score` alone is safe at 9.362 µm, in either direction.**
This is the same lesson as L51, one level down: the test was calibrated at a resolution we do not
work at, and its adaptive part does not adapt far enough.

### The second instrument, which does agree with itself

`sheet_contrast` on stacks rendered **here, by their renderer, at identical settings for control
and for ours**, so there is no renderer confound. One documented change: the span is reported as a
curve (3-25 layers) rather than at the default 25 only, because 25 layers at 9.362 µm is 234 µm,
more than the sheet spacing on these scrolls, so the default probe lands on the next sheet.

| | span 5 | span 10 | span 25 |
|---|---|---|---|
| **control ctl_w016** (known text) | **+21.8** | **+21.4** | **+17.5** |
| PHerc0846A, 16 windows, median | +1.44 | +0.89 | +2.58 |
| PHerc0813, 6 windows, median | +2.21 | +2.70 | +4.96 |
| PHerc0211, 6 windows, median | +3.81 | +2.59 | +3.69 |
| best of ours (`z7920_w020`) | **+13.2** | **+13.0** | +8.8 |

The control is strongly positive at **every** span from 5 to 25 and our medians are near zero at
every span, so the aggregate finding does not depend on the probe distance. For scale, their
seated reference is +30.0/+38.7 at 2.4 µm and their known cross-cut is −0.1.

---

## 5. The measurement that settles it

Render a 161-layer stack (±750 µm, several winding spacings) along the mesh's own normals and
evaluate **their own `sheet_contrast` formula at every candidate centre** instead of only the
middle. One render gives the whole offset curve. This is the most direct instrument available and
it is also *exactly what the ink model consumes*, so it cannot be accused of measuring something
the model does not see.

| mesh | scroll | sheet peak at | contrast at the mesh | profile range |
|---|---|---|---|---|
| **ctl_w016 (known text)** | 0139 | **+2 layers (+18.7 µm)** | **+21.43** | **33.7** |
| `z7696_w020` | 0813 | **+0 layers (0.0 µm)** | +4.11 | 24.9 |
| `zoom_r50_c70` | 0846A | **−1 layer (−9.4 µm)** | +8.53 | 24.1 |
| `z11904_w020` | 0813 | **+1 layer (+9.4 µm)** | +10.64 | 20.1 |
| `z7920_w020` | 0211 | **+2 layers (+18.7 µm)** | +13.03 | 28.1 |
| `zoom_r75_c45` | 0846A | +3 layers (+28.1 µm) | +2.17 | 8.4 |
| `z13088_w040` | 0813 | +3 layers (+28.1 µm) | +2.40 | 14.7 |
| `034621782_r5_c45` | 0846A | −6 layers (−56.2 µm) | +7.35 | 32.4 |
| `z6112_w080` | 0211 | −14 layers (−131.1 µm) | −4.59 | 9.6 |
| `z12496_w040` | 0813 | −15 layers (−140.4 µm) | +4.93 | 20.2 |
| `072318733_r95_c10` | 0846A | −18 layers (−168.5 µm) | +4.57 | 15.3 |
| `z9120_w020` | 0211 | +26 layers (+243.4 µm) | +1.59 | 13.4 |
| `073911423_r60_c45` | 0846A | −32 layers (−299.6 µm) | −0.48 | 12.3 |
| `z13920_w040` | 0211 | −35 layers (−327.7 µm) | +1.44 | 5.7 |

Two things fall out.

**All three scrolls have resolvable sheet structure at 9.362 µm.** Profile ranges of 20-32 against
the control's 33.7, on all three scrolls. So "there is no sheet to sit on" is not available as an
excuse, in either direction.

**About half our windows sit on a sheet and about half do not.** Eight of the thirteen are within
56 µm of a sheet centre; the rest are off by 131-328 µm, one to two full windings. Both groups
exist on every scroll.

### And the well-seated ones answer exactly like the badly-seated ones

Joining the depth profile onto PLAN_D's swept windows:

| | n | median forward ink | median × its scroll's own null | reverse-dominant |
|---|---|---|---|---|
| **provably ON a sheet** (peak within 6 layers / 56 µm) | 6 | 18.9 % | **1.20** | 3 of 6 |
| **provably OFF a sheet** (peak beyond 6 layers) | 5 | 13.0 % | **1.00** | 4 of 5 |
| **control `w016`, real text, identical pipeline** | 1 | 18.9 % on / 0.8-2.4 % off | **8-24** | forward only |

And across all 28 swept windows, neither instrument predicts the ink response:

| Spearman rho vs PLAN_D | forward ink share | × scroll null |
|---|---|---|
| `seating_score` | **−0.013** | +0.307 |
| `sheet_contrast` span 10 | **−0.266** | +0.297 |

The correlation with the forward ink share is zero or slightly negative — if anything the
*worse*-seated windows fire more.

**The single cleanest row: `z7696_w020` on PHerc0813 sits exactly on a sheet (peak at +0 layers,
profile range 24.9) and was already the strongest mesh in that whole run — on/off 1.98, and
stronger in the reverse depth order on both checkpoints. A surface centred on a sheet to within
one layer, answering 1.98× its off-sheet null, backwards, where real text gives 8-24× forwards.**

---

## 6. What this means for each of the three scroll conclusions

- **PHerc0846A (`PLAN_A_RESULT.md`, `PLAN_C_0846A_9UM.md`, `NINE_UM_CHECK.md`) — stands.** Three
  of its windows are within 56 µm of a sheet centre, one of them (`034621782_r5_c45`) on a patch
  whose sheet structure is as strong as the control's (range 32.4 vs 33.7), and it answers
  reverse-dominant at **0.80×** its own scroll's null — weaker than the average ordinary window.
- **PHerc0813 (`PLAN_B_0813_RESULT.md`) — stands, on the strongest single row in the check**
  (`z7696_w020`, above).
- **PHerc0211 (`PLAN_B_0211_RESULT.md`) — stands.** `z7920_w020` is seated to within 19 µm with a
  profile range of 28.1 and is the best of ours on `sheet_contrast` (+13.0); it was also that
  run's top mesh by on/off ratio (1.90) and is reverse-dominant.
- **`PLAN_D_RESULT.md` (the depth sweep) — stands, and is now closed from the other side.** The
  sweep's own worry was that we were looking at the wrong 0.2 mm. The windows that are provably on
  the right 0.2 mm answer no better.

### What we may no longer write, and what we must now write

1. **Correct `evidence_0912/SHEET_CHECK.md`.** Its headline — *"the 0846A grown surfaces are on a
   papyrus sheet, not in the gaps"* — is too strong. It measured whether a bright band exists near
   the mesh, not whether the mesh sits on it; two of the windows it cleared are 168 and 300 µm off
   the nearest sheet centre. Its *other* finding, that over-firing tracks **good** mesh position
   rather than bad, survives and is now confirmed by two further instruments.
2. **Do not claim our meshes are well seated as a population.** Roughly half are not. The method
   report's Honest Limits must say so, and must stop leaning on TAUIL's mesh-angle numbers
   (0211 median 7.8°, 0813 9.0°) as though they settled seating — angle to the team's surface
   prediction and seating on a sheet are different measurements and they disagree here.
3. **Make the argument on the provably-seated windows.** That form is both honest and stronger
   than the population form, and it is what the evidence actually supports.
4. **Credit axiosdevs** in the method report and rewrite `registration_tool/PUBLISH_PLAN.md` §4,
   which still records that repo as "shift and tilt only". Say we ran their test, not an
   equivalent of our own.
5. **Do not quote a bare `seating_score` for any 9.362 µm mesh, ours or anyone's.** It has false
   positives and false negatives at this resolution, demonstrated above. If a single number is
   needed, use the depth-profile offset.
6. **STILL OPEN: the PHerc1203 First Letters report was not covered here.** It rests on a
   cross-scan transform — the exact case their test was built to catch and where they measured
   −0.2. Run this on the 1203 transform before that report moves anywhere. Flag I of the duplicate
   check stays open.

---

## 7. Other work by the same author bearing on our conclusions (task 5)

The author has 100 public repos; every other one is crypto / AI-agent listware. Only
`herculaneum-scroll-tools` is Vesuvius work. Inside it, four things touch ours:

1. **A published coarse-scan caveat.** Their detectability atlas: *"At ~8 µm the checkpoint
   saturates and must not be trusted"* — the 2 µm model returns 100 % ink in ten of twelve
   PHerc0172 windows at 7.91 µm — and *"a positive from this model on any 8-9 µm scan carries no
   information"*. This is the **2 µm** model out of domain, not the released 9 µm models on 9 µm
   data, so it is **not** our claim and must not be cited as if it were. It cuts our way and
   belongs in the prior-art list.
2. **Phantom voxels in exactly the batch our PHerc0846A surfaces were grown from.** Their
   `ct_support` measured m7 run `20260413222639` voxel-exactly: **PHerc0846A 58.2 % phantom**,
   PHerc0813 43.4 %, PHerc0211 43.3 %, warning that *"seed-growers that don't consult the CT can
   ride the phantom shell"*. `fetch_ngrid_0846a.py` confirms our 0846A surfaces were grown from
   `...-surface-20260413222639-surface-m7-L0-th0.2.normal-grids` — that run. **We did not ride
   phantom**: 0.96-1.00 of our sampled surface points read above 40 in the masked CT, so our
   surfaces are inside real material. The failure measured here is orientation, not phantom. Worth
   stating explicitly, because it is the first thing a reviewer will ask.
3. **A calibrated letterness scorer** — AUC 0.885, held out 0.911, on PHerc0139 known text. Our
   `scorer_calibration.md` found no scorer that separates. Theirs is a published one that does, on
   2 µm data. Worth testing against ours before we repeat the "no working scorer" line.
4. **`fit_seating.py`'s conclusion that the coarse-to-fine map on these scroll classes is not
   rigid**, and that a slice correlation of 0.86 will hide that. This bites `registration_tool/`
   and the 1203 report, not the three-scroll negative.

---

## 8. Files, and what was run

On box A underseatcheck/`: their unmodified `ink/` tree plus the drivers written
here — `handtest_seat.py` (the L44 hand-test), `calibrate.py` (bands A and B), `score_ours.py`
(79 meshes), `contrast.py` (`sheet_contrast` on matched renders), `depthprofile.py` and
`depthprofile_best.py` (the 161-layer offset curves), `diag.py` (probe resolution and the in-plane
null), `summarise.py`, `join_plan_d.py`, `agree.py`. Raw results: `calibration.json`, `ours.json`,
`contrast.json`, `depthprofile.json`, `depthprofile_best.json`, `diag.json`, and every log.
Copies of the drivers, results and logs are in `evidence_0914/seating_files/`; their code is not
vendored into this repo.

Every batch reports a counted failure list. **All five batches finished with 0 failures**; the
three zero-coverage meshes and the two `seating_score` errors of direction are reported above
rather than dropped.

Cost: box A CPU only, about 95 minutes wall across four concurrent jobs, all streaming ranged
reads from the public bucket. No GPU, no spending, no downloads into `<project>`. Box A free disk
stayed at 89 GB throughout.
