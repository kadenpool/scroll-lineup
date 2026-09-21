# PLAN B PREP — PHerc0813 renders + ink_9um kernel, ready to run (12 Sep 2026)

Private preparation only (Kaden, 22:55 AEST: "if A doesn't work then go to B"). Nothing public: no GitHub, no Discord,
the Kaggle dataset is private, the kernel folder is written but NOT pushed. Times below are AEST from `date`
(box A's clock is UTC, +10 h). Started 22:57, renders done 23:34, dry run 23:11–23:17, upload started 23:34. Work lives
on box A in `<run-dir>/p0813/` (17 GB while the tars and their uncut copies both existed; 8.6 GB at the end after
the uncut copies were deleted once the upload was verified; box A has 130 GB free) and the
scripts, selection, manifest, pictures and dry-run summary are copied to `evidence_0912/plan_b_0813_files/`.

## 1. Short version

1. **Selected 32 of pscamillo's 75 PHerc0813 meshes, 131.8 cm²**: the 12 judged usable by eye (11 `aprova` + 1
   `parcial`) plus the 20 unjudged w040/w060 meshes at the same 11 z-windows (3.5–6.0 cm² each, so every region has
   a mesh over the 4 cm² rule; the two meshes judged `reprova` at those z, z6496_w060 and z8288_w040, are skipped).
2. **Every selected mesh sits inside the eligible volume `20250821151723` (9.362 µm, z 16993 × 7947 × 7947) in that
   volume's own voxel frame** — x/y/z.tif ranges checked against the live `.zarray`, `meta.json` bbox and area
   re-derived and matched to `index.csv`, grid scale 0.05. No mesh needs a transform.
3. **Rendered all 32 with exactly the 9 µm check recipe** (101 slices 1 voxel apart centred on the mesh,
   `--flip-normals`, `--auto-crop`, scale 1, cache 4 GB, timeout 120) and cut the three 21-slice windows the same way
   as Plan A (`on` = slices [40,61), `offA` = [0,21), `offB` = [80,101)). Hand test first (z7104_w020, L44): fibre weave
   visible, 56% of the canvas on-mesh, flat depth profile (packed sheets, as on 0846A). Then all 32 in 31 min wall
   (two workers, 57–196 s each, 0 failures): 128.8 of 131.8 cm² came back on-mesh (97.7%), canvases from 1941×1761 to
   12301×1821 px, on-mesh fraction 0.40–0.79 of each canvas; 32 tars, 8.24 GB.
4. **The PHerc0139 w016 control is the same render the 9 µm check validated** (AUC 0.88 / 0.85), copied from box B and
   cut into the same three windows, with its held-out labels on the render grid packed alongside.
5. **Private Kaggle dataset `<kaggle-user>/p0813-nineum-b0`** (7.7 GiB, 37 files: one tar per mesh, the control tar,
   the villa inference source, manifest + selection). Uploaded 23:34–23:41, status `ready` at 23:43 AEST, dataset id
   11995562, `isPrivate: true` (metadata API). Kaggle extracted every tar on ingest, so the mount holds
   `<name>/<name>/on|offA|offB/surface-volume.zarr/...` — the layout the kernel globs for. Verified file by file
   (`check_ds.sh`, 171 pages of 200): **34,073 files, 8,224,512,130 bytes, every name and byte size equal to the local
   copy, 0 missing / 0 mismatched / 0 extra**; 36 top-level entries = 32 meshes + `ctl_w016` + `villa_vesuvius_src` +
   the two JSONs.
