# run_canon.py: the challenge's 2 µm ink model on our own layers (Kaggle)

`run_canon.py` runs `scrollprize/ink_canonical_2um` (ResNet3D-152 + 3D decoder, recipe
`new_canon_autoresearch_recipe`) on a local folder of numbered TIF layers. It follows the
official `ink-detection/optimized_inference/` code path (ScrollPrize/villa `origin/main`
@ `777cb16`, 2026-09-10) with the S3/boto3/webKnossos/zarr/profiling parts removed.
It writes a PNG and a 16-bit TIF to `/kaggle/working` and always ends by printing `CANON_DONE`.

## 1. Run it on Kaggle

1. Attach the layers dataset (`00.tif` … `108.tif`). Settings: **Accelerator = GPU T4 x2**, **Internet = on**.
2. In a cell: `!python /kaggle/input/<code-dataset>/run_canon.py`. You can also paste the file into a cell.
   - Layers folder: set `CANON_LAYERS_DIR=/kaggle/input/<slug>/...`. If you leave it unset, the script picks the folder under `/kaggle/input` that has the most numbered TIFs, and prints its choice.
   - Everything else is already set to the official recipe: layers `[1, 63)`, tile 256, stride 128. The optional knobs are listed at the top of the script.
3. What it does, in order:
   - checks or installs dependencies;
   - checks torch against the T4;
   - reads layers 01–62 into RAM (about 0.56 GB for 3000×3000);
   - downloads the weights (1.55 GB, into `/tmp/canon_models`, not into `/kaggle/working`) and checks their sha256;
   - runs 529 tiles for a 3000×3000 patch;
   - writes the outputs.

