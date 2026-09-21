# PLAN B PREP — PHerc0211 renders + ink_9um kernel, ready to run (13 Sep 2026)

Private preparation only, the pre-registered fallback after PHerc0813 (PLAN_B_SHORTLIST_0912.md section 2 item 2 and
section 4 step 8: "if the 0813 maps show the 0846A pattern ... run the identical pipeline on 0211's approved meshes").
The 0813 run (kernel v2 + the box A score-only pass) showed that pattern overall: seed43 median on-sheet share 11.0 %
vs off-sheet 9.4 %, seed42 18.1 % vs 15.0 %, best on/off 1.98 — on-sheet only a little above off-sheet, both directions
alike. So this is 0211, prepared exactly the way 0813 was (evidence_0912/PLAN_B_0813_PREP.md), by an agent while Kaden
sleeps. Nothing public: no GitHub, no Discord; the Kaggle dataset is private; the kernel folder is private. Times are AEST
from `date` (box A's clock is UTC, +10 h). Started 02:31, selection 02:38, hand test 02:39–02:41, renders 02:44–03:06,
dry run 02:45–02:52, upload started 03:07. Work lives on box A inp0211/` (16 GB while the tars and
their uncut copies both exist; box A has 92 GB free, the survey chain and Plan C were not touched) and the scripts,
selection, manifest, pictures and dry-run summary are in `evidence_0912/plan_b_0211_files/`.

## 1. Short version

1. **Selected 30 of pscamillo's 90 PHerc0211 meshes, 131.1 cm²**: the 15 judged usable by eye (10 `aprova` + 5
   `parcial`, 53.5 cm²) plus 15 unjudged w040/w060 meshes at the same 11 z-windows (3.8–6.6 cm² each, so every region
   has a mesh over the 4 cm² rule; the two meshes judged `reprova` at those z, z4912_w080 and z11520_w040, are skipped).
   Five more unjudged w040/w060 (24.3 cm²) sit in regions already cleared by a usable mesh ≥ 4 cm² and were dropped to
   stay at ~130 cm² like 0813; they are listed in `selection.json` (`dropped_extras`) as an optional second batch.
2. **Every selected mesh sits inside the eligible volume `20250821151803` (9.362 µm, 113 keV, z 19416 × 7948 × 7948) in
   that volume's own voxel frame** — x/y/z.tif ranges checked against the live `.zarray`, `meta.json` bbox and area
   re-derived and matched to `index.csv`, grid scale 0.05. No mesh needs a transform. The catalogue holds no official
   segment for 0211 (0), a published umbilicus (`20250821151803-umbilicus-20260808112626.json`), surface-m7 predictions
   and lasagna; the only community surfaces are pscamillo's (flummoxjr published none for 0211).
3. **Rendered all 30 with exactly the 9 µm check recipe** (101 slices 1 voxel apart centred on the mesh, `--flip-normals`,
   `--auto-crop`, scale 1, cache 4 GB, timeout 120) and cut the three 21-slice windows the same way as 0813 and Plan A
   (`on` = slices [40,61), `offA` = [0,21), `offB` = [80,101)). Hand test first (z10320_w020, L44): fibre weave visible,
   76 % of the canvas on-mesh, flat depth profile (packed sheets, as on 0813 and 0846A). Then all 30 in 22 min wall (two
   nice'd workers, 44–143 s each, 0 failures): 127.2 of 131.1 cm² came back on-mesh (97.0 %), canvases from 2161×1181 to
   12181×1441 px, on-mesh fraction 0.54–0.85 of each canvas; 30 tars, 8.45 GB.
4. **The PHerc0139 w016 control is the same tar as in the 0813 dataset** (`ctl_w016.tar`, md5 87aed0c6…: the 9 µm
   check's validated render cut into the same three windows, with its held-out labels on the render grid), and the villa
   inference source is the same tar (`villa_vesuvius_src.tar`, md5 e72f5d37…).
5. **Private Kaggle dataset `kadenbrodie/p0211-nineum-b0`** (7.9 GiB, 35 files: one tar per mesh, the control tar, the villa inference source, manifest + selection). Uploaded
   03:07–03:14, status `ready` at 03:15:42 AEST, dataset id 11997755, `isPrivate: true` (metadata API). Kaggle extracted every
   tar on ingest, so the mount holds `<name>/<name>/on|offA|offB/surface-volume.zarr/...` — the layout the kernel globs for.
   Verified file by file (`check_ds.sh`, 169 pages of 200): **33,620 files, 8,442,241,349 bytes, every name and byte size
   equal to the local copy, 0 missing / 0 mismatched / 0 extra**; 34 top-level entries = 30 meshes + `ctl_w016` +
   `villa_vesuvius_src` + the two JSONs. Only then were the 8 GB of uncut copies deleted from box A.
6. **Kernel folder leverkag/n9_0211/`** (`nb.ipynb` + `kernel-metadata.json`, private, id
   `kadenbrodie/vesuvius-n9-0211`, GPU, internet, dataset source `kadenbrodie/p0211-nineum-b0`): `n9_0211.py` = the 0813
   kernel's v3 (`--no-deps` imagecodecs) with only paths/ids/names changed plus the L72 check (below). Its exact code was
   dry-run on box A CPU (seed43, on-sheet window) on the control + one 0211 mesh: **control AUC 0.877 forward / 0.525
   reverse, 18.9 % ink share in the validation region, 57.2 % of labelled-ink px vs 7.4 % of background px called ink,
   trained-area AUC 0.928 / 0.451, whole-crop share 12.9 % / 5.9 % — the 0813 dry run and the 9 µm check to the digit**,
   0 missing / 0 unexpected checkpoint keys, layer indices 2..18 and 18..2. First 0211 mesh (z10320_w020): 5.0 % forward /
   13.2 % reverse on the sheet, scattered blobs, no rows (one mesh, one checkpoint, no off-sheet windows yet: a smoke
   test, not a verdict; 0813's first mesh was 8.9 / 13.6).
7. **Push** (one command, from box A): `ssh box A 'p0211/push_kernel.sh'` (refuses unless the metadata says
   private and the id is right; then `kaggle kernels status kadenbrodie/vesuvius-n9-0211` and `kaggle kernels output
   kadenbrodie/vesuvius-n9-0211 -p kag_out/n9_0211`). Rule: only after `chain_0846a2_rest.log` shows CHAIN_DONE/CHAIN_ABORT
   and no s0846a2 kernel is running on kadenbrodie (one status check, no poll loop). CHAIN_DONE appeared at 17:13Z (03:13 AEST)
   with b10 pushed that same minute; both survey kernels completed by 03:36 (outputs fetched by the main session), the one
   status check at 03:37 said COMPLETE for both, and **the kernel was pushed at 03:37 AEST (v1, RUNNING)** — section 7. Expected GPU time on 2×T4 ~1.5–2 h
   (0813 v2: 1 h 51 min for 32 meshes; 0211 has 30 meshes and 18 % less canvas).

## 2. Selection (task 1) — `p0211/selection.json`, `select_and_check.py`

Source: `github.com/pscamillo/vesuvius-eligible-meshes` at `0c966f8` (the clone already on box A from the 0813 prep, copied
read-only into `p0211/meshes-repo/` — index.csv, docs, and the 90 PHerc0211 mesh folders). `data/index.csv` has 90
PHerc0211 rows (18 z-windows z3712–z14512 × w020..w100), 25 with a `gate_verdict`: 10 `aprova`, 5 `parcial`, 10
`reprova`, 65 unjudged. Same criterion as for 0813 (`docs/QUALITY.md`): weave = crossing bands 70–150 px wide at 9 µm;
approve = coherent weave over most of the panel; partial = at least one continuous patch of several cm²; reject =
melting everywhere. Meshes are one winding per 800-voxel z-window (≈2 cm² at w020, 4 at w040, 6 at w060), sit within
~5 voxels of the sheet, grid scale 0.05.

Rule applied (shortlist section 4 step 1, as for 0813): every mesh judged usable + the unjudged w040 and w060 at the
same z, skipping any judged `reprova`; then, to stay at ~130 cm², the unjudged w040/w060 in regions ALREADY cleared by
a usable mesh ≥ 4 cm² were dropped (0813 kept its four such extras; here they would have made 35 meshes / 155 cm²).

| z-window | usable by eye | added unjudged | region area selected |
|---|---|---|---|
| z3712 | w020 aprova 1.98 | w040 3.98, w060 5.86 | 11.8 cm² |
| z4912 | w020 aprova 2.01 | w040 4.10, w060 6.30 (w080 is reprova) | 12.4 |
| z5520 | w020 aprova 1.87 | w040 3.99, w060 6.26 | 12.1 |
| z6112 | w020 aprova 1.95, **w080 parcial 8.72** | none (w040 4.10, w060 6.42 dropped: region cleared by w080) | 10.7 |
| z6720 | w020 aprova 1.96, **w060 parcial 6.43** | none (w040 4.17 dropped: region cleared by w060; w100 is reprova) | 8.4 |
| z7920 | w020 aprova 1.85 | w040 3.90, w060 6.23 | 12.0 |
| z9120 | w020 aprova 2.09 | w040 4.16, w060 6.36 (w100 is reprova) | 12.6 |
| z10320 | w020 aprova 2.25 | w040 4.58, w060 6.57 | 13.4 |
| z11520 | w020 aprova 1.97 | w060 5.59 (w040 is reprova) | 7.6 |
| z13920 | w020 aprova 1.64 | w040 3.75, w060 5.92 (w080 is reprova) | 11.3 |
| z14512 | w020 parcial 1.70, **w080 parcial 7.75, w100 parcial 9.36** | none (w040 3.69, w060 5.93 dropped: region cleared by w080/w100) | 18.8 |

Total 30 meshes, 131.08 cm² (15 usable = 53.53 cm²; 15 unjudged = 77.55 cm²). Not taken: the 10 `reprova`, the 50
unjudged meshes at z-windows with no usable verdict (z4320, z7312, z9712, z10912, z12112, z12720, z13312) or at
w080/w100, and the 5 dropped extras (`dropped_extras` in `selection.json`: z6112_w040/w060, z6720_w040,
z14512_w040/w060, 24.31 cm²). The 15 unjudged w040/w060 double as the within-scroll baseline the shortlist asks for
(step 6b: ≥ 8 ordinary meshes through the same pipeline).

## 3. Frame and bounds check (task 1) — `p0211/select_and_check.py`, `logs/select_and_check.log`

- Volume: the only PHerc0211 volume in the bucket (catalogue `metadata.json`, gzip, read anonymously 02:33: one volume,
  `segments: {}`), `https://vesuvius-challenge-open-data.s3.amazonaws.com/PHerc0211/volumes/20250821151803-9.362um-1.2m-113keV-masked.zarr/`
  (level 0: shape z 19416 × y 7948 × x 7948, uint8, 128³ chunks, uncompressed; levels 1–5 present; scan
  `20250720140115`, ESRF bm18, 113 keV, 9.362 µm, same July-2025 campaign as 0813 and the calibrator 0139). No
  `meta.json` in the zarr (`vc_render_tifxyz` prints "Voxel size: 1.0 (no metadata)" as for 0813, 0846A and 0139).
- For each selected mesh, x/y/z.tif were read (float32, −1 = no point; the three valid masks agree), min/max of the
  valid points compared with the volume shape: **all 30 inside** (x 749–6300, y 1448–5269, z 3713–15311). The
  `meta.json` bbox matches the tif ranges to < 1 voxel (30/30), `area_vx2 × (9.362 µm)²` matches `index.csv` to
  < 0.02 cm² (30/30), scale is 0.05 (30/30), and each mesh's z range lies inside its named window [z, z+800) (30/30).
  `fit_config` in `meta.json` names no volume; the frame is established by the README ("full-resolution voxels of the
  volume", same 0.05 grid scale as the team's PHerc0139 meshes) and confirmed by the render: the hand-test render shows
  papyrus weave, not noise or black, at the mesh's own coordinates with no affine.
- **No mesh needs a transform.**

## 4. Renders (task 2) — `p0211/render_one.sh`, `render_all.sh`, `cut3.py`, `manifest.json`

Recipe = the 0813 scripts with only the volume URL / folder changed (derived by `make_0211_files.py`, which asserts every
replacement count and that no 0813 path survives):
`vc_render_tifxyz --volume URL --remote-url URL -s <mesh> --auto-crop --scale 1 -g 0 --num-slices 101 --slice-step 1
--flip-normals --zarr-output <out>.zarr --pyramid 0 --timeout 120 --cache-gb 4` (villa build on box A, the same binary
as the 9 µm check, the 0813 prep and the 0846A survey). Each mesh rendered alone in its own process (fresh 4 GB cache),
the "direct" tiling of the within-scroll null (NINE_UM_CHECK section 10.1 point 7). Two nice'd workers, one render at
a time each; the 0846A survey chain (one render at a time) and Plan C's poller kept running on box A untouched (load
peaked ~3 on 8 cores).

Hand test (L44), z10320_w020, 02:39–02:41: `auto-crop: [3001×1101 from (19,19)]`, 94 s, 244 MB, shape
(101, 1101, 3001); slice 50 on-mesh fraction 0.757, mean grey 109.5 ± 39.0; depth profile flat (mean grey 106.3 at
slice 0 → 109.5 at 50 → 110.9 at 100, 106–115 throughout: packed sheets, the off-sheet windows land on neighbouring
wraps, as on 0813 and 0846A). Picture: `plan_b_0211_files/hand_z10320_w020_s50_crop800.png` (800 px full-res crop at
the mesh centre: clear crossing fibre bands, dark melt patches and cracks — a little more melt than 0813's hand test,
as the separability rank 9 predicts) and `..._s{10,50,90}_ds4.png`.

Cut (`cut3.py` = the 0813 script with the attrs text changed): `<name>/on|offA|offB/surface-volume.zarr` (zarr v2, array
"0", (21, H, W) uint8, chunks (21,128,128), zstd), `valid.npy` (= on-window max > 0), `cut_info.json`; every write read
back. One tar per mesh in `p0211/kds/`.

Per mesh (from `manifest.json`; canvas = auto-crop render size; on-mesh = fraction of the canvas the mesh covers; grey =
mean of the centre slice on the mesh, then of the two off-sheet windows; tar = the three 21-slice windows, MB):

| mesh | verdict | cm² (index) | z range | canvas px | on-mesh | cm² rendered | render s | grey on | grey offA/offB | tar MB |
|---|---|---|---|---|---|---|---|---|---|---|
| z3712_w020 | aprova | 1.98 | 3716–4506 | 2721×1161 | 0.69 | 1.92 | 90 | 121 | 122/120 | 128 |
| z4912_w020 | aprova | 2.01 | 4913–5707 | 2981×1081 | 0.69 | 1.96 | 77 | 109 | 109/103 | 128 |
| z5520_w020 | aprova | 1.87 | 5523–6317 | 2841×861 | 0.85 | 1.81 | 44 | 107 | 104/101 | 117 |
| z6112_w020 | aprova | 1.95 | 6119–6910 | 2921×921 | 0.80 | 1.89 | 54 | 104 | 106/100 | 120 |
| z6112_w080 | parcial | 8.72 | 6114–6911 | 12141×1341 | 0.60 | 8.51 | 143 | 121 | 118/120 | 563 |
| z6720_w020 | aprova | 1.96 | 6721–7518 | 3021×881 | 0.81 | 1.90 | 50 | 110 | 110/108 | 121 |
| z6720_w060 | parcial | 6.43 | 6722–7519 | 9321×1121 | 0.68 | 6.27 | 122 | 118 | 118/115 | 412 |
| z7920_w020 | aprova | 1.85 | 7922–8717 | 2861×841 | 0.85 | 1.79 | 80 | 108 | 103/101 | 112 |
| z9120_w020 | aprova | 2.09 | 9120–9919 | 2981×1041 | 0.75 | 2.03 | 98 | 106 | 103/103 | 130 |
| z10320_w020 | aprova | 2.25 | 10322–11118 | 3001×1101 | 0.76 | 2.19 | 94 | 110 | 110/113 | 142 |
| z11520_w020 | aprova | 1.97 | 11521–12318 | 2601×1081 | 0.78 | 1.92 | 71 | 117 | 116/111 | 123 |
| z13920_w020 | aprova | 1.64 | 13924–14715 | 2161×1181 | 0.71 | 1.60 | 77 | 104 | 114/98 | 101 |
| z14512_w020 | parcial | 1.70 | 14515–15308 | 2301×1121 | 0.73 | 1.66 | 63 | 109 | 108/100 | 107 |
| z14512_w080 | parcial | 7.75 | 14514–15311 | 9901×1561 | 0.56 | 7.59 | 143 | 115 | 115/114 | 497 |
| z14512_w100 | parcial | 9.36 | 14513–15311 | 12181×1441 | 0.55 | 8.43 | 138 | 111 | 108/111 | 540 |
| z3712_w040 | unjudged | 3.98 | 3714–4510 | 5101×1341 | 0.65 | 3.89 | 94 | 114 | 114/114 | 256 |
| z3712_w060 | unjudged | 5.86 | 3713–4511 | 7361×1381 | 0.64 | 5.74 | 112 | 115 | 114/113 | 376 |
| z4912_w040 | unjudged | 4.10 | 4913–5710 | 5961×1141 | 0.67 | 4.00 | 92 | 113 | 114/109 | 262 |
| z4912_w060 | unjudged | 6.30 | 4914–5711 | 8801×1101 | 0.72 | 6.14 | 99 | 115 | 114/112 | 399 |
| z5520_w040 | unjudged | 3.99 | 5522–6316 | 5921×1081 | 0.69 | 3.88 | 82 | 116 | 116/110 | 252 |
| z5520_w060 | unjudged | 6.26 | 5521–6318 | 8861×1461 | 0.54 | 6.10 | 95 | 120 | 120/118 | 403 |
| z7920_w040 | unjudged | 3.90 | 7924–8718 | 5781×1041 | 0.72 | 3.80 | 95 | 113 | 110/106 | 242 |
| z7920_w060 | unjudged | 6.23 | 7922–8718 | 8901×1161 | 0.67 | 6.08 | 116 | 116 | 114/112 | 398 |
| z9120_w040 | unjudged | 4.16 | 9122–9919 | 5921×1161 | 0.67 | 4.06 | 96 | 110 | 108/107 | 260 |
| z9120_w060 | unjudged | 6.36 | 9121–9919 | 9021×1161 | 0.68 | 6.21 | 116 | 117 | 116/116 | 408 |
| z10320_w040 | unjudged | 4.58 | 10321–11119 | 6041×1121 | 0.75 | 4.47 | 87 | 114 | 110/110 | 285 |
| z10320_w060 | unjudged | 6.57 | 10321–11118 | 8841×1161 | 0.71 | 6.41 | 113 | 117 | 116/116 | 418 |
| z11520_w060 | unjudged | 5.59 | 11521–12319 | 7441×1181 | 0.71 | 5.46 | 98 | 115 | 115/111 | 355 |
| z13920_w040 | unjudged | 3.75 | 13922–14719 | 5021×1221 | 0.68 | 3.66 | 109 | 110 | 108/108 | 235 |
| z13920_w060 | unjudged | 5.92 | 13921–14718 | 7761×1361 | 0.63 | 5.79 | 133 | 110 | 109/106 | 375 |

Totals: 30 meshes, 131.08 cm² indexed, 127.15 cm² rendered (the 3.0 % gap is edge cells and holes: no render came back
empty; the lowest on-mesh fraction is 0.54, z5520_w060), 220 Mpx of canvas per window of which 145 Mpx on-mesh, 48 min
of render time, 8.45 GB of tars. The grey levels on and off the sheet are alike (104–121 vs 98–122): the off-sheet
windows sit on neighbouring wraps, as on 0813 and 0846A, so the null is "another sheet at a random depth", not air.

Control: `ctl_w016` = the 0813 dataset's control tar, byte-identical (md5 87aed0c69d9540304d2cba81285979da): the 9 µm
check's own render of the official 9.362 µm mesh of PHerc0139 segment `20250108000004-w029` (pherc0139-w016) from
`PHerc0139/volumes/20250728140407-9.362um-1.2m-113keV-masked.zarr`, same flags, explicit crop 2884×1309 from (1510,4659),
cut into the same three windows (on-mesh fraction 1.0, mean grey 86 on), with its held-out labels on the render grid
(`labels_on_render.npz`: V validation 188,247 px, I ink 166,710 px, S supervision 528,791 px, valid eroded 4 px).

## 5. Dataset and kernel (task 3)

**Dataset** `kadenbrodie/p0211-nineum-b0` (private; `p0211/upload_ds.sh`, token `~/.kaggle/token.env` = kadenbrodie, the
way 0813's upload ran): 35 files — 30 mesh tars (101–563 MB each), `ctl_w016.tar` (188 MB), `villa_vesuvius_src.tar`
(15 MB), `manifest.json`, `selection.json`, `dataset-metadata.json`
(`{"title": "p0211 nineum b0", "id": "kadenbrodie/p0211-nineum-b0", "licenses": [{"name": "other"}]}`).
Created with `kaggle datasets create -p p0211/kds --dir-mode skip` (private by default). Uploaded 03:07–03:14 AEST (`logs/upload_ds.log`; the status API answered 403 three times
during ingest, as with 0813, then `ready` at 03:15:42), id 11997755, `isPrivate: true`. Kaggle auto-extracts the tars,
so the mount holds `<name>/<name>/on/...`; the kernel finds windows by globbing `**/on/surface-volume.zarr` and still handles
un-extracted tars. Verified by listing every file (`check_ds.sh` → `logs/check_ds.json`, copied to `plan_b_0211_files/`):
33,620 of 33,620 files present, all byte sizes equal (8,442,241,349 bytes), 0 extra, 34 top-level entries.

**Kernel** `kag/n9_0211/` — `make_nb.py` writes `nb.ipynb` (cell 1 `%%writefile /kaggle/working/n9_0211.py`, verified
byte-identical to `p0211/n9_0211.py`; cell 2 `!python -u /kaggle/working/n9_0211.py`; cell 3 prints the summary) and
`kernel-metadata.json` (private, GPU, internet, dataset source `kadenbrodie/p0211-nineum-b0`). `n9_0211.py` is
`n9_0813.py` v3 (the `--no-deps` imagecodecs version that the 0813 v2 failure led to) with exactly these edits
(`make_0211_files.py`, diff-checked): the docstring/`SCRIPT_VERSION`/summary headings say 0211, and
**`check_report_imports(tag)` — one subprocess line that imports `numpy, scipy.ndimage, scipy.stats, tifffile,
PIL.Image` and prints their versions — is called twice: in the first second of `main` (right after the imagecodecs
step) and again right before `run_inference` (after `setup_env`'s possible `--no-deps` installs); either failure
raises before any GPU work (L72)**. Everything else is unchanged: it finds the dataset by its `manifest.json`, puts the
shipped villa `vesuvius` package on `PYTHONPATH`, downloads and byte-checks `hybrid_3d2d-seed43/step-060000.pth` and
`hybrid_3d2d-seed42/step-010000.pth` from `huggingface.co/scrollprize/ink_9um`, runs villa's folder mode once per
checkpoint per GPU (`--layer-start 0 --layer-end 21 --direction both --overlap 0.5 --blend-mode hann --batch-size 8
--num-workers 2 --no-compile`), scrapes missing/unexpected keys and the selected layer indices, and writes
`results.json` + `summary.md` (ink share > 0.5 per window/checkpoint/direction on the 4-px-eroded valid area, on/off with
the 0.005 floor, control AUC in the held-out region) + `maps/` + `preview/`.

Pass/fail to read first when it has run: control AUC ≥ 0.85 forward on-sheet for seed43 (0.877 CPU fp32 here; T4 fp16
differs in the third decimal), ≈ 0.5 reverse and off-sheet, 0 missing / 0 unexpected keys, and both
"report-stage imports OK" lines in the first minute of the log. Then the 0211 tables: the 0846A/0813 pattern (on-sheet
only a little above off-sheet, both directions alike, blobs, no rows) means the fallback is exhausted too and the
decision goes back to Kaden (0358's eight flummoxjr patches are the next name on the shortlist); anything above the
ordinary meshes' own on/off spread on both checkpoints and both directions gets the by-eye side-by-side.

## 6. Dry run of the kernel code on box A CPU (02:45–02:52)

The unchanged `n9_0211.py` run on box A with `N9_INPUT=p0211/dry_in` (the real tars `ctl_w016.tar`, `z10320_w020.tar`,
`villa_vesuvius_src.tar` + `manifest.json`), `N9_DEVICE=cpu`, `N9_CKPT_DIR=ckpts` (the checkpoints the
9 µm check used; byte size verified), `N9_WINDOWS=on`, `N9_CKPTS=seed43_step060000`, `N9_PIP=0`, 4 threads, nice 10, from
the `p0211/` folder (L70). Launcher `dry_run.sh`; log `p0211/logs/dry_run.log`; outputs `p0211/dry_work/out/` (summary
copied to `plan_b_0211_files/dry_run_summary.md`).

- Import check: `report-stage imports OK (first minute, after imagecodecs): numpy 2.5.3 scipy 1.18.1 tifffile 2026.8.23`
  at 1 s, and again at 4 s "before the GPU stage, after setup_env".
- Input staging: found the manifest, extracted the three tars, found 2 segments (control present) and the villa source;
  `from vesuvius.ink_detection.inference import infer` OK with no pip install; torch 2.14.0+cpu.
- Inference: villa folder mode, one process, `exit 0`, 398 s for 2 windows × 2 directions (900 patches on the control),
  `missing_keys=0 unexpected_keys=0`, selected layer indices `[2..18]` forward and `[18..2]` reverse (= render slices
  42..58).
- Control (held-out validation region, 187,915 px after the 4-px erosion): **seed43 forward AUC 0.877, reverse 0.525**;
  ink share in the region 18.9 % / 7.2 %; 57.2 % of labelled-ink px vs 7.4 % of background px above 0.5 (forward); AUC in
  the trained area 0.928 / 0.451; whole-crop share 12.9 % / 5.9 %. PLAN_B_0813_PREP section 6: 0.877 / 0.525 / 18.9 % /
  7.2 % / 57.2 % / 7.4 % / 0.928 / 0.451 / 12.9 % / 5.9 %. Identical, so the copied control, the cut windows, the symlinked
  folder mode, the label masks and the metric code all line up with the validated run.
- z10320_w020 on-sheet: 5.0 % forward / 13.2 % reverse (mean p 0.31 / 0.37), fwd-vs-rev r 0.14; the maps
  (`plan_b_0211_files/dry_z10320_w020_seed43_{forward,reverse}_ds4.png`) are scattered blobs with no row structure.
  For scale: 0813's first mesh gave 8.9 / 13.6 %, 0846A regions 15–48 %, known text 13 % forward / 6 % reverse.
  Off-sheet and seed42 were not run on CPU (they are the Kaggle job).

## 7. Push (task 4)

Rule (task 4): the kadenbrodie account's two GPU sessions run the 0846A survey kernels untilchain_0846a2_rest.log` shows `CHAIN_DONE` or `CHAIN_ABORT`; push only after that line exists AND one
status check shows no `vesuvius-s0846a2-b*` kernel running. State at 03:20 AEST: `CHAIN_DONE 17:13 | SURVEY0846A2_REST_DONE
17:13:52` is in the log (b9 pushed 16:46:03Z, b10 pushed 17:13:52Z; batches b7→b8→b9→b10 took 31, 34, 28 min each), so b10
is expected to finish ~17:45Z (03:45 AEST). Push command, kept ready:

    ssh box A 'p0211/push_kernel.sh'
    ssh box A 'cd && ./kagenv/bin/kaggle kernels status kadenbrodie/vesuvius-n9-0211'
    ssh box A 'cd && ./venv/bin/python kout2.py kadenbrodie vesuvius-n9-0211 ~/.kaggle/token.env kag_out/n9_0211 200 .log,.json,.png'

Outcome: b9's and b10's outputs were fetched by the main session at 17:31Z and 17:36Z (so both had completed); the single
status check at 17:37:13Z answered `KernelWorkerStatus.COMPLETE` for both, and `push_kernel.sh` ran in the same call:
**`kadenbrodie/vesuvius-n9-0211` version 1 pushed at 03:37 AEST, private, 2×T4, status `RUNNING` 20 s later**
(`p0211/logs/push.log`). No new poller was started (the kadenbrodie account already has the main session's watcher, L49);
fetch when complete with the `kout2.py` line above, then read `summary.md` (both "report-stage imports OK" lines, control
AUC, then the 0211 tables per section 5's pass/fail).

## 8. Problems and notes

1. **Running on Kaggle since 03:37 AEST, not yet read**; what the dry run could not exercise is the same list as for 0813 (T4
   fp16, Kaggle's package set, the auto-extracted mount layout). The 0813 v1 and v2 failures are both covered: LZW TIFF
   layers (imagecodecs installed `--no-deps` up front) and the numpy clash (the import check now fails in the first
   minute instead of after two GPU hours). First lines to check in the Kaggle log: both "report-stage imports OK" lines,
   "villa inference imports OK", "checkpoint ... ok", "missing_keys": 0, then the control table.
2. **GPU time**: 0813 v2 took 1 h 51 min on 2×T4 for 32 meshes / 99 windows per checkpoint (55 min per checkpoint);
   0211 has 30 meshes / 93 windows and 18 % less canvas (220 vs 267 Mpx per window), so expect ~1.5–2 h. `N9_WINDOWS` /
   `N9_LIMIT` shorten a run.
3. **Selection is 30 meshes, not the rule's 35**: the five cleared-region extras were dropped to keep ~130 cm² as asked
   (`selection.json` `dropped_extras`); rendering them later is ~8 min and ~1.5 GB if the baseline needs more ordinary
   meshes than the 15 included.
4. **Tiling is stated:** every mesh rendered alone with `--auto-crop` (a ~20 px black frame; villa normalises each tile
   including the frame), the "direct" tiling of the within-scroll null. Any future comparison must use the same.
5. **Depth order is per mesh.** On the control "forward" (as rendered with `--flip-normals`) is the official order; on
   0813 and 0846A half the meshes were stronger in reverse and z10320_w020 already is. The kernel reports both and the
   stronger one; do not read "forward" as "correct" on 0211.
6. **Off-sheet windows are other wraps** (grey levels alike on and off the sheet), the same null as on 0813 and 0846A.
7. **More melt than 0813**: pscamillo's usable rate at w020 is 77 % on 0211 vs 73 % on 0813, but the separability rank
   is 9 vs 3; the hand-test crop shows more dark melt patches than 0813's. The on-mesh fractions (0.54–0.85) are still
   above 0813's (0.40–0.79) because the 0211 meshes are less wavy.
8. **The manifest carries `render_size_wh` / `crop_xywh` for every mesh** (the 0813 regex fix for the Unicode "×" was in
   the copied script), so the dataset's manifest is complete this time.
9. **Box A was shared** with the 0846A rest-survey chain (rendering/pushing b9 and b10) and Plan C's poller the whole
   time; neither was touched, load peaked ~3 on 8 cores, disk never below 91 GB free.
10. **Self-caught (L69 again):** the two `render_all.sh` launches with `setsid nohup ... &` still held their ssh calls
    open until the workers finished (the jobs ran fine); the later launches used `ssh -f` and returned at once.
11. **Upload bookkeeping** as for 0813: `upload_ds.sh` keeps only the last lines of the CLI output and the status API
    answered 403 three times during ingest before `ready`; the file-by-file listing is the verification, not the status.

## 9. Files

- leverp0211/`: `selection.json`, `manifest.json`, `select_and_check.py`, `setup_p0211.sh`,
  `render_one.sh`, `render_all.sh`, `cut3.py`, `inspect_render.py`, `manifest.py`, `n9_0211.py`, `make_nb.py`, `dry_run.sh`,
  `upload_ds.sh`, `push_kernel.sh`, `check_ds.sh`, `kds/` (the dataset exactly as uploaded), `seg/` (the uncut copies,
  delete once the dataset check has passed), `logs/` (every render and cut log, `select_and_check.log`, `dry_run.log`,
  `upload_ds.log`, `dataset_files_all.txt`, `check_ds.json`, `push.log`), `meshes-repo/` (index + the 90 PHerc0211 meshes + docs,
  `SOURCE_COMMIT.txt`), `villa_vesuvius_src/`, `dry_in/`, `dry_work/` (dry-run outputs and maps).
- leverkag/n9_0211/`: `nb.ipynb`, `kernel-metadata.json`.
- `evidence_0912/plan_b_0211_files/`: every script above plus `make_0211_files.py` (the derivation) and `tables_0211.py`
  (the tables in this file from the JSONs), `selection.json`, `manifest.json`, `select_and_check.log`, `render_w0.log`,
  `render_w1.log`, `inspect_z10320_w020.log`, `cut_z10320_w020.log`, `dry_run.log`, `dry_run_summary.md`, `check_ds.json`, `upload_ds.log`, `push.log`,
  the hand-test pictures (`hand_z10320_w020_s50_crop800.png`, `..._s{10,50,90}_ds4.png`) and the first two 0211 maps
  (`dry_z10320_w020_seed43_{forward,reverse}_ds4.png`).