6. **Kernel folder box A `<run-dir>/kag/n9_0813/`** (`nb.ipynb` + `kernel-metadata.json`, private, id
   `<kaggle-user>/vesuvius-n9-0813`, GPU, internet): runs ink_9um seed43 step-060000 and seed42 step-010000, both depth
   orders, on every mesh's on-sheet window, both off-sheet windows and the control; writes `results.json` +
   `summary.md` (ink share > 0.5 per window/checkpoint/direction, on/off ratio, control AUC). **Not pushed.** Its
   exact code was dry-run on box A CPU (seed43, on-sheet window) on the control + one 0813 mesh: **control AUC 0.877
   forward / 0.525 reverse, 18.9% ink share in the validation region, 57% of labelled-ink px vs 7.4% of background px
   called ink — the 9 µm check's numbers to the digit (0.877 / 0.53 / 18.9% / 57% / 7.4%)**, 0 missing / 0 unexpected
   checkpoint keys, layer indices 2..18 and 18..2. First 0813 mesh (z7104_w020): 8.9% forward / 13.6% reverse on the
   sheet, blotchy blobs, no rows (one mesh, one checkpoint, no off-sheet windows yet: a smoke test, not a verdict).
7. **Push (one command, from box A, only after Plan A's verdict):** `ssh box A '<run-dir>/p0813/push_kernel.sh'`
   (refuses unless the metadata says private and the id is right; then `kaggle kernels status <kaggle-user>/vesuvius-n9-0813`
   and `kaggle kernels output <kaggle-user>/vesuvius-n9-0813 -p kag_out/n9_0813`). Expected GPU time on 2×T4: roughly
   2–5 h (267 Mpx of canvas per window, 55% of it on-mesh so villa's occupancy scan skips the rest; 3 windows × 2
   checkpoints × 2 directions; the CPU dry run did 16.6 Mpx of map in 380 s on 4 threads and a T4 in fp16 should be
   20–50× that). One session (12 h cap) and one week's 30 GPU-h quota cover it either way; to shorten, run with
   `N9_WINDOWS=on,offA` (one off-sheet window, −1/3) or `N9_LIMIT=<n meshes>` in the notebook's run cell.

## 2. Selection (task 1) — `p0813/selection.json`

Source: `github.com/pscamillo/vesuvius-eligible-meshes` at `0c966f8` (9 Sep, "README: positional precision limit"),
cloned to box A `p0813/meshes-repo/` (182 MB). `data/index.csv` has 75 PHerc0813 rows (15 z-windows × w020..w100),
24 with a `gate_verdict`: 11 `aprova`, 1 `parcial`, 12 `reprova`. Their criterion (`docs/QUALITY.md`): weave =
crossing bands 70–150 px wide at 9 µm; approve = coherent weave over most of the panel; partial = at least one
continuous patch of several cm²; reject = melting everywhere. Meshes are one winding per 800-voxel z-window
(≈2.2 cm² at w020, 4.3 at w040, 6.3 at w060), sit within ~5 voxels of the sheet, grid scale 0.05.

Rule applied (shortlist section 4 step 1): every mesh judged usable + the unjudged w040 and w060 at the same z
(the smallest wraps that clear 4 cm², and the wraps with the best usable rate after w020: 50%/50% vs 38%/33% for
w080/w100), skipping any judged `reprova`.

| z-window | usable by eye | added unjudged | region area available |
|---|---|---|---|
| z6496 | w020 aprova 2.21 | w040 4.27 (w060 is reprova) | 6.5 cm² |
| z7104 | w020 aprova 2.27 | w040 4.17, w060 5.99 | 12.4 |
| z7696 | w020 aprova 1.81 | w040 3.69, w060 5.56 | 11.1 |
| z8288 | w020 aprova 1.78 | w060 5.57 (w040 is reprova) | 7.4 |
| z11296 | w020 aprova 1.72 | w040 3.71, w060 5.67 | 11.1 |
| z11904 | w020 aprova 1.75 | w040 3.69, w060 5.92 | 11.4 |
| z12496 | w020 aprova 1.73 | w040 3.66, w060 5.90 | 11.3 |
| z13088 | w020 aprova 1.73 | w040 3.45, w060 5.68 | 10.9 |
| z13696 | w020 aprova 1.78 | w040 3.69, w060 5.78 | 11.3 |
| z14304 | w020 parcial 2.02, **w100 aprova 9.58** | w040 4.10, w060 5.98 (region already cleared by w100; kept as 4–6 cm² candidates at better-yield wraps) | 21.7 |
| z14896 | **w080 aprova 7.49** (w020 is reprova) | w040 3.83, w060 5.65 (same reason) | 17.0 |

Total 32 meshes, 131.8 cm² (12 usable = 35.9 cm²; 20 unjudged = 95.9 cm²). Not taken: the 12 `reprova`, the 31
unjudged meshes at z-windows with no usable verdict (z4704, z5296, z5888, z9504) or at w080/w100, and flummoxjr's
0813 patches (tilted across the sheets, their own ink test withdrawn). The unjudged w040/w060 double as the
within-scroll baseline the shortlist asks for (step 6b: ≥ 8 ordinary meshes through the same pipeline).

## 3. Frame and bounds check (task 2) — `p0813/select_and_check.py`

- Volume: the only PHerc0813 volume in the bucket,
  `https://vesuvius-challenge-open-data.s3.amazonaws.com/PHerc0813/volumes/20250821151723-9.362um-1.2m-113keV-masked.zarr/`
  (level 0: shape z 16993 × y 7947 × x 7947, uint8, 128³ chunks, uncompressed; levels 1–5 present). No `meta.json`
  in the zarr (voxel size comes from the name; `vc_render_tifxyz` prints "Voxel size: 1.0 (no metadata)" as it did
  for 0846A and 0139).
- For each selected mesh, x/y/z.tif were read (float32, −1 = no point; the three valid masks agree), min/max of the
  valid points compared with the volume shape: **all 32 inside** (x 924–6467, y 1592–6259, z 6499–15695). The
  `meta.json` bbox matches the tif ranges to < 1 voxel, `area_vx2 × (9.362 µm)²` matches `index.csv` to < 0.02 cm²,
  scale is 0.05, and each mesh's z range lies inside its named window [z, z+800). `fit_config` in `meta.json` names
  no volume; the frame is established by the README ("full-resolution voxels of the volume", same 0.05 grid scale as
  the team's PHerc0139 meshes) and confirmed by the render: the hand-test render shows papyrus weave, not noise or
  black, at the mesh's own coordinates with no affine.
- **No mesh needs a transform.** (Contrast 0846A/1203, where our own grown surfaces needed a frame fix.)

## 4. Renders (task 3) — `p0813/render_one.sh`, `render_all.sh`, `cut3.py`, `manifest.json`

Recipe = `evidence_0912/nine_um_files/render_one.sh` with only the volume URL changed:
`vc_render_tifxyz --volume URL --remote-url URL -s <mesh> --auto-crop --scale 1 -g 0 --num-slices 101 --slice-step 1
--flip-normals --zarr-output <out>.zarr --pyramid 0 --timeout 120 --cache-gb 4` (villa build on box A, the same binary
as the 9 µm check and the 0846A survey). Each mesh is rendered alone in its own process (fresh 4 GB cache, so
pscamillo's "nothing found at path" cache carry-over cannot happen) — the "direct" tiling of the within-scroll null
(NINE_UM_CHECK section 10.1 point 7: state the tiling; this is it). Two nice'd workers, one render at a time each,
so the running 0846A survey on box A was not disturbed (load stayed under the core count).

Hand test (L44), z7104_w020, 23:01–23:03 AEST: `auto-crop: [2781×1621 from (19,19)]`, 118 s, 248 MB, shape
(101, 1621, 2781); slice 50 on-mesh fraction 0.563, mean grey 99.8 ± 37.3; depth profile flat (mean grey 110.7 at
slice 0 → 99.8 at 50 → 96.3 at 100: packed sheets, the off-sheet windows land on neighbouring wraps, as on 0846A).
Picture: `plan_b_0813_files/hand_z7104_w020_s50_crop800.png` (800 px full-res crop at the mesh centre: clear
crossing fibre bands, some dark melt patches and cracks).

Cut (`cut3.py` = Plan A's `cut_slabs.py` heldout path): `<name>/on|offA|offB/surface-volume.zarr` (zarr v2, array
"0", (21, H, W) uint8, chunks (21,128,128), zstd), `valid.npy` (= on-window max > 0), `cut_info.json`; every write
read back. One tar per mesh in `p0813/kds/`.

Per mesh (from `manifest.json`; canvas = auto-crop render size; on-mesh = fraction of the canvas the mesh covers; grey =
mean of the centre slice on the mesh, then of the two off-sheet windows; tar = the three 21-slice windows, MB):

| mesh | verdict | cm² (index) | z range | canvas px | on-mesh | cm² rendered | render s | grey on | grey offA/offB | tar MB |
|---|---|---|---|---|---|---|---|---|---|---|
| z6496_w020 | aprova | 2.21 | 6500–7294 | 2981×1561 | 0.53 | 2.16 | 92 | 106 | 103/98 | 137 |
| z7104_w020 | aprova | 2.27 | 7107–7900 | 2781×1621 | 0.56 | 2.22 | 118 | 100 | 110/100 | 142 |
| z7696_w020 | aprova | 1.81 | 7699–8491 | 1941×1761 | 0.59 | 1.77 | 111 | 95 | 86/73 | 105 |
| z8288_w020 | aprova | 1.78 | 8291–9083 | 2381×1601 | 0.52 | 1.75 | 108 | 90 | 96/91 | 108 |
| z11296_w020 | aprova | 1.72 | 11301–12093 | 2281×1101 | 0.76 | 1.68 | 61 | 79 | 84/71 | 97 |
| z11904_w020 | aprova | 1.75 | 11908–12702 | 2461×1081 | 0.73 | 1.70 | 57 | 83 | 80/67 | 95 |
| z12496_w020 | aprova | 1.73 | 12499–13293 | 2521×1001 | 0.76 | 1.68 | 60 | 74 | 81/69 | 95 |
| z13088_w020 | aprova | 1.73 | 13091–13881 | 2381×1021 | 0.79 | 1.68 | 65 | 74 | 75/68 | 94 |
| z13696_w020 | aprova | 1.78 | 13698–14494 | 2461×1041 | 0.77 | 1.73 | 66 | 86 | 86/82 | 103 |
| z14304_w020 | parcial | 2.02 | 14307–15103 | 2321×1361 | 0.71 | 1.97 | 98 | 101 | 94/103 | 126 |
| z14304_w100 | aprova | 9.58 | 14305–15103 | 12301×1821 | 0.48 | 9.37 | 196 | 107 | 104/105 | 604 |
| z14896_w080 | aprova | 7.49 | 14897–15695 | 9481×1621 | 0.54 | 7.33 | 164 | 106 | 105/104 | 470 |
| z6496_w040 | unjudged | 4.27 | 6499–7293 | 6021×1981 | 0.40 | 4.17 | 176 | 113 | 114/111 | 270 |
| z7104_w040 | unjudged | 4.17 | 7105–7901 | 5341×1821 | 0.48 | 4.08 | 158 | 109 | 111/109 | 264 |
| z7104_w060 | unjudged | 5.99 | 7105–7903 | 7861×2041 | 0.42 | 5.87 | 123 | 114 | 110/113 | 381 |
| z7696_w040 | unjudged | 3.69 | 7698–8494 | 4581×1861 | 0.48 | 3.62 | 126 | 108 | 113/105 | 233 |
| z7696_w060 | unjudged | 5.56 | 7697–8494 | 7021×1961 | 0.45 | 5.45 | 142 | 116 | 115/114 | 355 |
| z8288_w060 | unjudged | 5.57 | 8289–9087 | 7361×1621 | 0.52 | 5.45 | 140 | 112 | 111/108 | 352 |
| z11296_w040 | unjudged | 3.71 | 11298–12093 | 4741×1481 | 0.59 | 3.63 | 94 | 98 | 97/89 | 226 |
| z11296_w060 | unjudged | 5.67 | 11297–12094 | 7461×1481 | 0.57 | 5.54 | 145 | 106 | 106/100 | 353 |
| z11904_w040 | unjudged | 3.69 | 11905–12700 | 5061×1240 | 0.65 | 3.59 | 113 | 100 | 99/91 | 219 |
| z11904_w060 | unjudged | 5.92 | 11906–12702 | 7781×1501 | 0.56 | 5.78 | 113 | 106 | 107/103 | 365 |
| z12496_w040 | unjudged | 3.66 | 12499–13295 | 5101×1221 | 0.65 | 3.57 | 83 | 99 | 96/87 | 212 |
| z12496_w060 | unjudged | 5.90 | 12498–13296 | 7861×1601 | 0.52 | 5.77 | 92 | 104 | 103/102 | 360 |
| z13088_w040 | unjudged | 3.45 | 13095–13885 | 4721×1141 | 0.71 | 3.36 | 98 | 93 | 94/88 | 197 |
| z13088_w060 | unjudged | 5.68 | 13091–13886 | 7461×1461 | 0.58 | 5.55 | 80 | 106 | 97/97 | 339 |
| z13696_w040 | unjudged | 3.69 | 13698–14493 | 4721×1240 | 0.70 | 3.60 | 74 | 96 | 93/88 | 217 |
| z13696_w060 | unjudged | 5.78 | 13696–14494 | 7221×1560 | 0.57 | 5.66 | 91 | 106 | 98/98 | 350 |
| z14304_w040 | unjudged | 4.10 | 14307–15101 | 5201×1421 | 0.62 | 4.02 | 112 | 100 | 98/93 | 246 |
| z14304_w060 | unjudged | 5.98 | 14306–15101 | 7601×1561 | 0.56 | 5.85 | 97 | 105 | 102/101 | 365 |
| z14896_w040 | unjudged | 3.83 | 14900–15695 | 4961×1281 | 0.67 | 3.74 | 101 | 97 | 96/93 | 228 |
| z14896_w060 | unjudged | 5.65 | 14898–15695 | 7121×1541 | 0.57 | 5.52 | 116 | 101 | 97/94 | 342 |

Totals: 32 meshes, 131.83 cm² indexed, 128.83 cm² rendered (the 2.3% gap is edge cells and holes: no render came back
empty), 267 Mpx of canvas per window of which 147 Mpx on-mesh, 58 min of render time, 8.24 GB of tars. The grey levels
on and off the sheet are alike (74–116 vs 67–115): the off-sheet windows sit on neighbouring wraps, as on 0846A, so the
null is "another sheet at a random depth", not air.

Control: `ctl_w016` = the 9 µm check's own render of the official 9.362 µm mesh of PHerc0139 segment
`20250108000004-w029` (pherc0139-w016) from `PHerc0139/volumes/20250728140407-9.362um-1.2m-113keV-masked.zarr`,
same flags, explicit crop 2884×1309 from (1510,4659) — copied byte-for-byte from box B `<work-dir>/n9/ctl/ctl_w016.zarr`
(379,718,647 bytes) and cut into the same three windows (on-mesh fraction 1.0, mean grey 86 on / 72–74 off). Its
labels on the render grid (`n9 results/ctl_labels_on_render.npz`: V validation 188,247 px, I ink 166,710 px, S
supervision 528,791 px, valid eroded 4 px) travel in the tar as `labels_on_render.npz`.

## 5. Dataset and kernel (task 4)

**Dataset** `<kaggle-user>/p0813-nineum-b0` (private; `p0813/upload_ds.sh`, token `~/.kaggle/token.env` =
<kaggle-user>, checked with `kaggle datasets list --mine`): 37 files, 7.7 GiB — 32 mesh tars (94–604 MB each),
`ctl_w016.tar` (188 MB), `villa_vesuvius_src.tar` (15 MB), `manifest.json`, `selection.json`,
`dataset-metadata.json` (`{"title": "p0813 nineum b0", "id": "<kaggle-user>/p0813-nineum-b0", "licenses": [{"name": "other"}]}`).
Created with `kaggle datasets create -p p0813/kds --dir-mode skip` (private by default). Kaggle auto-extracts the tars, so
the mount holds `<name>/<name>/on/...`; the kernel finds windows by globbing `**/on/surface-volume.zarr` and still
handles un-extracted tars.

**Kernel** `kag/n9_0813/` — `make_nb.py` writes `nb.ipynb` (cell 1 `%%writefile /kaggle/working/n9_0813.py`, verified
byte-identical to `p0813/n9_0813.py`; cell 2 `!python -u /kaggle/working/n9_0813.py`; cell 3 prints the summary) and
`kernel-metadata.json` (private, GPU, internet, dataset source `<kaggle-user>/p0813-nineum-b0`). What the script does:

1. Finds the dataset by its `manifest.json`, the villa `vesuvius` package shipped in the dataset
   (`villa_vesuvius_src.tar` = the 9 µm check's own source copy, box A `n9/src`, 453 files, md5
   e72f5d3704d363aa5520a99743a8c8e7) goes on `PYTHONPATH` — so the inference code is the one the control was validated
   with, and no GitHub clone or Python-3.14 venv is needed (Kaggle's own torch is used; missing modules are pip-installed
   `--no-deps` from an import-check loop, `zarr<4` / `numcodecs<0.17` if absent).
2. Downloads `hybrid_3d2d-seed43/step-060000.pth` and `hybrid_3d2d-seed42/step-010000.pth` from
   `huggingface.co/scrollprize/ink_9um` (public, no token) and checks the exact byte sizes (138,360,231 / 138,360,039).
3. Builds a folder of symlinks per checkpoint and per GPU (biggest windows first, dealt round-robin) and runs villa's
   folder mode once per checkpoint per GPU — one process per T4 with `CUDA_VISIBLE_DEVICES` (never DataParallel, which
   crashes villa's inference on 2 GPUs): `python -m vesuvius.ink_detection.inference.infer --folder <g> --checkpoint-path
   <ckpt> --layer-start 0 --layer-end 21 --direction both --overlap 0.5 --blend-mode hann --batch-size 8 --num-workers 2
   --no-compile --gpus 0`. On a 21-slice window this selects layers 2..18 forward and 18..2 reverse = render slices
   42..58, the 9 µm check's band. It scrapes `missing_keys`/`unexpected_keys` from villa's log (must be 0/0; flat
   inference loads with strict=False) and the selected layer indices into `results.json`.
4. Per window × checkpoint × direction: ink share (p > 0.5 and > 0.6) and mean p over the valid area eroded 4 px
   (the 9 µm check's convention; the raw-valid share is also stored for Plan-A comparability); per checkpoint:
   on = mean(fwd, rev), off = mean of offA/offB × fwd/rev, on/off with the Plan-A floor 0.005, max(on)/off, the
   stronger direction, fwd-vs-rev r; checkpoint agreement r; for the control: AUC in the held-out validation region
   (rank AUC, `scipy.stats.rankdata`, same function as `n9_control.py`) for every window and direction, share on
   labelled ink vs background, AUC in the trained area.
5. Writes `/kaggle/working/out/`: `results.json`, `summary.md` (control table; per-checkpoint mesh table sorted by
   on/off; checkpoint agreement), `maps/` (every probability map, uint8 zlib TIFF), `preview/` (¼-scale PNG of every
   on-sheet map), `log.txt`, villa logs. Bulky temporaries go to `/kaggle/tmp`.

Pass/fail to read first when it has run: control AUC ≥ 0.85 forward on-sheet for seed43 (the 9 µm check: 0.877 CPU
fp32; T4 fp16 will differ in the third decimal), ≈ 0.5 reverse and off-sheet, and 0 missing / 0 unexpected keys.
Then the 0813 tables: the 0846A pattern (blotchy, 15–48% on-sheet and nearly as much off-sheet, no rows) means
"stop, run 0211" per the shortlist's pre-registered day-1 gate; anything above the ordinary meshes' own on/off
spread on both checkpoints and both directions gets the by-eye side-by-side.

## 6. Dry run of the kernel code on box A CPU (23:11–23:17 AEST)

The unchanged `n9_0813.py` run on box A with `N9_INPUT=p0813/dry_in` (the real tars `ctl_w016.tar`, `z7104_w020.tar`,
`villa_vesuvius_src.tar` + `manifest.json`), `N9_DEVICE=cpu`, `N9_CKPT_DIR=<run-dir>/ckpts` (the checkpoints the
9 µm check used; byte sizes verified), `N9_WINDOWS=on`, `N9_CKPTS=seed43_step060000`, `N9_PIP=0`, 4 threads, nice 10.
Log: `p0813/logs/dry_run.log`; outputs `p0813/dry_work/out/` (summary copied to `plan_b_0813_files/dry_run_summary.md`).

- Input staging: found the manifest, extracted the three tars, found 2 segments (control present) and the villa source;
  `from vesuvius.ink_detection.inference import infer` OK with no pip install; torch 2.14.0+cpu.
- Inference: villa folder mode, one process, `exit 0`, 380 s for 2 windows × 2 directions (900 + ~1,050 patches per
  direction), `Loaded model weights ... (missing_keys=0 unexpected_keys=0)`, selected layer indices
  `[2..18]` forward and `[18..2]` reverse (= render slices 42..58).
- Control (held-out validation region, 187,915 px after the 4-px erosion): **seed43 forward AUC 0.877, reverse 0.525**;
  ink share in the region 18.9% / 7.2%; 57.2% of labelled-ink px vs 7.4% of background px above 0.5 (forward); AUC in
  the trained area 0.928 / 0.451; whole-crop share 12.9% / 5.9%. NINE_UM_CHECK section 4 Table 1 / section 9 (01:56):
  0.877, 0.53, 18.9%, 57% / 7.4%, 12.9% / 6%. Identical, so the cut windows, the symlinked folder mode, the label masks
  on the render grid and the metric code all line up with the validated run.
- z7104_w020 on-sheet: 8.9% forward / 13.6% reverse (mean p 0.34 / 0.36), fwd-vs-rev r 0.30; the maps
  (`plan_b_0813_files/dry_z7104_w020_seed43_{forward,reverse}_ds4.png`) are scattered blobs with no row structure.
  For scale: 0846A regions gave 15–48% on-sheet, known text 13% forward / 6% reverse. Off-sheet and seed42 were not
  run on CPU (they are the Kaggle job).
- Maps re-saved as zlib TIFFs (1.6–1.9 MB each for 2781×1621 / 2884×1309), ¼-scale PNG previews, `results.json`,
  `summary.md` written; total output 7 MB for 4 maps → the full run's `out/` will be about 0.5 GB.

## 7. Problems and notes

1. **Untested on Kaggle itself** (by design: no kernel push). What the dry run could not exercise: T4 fp16 inference
   (villa reads `mixed_precision` from the checkpoint; the 9 µm check and this dry run were CPU fp32, so expect
   third-decimal differences, not more), Kaggle's package set (the import-check loop pip-installs anything missing
   `--no-deps`; `zarr<4` / `numcodecs<0.17` if zarr is absent), and the auto-extracted mount layout (the kernel globs
   `**/on/surface-volume.zarr` at any depth, and the un-extracted path was exercised). First lines to check in the
   Kaggle log: "villa inference imports OK", "checkpoint ... ok", "missing_keys": 0, then the control table.
2. **GPU time is a range, 2–5 h** (section 1 item 7); the a0846 harness's 75 small windows took 18 min on 2×T4 but
   that included setup, so the T4 throughput is not pinned down. `N9_WINDOWS` / `N9_LIMIT` shorten a run.
3. **The dataset's `manifest.json` lacks the `render_size_wh` / `crop_xywh` fields** (the regex that reads them from the
   render logs missed the Unicode "×" in `crop [2781×1621 ...]`; fixed after the upload had started). The kernel only
   reads `verdict`, `area_cm2`, `z_range` from it; the corrected manifest is in `p0813/` and
   `evidence_0912/plan_b_0813_files/manifest.json`.
4. **Tiling is stated:** every mesh rendered alone with `--auto-crop` (a ~20 px black frame; villa normalises each tile
   including the frame), the "direct" tiling of the within-scroll null. Any future comparison must use the same.
5. **Depth order is per mesh.** On the control "forward" (as rendered with `--flip-normals`) is the official order;
   on 0846A half the meshes were stronger in reverse and z7104_w020 already is. The kernel reports both and the
   stronger one; do not read "forward" as "correct" on 0813.
6. **Off-sheet windows are other wraps** (grey levels alike on and off the sheet), the same null as on 0846A.
7. **Four extra renders** (w040/w060 at z14304 and z14896, whose regions were already cleared by an approved
   w100/w080): ~1 GB and 7 min; they add ordinary-mesh baseline, which the shortlist wants ≥ 8 of.
8. **`--layer-start 0 --layer-end 21`** is passed explicitly on the 21-slice windows (Plan A omitted it; villa selects
   the same centre 17 either way, confirmed in the log).
9. **Box A was shared** with the running 0846A survey the whole time (not touched; load peaked at 6.7 on 8 cores during
   dry run + two renders, renders nice'd). The box B box was only read (control copy, 380 MB).
10. **Self-caught:** a remote `nohup ... &` without `< /dev/null` kept the ssh call open until the render ended
    (lesson L69 in `tasks/lessons.md`). No data was affected.
11. **Upload bookkeeping:** `upload_ds.sh` keeps only the last three lines of the CLI output (`tail -3`), so the log is
    not a per-file record, and the status API answered 403 three times during ingest before `ready` (transient, seen
    before). The dataset was therefore verified afterwards by listing every file (`check_ds.sh`, 200 per page) and
    comparing names and byte sizes with the local copies: 34,073 of 34,073 files present, all sizes equal
    (`plan_b_0813_files/check_ds.json`). Only then were the 7.8 GB of uncut local copies deleted.

## 8. Files

- box A `<run-dir>/p0813/` (8.6 GB): `selection.json`, `manifest.json`, `select_and_check.py`, `render_one.sh`,
  `render_all.sh`, `cut3.py`, `inspect_render.py`, `manifest.py`, `n9_0813.py`, `make_nb.py`, `upload_ds.sh`,
  `push_kernel.sh`, `check_ds.sh`, `kds/` (the dataset exactly as uploaded, 7.7 GiB), `logs/` (every render and cut
  log, `dry_run.log`, `upload_ds.log`, `dataset_files_all.txt`, `check_ds.json`), `meshes-repo/` (the clone),
  `ctl/` (control render + labels), `villa_vesuvius_src/`, `dry_in/`, `dry_work/` (dry-run outputs and maps).
- box A `<run-dir>/kag/n9_0813/`: `nb.ipynb`, `kernel-metadata.json` (not pushed).
- `evidence_0912/plan_b_0813_files/`: every script above, `selection.json`, `manifest.json`, `check_ds.json`,
  `dry_run.log`, `dry_run_summary.md`, the hand-test pictures (`hand_z7104_w020_s50_crop800.png`, `..._ds4.png`) and
  the first two 0813 maps (`dry_z7104_w020_seed43_{forward,reverse}_ds4.png`).