**Estimated time on one T4:** a few minutes, not measured.
- The model costs 1.72 TFLOP per 256-px tile (counted with torch's FLOP counter).
- 529 tiles ≈ 0.9 PFLOP, which is about 1–3 min at a realistic 5–15 TFLOPS in fp16.
- Even 10× slower is still under the 1 h budget.

## 2. Outputs and orientation

| file | what it is |
|---|---|
| `canon_pred_asinput.png` | uint8. Same values as the official output (`processing.py:692-695`). Same pixel grid as **your TIFs** (vc_render_tifxyz orientation = **mirrored** left-right vs the challenge). |
| `canon_pred_asinput_16bit.tif` | The same prediction as uint16 (`rint(p·65535)`) |
| `canon_pred_readable.png` | `asinput[:, ::-1]`: flipped back to the **challenge orientation**, so text reads the right way |
| `canon_pred_readable_16bit.tif` | uint16 version of the readable image |
| `canon_run_info.json` | settings, versions, GPU, checkpoint sha256, tile counts, timings, stats |

- By default the network sees your TIFs as-is (mirrored).
- `CANON_FLIP_INPUT=1` mirrors the layers *before* inference, so the network sees exactly the challenge orientation. The file names keep their meaning either way.
- Why the two are not bit-identical:
  - The tile grid starts at the left edge.
  - The model is not exactly mirror-symmetric. Training used `HorizontalFlip` (`deprecated/ink-detection/train_resnet3d_3d_decoder.py:137`), so it is close.

## 3. The official path this mirrors (file:line on `origin/main`)

| step | official code | in run_canon.py |
|---|---|---|
| Model key → weights | `entrypoint.py:436-500`. It first tries the private S3 registry `s3://scrollprize-models-registry/ink-detection/<MODEL>/` (`:444-482`), then `snapshot_download(repo_id=MODEL)` (`:487`). **There is no lookup table** (the upstream README says there is, at `README.md:325`): `MODEL` is used as the HF repo id as-is. Weight choice: walk the snapshot, prefer `.ckpt > .safetensors > .bin > .pt`, then `sorted[0]` (`:447-455`, `:488-496`). | Same logic, HF only. The snapshot holds `README.md`, `config.json`, and `r152_3ddec_v2_l5_epoch13.ckpt` (1,549,556,213 B, sha256 `36dd0de8…73c3e0`, HF repo sha `075855bc`), so the `.ckpt` is chosen. |
| Layer window | `README.md:44` (resnet3d-152-3d-decoder: `TILE_SIZE=256`, `START_LAYER=1`, `END_LAYER=63`). `entrypoint.py:332-372`: `int(name)`, keep `[start, end)`, numeric sort. `CFG.in_chans = end-start = 62` (`:704`). | same |
| Surface volume | Each segment with a published `…new_canon_autoresearch_recipe-tile256-stride128` prediction lists a pre-built surface-volume zarr in the data_browser `index.json` (field `layers`). Its public `.zattrs` says `num_slices: 109`, `slice_step 1.0`, 2.4 µm, ZYX (checked on PHercParis4 `20260623170305`). The production run is inferred to have used `SURFACE_VOLUME_ZARR` = that zarr. `inference.py:122-209` (`LayersSource`) takes level `"0"`, transposes ZYX→YXZ (`:165-171`) and crops z to `[1,63)` (`:173-184`). | Same 109-layer convention: TIF i = slice i, layers 01–62 → an (H,W,62) uint8 array |
| Decode | `processing.py:162-183`: tifffile; `ndim>2` → channel 0; non-uint8 is **clipped** to 0–255, not rescaled | same (OpenCV is the fallback if tifffile lacks a codec) |
| Model | `model_resnet3d_3d_decoder.py:16-172` and `models/resnetall.py:9-240` | Same code, only reformatted. Proven identical: same state_dict and a bit-identical forward pass against the official module |
| Load | `model_resnet3d_3d_decoder.py:210-238`. Strip `model.`/`module.` prefixes. `with_norm` auto-detected from `normalization.*` (true here, so there is a BatchNorm3d(1) on the input). `strict=False`. DataParallel when more than one GPU is visible. | same (see deviations 6, 7, 13) |
| Grid | `inference.py:58-64` `_grid_1d` (the last tile is forced to the border); `:293-299` y-major order | verbatim |
| Tile preprocessing | `inference.py:272-281`: optional layer reverse; valid = any layer ≠ 0, computed **before** clipping; clip to 0–200 (`:102`, `:278`); `A.ToFloat(max_value=200)` + `ToTensorV2` (`:348-356`), giving (1,62,256,256) | same (deviation 3) |
| Forward | `inference.py:440-448`: `torch.autocast` (fp16 on CUDA, bf16 on CPU), sigmoid, bilinear upsample 64→256 with `align_corners=False` | same |
| Blend | `inference.py:50-56` (2D Hann window normalised to sum 1), `:458-467`, `:480-484` (`pred += p·w·valid`, `count += w·valid`) | same |
| Reduce | `processing.py:692-695`: `pred/clip(count,1e-6)`, clip 0–1, `(x*255).astype(uint8)` | same |
| Runtime | `inference.py:37` cudnn.benchmark; `entrypoint.py:765` device; `:788-792` TF32 (no effect on a T4); `Dockerfile:42` `CUDA_VISIBLE_DEVICES=0` (one GPU) | same |

## 4. Every deviation

1. **No S3, boto3, webKnossos, zarr or profiling.**
   - Layers come from a local folder into RAM, not from the prepare-step zarr.
   - The S3 model registry is skipped because it is private. The HF model card says the HF file is the registry checkpoint, renamed with the contents unchanged.
2. **No DataLoader or worker processes.** Tiles are built in the main process, because spawn workers are fragile in Kaggle notebooks. The values are identical (tested).
3. **clip + `A.ToFloat(200)` is a 256-entry float32 lookup table.** It is the same table albucore builds (`np.arange(256, float32)/200`), and the test shows it is identical. The batch is built C-contiguous, exactly like `default_collate`.
   - *Found while testing:* a layers-last (non-contiguous) batch gave ~1e-6 different conv outputs. That was fixed; the outputs are now bit-identical.
4. **Empty tiles are skipped one by one.** Upstream skips only batches where every tile is empty (`inference.py:427-432`). An empty tile adds `×0`, so the output does not change and fewer forward passes run.
5. **torch.compile is off.** Upstream's default is `COMPILE=1`, `reduce-overhead` (`entrypoint.py:794-825`). It only affects speed, and Triton on a T4 is a risk.
6. **`torch.load(weights_only=True, mmap=True)`** instead of `weights_only=False` (`model_resnet3d_3d_decoder.py:217`).
   - The checkpoint's pickle only references `OrderedDict` and tensor storages. I checked this with `pickletools` without running it.
   - Both loads give the identical 978 tensors (tested).
   - `CANON_ALLOW_PICKLE=1` brings back the full pickle load for other files.
7. **Hard stop if any weight is missing.** Upstream only warns (`:223-226`) and would carry on with random weights. This checkpoint has 978 tensors, 0 missing, 0 unexpected.
8. **Batch size 8, halved automatically on CUDA OOM.** Upstream's default of 256 would OOM for this model on a T4. Batch size does not change the values: bit-exact on CPU at batch 1 and 4, and through the simulated OOM path.
9. **Torch version.**
   - `requirements.txt` only asks for `torch>=2.0.0`. The Kaggle torch is used if a T4 fp16 conv3d self-test passes.
   - The upstream Docker image uses torch 2.10.0 + CUDA 12.8 (`Dockerfile:3`). `CANON_TORCH_PIN=1` installs exactly that, and the script falls back to it automatically if the self-test fails.
   - Other missing dependencies are pip-installed with numpy pinned, so Kaggle's numpy never changes.
10. **Layer check.** It stops unless layers 1–62 each appear exactly once. Upstream uses whatever subset it finds.
11. **Edge handling.** Accumulation is clipped at the image edge. This only matters for images smaller than one tile, where upstream crashes with a broadcast error.
12. **Outputs.** PNG (same uint8 values as upstream's TIF) + 16-bit TIF (extra precision; not upstream) + flipped "readable" copies + JSON. Upstream writes one uint8 tiled deflate TIF (`processing.py:717-777`).
13. **The model wrapper unwraps DataParallel in `get_output_scale_factor`.** Upstream calls it every batch (`inference.py:456`), and its wrapper raises `AttributeError` under DataParallel (tested with the official class). So upstream would crash if more than one GPU were visible. The Docker image avoids that by exposing only one GPU.
14. **`OPENCV_IO_MAX_IMAGE_PIXELS` is 2^40, not upstream's `"0"`** (`entrypoint.py:8`, `inference.py:12`, `processing.py:8`).
    - OpenCV reads 0 literally, so **every `cv2.imread` fails** (checked on OpenCV 4.10 and 5.0).
    - Found when this script's PNG read-back check failed.
    - It has no effect on values: the TIF path uses tifffile.
15. **Extra knobs not in upstream:** `CANON_FLIP_INPUT`, `CANON_CROP`, `CANON_CKPT_PATH`.

## 5. What was verified (this Mac, CPU, throwaway venv `_venv`: py3.12, torch 2.10.0)

`smoke_test.py` runs the **official files** (extracted read-only into `_official/`) against `run_canon.py`.
- `unit`: **7/7 PASS**
  - Preprocessing is identical to the official albumentations transform (max diff 0).
  - The model state_dict is identical (978 tensors, same order), and the forward pass is bit-identical to the official model code.
  - The full pipeline matches the official one **bit-exactly** (`mask_pred`, `mask_count` and the final uint8), at batch 1 and 4, and with reverse on.
    - Official side: `LayersSource` on a production-style 109-slice ZYX zarr, then `predict_fn`, `reduce_partitions` and `write_tiled_tiff`.
    - Test data: a synthetic 150×170×109 LZW volume with invalid regions, tile 64 / stride 32.
    - These comparisons ran fp32, with autocast forced off in both pipelines, because CPU bf16 is ~100× slower here.
- `extras`: **4/4 PASS**
  - Layer folder auto-discovery works.
  - A missing layer is rejected.
  - The simulated CUDA-OOM fallback goes 8→4→2 and the output stays bit-identical.
  - Our wrapper works under DataParallel. The upstream wrapper raises `AttributeError: 'DataParallel' object has no attribute 'get_output_scale_factor'`.
- **End-to-end** (`_smoke/e2e.log`): the script run as a program with its **real autocast** (bf16 on CPU) and the real checkpoint.
  - Input: a 112×120×109 LZW TIF folder, tile 64 / stride 64. That gives 4 tiles; 1 is empty and skipped.
  - It ended with `CANON_DONE status=ok`, exit 0, and all 5 files were written.
  - **Pixel-identical to the official pipeline** on the same data (0 of 13,440 pixels differ).
  - `readable == asinput[:, ::-1]` for both the PNG and the 16-bit TIF.
  - The failure path was also exercised: a crash still writes the JSON and prints `CANON_DONE status=FAILED`, then exits 1.
- The real checkpoint was downloaded with `snapshot_download` (through the script's own HF path too), and its sha256 matches the HF LFS record.

## 6. What could still fail on Kaggle

- **The GPU path is not run here** (there is no CUDA on this Mac). Untested: fp16 autocast on the T4, the real OOM behaviour and the batch-8 memory use (a rough estimate is ~7 GB of 15), and the DataParallel speed-up. GPU fp16 numbers will differ from CPU at fp16 precision, which is also true of upstream.
- **Comparing with a published prediction won't be bit-for-bit.** Even with identical layers, the official run tiled the *whole segment*, while we tile *your patch* from its own top-left corner. The tile grid, and so the Hann blending, falls differently, so expect small local differences, not identical pixels.
- **Torch reinstall.** If Kaggle's preinstalled torch fails the self-test, the script installs 2.10.0+cu128 and relaunches itself. That relaunch works with `!python run_canon.py`. If you pasted the file into a cell, you have to restart the kernel.
- **LZW TIFs need `imagecodecs` for tifffile.** The script installs it, or falls back to OpenCV.
- **Weights download.** An unauthenticated HF download can hit rate limits. Fixes: add an `HF_TOKEN` secret, or attach the `.ckpt` as a dataset and set `CANON_CKPT_PATH`.

## 7. Upstream observations (not changed; for Kaden's judgement)

1. **The two-step flow drops a layer.** Running `STEP=prepare` and then `STEP=inference`, both with `START_LAYER=1, END_LAYER=63`, crops the layers twice.
   - The prepare zarr has 62 channels, and inference then crops `[1,63)` again, which clamps to **61 layers (02–62)** (`inference.py:173-184`).
   - Checked with the official code: shape `(100,120,61)`.
   - The published predictions used the 109-slice zarr instead, where `[1,63)` means layers 01–62. `run_canon.py` does the same.
2. **The training normalisation may differ.** The deprecated training and inference scripts divide by 255 after clipping at 200 (`train_resnet3d_3d_decoder.py:150,156`). `optimized_inference` divides by 200 (`inference.py:102,353`). The canonical checkpoint may come from different training code. This script follows the official inference (/200).
3. **Dark border.** The Hann weights plus the `1e-6` floor (`processing.py:693`) darken the outer ~11 px of any prediction. That is upstream behaviour.
4. **PNG/JPG layers cannot be read.** Because `OPENCV_IO_MAX_IMAGE_PIXELS="0"` breaks `cv2.imread`, the upstream reader fails on PNG/JPG layers (`processing.py:180` returns None, so "Failed to read image"). TIF layers are fine.
5. **Narrow volumes are misread.** `LayersSource` decides which axis is depth by picking the **smallest** one (`inference.py:165-171`). So a surface volume narrower than its slice count is read along the wrong axis, for example a 109-slice zarr less than 109 px wide. My own first end-to-end test hit this with an 80×100 px volume. Real segments are far bigger, and `run_canon.py` does not use this rule.

## Files

- `run_canon.py`: the Kaggle script
- `smoke_test.py`: the equivalence tests
- `_official/`: extracted upstream files
- `_venv/`, `_models/`, `_smoke/`, `_uvcache/`, `_tmp/`: throwaway; safe to delete
