# scanreg: line up two CT scans of the same scroll

One command. Two public OME-Zarr volumes of the same scroll in, a `transform.json` in the Vesuvius Challenge's own
format out, plus a report with every intermediate number and a picture to check by eye. CPU only, no GPU, no
hand-placed landmarks.

```
python scanreg.py MOVING_URL FIXED_URL --out DIR [--write-inverse]
```

Version 0.2.1. Built with an LLM coding assistant (Claude Code) under kadenpool's direction; see the last section
for who did what.

## Why

Several scrolls in the open data have more than one scan (a whole-scroll scan at about 9 um and a sharper partial
scan at about 2.4 um). To use a surface found in one scan on the other you need the transform between them. The
challenge publishes one for some pairs, fitted from hand-placed landmarks, and none for others. This tool finds it
automatically, for any two volumes of the same object, and checks itself against the published ones.

## Install

Python 3.10 or newer, and

```
pip install numpy scipy fsspec s3fs Pillow
```

(`numcodecs` too if a volume is compressed). Reads 0.4 to 2.5 GB per pair straight from the public bucket; 3 to
16 minutes on 8 cores; 3 to 6 GB of RAM. `https://vesuvius-challenge-open-data.s3.amazonaws.com/...zarr/` URLs
become anonymous S3 reads; other `https://` hosts (for example the 2023 scans on
`https://data.aws.ash2txt.org/samples/...`) are read over plain HTTP.

## Example: PHerc1203

PHerc1203 has a 9.362 um scan of the whole scroll and a 2.403 um scan of 36 mm of it, and the challenge publishes
no transform between them.

```
B=s3://vesuvius-challenge-open-data/PHerc1203/volumes
python scanreg.py $B/20260319130212-2.403um-0.2m-77keV-masked.zarr \
                  $B/20250820131727-9.362um-1.2m-113keV-masked.zarr --out out_1203 --write-inverse
```

About 200 s and 1.3 GB read. Result: confidence `HIGH`; 29 of 30 blocks matched at the finest (19 um) level with a
median block correlation of 0.98 and a residual of 5.8 um RMS; the sharp scan sits with its first slice at 9.362 um
voxel z 7935 (74.29 mm along the scroll), scale 0.03 % under nominal, tilt 0.09 degrees. Two independent runs on
12 Sep 2026 put that first slice at z 7935.2 and 7935.3. The outputs of one of them are in `examples/pherc1203/`.

Cross-check against the two public PHerc1203 registrations (`compare1203.py`, over 5000 points in scroll
material): ours agrees with 7jycwjmbfn-eng's block-matching registration (pherc0139-physical-audit,
`pass3_final.npz`) to 3.5 um median and 6 um max. flummoxjr's transform (measure-before-you-hunt,
`pherc1203_2403um_to_9362um.json`) differs from ours by 29 um median, mostly in height. On 48 held-out image cubes
the correction still needed is 4.6 um (ours), 5.0 um (7jycwjmbfn-eng) and 33 um (flummoxjr). Our own first attempt
at this pair, made by hand before this tool existed, had the same 29 um height error; that is why the tool exists.

## Output

| file | what |
|---|---|
| `DIR/transform.json` | `schema_version`, `fixed_volume`, `transformation_matrix` (3x4), `fixed_landmarks`, `moving_landmarks`: the same keys as the official `<volume>.zarr/transform.json` files |
| `DIR/transform_inverse.json` | with `--write-inverse`: the same transform the other way round (fixed to moving) |
| `DIR/report.json` | every intermediate number: search candidates and scores, block matches, residuals, the transform decomposed into scale / rotation / tilt / mirror / upside-down, and a `confidence` verdict |
| `DIR/qc.png` | three cross-sections of the shorter scan, the other scan sampled on the same plane through the transform, and a checkerboard of the two (tiles alternate between scans; wrap lines and cracks must run on across tile edges). Look at it. |

**Convention (same as the official files):** `transformation_matrix` maps a MOVING level-0 voxel `(x, y, z)` to a
FIXED level-0 voxel `(x, y, z)`: `fixed = M[:, :3] @ moving + M[:, 3]`. The order is x, y, z, while zarr arrays are
indexed `[z, y, x]`. The landmarks are the automatic block matches used in the final fit, in the same coordinates,
so anyone can check or re-fit the file.

## Method

1. **G1, whole-scroll search (about 300 um; finer for small objects).** The taller scan is read whole at a coarse
   pyramid level; five cross-sections of the shorter scan are read at about 75 um. Each cross-section becomes a
   polar signature around its material centroid (outline plus band-passed inner detail), so one FFT scores all 360
   rotations, and mirror images and upside-down placements are scored too. The five heights must match five heights
   of the other scan at the right spacing, which pins the height. If the best answer does not clearly beat the next
   one, or the shorter scan sees only part of the cross-section (the 1.129 um mosaic tiles), a full 2D search (every
   5 degrees, both mirror images, every height) is added.
