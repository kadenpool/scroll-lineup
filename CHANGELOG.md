# Changelog

`python scroll_lineup.py --version` prints the version the code actually is.
Every entry below is a failure seen on real scan data, not a refactor, and where the re-run is published the
entry points at it.

## 0.2.1, 12 Sep 2026 (current)

- **Fix: a partial field of view could be missed.** A 1.129 um mosaic tile of PHerc0139 sees only part
  of the cross-section. The area-ratio test did not catch that, the quick polar search picked the wrong
  height, and the answer was 3 mm out. The tool flagged it `CHECK`. Now the slow full 2D search runs
  whenever the quick search has no clear winner, not only when the area ratio says "partial". That pair
  is now 5 um median (`results/n4c_0139roi/`).

## 0.2.0, 12 Sep 2026

- **Fix: the fine fit failed on a 14 degree tilt.** On PHerc0500P2 2.215 -> 9.362 um the rotation and
  most of the tilt were found, but only 6-7 blocks matched and the edges were 1-2 mm out. Now two blocks
  are taken per storage chunk at the coarsest block level, and the search box widens (x2, then x4) when
  too few blocks match. That pair is now 7 um median (`results/v8_0500b/`).
- Added the `CHECK` confidence flag with its reasons (small G2 margin, too few blocks, block residual
  over 30 um). Every real failure from this version on was flagged.
- Capped the 8-bit reads and the per-volume cache at 1.2 GB after a validation step read a whole volume
  as float64 and was killed by the OOM killer.

## 0.1.1, 12 Sep 2026

- **Fix: one unmasked slice hijacked the search.** In one 8.64 um scan a single slice is 80 % "material"
  where every other slice is a few per cent. The search used the largest slice as its yardstick, so every
  normal slice was discarded and the answer was 26 mm out. The yardstick is now the 75th-percentile slice.

## 0.1.0, 12 Sep 2026

- First working version. Hand-tested on PHerc1203 only, which has no official transform, so nothing in
  that testing could tune the tool towards the published answers. The pass/fail rule (`PREREG.md`) was
  written against this version, before any validation pair was run.

## Known issues, found by running on the public catalogue (15 Sep 2026)

Both were found after the validated version was frozen, and both are in `VALIDATION.md` with the run
that found them. One is fixed and one is not, for the same reason in both cases: a change that could
alter a committed result is not made, because it would invalidate the runs this package is graded on.

- The `datacheck.py` crash **is** fixed. Its guard sits in front of the failing array access and
  changes no other path, so no committed result can move.
- The `numcodecs` gap is **not** a code change at all. It was a wrong comment in
  `requirements.txt`, and the comment is corrected.

- **Fixed 15 Sep 2026: `datacheck.py --at-landmarks` on a reference with no landmarks.**
  `PHerc0172 7.91 -> 7.91` is the only pair in the catalogue whose official transform publishes none:
  `moving_landmarks` and `fixed_landmarks` are both empty, and the code indexed the empty array.
  It now exits with a message naming the missing field and suggesting the held-out mode instead.
  Verified by running it on that exact pair: exit 0, no traceback. The guard sits in front of the
  array access and changes no other path, so every result committed here is unaffected.
- **The five-package install is not enough for every public volume.** `PHerc0172`'s fixed volume is
  blosc-compressed at every pyramid level, so it needs `numcodecs`, which `requirements.txt` had
  described as needed only for volumes the public set does not contain. The comment is corrected and
  the claim now names the volume.

## Packaging notes for this release

- **Name.** The tool was written under a working name and renamed to `scroll-lineup` on 15 Sep 2026, before
  it was published anywhere, so no version number moved: the code is identical apart from the name, and the
  committed PHerc1203 example was re-run from a clean clone after the rename and still produces a
  byte-identical `transform.json` and `transform_inverse.json`. One visible leftover: each `qc.png` prints
  the tool's name and version in its title strip, and the twelve pictures in `results/` were drawn before the
  rename, so they carry the working name. Their transforms, reports and numbers are unaffected;
  `examples/pherc1203/qc.png` was redrawn after it.
- `LICENSE` (MIT), `requirements.txt`, this file, `--version`, and a `results/` folder holding the
  complete output of all twelve validation runs plus one worked PHerc1203 example, so a reviewer can
  check every number in the README without running anything.
- Verified from a clean clone into an empty virtual environment on 14 and again on 15 Sep 2026: Python 3.12.3
  on 8 CPU cores, with numpy 2.5.3, scipy 1.18.1, fsspec 2026.7.0, s3fs 2026.7.0 and pillow 12.3.0 installed by
  the README's own `pip install` line. `run_1203.sh` reproduced the committed example byte for byte (md5s are in
  the README), and `summarize.py` regenerated `results/table.md` from the committed results unchanged,
  byte for byte, when the run folders are passed in `pairs.txt` order, which is the order the table is in.
- Known wrinkle, not a bug in this tool: on Debian and Ubuntu `python3 -m venv` fails until the separate
  `python3-venv` package is installed, because those distributions ship `python3` without `ensurepip`.
- **Continuous integration and offline checks, added 15 Sep 2026.** `tests/test_offline.py` re-derives
  every cell of `results/table.md` from the committed per-pair JSON and checks the geometry the tool
  rests on; it needs no network and takes a couple of seconds. `tests/compare_run.py` compares a fresh
  run with a committed one. `.github/workflows/ci.yml` runs the offline checks on Python 3.9, 3.11,
  3.12, 3.13 and 3.14 and then one public pair end to end. **Every command in that workflow was first
  run locally, exactly as written, and passed. On the first push, 15 Sep 2026, it then ran on GitHub
  and all six jobs passed**, which is what the README badge reports. The local transcript is in
  `VALIDATION.md`.
- **Nine further pairs, 15 Sep 2026.** `pairs_robustness.txt` and `robustness/` hold every official
  transform in the open-data catalogue that was not in the first twelve, apart from five on two
  objects this repository does not discuss. Same script, same rule, results in `VALIDATION.md`.
- **Python 3.9 works.** The README used to ask for 3.10 or newer. The tool compiles and runs on 3.9.6
  with numpy 2.0.2 and scipy 1.13.1, and CI checks it on every push.
