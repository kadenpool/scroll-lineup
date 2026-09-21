# The report's headline numbers, and the files they come from

`trace_numbers.py` recomputes the numeric claims below from the
committed JSON and fails if any of them disagrees with `README.md`.
This page adds the things a script cannot check: which rule was
written down before which number existed, and where the prose in the
report was cut back from.

Run it with:

```
python3 trace_numbers.py
```

---

## 1. The pre-registrations

Each rule below was committed before the data it judges existed. The
timestamps are in git.

| run | rule fixed in | rule |
|---|---|---|
| adaptation | `data/evidence_0912/PLAN_A_PREREG.md` §5 | G1 median validation AUC >= 0.83; G2 off-sheet share after / before < 1/3; G3 one candidate >= 2 % on-sheet with on / max(off, 0.005) > 3 |
| PHerc0813 survey | `data/evidence_0912/PLAN_B_0813_PREP.md` §5 | control AUC >= 0.85 forward, about 0.5 reversed and off-sheet, 0 missing keys; then anything above the ordinary meshes' own on/off spread on both checkpoints and both directions gets a by-eye look |
| PHerc0211 survey | `data/evidence_0912/PLAN_B_0211_PREP.md` §5 | the same |
| depth sweep | `data/evidence_0913/PLAN_D_PREREG.md` §3 | G0 the control must peak >= 0.85 and fall >= 0.10 at every far position; G1 >= 2 % on-sheet, on/off >= 3, forward-dominant; G2 the answer must fall away with depth; G3 beat the window's own swept null and the scroll's own ordinary windows |

Deviations are logged in the pre-registrations themselves, before the
data they affected: `plan_a_files/DEVIATIONS.md`, and
`PLAN_D_PREREG.md` §6 (step halved from 10 layers to 5 after the
control calibration; the off-sheet band widened to match).

## 2. Number by number

| number in the report | source |
|---|---|
| 60 grown surfaces, 170 window-direction readings | our working log (not public) 13 Sep 03:40 |
| 51.1 %, 46.8 %, 44.3 % | same entry |
| the scorer separates text from shuffled blobs at AUC 0.60 | `data/evidence_0912/scorer_calibration.md` §1.2 |
| 6 candidate regions, 15 to 48 % on, 7 to 36 % off | `data/evidence_0912/NINE_UM_CHECK.md` §1.2, §3 |
| "can't tell", then resolved against the null | `NINE_UM_CHECK.md` §1 and §10.1 |
| 115 windows, median 24.0 %, p90 34.5 %, range 9.1 to 44.6 % | `data/evidence_0912/PLAN_C_0846A_9UM.md` §3 |
| G1 0.876, G2 pass, G3 fail | `data/evidence_0912/PLAN_A_RESULT.md` §8, §9 |
| candidates 0 to 1.8 %, ordinary held-out 2.2 % | `PLAN_A_RESULT.md` §8, §9 |
| 32 meshes, 128.8 of 131.8 cm2 | `plan_b_0813_files/manifest.json` |
| 30 meshes, 127.2 of 131.1 cm2 | `plan_b_0211_files/manifest.json` |
| 32 of pscamillo's 75 PHerc0813 meshes, 30 of his 90 PHerc0211 | `PLAN_B_0813_PREP.md` and `PLAN_B_0211_PREP.md`, item 1 of each |
| section 5: every reading of TAUIL's two locations, both checkpoints | `plan_b_0813_files/v2_result/results.json` and `plan_b_0211_files/v1_result/results.json`, `per_segment` |
| section 5: the two shape-gate windows, their directions and ratios | `plan_d_files/results.json` `gates_G1`; the shape gate recomputed in `trace_numbers.py` with `analyse_sweep.py`'s rule |
| other people's surveys: 324, 82 and 71 meshes; 340 rendered; 12 windings; 31.2 % | `CITATIONS.md`, last section |
| median 11.0 % on against 9.4 % off, on/off 1.15 | `PLAN_B_0813_RESULT.md` §2 |
| median 10.1 % on against 10.1 % off, on/off 1.00 | `PLAN_B_0211_RESULT.md` §1.2 |
| two 0813 meshes kept, 1.96x and 1.85x | `PLAN_B_0813_RESULT.md` §1.4, §2 |
| control 18.9 % on, 0.8 to 2.4 % off, 8 to 24x | `PLAN_B_0813_RESULT.md` §2 and `PLAN_B_0211_RESULT.md` §2, identical rows |
| control AUC 0.877 forward, 0.525 reversed | both result files §1.1; `NINE_UM_CHECK.md` line 280 |
| 57.2 % of labelled ink, 7.4 % of labelled background | `ctl_curve.json` row `ctl_d40` |
| 0.877 / 0.571 / 0.537, 94 um | `ctl_curve.json` rows `ctl_d40`, `ctl_d30`, `ctl_d50` |
| known text, weakest / strongest depth 0.06 | `ctl_curve.json`, recomputed |
| 28 windows, 17 positions, 476 readings | `plan_d_files/results.json` |
| 0 of 28, best on/off 2.41, bar of 3 | `results.json` `gates_G1`; bar in `analyse_sweep.py` |
| 0846A candidates 0.69 to 1.18x, four below | `results.json`, recomputed |
| 10 of 28 peak at the centre, 15 of 28 stronger reversed | `results.json` `gates_G1` |
| scroll windows, median 0.59, range 0.29 to 0.85 | `results.json`, recomputed |
| 34.88, 131 um off, contrast at the mesh minus 4.59 | `seating_files/ours.json`, `depthprofile_best.json` |
| 2.76, seated to 19 um | `ours.json`, `depthprofile.json` |
| band 11.19 to 13.98, median 12.18, five segments | `calibration.json` band B plus the w016 control row |
| 9 of 15 within 6 layers, 6 off by 131 to 328 um | both depth-profile files, recomputed |
| six seated swept windows, median 1.20x | intersection of the above with `results.json` |
| rho minus 0.01 and plus 0.30 | `ours.json` stage2 rows against `results.json` |
| rho plus 0.35 to plus 0.51, 26 windows | `ours.json` against `contrast.json` |
| Spearman plus 0.57 over 27 windows | `sheet_check_files/ink_vs_band.json` |
| GPU hours | `PLAN_A_RESULT.md` §8; `PLAN_B_0813_RESULT.md` §5; `PLAN_B_0211_RESULT.md` §4; `PLAN_C_0846A_9UM.md` §3; `PLAN_D_RESULT.md` §6 |