2. **G2, re-score the best answers (about 150 um).** Full 2D image matching of the inner detail at the five
   heights, refining rotation (0.25 deg), height and height scale. Winner and margin over the runner-up are
   reported. The five placements give a first 3D transform; the xy drift with height gives the tilt.
3. **B, 3D block matching (about 75, 37 and 19 um).** Dozens of small cubes of the shorter scan (one per storage
   chunk, spread over height and area, inside material) are matched inside the other scan by masked normalised
   cross-correlation with sub-voxel peaks. Each match is a landmark pair; a 12-parameter affine is fitted with
   outlier rejection, two rounds per resolution. If too few cubes match, the search box widens (x2, x4).
4. **Confidence.** `HIGH`, or `CHECK` with the reasons (small G2 margin, too few blocks, block residual over 30 um).
   Every failure seen in validation from v0.2 on was flagged `CHECK`.

Pyramid levels are 2x2x2 means (checked: level 1 equals mean-pooled level 0 to r = 0.99997), so level-L voxel `i`
is centred on level-0 coordinate `2^L i + (2^L - 1)/2`; the tool uses that everywhere.

## How good is it: checked against the challenge's own transforms

The rule was fixed before any validation pair ran (`PREREG.md`). Error = distance between where ours and the
official transform put the same point, over 4000 random points in scroll material. PASS = 95th percentile within
30 um (about 3 voxels of a 9.4 um scan, 12 of a 2.4 um scan); WEAK = within 150 um (right place, not good enough to
render a segment from the other scan); FAIL = worse, or no answer. The official transforms come from the open-data
`metadata.json`.

Twelve official pairs on 7 objects, voxel sizes 1.129 to 9.362 um, including the 2023 7.91 um scans (turned over,
81 and 121 degree turns), 176 and 178 degree turns, a 14 degree tilt, and 1.129 um tiles that see only part of the
cross-section. Current version (0.2.1) on all twelve:

| pair (moving to fixed, um) | what the official transform says | error vs official: median / 95th pct / max (um) | verdict | held-out image cubes must move: ours / official (median um) |
|---|---|---|---|---|
| PHerc0139 2.403 (scan 20250820105138) to 9.362 | plain | 43 / 107 / 152 | WEAK | 21 / 42 |
| PHerc0009B 8.64 to 2.401 | 2.8 deg tilt | 15 / 37 / 153 | WEAK | 6 / 18 |
| PHerc0814 2.399 to 9.362 | 176 deg turn | 13 / 36 / 53 | WEAK | 9 / 18 |
| PHerc0139 2.403 (scan 20250822062710) to 9.362 | plain | 12 / 24 / 33 | PASS | 9 / 17 |
| PHerc0139 2.399 (scan 20260102150214) to 9.362 | 178 deg turn | 18 / 31 / 38 | WEAK | 14 / 22 |
| PHerc0500P2 4.317 to 2.215 | plain | 18 / 45 / 68 | WEAK | 8 / 22 |
| PHerc0500P2 2.215 to 9.362 | 14 deg tilt, 163 deg turn | 7 / 33 / 39 | WEAK (flagged CHECK; placement right) | 6 / 9 |
| PHercMANBp 1.129 to 2.399 | plain | 6 / 13 / 27 | PASS | 10 / 10 |
| PHerc1667 2.399 to 7.91 (2023) | upside down, 81 deg turn, 4 deg tilt | 14 / 24 / 34 | PASS | 8 / 21 |
| PHerc0332 2.399 to 7.91 (2023) | upside down, 121 deg turn, 2 deg tilt | 37 / 69 / 87 | WEAK | 9 / 45 |
| PHerc0814 1.129 to 2.399 | partial view | 4 / 8 / 12 | PASS | 5 / 6 |
| PHerc0139 1.129 to 2.399 | partial view | 5 / 7 / 9 | PASS | 5 / 4 |

Summary: right placement 12 of 12; 5 PASS, 7 WEAK, 0 FAIL; median error 4 to 43 um. Full per-pair outputs are in
`results/<pair>/` (transform, official transform, validation numbers, image checks, `qc.png`, log).

**What the WEAK verdicts mean.** In all 7 WEAK pairs the held-out image cubes need less correction under our
transform than under the official one (right-hand column). That referee uses the same block-matching idea as the
fit itself, so read it as a hint, not a verdict that the official files are off. Two of the WEAKs have a visible
cause: for PHerc0332 the official transform's own landmarks sit 103 um RMS off its own matrix, so the reference is
noisy; for PHerc0139 2.403 to 9.362 (Aug 2025) the two scans bend relative to each other by up to about 100 um,
which no single matrix can fit. Verdicts are kept exactly as the pre-set rule gives them.

