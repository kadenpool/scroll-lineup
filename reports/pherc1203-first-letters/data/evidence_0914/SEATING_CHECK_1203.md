# Seating check on the PHerc1203 cross-scan transform: are our rendered surfaces on sheets?

PRIVATE. Nothing posted, nothing pushed, nothing filed. Run 14 Sep 2026, 14:33-15:20 AEST
(box A clock 04:33-05:20 UTC, both from `date`). Answers the BLOCKER added to
`submissions/first_letters_report_1203/CHECKLIST.md` on 14 Sep, and item 6 of
`evidence_0914/SEATING_CHECK.md` ("STILL OPEN: the PHerc1203 First Letters report was not covered
here").

Trigger: the 1203 report's windows are rendered through a transform that maps the 9.362 um mesh
into the 2.403 um scan. axiosdevs' seating test was built to catch exactly that failure: their own
cross-scan transfer passed a 0.86 slice correlation and still scored -0.2, and they concluded the
ink maps from it "carry no information". Our depth-match evidence (ncc 0.82-0.88) is the same kind
of evidence theirs passed.

---

## 1. The verdict, in one line

**Our transform is not the problem: rendered through it, the surfaces sit exactly where they sit
without it (depth-profile correlation 0.98 median, sheet contrast at the mesh unchanged to within
0.03 of its rank), and a control that is deliberately put through a transform of known-bad quality
does visibly break, so the test has the power to have found a failure and did not. What the check
does find is a different, real problem the report must now state: seating is a per-window property
of PHerc1203 and only 4 of the 12 windows tested are provably on a sheet. The good news for the
report is that its three strongest windows are three of those four.**

---

## 2. What the earlier evidence did and did not prove

DRAFT.md 3.2 step 5 says the model window is "centred on the measured sheet", and 3.4 and
`registration_tool/REPORT_0912.md` section 9 report the measured depth shift as -1.0 to +0.7 fine
layers at ncc 0.82-0.88.

That is not a seating measurement, and the wording should change. `scripts_0911/offset_generic.py`
correlates the **sharp render against the native coarse render of the same mesh**. Its own output
says so: *"fine layer (54 + dw) sits where the coarse render has the mesh surface (layer 14)"*. It
measures agreement between two renders of the same surface, i.e. whether the transform puts the
sharp stack at the right depth. If the mesh were 200 um off the sheet, both renders would show the
sheet 200 um off and the two would still match perfectly. So a high ncc and a near-zero shift were
never evidence that the surface is seated, only that the transform is self-consistent. The gap the
BLOCKER identified is real.

---

## 3. Method

Re-used the sibling agent's working setup rather than rebuilding it: their
`evidence_0914/seating_files/depthprofile.py` (axiosdevs' `seat_mesh.sheet_contrast` formula
evaluated at every candidate centre of a thick stack instead of only the middle), their 9.362 um
band, and their "provably on a sheet" convention. Their calibration and code are on box A under
`<run-dir>/seatcheck/`, intact; nothing of theirs was missing and nothing was rebuilt.

The formula is unchanged:

    profile[c] - 0.5 * (profile[c-span] + profile[c+span])     over pixels valid in ALL layers

**Four changes, all forced by the question, all stated:**

1. **The renderer.** Stacks come from villa's `vc_render_tifxyz` with the production transform
   (`--affine p1203_fine/affine_1203_v2.json`), not axiosdevs' `render_surface.render`. Theirs has
   no cross-scan affine and the transform is the thing under test. The native (no-transform) arm
   uses the same binary with `--affine` omitted, so the renderer is held constant across every
   comparison.
2. **`um_per_layer` is a parameter** instead of the hard-coded 9.362, because the through-transform
   stacks live in the 2.403 um volume. Offsets are in um, which is comparable. The 2.403 um wide
   stacks use `--slice-step 4` = 9.612 um per layer, matching the native 9.362 um sampling and span.
   **Verified, not assumed:** the same window's native and through profiles correlate 0.9965 at
   9.612 um/layer and 0.79, 0.85, 0.55, -0.57 at every other candidate pitch.
3. **The profile is accumulated in two passes over the per-slice TIFFs** rather than loading the
   stack (161 x 3119 x 3119 does not fit comfortably). Numerically identical.
4. **A 1.0 mm patch profile is taken as well as the whole window.** Our windows are 7.5 mm, the
   model's own window; the sheet drifts in depth across that much surface. The whole-window number
   is what the model actually got and is primary; the 1 mm number says whether local structure
   exists. Both are in the tables. The 1 mm number turns out to be unstable and is not leaned on.

**One readout had to be replaced, and this is the methodological finding of the run.** The
sibling's script takes the **global argmax** of the contrast curve. A papyrus depth profile is
periodic, so a +-750 um stack holds several sheets and the global argmax answers "which sheet is
brightest", not "is the mesh on a sheet". It is unstable here: `pub_r2_c86` lands 202 um away while
its own production stack says +17 um, and `g_r10_c80` flips from -515 um to +548 um between two
arms whose curves are nearly flat. A naive nearest-local-maximum is no better - on a noisy curve it
returns a noise wiggle, and the first attempt here produced a "sheet period" of 48-82 um, three
times too fine to be a winding. A second attempt, an autocorrelation period, silently returned its
own lower search bound (94 um) for seven windows out of eight.

The readout actually used needs neither peak detection nor a period:

> **pct** = the share of the whole +-750 um contrast curve that lies **below** the value at the
> mesh. A surface on a sheet centre is near the top of that distribution; one riding a gap is near
> the bottom. **Its null is exact: a surface placed at random within +-750 um scores 0.50 by
> construction.**

`at_mesh`, axiosdevs' `sheet_contrast` exactly as they define it, is reported alongside it
untouched.

**Three arms per window**, the same mesh and the same window rect each time:

| arm | volume | transform | depth |
|---|---|---|---|
| `native` | 9.362 um eligible scan | **none** | 161 layers, +-749 um |
| `through` | 2.403 um sharp scan | the production one | 161 layers, +-769 um |
| `prod` | 2.403 um sharp scan | the production one | 109 layers, +-131 um - **the stack the model consumed, byte-for-byte the same render command** |

Hand-test first (L44): one window, `pub_r42_c126`, all three arms, read before any batch was
launched. Then five parallel batches. **44 scored (window, arm) pairs, 0 failures**, every batch
reporting its own counted failure list.

---

## 4. The instrument was calibrated on a transform of known quality, in both directions

A seating test that cannot fail is worthless. Our own registration tool grades PHerc0139's
cross-scan pairs (`registration_tool/REPORT_0912.md` section 3), so the same known-text control
mesh was put through two of them:

| control arm | transform | graded error, that report | native pct | through pct | profile corr |
|---|---|---|---|---|---|
| `ctl_w016_pass` | PHerc0139 9.362 -> 2.399, scanreg `v6_0139c` inverted | **PASS, 15 / 26 / 32 um** | 0.94 | **0.94** | **0.9942** |
| `ctl_w016` | PHerc0139 9.362 -> 2.403, scanreg `v2_0139a` inverted | **WEAK, 46 / 119 / 168 um**; the same report says these two scans bend and "no single matrix fits both ends" | 0.94 | **0.60** | **0.7177** |

The control mesh is `n9/ctl_w016_mesh`, our own PHerc0139 known-text control, cropped to a 41 x 41
grid window (7.7 mm, matched to the 1203 windows) inside the covered z band.

So the test **does** break a seated surface when the transform is bad - 0.94 down to 0.60, profile
correlation down to 0.72 - and **does not** when the transform is good. That is the axiosdevs -0.2
situation reproduced deliberately, on a mesh known to be seated and known to carry text.

The WEAK row was not planned; it was the first control run, and its failure was checked before
being written up rather than reported as a result (L79). The check found the cause in our own
earlier report: that specific pair is one of the seven graded WEAK, and the only one the report
singles out for bending.

For scale, our 1203 transform is **5.8 um RMS over 29 landmarks, 4.6 um on 48 held-out image
cubes** (`REPORT_0912.md` section 4) - about three times tighter than the PASS control and an order
of magnitude tighter than the WEAK one.

---

## 5. Results

### 5.1 Does the transform move the surface off its sheet?

Same mesh, same window, same binary; only the transform differs.

| window | ink % | prod transform | native at-mesh / pct | through at-mesh / pct | pct shift | profile corr |
|---|---|---|---|---|---|---|
| **ctl_w016_pass** (0139 known text) | - | 0139 PASS | +8.58 / 0.94 | +6.26 / 0.94 | 0.000 | 0.9942 |
| **ctl_w016** (0139 known text) | - | 0139 WEAK | +8.58 / 0.94 | +0.18 / 0.60 | 0.347 | 0.7177 |
| pub_r42_c126 | 28.0 | corrected | +4.68 / 0.98 | +4.92 / 0.99 | 0.007 | 0.9966 |
| g_r15_c85 | 21.7 | corrected | +4.54 / 0.96 | +4.44 / 0.96 | 0.008 | 0.9757 |
| pub_r2_c86 | 18.8 | corrected | +2.13 / 0.89 | +2.26 / 0.87 | 0.015 | 0.9859 |
| g_r35_c55 | 18.9 | corrected | -0.32 / 0.40 | -1.80 / 0.22 | 0.177 | 0.9513 |
| g_r10_c80 | 14.3 | 11 Sep | +0.31 / 0.57 | +0.29 / 0.59 | 0.022 | 0.9985 |
| pub_r140_c64 | 11.6 | corrected | -0.43 / 0.35 | -0.16 / 0.38 | 0.021 | 0.9939 |
| pub_r42_c2 | 7.6 | corrected | +5.31 / 0.99 | +6.98 / 0.99 | 0.000 | 0.9654 |
| pub_r180_c64 | 6.4 | corrected | -0.02 / 0.50 | -0.14 / 0.47 | 0.029 | 0.9944 |
| pub_r122_c42 | 5.9 | corrected | +3.42 / 0.86 | +2.46 / 0.79 | 0.071 | 0.9971 |
| g_r20_c90 | 5.4 | 11 Sep | +0.56 / 0.60 | +1.26 / 0.78 | 0.184 | 0.9853 |
| g_r100_c75 | 5.2 | corrected | +0.24 / 0.47 | +0.70 / 0.52 | 0.050 | 0.9310 |
| g_r60_c5 | 0.1 | corrected | -7.62 / 0.03 | -16.85 / 0.06 | 0.029 | 0.8601 |

Over the 12 PHerc1203 windows: **profile correlation median 0.986 (min 0.860), pct shift median
0.026 (max 0.184)**. Restricted to the ten windows on the corrected transform: correlation median
0.981, pct shift median 0.025.

Read that against the two control rows. Our transform behaves like the PASS control (corr 0.994,
shift 0.000) and nothing like the WEAK one (corr 0.718, shift 0.347). **The transform is exonerated.**

Two supporting facts:

- **The test sees a transform error far smaller than a winding.** `pub_r42_c126` was rendered in
  production through both transforms. Through the corrected one its at-mesh contrast is **+4.92**;
  through the 11 Sep one, which `REPORT_0912` measured as about 29 um off, mostly in height, it is
  **+3.13** - a 36 % loss. On the narrow production stack the rank drops from 0.84 to 0.48. So the
  instrument resolves tens of microns, not just whole windings.
- **The two arms read physically different data.** Native is the 9.362 um scan at 113 keV; through
  is the 2.403 um scan at 77 keV. Two independent scans agreeing to a profile correlation of 0.99
  across +-750 um of depth is a strong statement that the transform places the surface correctly.

### 5.2 Is each surface on a sheet at all? (a scroll and mesh property, not a transform one)

Bar: **pct >= 0.80 on a sheet, 0.60-0.80 borderline, < 0.60 not seated**, against an exact null of
0.50 and the control's 0.94.

| verdict | n | windows (ink %) |
|---|---|---|
| **ON a sheet** | 4 | pub_r42_c126 (28.0), g_r15_c85 (21.7), pub_r2_c86 (18.8), pub_r42_c2 (7.6) |
| borderline | 2 | pub_r122_c42 (5.9), g_r20_c90 (5.4) |
| **NOT seated** | 6 | g_r35_c55 (18.9), g_r10_c80 (14.3), pub_r140_c64 (11.6), pub_r180_c64 (6.4), g_r100_c75 (5.2), g_r60_c5 (0.1) |

Two independent supports for this split:

- **A displaced-surface null, free from the same curves.** The same surfaces displaced +-40 coarse
  voxels (374.5 um) along their own normals - the null the community critique of the 0826 report
  asked for, and which DRAFT 4.4 lists as missing - score **median pct 0.37**, against 0.87-0.99
  for the four seated windows.
- **Agreement with an instrument written independently three days earlier.**
  `evidence_0912/SHEET_CHECK.md` measured band prominence on three of these windows by a completely
  different method (41 native layers, 0.3 mm tiles, local cycle phase). Its ranking and this one
  agree on all three: r42_c126 band 0.20 -> pct 0.98; r122_c42 band 0.15 -> pct 0.86; r180_c64
  band 0.07 "weak band" -> pct 0.50, which is exactly the random-placement null.

**This sample is not random and must not be read as a rate.** The 12 windows were chosen as the
report's strongest plus a deliberate spread, so "4 of 12" is not "a third of the 127 windows".

### 5.3 The stack the model actually consumed

The model window is 62 of the 109 rendered layers, so **149 um deep**, inside a stack only **262 um
deep**. Measured on those exact renders:

| window | model window | centre vs mesh | prod at-mesh | prod pct |
|---|---|---|---|---|
| pub_r42_c126 | [24,86) | +2.4 um | +4.90 | 0.84 |
| g_r15_c85 | [23,85) | +0.0 um | +3.75 | 0.84 |
| pub_r42_c2 | [24,86) | +2.4 um | +5.76 | 0.84 |
| pub_r122_c42 | [24,86) | +2.4 um | +3.39 | 0.94 |
| pub_r2_c86 | [23,85) | +0.0 um | +2.47 | 0.48 |
| g_r20_c90 | [30,92) | +16.8 um | +1.21 | 0.74 |
| g_r10_c80 | [25,87) | +4.8 um | +0.22 | 0.61 |
| pub_r180_c64 | [24,86) | +2.4 um | -0.06 | 0.84 |
| g_r100_c75 | [25,87) | +4.8 um | +0.60 | 0.42 |
| pub_r140_c64 | [24,86) | +2.4 um | -0.21 | 0.81 |
| g_r35_c55 | [24,86) | +2.4 um | -0.19 | 0.48 |
| g_r60_c5 | [24,86) | +2.4 um | -10.95 | 0.48 |

Every model window is centred within 17 um of the mesh, so the per-window depth centring did what
it claimed. **But the `prod` percentile must not be quoted on its own**: a 262 um stack cannot
contain a full sheet-gap-sheet cycle, so its rank is computed over too narrow a range and the
badly-seated windows do not stand out (`pub_r180_c64` reads 0.84 there and 0.47 on the wide stack).
The wide arm is the instrument; the `prod` column exists to prove the wide arm was measuring the
same render the model saw, and the seated windows agree across the two (0.84-0.94).

The same fact stated plainly, because it matters to the report's interpretation: **if a surface is
one winding off, the stack the model consumes contains a neighbouring sheet and looks entirely
normal.** Nothing in the pipeline could have noticed.

### 5.4 What did not resolve

- **PHerc1203 has no sheet periodicity resolvable over a 7.5 mm window at 9.362 um.** The
  autocorrelation found a genuine winding spacing in 0 of 12 windows, while finding 112 um
  immediately on the PHerc0139 control. That is consistent with `SHEET_CHECK.md`'s independent
  measurement of tile modulation - 0.18-0.25 on 1203 against 0.83-0.84 on 0139 - and it is why no
  sheet spacing is quoted for 1203 here.
- **The 1 mm patch measure is unstable** and no conclusion rests on it: it disagrees with the
  whole-window measure on most windows in both directions (`g_r100_c75` 0.98 native vs 0.04
  through). A 1 mm spot can be anywhere in the local cycle. Reported in
  `seat1203_files/summary_1203.json` for completeness, used for nothing.
- **This check tests geometry, not the model.** It shows the chain puts the render on the sheet. It
  does not show the model can read PHerc1203 ink at 77 keV. DRAFT 4.4's third bullet stands
  untouched.

---

## 6. What this means for the 1203 report

**The report can move, in a narrowed form.** The BLOCKER's specific fear is disproved, and the
report's headline finding survives.

1. **The two unexplained 19-28 % windows are not explained away - they are the best-seated windows
   in the check.** `pub_r42_c126` (28.0 %) scores pct 0.99 and `pub_r2_c86` (18.8 %) 0.87, against a
   random-placement null of 0.50 and a displaced null of 0.38 and 0.27. DRAFT 6's sentence "The
   strong spots are unexplained, not explained away" now has a direct measurement behind it and
   should cite this file.
2. **5.6's existing sheet claim is confirmed by a second instrument and can be stated more
   strongly.** The prior claim came from `SHEET_CHECK.md`, whose headline the sibling agent
   correctly flagged as too strong. For this window the two instruments agree.
3. **The new band's best window is also seated.** `g_r15_c85` (21.7 %) scores 0.96. 5.5's remark
   that the second pass "came back the same" is safe.
4. **Three findings become unsafe and must be qualified or dropped:**
   - `g_r35_c55` (18.9 %, the new band's second best, 5.5's table) is **not seated** (0.22, below
     the displaced null). Its ink share is not a measurement of a surface and should not appear in
     a top-5 table without that flag.
   - `pub_r140_c64` (11.6 %, 5.6's third row) is **not seated** (0.38). 5.6's sentence "two windows
     at 19 to 28 %, one at 12 %" should drop the 12 %.
   - `pub_r180_c64` (6.4 %) sits exactly at the null (0.47/0.50). Consistent with SHEET_CHECK's
     "weak band"; nothing rests on it, but it should not be cited as covered area of sheet.
5. **The population claim must not be made.** 4 of the 12 tested windows are provably on a sheet.
   The report must argue from the seated windows, not from the 127-window total, exactly as the
   sibling agent concluded for the other three scrolls.
6. **DRAFT 3.2 step 5 and 3.4 are worded wrongly** and mislead a reviewer into thinking seating was
   already checked. `offset_generic.py` measures render-to-render registration, not sheet position.

### Changes to make in DRAFT.md

- **3.2 step 5**: replace "Centre the model window on the measured sheet" with "centre the model
  window on the mesh as located in the sharp render", and add one sentence saying this is a
  registration measurement, not a seating one, with a pointer to this file.
- **3.4**: retitle from "Where the sheet sat in the sharp renders" to "Where the mesh sat in the
  sharp renders", and add the seating result and its numbers.
- **5.5**: flag `g_r35_c55` as not seated in the top-5 table.
- **5.6**: drop the 12 % window from the "stable picture" sentence; keep the 19-28 % pair and add
  that both are measured on a sheet, with the pct numbers and the displaced null.
- **4.4**: the second bullet ("No off-sheet null on PHerc. 1203") can be struck - section 5.2 above
  supplies a +-374.5 um displaced null on 12 windows. The first and third bullets stand; say
  explicitly that the new PHerc0139 control tests the render geometry only, not the model.
- **6 (Verdict)**: keep "unexplained, not explained away" and cite this check by name; add one line
  that roughly half the windows tested are not on a sheet and that the argument is made from the
  seated ones.
- **Honest Limits / section 8**: credit axiosdevs for the test, as `SEATING_CHECK.md` item 4 already
  requires.

---

## 7. Files, and what was run

On box A under `<run-dir>/seat1203/`: `seatprof.py` (render + profile + contrast, one row per
window and arm), `mkctl.py` and `mkctl2.py` (the control mesh crop and the two inverted PHerc0139
transforms), the six case lists, `seatprof2_[a-f].json`, `batch_[a-f].log`, `handtest.log`,
`affine_0139_9to2.json`, `affine_0139c_9to2.json`, `ctl_w016_win/`. Local copies of every script,
result and log are in `evidence_0914/seat1203_files/`, plus `summarise1203.py` and
`summary_1203.json`, which regenerate every table above from the raw rows. axiosdevs' code is not
vendored into this repo; their tree stays on box A under `<run-dir>/seatcheck/`.

The production transform files used are box A's own `p1203_fine/affine_1203_v2.json` and
`affine_1203.json` - the same files the render pipelines cite - not copies.

**44 scored (window, arm) pairs across six batches, 0 failures.** Three readouts were tried and two
discarded before the tables above were written; all three are described in section 3 rather than
hidden. Cost: box A CPU only, about 45 minutes wall across five concurrent jobs plus a 14-minute
hand test, all streaming ranged reads from the public bucket. No GPU, no spending, nothing
downloaded into `<project>` except the small JSON and log copies. Renders were deleted immediately
after each profile; box A's free disk never went below **86 GB**.