## 3. Numbers that were cut rather than softened

Four figures that appeared in an earlier draft are gone, because they
could not be traced.

**"About 400 cm2."** No area in cm2 was ever recorded for PHerc0846A.
The two mesh scrolls sum to 255.98 cm2 rendered, and PHerc0846A was
scored in 7.5 mm windows, which is a different unit. The report now
gives 256 cm2 for the two scrolls and counts the third in surfaces
and windows.

**"About 12 GPU hours."** The named runs sum to 15.1 h of session
wall clock, most of it on two-T4 sessions. The report now prints the
per-run table and its total.

**"0.37 mm into the air."** `NINE_UM_CHECK.md` §6.5 says the
opposite: *"The 'off-sheet' windows are other wraps, not air."* At
150 to 250 um sheet spacing, 0.37 mm lands one to two sheets away.
The report says so.

**"187,915 scored pixels (the published validation region inside the valid render), of which 43,540 are labelled ink"** (in the companion depth write-up).
1309 x 2884 is the whole render canvas, not the labelled region. The
scored region is the held-out w016 validation mask, and the three
files that quote a pixel count for it disagree, so no count is
printed.

## 4. Numbers where the evidence files disagree with themselves

Recorded here so nobody has to rediscover them.

- **Reverse-dominant windows.** `PLAN_D_RESULT.md` §5 says 16 of 28.
  Every definition computed from `results.json` gives **15**, and so
  does hand-counting `PLAN_D_STAGE2_TABLE.md`. The report uses 15.
- **Control off-sheet share.** The two Plan B result tables say
  0.8 to 2.4 %; `PLAN_D_RESULT.md` §3 says 0.5 to 2.4 % in a row
  whose own 8-to-24x ratio only works with 0.8. The report uses
  0.8 to 2.4 %.
- **Seated fraction.** `data/evidence_0914/SEATING_CHECK.md` §5 says
  "eight of the thirteen", counting the control inside the numerator.
  Of our own 15 profiled meshes, 9 are within 6 layers and 6 are not.
  The report uses 9 of 15.
- **"Every candidate below the ordinary windows."**
  `PLAN_D_RESULT.md` §1 says that of PHerc0846A while printing
  "ratios 0.69 to 1.18" in the same sentence, and a ratio above 1 is
  above. The report gives the range and says four of six are below.
- **Offset sign.** `SEATING_CHECK.md` §5 prints minus 14 layers for
  the mesh that `depthprofile_best.json` stores as plus 14. Only the
  magnitude is used.

## 5. What the depth sweep also showed, and the report does not

- Two windows pass the shape gate G2: `z13088_w040` on PHerc0813 and
  `z9120_w020` on PHerc0211. Both fail G1 and G3. The report now gives
  both, in section 4 and section 5. **An earlier version of the report
  called both "forward-dominant". `z9120_w020` is not: it answers
  14.8 % in reverse against 11.0 % forward.** G2 takes whichever
  direction is stronger, so it passes on its reverse answer, and
  forward-dominance belongs to G1, which it fails. Corrected 19 Sep.
- Four of the 28 windows peak inside the off-sheet band.
- The within-scroll nulls, swept over all 17 positions: PHerc0846A
  40.7 % over 10 ordinary windows, PHerc0211 14.9 % over 4,
  PHerc0813 10.5 % over 4.
- Mesh orientation is a separate open question. A sweep cannot flip a
  normal, so the reverse-dominant answers stay unexplained here.
  villa tracks that as issue #1648.

## 6. What the seating work also showed

- The two instruments agree only at rho plus 0.35 to plus 0.51 over
  26 windows, so neither is quoted per item without the other.
- At 9.362 um the seating probe's smallest returnable half-gap is
  150 um against a 150 to 250 um sheet spacing; on the control it
  returned 374.5 um. Halving the voxel size moves the control's own
  score from 11.38 to 14.84.
- PHerc0846A, PHerc0813 and PHerc0211 have no published segments at
  all, so the known-good band could only be built on PHerc0139.