**How blind this was.** The first round (v0.1; 8 of the pairs above) ran after the rule was fixed and before any of
them had been looked at: 7 of 8 placed right, the 14 degree tilt pair failed. A second round on 4 pairs never run
before (v0.2): 3 of 4 placed right; the PHerc0139 1.129 um partial-view pair failed and was flagged `CHECK`. Each
failure was fixed in code and re-run (next section). The table is the current version on all 12, so the table
itself is not blind.

## What failed and was fixed

1. v0.1.0: one unmasked slice of an 8.64 um scan counted as 80 % "material" and became the yardstick, so every
   normal slice was discarded; answer 26 mm off. Fix: the 75th-percentile slice.
2. v0.1.1 on the 14 degree tilt pair: rotation and most of the tilt found, fine fit failed (1 to 2 mm off at the
   edges, only 6 to 7 cubes). Fix (v0.2.0): two cubes per storage chunk at the coarsest level and a search box that
   widens when cubes fail. Now 7 um median.
3. v0.2.0 on the PHerc0139 1.129 um tile: 3 mm off, flagged `CHECK`; the partial view was missed by the area-ratio
   test. Fix (v0.2.1): run the slow 2D search whenever the quick search has no clear winner. Now 5 um.
4. Bending between scans (PHerc0139 2.403 vs 9.362): not a bug, a limit of any single matrix; the block residuals
   and `datacheck.py` show how much.

## Checking a result

- `report.json -> confidence`: `HIGH`, or `CHECK` plus reasons.
- `report.json -> g2.results`: the winner's detail score should stand well above the runner-up (PHerc1203: 0.89
  vs 0.15).
- `report.json -> blocks[-1]`: blocks used / tried, median block NCC, residual RMS. On good pairs: most blocks
  used, NCC about 0.9 or better, residual RMS 5 to 15 um.
- `qc.png`: in the checkerboard, wrap lines and cracks must run on across tile edges, not jump.
- `validate.py` compares a result with the official transform where one exists; `datacheck.py` asks the images
  which of several transforms fits better (held-out blocks, or blocks at given landmarks).

## Limits

- One affine matrix, no bending. Scans taken months apart can bend relative to each other (PHerc0139 2.403 vs
  9.362: up to about 100 um).
- Tilt: validated up to 14 degrees (one pair, after the v0.2 fix). Larger tilts are untested.
- Partial fields of view: validated on two 1.129 um tiles; the 2D search they need takes about 10 to 15 minutes.
- Mirror images and upside-down placements are searched for; upside-down is exercised by the two 2023 pairs in
  the table, mirror is not exercised by any pair in the table.
- Only zarr v2 pyramids with a `0..N` level layout; masked volumes (zero outside the scroll) are assumed; the voxel
  size is read from the volume name (`-2.403um-`) unless `--um-moving` / `--um-fixed` are given.
- The `CHECK` flag is cautious: one listed pair was flagged and is right; every real failure since v0.2 was flagged.

## Files

| file | what |
|---|---|
| `scanreg.py` | the tool |
| `validate.py` | error of a result against the official transform in the open-data `metadata.json` |
| `datacheck.py` | which of several transforms the images agree with (held-out blocks, or blocks at given landmarks) |
| `compare1203.py` | PHerc1203: our result against the two public transforms, with the image check |
| `summarize.py` | results table from run folders |
| `run_validation.sh`, `pairs.txt` | the validation batch (the 12 pairs above) |
| `run_1203.sh` | the PHerc1203 example, then the comparison |
| `PREREG.md` | the pass/fail rule as written before the validation ran |
| `examples/pherc1203/` | one complete PHerc1203 run: `transform.json`, `transform_inverse.json`, `report.json`, `qc.png`, `log.txt` |
| `results/<pair>/` | the 12 validation runs |

## Credits and disclosure

- 7jycwjmbfn-eng, pherc0139-physical-audit: the first public 2.403 to 9.362 um registration of PHerc1203 (about
  19,000 block matches). Our result agrees with it to 3.5 um, which is the strongest check we have on this pair.
- flummoxjr, measure-before-you-hunt: a public PHerc1203 transform, and the scan-quality survey of the eligible
  scrolls.
- Paul Geiger, VesuviusScrollAlignment (2024): automatic refinement of an existing transform. The challenge's
  `find_transform.py` (hand-placed landmarks) defines the output format this tool writes.
- The challenge's published `transform.json` files are the reference for every number in the table.
- This tool was built with an LLM coding assistant (Claude Code) under kadenpool's direction: the assistant wrote
  the code and ran the validation batches; kadenpool set the goal, ran the PHerc1203 example himself and checked its
  picture. Every number above traces to a file in this repository.
