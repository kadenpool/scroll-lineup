#!/usr/bin/env python3
"""
run_canon.py -- run the Vesuvius Challenge canonical 2 um ink model
(HF: scrollprize/ink_canonical_2um, ResNet3D-152 + 3D decoder) on a LOCAL
surface volume given as numbered TIF layers, on a Kaggle GPU box.

It mirrors ScrollPrize/villa ink-detection/optimized_inference (entrypoint.py,
inference.py, processing.py, model_resnet3d_3d_decoder.py, models/resnetall.py)
minus the S3 / boto3 / webKnossos / zarr / profiling plumbing. README.md next to
this file lists the exact upstream lines mirrored and every deviation.

Run on Kaggle:   !python run_canon.py        (or paste the file into one cell)

Environment variables (all optional):
  CANON_LAYERS_DIR     folder holding 00.tif ... NN.tif. Default: auto-find the
                       folder with the most numbered TIFs under /kaggle/input
  CANON_OUT_DIR        output folder                           [/kaggle/working]
  CANON_START_LAYER    first layer, inclusive   (upstream START_LAYER)     [1]
  CANON_END_LAYER      last layer, EXCLUSIVE    (upstream END_LAYER)       [63]
  CANON_TILE_SIZE      tile = network input size (upstream TILE_SIZE)     [256]
  CANON_STRIDE         sliding-window stride     (upstream STRIDE)        [128]
  CANON_BATCH_SIZE     tiles per forward pass; halved on CUDA OOM          [8]
  CANON_MODEL          HF repo id (upstream MODEL)  [scrollprize/ink_canonical_2um]
  CANON_MODEL_REVISION HF revision/commit; empty = latest, as upstream      []
  CANON_CKPT_PATH      use this local .ckpt instead of downloading          []
  CANON_MODEL_DIR      where the HF snapshot is stored     [/tmp/canon_models]
  CANON_REVERSE        1 = reverse layer order (upstream FORCE_REVERSE)     [0]
  CANON_FLIP_INPUT     1 = mirror the layers left-right BEFORE inference, so
                       the network sees the challenge orientation           [0]
  CANON_CROP           "y0:y1,x0:x1" -> run on a sub-rectangle (quick tests) []
  CANON_ALLOW_CPU      1 = allow running without a GPU (very slow)          [0]
  CANON_SKIP_INSTALL   1 = never pip-install anything                       [0]
  CANON_TORCH_PIN      1 = install torch==2.10.0+cu128 (= upstream Docker
                       image torch) instead of using Kaggle's torch         [0]
  CANON_ALLOW_PICKLE   1 = allow a full-pickle torch.load if the safe
                       weights_only load fails (only for a trusted .ckpt)   [0]
  CUDA_VISIBLE_DEVICES defaults to "0" like the upstream Dockerfile (1 GPU).
                       Set "0,1" to use both T4s (upstream DataParallel path).

Outputs (in CANON_OUT_DIR):
  canon_pred_asinput.png        uint8, same pixel grid/orientation as the input TIFs
  canon_pred_asinput_16bit.tif  uint16 version of the same
  canon_pred_readable.png       = asinput[:, ::-1]  (flipped back left-right ->
                                challenge orientation, text reads the right way)
  canon_pred_readable_16bit.tif uint16 version of the same
  canon_run_info.json           settings, versions, timings, checksums, stats
The last line printed is always "CANON_DONE ..." (status=ok or status=FAILED).
"""
import os

# --- process-level settings that must happen before torch / cv2 are imported ---
# Upstream sets "0" here (entrypoint.py:8) meaning "no limit", but OpenCV reads it
# literally: with 0 EVERY cv2.imread fails (checked on OpenCV 4.10 and 5.0). 2**40 = no limit.
os.environ.setdefault("OPENCV_IO_MAX_IMAGE_PIXELS", str(1 << 40))
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "0")         # Dockerfile:42 (single GPU)
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")  # keep Kaggle logs readable
os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")

import gc
import sys
import json
import time
import shutil
import hashlib
import platform
import subprocess
import traceback
import importlib
import importlib.metadata as ilm

T0 = time.time()


def log(msg):
    print(f"[canon {time.time() - T0:7.1f}s] {msg}", flush=True)


def env_str(name, default):
    v = os.environ.get(name, "")
    return v.strip() if v.strip() else default


def env_int(name, default):
    return int(env_str(name, str(default)))


def env_flag(name):
    return env_str(name, "0").lower() in ("1", "true", "yes")


CFG = dict(
    layers_dir=env_str("CANON_LAYERS_DIR", ""),
    out_dir=env_str("CANON_OUT_DIR", "/kaggle/working"),
    start_layer=env_int("CANON_START_LAYER", 1),
    end_layer=env_int("CANON_END_LAYER", 63),
    tile_size=env_int("CANON_TILE_SIZE", 256),
    stride=env_int("CANON_STRIDE", 128),
    batch_size=env_int("CANON_BATCH_SIZE", 8),
    model=env_str("CANON_MODEL", "scrollprize/ink_canonical_2um"),
    model_revision=env_str("CANON_MODEL_REVISION", "") or None,
    ckpt_path=env_str("CANON_CKPT_PATH", ""),
    model_dir=env_str("CANON_MODEL_DIR", "/tmp/canon_models"),
    reverse=env_flag("CANON_REVERSE"),
    flip_input=env_flag("CANON_FLIP_INPUT"),
    crop=env_str("CANON_CROP", ""),
    allow_cpu=env_flag("CANON_ALLOW_CPU"),
    skip_install=env_flag("CANON_SKIP_INSTALL"),
    torch_pin=env_flag("CANON_TORCH_PIN"),
)

# Upstream constants (ink-detection/optimized_inference/inference.py)
MAX_CLIP_VALUE = 200          # inference.py:102
# Calibration knob (default = upstream): divide by this after clipping. The deprecated training scripts divide by
# 255 after clipping at 200 (train_resnet3d_3d_decoder.py:150,156) while optimized inference divides by 200.
DIVISOR = float(os.environ.get("CANON_DIVISOR", "").strip() or MAX_CLIP_VALUE)
USE_HANN_WINDOW = True        # inference.py:105
# Known-good checkpoint (HF API, repo sha 075855bc69317ef6febf39a0d9d687b27d2b7c29)
KNOWN_CKPT_NAME = "r152_3ddec_v2_l5_epoch13.ckpt"
KNOWN_CKPT_SHA256 = "36dd0de84b7b7aa6590184192c7415466cd8a1ba7c1e59f42c6373846373c3e0"
TORCH_PIN = "2.10.0+cu128"    # Dockerfile:3  pytorch/pytorch:2.10.0-cuda12.8-cudnn9-runtime
TORCH_PIN_INDEX = "https://download.pytorch.org/whl/cu128"
LAYER_EXTS = {".tif", ".tiff", ".png", ".jpeg", ".jpg"}  # entrypoint.py:339
KAGGLE_INPUT = "/kaggle/input"   # searched when CANON_LAYERS_DIR is not set

INFO = {"config": dict(CFG), "timings_s": {}, "status": "running"}


# =============================================================================
# 0. Dependencies
# =============================================================================
def _pip(args):
    cmd = [sys.executable, "-m", "pip", "install", "-q", "--disable-pip-version-check",
           "--no-input"] + args
    log("pip " + " ".join(args))
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    tail = "\n".join(r.stdout.strip().splitlines()[-15:])
    if tail:
        print(tail, flush=True)
    if r.returncode != 0:
        raise RuntimeError(f"pip install failed ({r.returncode}): {' '.join(args)}")


def _has(mod):
    try:
        importlib.import_module(mod)
        return True
    except Exception:
        return False


def ensure_basic_deps():
    """numpy / tifffile / imagecodecs / huggingface_hub / cv2 (requirements.txt)."""
    if not _has("numpy"):
        if CFG["skip_install"]:
            raise RuntimeError("numpy missing and CANON_SKIP_INSTALL=1")
        _pip(["numpy"])
    import numpy as np
    pin_np = [f"numpy=={np.__version__}"]  # never let pip swap numpy under Kaggle's feet
    want = []
    if not _has("tifffile"):
        want.append("tifffile")
    if not _has("imagecodecs"):          # tifffile needs it for LZW (vc_render_tifxyz uses LZW)
        want.append("imagecodecs")
    try:
        import huggingface_hub
        hv = tuple(int(p) for p in huggingface_hub.__version__.split(".")[:2])
        if hv < (0, 23):
            want.append("huggingface_hub>=0.23.0")
    except Exception:
        want.append("huggingface_hub>=0.23.0")
    if not _has("cv2"):
        want.append("opencv-python-headless>=4.5.0")
    if want:
        if CFG["skip_install"]:
            log(f"WARNING missing {want} but CANON_SKIP_INSTALL=1")
        else:
            for pkg in want:  # one at a time: a failed optional codec must not block the rest
                try:
                    _pip([pkg] + pin_np)
                except Exception as e:
                    log(f"WARNING could not install {pkg}: {e}")
            importlib.invalidate_caches()
    for m in ("tifffile", "huggingface_hub", "cv2"):
        if not _has(m):
            raise RuntimeError(f"required module {m} unavailable")


def _torch_selftest(torch):
    """Tiny fp16-autocast conv3d on cuda:0 (catches 'no kernel image' arch mismatch)."""
    try:
        dev = torch.device("cuda:0")
        conv = torch.nn.Conv3d(1, 4, 3, padding=1).to(dev)
        x = torch.randn(1, 1, 4, 16, 16, device=dev)
        with torch.inference_mode(), torch.autocast(device_type="cuda", enabled=True):
            y = conv(x)
        torch.cuda.synchronize()
        return bool(torch.isfinite(y).all().item()), "ok"
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


def _reexec(reason):
    if os.environ.get("CANON_REEXEC") == "1":
        raise RuntimeError(f"torch still unusable after reinstall: {reason}")
    main_file = globals().get("__file__")
    if not main_file or not os.path.isfile(main_file):
        raise RuntimeError("torch was reinstalled; RESTART the notebook kernel and run again "
                           f"({reason})")
    log(f"re-launching the script with the freshly installed torch ({reason})")
    os.environ["CANON_REEXEC"] = "1"
    sys.stdout.flush()
    os.execv(sys.executable, [sys.executable, os.path.abspath(main_file)] + sys.argv[1:])


def _install_pinned_torch():
    if CFG["skip_install"]:
        raise RuntimeError("torch unusable and CANON_SKIP_INSTALL=1")
    _pip([f"torch=={TORCH_PIN}", "--index-url", TORCH_PIN_INDEX])
    importlib.invalidate_caches()


def ensure_torch():
    try:
        installed = ilm.version("torch")
    except ilm.PackageNotFoundError:
        installed = None
    if installed is None or (CFG["torch_pin"] and installed != TORCH_PIN):
        log(f"torch installed: {installed}; installing torch=={TORCH_PIN} (upstream Docker torch)")
        if "torch" in sys.modules:
            _install_pinned_torch()
            _reexec("torch was already imported")
        _install_pinned_torch()
    import torch
    has_nvsmi = shutil.which("nvidia-smi") is not None
    if not torch.cuda.is_available():
        if has_nvsmi and not CFG["allow_cpu"]:
            # GPU present but this torch cannot use it (CPU-only build / CUDA too new for driver)
            log(f"torch {torch.__version__} (cuda {torch.version.cuda}) cannot see the GPU; "
                f"reinstalling torch=={TORCH_PIN}")
            _install_pinned_torch()
            _reexec("CUDA not available with the preinstalled torch")
        if not CFG["allow_cpu"]:
            raise RuntimeError("No CUDA GPU visible. On Kaggle: Settings -> Accelerator -> "
                               "'GPU T4 x2', then run again (or set CANON_ALLOW_CPU=1).")
        log("WARNING: running on CPU (CANON_ALLOW_CPU=1) -- only sensible for tiny crops")
        return torch
    ok, msg = _torch_selftest(torch)
    if not ok:
        log(f"torch {torch.__version__} failed the T4 self-test: {msg}")
        _install_pinned_torch()
        _reexec("self-test failed")
    return torch


# =============================================================================
# 1. Model -- verbatim port of models/resnetall.py and model_resnet3d_3d_decoder.py
# =============================================================================
def build_model_classes(torch):
    from functools import partial
    import torch.nn as nn
    import torch.nn.functional as F

    # ---- models/resnetall.py:9-240 (verbatim apart from indentation) ----
    def get_inplanes():
        return [64, 128, 256, 512]

    def conv3x3x3(in_planes, out_planes, stride=1):
        return nn.Conv3d(in_planes, out_planes, kernel_size=3, stride=stride,
                         padding=1, bias=False)

    def conv1x1x1(in_planes, out_planes, stride=1):
        return nn.Conv3d(in_planes, out_planes, kernel_size=1, stride=stride, bias=False)

    class BasicBlock(nn.Module):
        expansion = 1

        def __init__(self, in_planes, planes, stride=1, downsample=None):
            super().__init__()
            self.conv1 = conv3x3x3(in_planes, planes, stride)
            self.bn1 = nn.BatchNorm3d(planes)
            self.relu = nn.ReLU(inplace=True)
            self.conv2 = conv3x3x3(planes, planes)
            self.bn2 = nn.BatchNorm3d(planes)
            self.downsample = downsample
            self.stride = stride

        def forward(self, x):
            residual = x
            out = self.conv1(x)
            out = self.bn1(out)
            out = self.relu(out)
            out = self.conv2(out)
            out = self.bn2(out)
            if self.downsample is not None:
                residual = self.downsample(x)
            out += residual
            out = self.relu(out)
            return out

    class Bottleneck(nn.Module):
        expansion = 4

        def __init__(self, in_planes, planes, stride=1, downsample=None):
            super().__init__()
            self.conv1 = conv1x1x1(in_planes, planes)
            self.bn1 = nn.BatchNorm3d(planes)
            self.conv2 = conv3x3x3(planes, planes, stride)
            self.bn2 = nn.BatchNorm3d(planes)
            self.conv3 = conv1x1x1(planes, planes * self.expansion)
            self.bn3 = nn.BatchNorm3d(planes * self.expansion)
            self.relu = nn.ReLU(inplace=True)
            self.downsample = downsample
            self.stride = stride

        def forward(self, x):
            residual = x
            out = self.conv1(x)
            out = self.bn1(out)
            out = self.relu(out)
            out = self.conv2(out)
            out = self.bn2(out)
            out = self.relu(out)
            out = self.conv3(out)
            out = self.bn3(out)
            if self.downsample is not None:
                residual = self.downsample(x)
            out += residual
            out = self.relu(out)
            return out

    class ResNet(nn.Module):
        def __init__(self, block, layers, block_inplanes, n_input_channels=3,
                     conv1_t_size=7, conv1_t_stride=1, no_max_pool=False,
                     shortcut_type='B', widen_factor=1.0, n_classes=400,
                     forward_features=False):
            super().__init__()
            self.forward_features = forward_features
            block_inplanes = [int(x * widen_factor) for x in block_inplanes]
            self.in_planes = block_inplanes[0]
            self.no_max_pool = no_max_pool
            self.conv1 = nn.Conv3d(n_input_channels, self.in_planes,
                                   kernel_size=(conv1_t_size, 7, 7),
                                   stride=(conv1_t_stride, 2, 2),
                                   padding=(conv1_t_size // 2, 3, 3), bias=False)
            self.bn1 = nn.BatchNorm3d(self.in_planes)
            self.relu = nn.ReLU(inplace=True)
            self.maxpool = nn.MaxPool3d(kernel_size=(1, 3, 3), stride=(1, 2, 2), padding=(0, 1, 1))
            self.layer1 = self._make_layer(block, block_inplanes[0], layers[0], shortcut_type)
            self.layer2 = self._make_layer(block, block_inplanes[1], layers[1], shortcut_type, stride=2)
            self.layer3 = self._make_layer(block, block_inplanes[2], layers[2], shortcut_type, stride=2)
            self.layer4 = self._make_layer(block, block_inplanes[3], layers[3], shortcut_type, stride=2)
            self.avgpool = nn.AdaptiveMaxPool3d((1, 1, 1))
            self.fc = nn.Linear(block_inplanes[3] * block.expansion, n_classes)
            for m in self.modules():
                if isinstance(m, nn.Conv3d):
                    nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
                elif isinstance(m, nn.BatchNorm3d):
                    nn.init.constant_(m.weight, 1)
                    nn.init.constant_(m.bias, 0)

        def _downsample_basic_block(self, x, planes, stride):
            out = F.avg_pool3d(x, kernel_size=1, stride=stride)
            zero_pads = torch.zeros(out.size(0), planes - out.size(1), out.size(2),
                                    out.size(3), out.size(4))
            if isinstance(out.data, torch.cuda.FloatTensor):
                zero_pads = zero_pads.cuda()
            out = torch.cat([out.data, zero_pads], dim=1)
            return out

        def _make_layer(self, block, planes, blocks, shortcut_type, stride=1):
            downsample = None
            if stride != 1 or self.in_planes != planes * block.expansion:
                if shortcut_type == 'A':
                    downsample = partial(self._downsample_basic_block,
                                         planes=planes * block.expansion, stride=stride)
                else:
                    downsample = nn.Sequential(
                        conv1x1x1(self.in_planes, planes * block.expansion, stride),
                        nn.BatchNorm3d(planes * block.expansion))
            layers = []
            layers.append(block(in_planes=self.in_planes, planes=planes, stride=stride,
                                downsample=downsample))
            self.in_planes = planes * block.expansion
            for i in range(1, blocks):
                layers.append(block(self.in_planes, planes))
            return nn.Sequential(*layers)

        def forward(self, x):
            x = self.conv1(x)
            x = self.bn1(x)
            x = self.relu(x)
            if not self.no_max_pool:
                x = self.maxpool(x)
            x1 = self.layer1(x)
            x2 = self.layer2(x1)
            x3 = self.layer3(x2)
            x4 = self.layer4(x3)
            if self.forward_features:
                return [x1, x2, x3, x4]
            else:
                x = self.avgpool(x4)
                x = x.view(x.size(0), -1)
                x = self.fc(x)
                return x

    def generate_model(model_depth, **kwargs):
        assert model_depth in [10, 18, 34, 50, 101, 152, 200]
        if model_depth == 10:
            model = ResNet(BasicBlock, [1, 1, 1, 1], get_inplanes(), **kwargs)
        elif model_depth == 18:
            model = ResNet(BasicBlock, [2, 2, 2, 2], get_inplanes(), **kwargs)
        elif model_depth == 34:
            model = ResNet(BasicBlock, [3, 4, 6, 3], get_inplanes(), **kwargs)
        elif model_depth == 50:
            model = ResNet(Bottleneck, [3, 4, 6, 3], get_inplanes(), **kwargs)
        elif model_depth == 101:
            model = ResNet(Bottleneck, [3, 4, 23, 3], get_inplanes(), **kwargs)
        elif model_depth == 152:
            model = ResNet(Bottleneck, [3, 8, 36, 3], get_inplanes(), **kwargs)
        elif model_depth == 200:
            model = ResNet(Bottleneck, [3, 24, 36, 3], get_inplanes(), **kwargs)
        return model

    # ---- model_resnet3d_3d_decoder.py:16-172 (verbatim apart from indentation) ----
    class ResConvBlock3D(nn.Module):
        def __init__(self, in_ch, out_ch):
            super().__init__()
            self.conv1 = nn.Conv3d(in_ch, out_ch, 3, padding=1, bias=False)
            self.gn1 = nn.GroupNorm(min(32, out_ch), out_ch)
            self.conv2 = nn.Conv3d(out_ch, out_ch, 3, padding=1, bias=False)
            self.gn2 = nn.GroupNorm(min(32, out_ch), out_ch)
            self.shortcut = nn.Conv3d(in_ch, out_ch, 1, bias=False) if in_ch != out_ch else nn.Identity()

        def forward(self, x):
            identity = self.shortcut(x)
            x = F.relu(self.gn1(self.conv1(x)), inplace=True)
            x = self.gn2(self.conv2(x))
            x = F.relu(x + identity, inplace=True)
            return x

    class DepthAttentionCollapse(nn.Module):
        def __init__(self, in_ch):
            super().__init__()
            self.attn_conv = nn.Conv3d(in_ch, 1, 1)

        def forward(self, x):
            attn = self.attn_conv(x)
            attn = F.softmax(attn, dim=2)
            return (x * attn).sum(dim=2)

    class AuxHead(nn.Module):
        def __init__(self, in_ch, target_size=64):
            super().__init__()
            self.pool = nn.AdaptiveAvgPool3d((1, None, None))
            self.conv = nn.Conv2d(in_ch, 1, 1)
            self.target_size = target_size

        def forward(self, x):
            x = self.pool(x).squeeze(2)
            x = self.conv(x)
            if x.shape[-1] != self.target_size:
                x = F.interpolate(x, size=(self.target_size, self.target_size),
                                  mode="bilinear", align_corners=False)
            return x

    class Decoder3DUNet(nn.Module):
        def __init__(self, encoder_dims=(256, 512, 1024, 2048),
                     decoder_dims=(64, 128, 256, 512), deep_supervision=True):
            super().__init__()
            self.deep_supervision = deep_supervision
            self.channel_reduce = nn.ModuleList([
                nn.Sequential(
                    nn.Conv3d(enc_d, dec_d, 1, bias=False),
                    nn.GroupNorm(min(32, dec_d), dec_d),
                    nn.ReLU(inplace=True),
                )
                for enc_d, dec_d in zip(encoder_dims, decoder_dims)
            ])
            self.decoder_blocks = nn.ModuleList([
                ResConvBlock3D(decoder_dims[i] + decoder_dims[i - 1], decoder_dims[i - 1])
                for i in range(len(decoder_dims) - 1, 0, -1)
            ])
            self.depth_collapse = DepthAttentionCollapse(decoder_dims[0])
            self.logit = nn.Conv2d(decoder_dims[0], 1, 1)
            if deep_supervision:
                self.aux_head_s2 = AuxHead(decoder_dims[2])
                self.aux_head_s1 = AuxHead(decoder_dims[1])

        def forward(self, feat_maps):
            feats = [self.channel_reduce[i](feat_maps[i]) for i in range(4)]
            aux_outputs = []
            x = feats[3]
            x = F.interpolate(x, size=feats[2].shape[2:], mode="trilinear", align_corners=False)
            x = torch.cat([x, feats[2]], dim=1)
            x = self.decoder_blocks[0](x)
            if self.deep_supervision and self.training:
                aux_outputs.append(self.aux_head_s2(x))
            x = F.interpolate(x, size=feats[1].shape[2:], mode="trilinear", align_corners=False)
            x = torch.cat([x, feats[1]], dim=1)
            x = self.decoder_blocks[1](x)
            if self.deep_supervision and self.training:
                aux_outputs.append(self.aux_head_s1(x))
            x = F.interpolate(x, size=feats[0].shape[2:], mode="trilinear", align_corners=False)
            x = torch.cat([x, feats[0]], dim=1)
            x = self.decoder_blocks[2](x)
            x = self.depth_collapse(x)
            x = self.logit(x)
            if self.deep_supervision and self.training:
                return x, aux_outputs
            return x

    class RegressionModel(nn.Module):
        def __init__(self, with_norm=False):
            super().__init__()
            self.backbone = generate_model(model_depth=152, n_input_channels=1,
                                           forward_features=True, n_classes=1039)
            self.decoder = Decoder3DUNet(encoder_dims=(256, 512, 1024, 2048),
                                         decoder_dims=(64, 128, 256, 512),
                                         deep_supervision=True)
            self.normalization = nn.BatchNorm3d(num_features=1) if with_norm else None

        def forward(self, x):
            if x.ndim == 4:
                x = x[:, None]
            if self.normalization is not None:
                x = self.normalization(x)
            feat_maps = self.backbone(x)
            return self.decoder(feat_maps)

        def get_output_scale_factor(self):
            return 4

    class ResNet3DDecoderWrapper:
        def __init__(self, model, device):
            self.model = model
            self.device = device

        def forward(self, x):
            return self.model(x)

        def get_output_scale_factor(self):
            m = self.model.module if isinstance(self.model, nn.DataParallel) else self.model
            return m.get_output_scale_factor()

        def eval(self):
            self.model.eval()

        def to(self, device):
            self.model.to(device)
            self.device = device

    return RegressionModel, ResNet3DDecoderWrapper


def _extract_state_dict(torch, checkpoint):
    """model_resnet3d_3d_decoder.py:175-195 (verbatim)."""
    if not isinstance(checkpoint, dict):
        raise RuntimeError("Checkpoint does not contain a usable state_dict")
    for key in ("state_dict", "model_state_dict"):
        state_dict = checkpoint.get(key)
        if isinstance(state_dict, dict):
            if state_dict and all(isinstance(n, str) and isinstance(v, torch.Tensor)
                                  for n, v in state_dict.items()):
                return state_dict
            raise RuntimeError(f"Checkpoint field '{key}' is not a valid tensor state_dict")
    if checkpoint and all(isinstance(n, str) and isinstance(v, torch.Tensor)
                          for n, v in checkpoint.items()):
        return checkpoint
    raise RuntimeError("Checkpoint does not contain a usable state_dict")


def _strip_known_prefixes(state_dict):
    """model_resnet3d_3d_decoder.py:198-207 (verbatim)."""
    from collections import OrderedDict
    normalized = OrderedDict()
    for key, value in state_dict.items():
        while key.startswith("model.") or key.startswith("module."):
            if key.startswith("model."):
                key = key[len("model."):]
            if key.startswith("module."):
                key = key[len("module."):]
        normalized[key] = value
    return normalized


def _torch_load_ckpt(torch, path):
    """Upstream: torch.load(path, map_location='cpu', weights_only=False)
    (model_resnet3d_3d_decoder.py:217). The canonical .ckpt pickle references only
    OrderedDict + tensor storages, so weights_only=True loads the identical tensors
    without executing arbitrary pickle code; mmap=True avoids a second RAM copy.
    Full-pickle loading is only used if CANON_ALLOW_PICKLE=1 (trusted file)."""
    errs = []
    for extra in ({"mmap": True}, {}):          # mmap needs torch >= 2.1
        try:
            return torch.load(path, map_location="cpu", weights_only=True, **extra)
        except Exception as e:  # noqa: BLE001
            errs.append(f"{type(e).__name__}: {e}")
    if not env_flag("CANON_ALLOW_PICKLE"):
        raise RuntimeError(f"safe (weights_only=True) load failed: {errs[-1]}. If you trust this "
                           "file, rerun with CANON_ALLOW_PICKLE=1 (upstream uses weights_only=False).")
    log(f"weights_only load failed ({errs[-1]}); CANON_ALLOW_PICKLE=1 -> full pickle load")
    return torch.load(path, map_location="cpu", weights_only=False)


def load_model(torch, model_path, device, num_frames=62):
    """model_resnet3d_3d_decoder.py:210-238, plus a hard check that no weights are missing."""
    import torch.nn as nn
    RegressionModel, Wrapper = build_model_classes(torch)
    log(f"loading ResNet3D-152 3D decoder from {model_path} with {num_frames} frames")
    checkpoint = _torch_load_ckpt(torch, model_path)
    hp = checkpoint.get("hyper_parameters") if isinstance(checkpoint, dict) else None
    if hp is not None:
        try:
            INFO["ckpt_hyper_parameters"] = {k: (v if isinstance(v, (int, float, str, bool, list, tuple))
                                                 else str(v)) for k, v in dict(hp).items()}
        except Exception:
            pass
    state_dict = _strip_known_prefixes(_extract_state_dict(torch, checkpoint))
    with_norm = any(key.startswith("normalization.") for key in state_dict)
    model = RegressionModel(with_norm=with_norm)
    missing, unexpected = model.load_state_dict(state_dict, strict=False)
    log(f"state_dict: {len(state_dict)} tensors, with_norm={with_norm}, "
        f"missing={len(missing)}, unexpected={len(unexpected)}")
    if unexpected:
        log(f"WARNING unexpected checkpoint keys (ignored, as upstream): {list(unexpected)[:10]}")
    if missing:
        # upstream only warns; a missing weight silently means garbage output, so stop.
        raise RuntimeError(f"checkpoint is missing {len(missing)} model weights, e.g. {list(missing)[:10]}")
    INFO["model"] = {"with_norm": with_norm, "n_tensors": len(state_dict),
                     "n_params": int(sum(p.numel() for p in model.parameters()))}
    del checkpoint, state_dict
    gc.collect()
    if torch.cuda.device_count() > 1:  # model_resnet3d_3d_decoder.py:228-230
        model = nn.DataParallel(model)
        log(f"model wrapped with DataParallel for {torch.cuda.device_count()} GPUs")
    model.to(device)
    model.eval()
    return Wrapper(model, device)


# =============================================================================
# 2. Weights (entrypoint.py:436-500, Hugging Face branch only)
# =============================================================================
def _prefer(weights):
    """entrypoint.py:447-455 (verbatim)."""
    if not weights:
        return None
    order = [".ckpt", ".safetensors", ".bin", ".pt"]
    for ext in order:
        matches = [w for w in weights if w.lower().endswith(ext)]
        if matches:
            return sorted(matches)[0]
    return sorted(weights)[0]


def _sha256(path, chunk=16 * 1024 * 1024):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def resolve_weights():
    if CFG["ckpt_path"]:
        if not os.path.isfile(CFG["ckpt_path"]):
            raise RuntimeError(f"CANON_CKPT_PATH not found: {CFG['ckpt_path']}")
        chosen = CFG["ckpt_path"]
        log(f"using local checkpoint {chosen}")
    else:
        from huggingface_hub import snapshot_download
        local_dir = os.path.join(CFG["model_dir"], CFG["model"].replace("/", "__"))
        os.makedirs(local_dir, exist_ok=True)
        log(f"downloading HF snapshot {CFG['model']} (rev={CFG['model_revision'] or 'latest'}) "
            f"-> {local_dir}  (~1.55 GB)")
        last = None
        for attempt in range(1, 4):
            try:
                snapshot_download(repo_id=CFG["model"], revision=CFG["model_revision"],
                                  local_dir=local_dir)
                last = None
                break
            except Exception as e:
                last = e
                log(f"download attempt {attempt} failed: {type(e).__name__}: {e}")
                time.sleep(15 * attempt)
        if last is not None:
            raise RuntimeError(f"Hugging Face download failed: {last}")
        candidates = []
        for root, _, files in os.walk(local_dir):
            for f in files:
                if f.lower().endswith((".ckpt", ".safetensors", ".bin", ".pt")):
                    candidates.append(os.path.join(root, f))
        if not candidates:
            raise RuntimeError("No model weight files (.ckpt/.safetensors/.bin/.pt) found in downloaded repo")
        chosen = _prefer(candidates)
    size = os.path.getsize(chosen)
    log(f"weights file: {chosen} ({size / 1e9:.3f} GB); hashing...")
    digest = _sha256(chosen)
    match = digest == KNOWN_CKPT_SHA256
    log(f"sha256 {digest} -> {'MATCHES' if match else 'DIFFERS FROM'} the known "
        f"{KNOWN_CKPT_NAME} (HF repo sha 075855bc)")
    if not match:
        log("WARNING: checkpoint differs from the one this script was checked against")
    INFO["weights"] = {"path": chosen, "bytes": size, "sha256": digest,
                       "matches_known_sha256": match}
    return chosen


# =============================================================================
# 3. Layers (entrypoint.py:332-372 selection, processing.py:162-183 decoding)
# =============================================================================
def find_layers_dir():
    if CFG["layers_dir"]:
        if not os.path.isdir(CFG["layers_dir"]):
            raise RuntimeError(f"CANON_LAYERS_DIR is not a folder: {CFG['layers_dir']}")
        return CFG["layers_dir"]
    root = KAGGLE_INPUT
    if not os.path.isdir(root):
        raise RuntimeError(f"CANON_LAYERS_DIR not set and {root} does not exist")
    best, cands = None, []
    for dirpath, dirnames, files in os.walk(root, followlinks=True):
        if dirpath[len(root):].count(os.sep) > 6:
            dirnames[:] = []
            continue
        n = sum(1 for f in files if os.path.splitext(f)[1].lower() in (".tif", ".tiff")
                and os.path.splitext(f)[0].isdigit())
        if n:
            cands.append((n, dirpath))
    if not cands:
        raise RuntimeError("no folder with numbered .tif layers found under /kaggle/input; "
                           "set CANON_LAYERS_DIR")
    cands.sort(key=lambda t: (-t[0], t[1]))
    for n, d in cands[:5]:
        log(f"  candidate layers folder: {d} ({n} numbered tifs)")
    best = cands[0][1]
    log(f"auto-selected CANON_LAYERS_DIR={best}")
    return best


def list_layers(folder, start_layer, end_layer):
    """entrypoint.py:332-372: numbered image files, [start, end), numeric sort."""
    keys = []
    for base in os.listdir(folder):
        name, ext = os.path.splitext(base)
        if ext.lower() not in LAYER_EXTS:
            continue
        try:
            layer_idx = int(name)
        except ValueError:
            continue
        if start_layer <= layer_idx < end_layer:
            keys.append((layer_idx, os.path.join(folder, base)))
    if not keys:
        raise RuntimeError(f"No layers found within range [{start_layer}, {end_layer}) in {folder}")
    keys.sort(key=lambda kv: kv[0])
    idxs = [k for k, _ in keys]
    # Deviation (check only): upstream would silently use whatever subset exists.
    if idxs != list(range(start_layer, end_layer)):
        raise RuntimeError(f"expected every layer {start_layer}..{end_layer - 1} exactly once, "
                           f"found {len(idxs)}: {idxs[:5]}...{idxs[-5:]}")
    return [p for _, p in keys]


def read_gray_any(path):
    """processing.py:162-183 (tifffile for .tif; ndim>2 -> channel 0; non-uint8 -> clip to 0..255),
    with an OpenCV fallback if tifffile lacks a codec."""
    import numpy as np
    import cv2
    ext = os.path.splitext(path)[1].lower()
    img = None
    if ext in (".tif", ".tiff"):
        try:
            import tifffile
            img = tifffile.imread(path)
        except Exception as e:
            if not INFO.get("_tifffile_fallback_logged"):
                INFO["_tifffile_fallback_logged"] = True
                log(f"tifffile could not read {os.path.basename(path)} ({type(e).__name__}: {e}); "
                    "using cv2 for this and any further failing layers")
            img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
        if img is None:
            raise RuntimeError(f"Failed to read image: {path}")
        if img.ndim > 2:
            img = img[..., 0]
        if img.dtype != np.uint8:
            INFO.setdefault("warnings", []).append(f"{os.path.basename(path)} dtype {img.dtype} "
                                                   "clipped to uint8 like upstream (no rescale)")
            img = np.clip(img, 0, 255).astype(np.uint8)
        return img
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise RuntimeError(f"Failed to read image: {path}")
    return img


def parse_crop(spec):
    if not spec:
        return None
    ys, xs = spec.split(",")
    y0, y1 = (int(v) for v in ys.split(":"))
    x0, x1 = (int(v) for v in xs.split(":"))
    return y0, y1, x0, x1


def load_volume(paths, crop):
    """Stack layers into an (H, W, C) uint8 array -- the layout the upstream prepare
    step writes to zarr (processing.py:268-296) and LayersSource reads (inference.py:122-209)."""
    import numpy as np
    from concurrent.futures import ThreadPoolExecutor
    first = read_gray_any(paths[0])
    H0, W0 = first.shape
    y0, y1, x0, x1 = crop if crop else (0, H0, 0, W0)
    y0, x0 = max(0, y0), max(0, x0)
    y1, x1 = min(H0, y1), min(W0, x1)
    if y1 <= y0 or x1 <= x0:
        raise RuntimeError(f"empty crop {crop} for layer size {(H0, W0)}")
    vol = np.empty((y1 - y0, x1 - x0, len(paths)), dtype=np.uint8)

    def _one(i):
        img = first if i == 0 else read_gray_any(paths[i])
        if img.shape != (H0, W0):
            raise RuntimeError(f"Layer size mismatch: {paths[i]} has {img.shape}, expected {(H0, W0)}")
        vol[:, :, i] = img[y0:y1, x0:x1]
        return i

    with ThreadPoolExecutor(max_workers=min(4, os.cpu_count() or 4)) as ex:
        for n, _ in enumerate(ex.map(_one, range(len(paths))), 1):
            if n % 16 == 0 or n == len(paths):
                log(f"  read {n}/{len(paths)} layers")
    INFO["input"] = {"full_layer_hw": [H0, W0], "crop_yyxx": [y0, y1, x0, x1],
                     "volume_hwc": list(vol.shape)}
    return vol


# =============================================================================
# 4. Sliding-window inference (inference.py:40-64, 247-282, 348-356, 379-486)
# =============================================================================
def hann2d(np, h, w):
    """inference.py:50-56 (verbatim)."""
    wy = np.hanning(h).astype(np.float32)
    wx = np.hanning(w).astype(np.float32)
    k = np.outer(wy, wx)
    s = k.sum()
    return k / (s if s > 0 else 1.0)


def _grid_1d(L, tile, stride):
    """inference.py:58-64 (verbatim)."""
    xs = list(range(0, max(1, L - tile + 1), stride))
    end = max(0, L - tile)
    if not xs or xs[-1] != end:
        xs.append(end)
    return xs


def _is_oom(e):
    s = str(e)
    return ("out of memory" in s.lower() or "CUBLAS_STATUS_ALLOC_FAILED" in s
            or "CUDNN_STATUS_ALLOC_FAILED" in s or "CUDNN_STATUS_NOT_SUPPORTED" in s
            or type(e).__name__ == "OutOfMemoryError")


def run_inference(torch, vol, model, device, reverse):
    import numpy as np
    import torch.nn.functional as F
    H, W, C = vol.shape
    tile = CFG["tile_size"]
    stride = CFG["stride"]
    xs = _grid_1d(W, tile, stride)              # inference.py:293
    ys = _grid_1d(H, tile, stride)              # inference.py:294
    xyxys = [(x1, y1, x1 + tile, y1 + tile) for y1 in ys for x1 in xs]  # inference.py:298-299

    # Per-pixel validity (inference.py:274-276): valid iff any z-layer != 0.
    # max over z > 0 is the same test for uint8 and avoids a (H,W,C) bool temp.
    valid_full = vol.max(axis=2) > 0
    # ROI with zero padding (inference.py:193-209)

    def read_roi(a, y1, y2, x1, x2):
        yy1, yy2 = max(0, y1), min(a.shape[0], y2)
        xx1, xx2 = max(0, x1), min(a.shape[1], x2)
        out = np.zeros((y2 - y1, x2 - x1) + a.shape[2:], dtype=a.dtype)
        if yy2 > yy1 and xx2 > xx1:
            out[(yy1 - y1):(yy2 - y1), (xx1 - x1):(xx2 - x1)] = a[yy1:yy2, xx1:xx2]
        return out

    # Upstream runs the forward pass on every tile of a batch and only skips a batch
    # when ALL its tiles are empty (inference.py:427-432); an all-empty tile adds
    # y*0 and w*0, i.e. nothing.  Skipping each empty tile is therefore output-identical.
    todo = [c for c in xyxys if read_roi(valid_full, c[1], c[3], c[0], c[2]).any()]
    log(f"grid {len(ys)} x {len(xs)} = {len(xyxys)} tiles of {tile}px, stride {stride}; "
        f"{len(todo)} contain valid pixels, {len(xyxys) - len(todo)} empty tiles skipped")
    INFO["tiles"] = {"grid_y": len(ys), "grid_x": len(xs), "total": len(xyxys),
                     "with_valid_pixels": len(todo)}
    if not todo:
        raise RuntimeError("No valid tiles (every pixel is zero in the selected layers)")

    # clip to [0, 200] (inference.py:278) then A.ToFloat(max_value=200) (inference.py:353):
    # albucore builds exactly this float32 table (np.arange(256, float32) / 200) for uint8.
    lut = (np.arange(256, dtype=np.float32) / np.float32(DIVISOR))[np.minimum(np.arange(256), MAX_CLIP_VALUE)]

    def make_batch(coords):
        # (B, 1, C, tile, tile) float32, C-contiguous exactly like the tensor that
        # DataLoader's default_collate (torch.stack) hands the model upstream. A
        # non-contiguous (layers-last) array gives ~1e-6 different conv results.
        batch = np.empty((len(coords), 1, C, tile, tile), dtype=np.float32)
        valids = []
        for k, (x1, y1, x2, y2) in enumerate(coords):
            t = read_roi(vol, y1, y2, x1, x2)                 # (tile, tile, C) uint8
            if reverse:
                t = t[:, :, ::-1]                              # inference.py:272-273
            valids.append(np.any(t != 0, axis=-1).astype(np.uint8))   # inference.py:276
            batch[k, 0] = lut[t].transpose(2, 0, 1)            # ToTensorV2: HWC -> CHW
        return batch, valids

    mask_pred = np.zeros((H, W), dtype=np.float32)            # inference.py:396-397
    mask_count = np.zeros((H, W), dtype=np.float32)
    weight_tensor = None
    w_cpu = None
    model.eval()
    amp_device = "cuda" if device.type == "cuda" else "cpu"
    bs = max(1, CFG["batch_size"])
    i = 0
    n_done = 0
    t_start = time.time()
    t_last = 0.0
    n_batches = 0
    peak_mem = 0
    with torch.inference_mode():
        while i < len(todo):
            coords = todo[i:i + bs]
            imgs_np, valids = make_batch(coords)
            oom = None
            try:
                images = torch.from_numpy(imgs_np).to(device, non_blocking=True)
                with torch.autocast(device_type=amp_device, enabled=True):   # inference.py:440-441
                    y_preds = model.forward(images)
                y_preds = torch.sigmoid(y_preds)                              # inference.py:442
                y_preds_resized = F.interpolate(y_preds.float(), size=(tile, tile),
                                                mode="bilinear", align_corners=False)  # :443-448
                if weight_tensor is None:                                     # :458-465
                    th, tw = y_preds_resized.shape[-2:]
                    weight_tensor = torch.from_numpy(hann2d(np, th, tw).astype(np.float32)).to(device)
                    w_cpu = weight_tensor.detach().cpu().numpy().astype(np.float32)
                y_weighted = (y_preds_resized * weight_tensor).squeeze(1)    # :467
                y_cpu = y_weighted.cpu().numpy()                              # :470
            except Exception as e:  # noqa: BLE001
                if not _is_oom(e):
                    raise
                oom = f"{type(e).__name__}: {str(e).splitlines()[0][:160]}"
            if oom is not None:
                images = y_preds = y_preds_resized = None
                gc.collect()
                torch.cuda.empty_cache()
                if bs == 1:
                    raise RuntimeError(f"CUDA OOM even at batch size 1: {oom}")
                bs = max(1, bs // 2)
                log(f"CUDA OOM ({oom}) -> retrying with batch size {bs}")
                continue
            for k, (x1, y1, x2, y2) in enumerate(coords):          # inference.py:480-484
                v = valids[k].astype(np.float32)
                # clip to the image (only matters when the image is smaller than a tile,
                # where upstream would raise a broadcast error)
                hh, ww = min(y2, H) - y1, min(x2, W) - x1
                mask_pred[y1:y1 + hh, x1:x1 + ww] += (y_cpu[k] * v)[:hh, :ww]
                mask_count[y1:y1 + hh, x1:x1 + ww] += (w_cpu * v)[:hh, :ww]
            i += len(coords)
            n_done += len(coords)
            n_batches += 1
            if device.type == "cuda":
                peak_mem = max(peak_mem, torch.cuda.max_memory_allocated() / 1e9)
            el = time.time() - t_start
            if n_batches == 1 or el - t_last >= 30 or n_done == len(todo):
                t_last = el
                rate = n_done / max(el, 1e-6)
                eta = (len(todo) - n_done) / max(rate, 1e-9)
                log(f"  tiles {n_done}/{len(todo)}  batch={bs}  {rate:.2f} tiles/s  "
                    f"ETA {eta / 60:.1f} min" + (f"  peak GPU mem {peak_mem:.1f} GB" if peak_mem else ""))
    INFO["inference"] = {"final_batch_size": bs, "batches": n_batches, "tiles_run": n_done,
                         "seconds": round(time.time() - t_start, 1),
                         "peak_gpu_mem_gb": round(peak_mem, 2)}
    return mask_pred, mask_count


# =============================================================================
# 5. Main
# =============================================================================
def main():
    log(f"run_canon.py  python {platform.python_version()}  config: "
        + json.dumps({k: v for k, v in CFG.items()}))
    t = time.time()
    ensure_basic_deps()
    torch = ensure_torch()
    import numpy as np
    INFO["timings_s"]["deps"] = round(time.time() - t, 1)
    INFO["versions"] = {"python": platform.python_version(), "torch": torch.__version__,
                        "torch_cuda": torch.version.cuda, "numpy": np.__version__}
    for m in ("tifffile", "cv2", "huggingface_hub", "imagecodecs"):
        try:
            INFO["versions"][m] = importlib.import_module(m).__version__
        except Exception:
            INFO["versions"][m] = None
    if torch.cuda.is_available():
        INFO["gpus"] = [torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())]
    log(f"versions: {INFO['versions']}  gpus: {INFO.get('gpus')}")

    s, e = CFG["start_layer"], CFG["end_layer"]
    if s > e:
        raise ValueError("START_LAYER must be <= END_LAYER")
    if CFG["stride"] > CFG["tile_size"]:
        log(f"WARNING STRIDE ({CFG['stride']}) > TILE_SIZE ({CFG['tile_size']}) may create gaps")
    os.makedirs(CFG["out_dir"], exist_ok=True)

    # ---- layers ----
    t = time.time()
    folder = find_layers_dir()
    paths = list_layers(folder, s, e)
    log(f"using {len(paths)} layers [{s}, {e}) from {folder}: "
        f"{os.path.basename(paths[0])} .. {os.path.basename(paths[-1])}")
    vol = load_volume(paths, parse_crop(CFG["crop"]))
    if CFG["flip_input"]:
        vol = np.ascontiguousarray(vol[:, ::-1, :])
        log("CANON_FLIP_INPUT=1: layers mirrored left-right before inference")
    valid_frac = float((vol.max(axis=2) > 0).mean())
    log(f"volume (H, W, C) = {vol.shape} uint8, {valid_frac * 100:.1f}% of pixels non-zero "
        f"in some layer, mean {float(vol.mean()):.1f}, frac>200 {float((vol > 200).mean()) * 100:.2f}%")
    INFO["input"].update({"layers_dir": folder, "first": os.path.basename(paths[0]),
                          "last": os.path.basename(paths[-1]), "valid_fraction": valid_frac})
    INFO["timings_s"]["read_layers"] = round(time.time() - t, 1)
    if vol.shape[2] != 62:
        log(f"WARNING model was trained with 62 layers; got {vol.shape[2]} (upstream only warns)")

    # ---- model ----
    t = time.time()
    weights = resolve_weights()
    INFO["timings_s"]["weights"] = round(time.time() - t, 1)
    t = time.time()
    torch.backends.cudnn.benchmark = True          # inference.py:37
    try:                                           # entrypoint.py:788-792 (no-op on T4)
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.set_float32_matmul_precision("high")
    except Exception:
        pass
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")   # entrypoint.py:765
    model = load_model(torch, weights, device, num_frames=vol.shape[2])
    INFO["timings_s"]["model_load"] = round(time.time() - t, 1)
    log(f"model ready on {device}")

    # ---- inference ----
    t = time.time()
    mask_pred, mask_count = run_inference(torch, vol, model, device, CFG["reverse"])
    INFO["timings_s"]["inference"] = round(time.time() - t, 1)
    del model, vol
    gc.collect()

    # ---- blend (processing.py:692-695, one partition) ----
    pred = mask_pred / np.clip(mask_count, 1e-6, None)
    pred = np.clip(pred, 0, 1)
    pred_u8 = (pred * 255).astype(np.uint8)                    # upstream truncation
    pred_u16 = np.rint(pred * 65535.0).astype(np.uint16)       # extra: 16-bit export
    covered = mask_count > 0
    INFO["prediction"] = {"hw": list(pred.shape), "covered_fraction": float(covered.mean()),
                          "mean_on_covered": float(pred[covered].mean()) if covered.any() else None,
                          "frac_gt_0.5_on_covered": float((pred[covered] > 0.5).mean()) if covered.any() else None}
    log(f"prediction {pred.shape}: mean on covered pixels {INFO['prediction']['mean_on_covered']}, "
        f">0.5 on {INFO['prediction']['frac_gt_0.5_on_covered']}")

    # ---- write ----
    import cv2
    import tifffile
    if CFG["flip_input"]:
        readable_u8, readable_u16 = pred_u8, pred_u16
        asin_u8, asin_u16 = pred_u8[:, ::-1], pred_u16[:, ::-1]
    else:
        asin_u8, asin_u16 = pred_u8, pred_u16
        readable_u8, readable_u16 = pred_u8[:, ::-1], pred_u16[:, ::-1]
    out = CFG["out_dir"]
    files = {
        "asinput_png": os.path.join(out, "canon_pred_asinput.png"),
        "asinput_tif16": os.path.join(out, "canon_pred_asinput_16bit.tif"),
        "readable_png": os.path.join(out, "canon_pred_readable.png"),
        "readable_tif16": os.path.join(out, "canon_pred_readable_16bit.tif"),
    }
    for key, arr in (("asinput_png", asin_u8), ("readable_png", readable_u8)):
        arr = np.ascontiguousarray(arr)
        if not cv2.imwrite(files[key], arr):
            raise RuntimeError(f"cv2.imwrite failed for {files[key]}")
        back = cv2.imread(files[key], cv2.IMREAD_UNCHANGED)
        if back is None or not np.array_equal(back, arr):
            raise RuntimeError(f"PNG read-back mismatch for {files[key]}")
    for key, arr in (("asinput_tif16", asin_u16), ("readable_tif16", readable_u16)):
        tifffile.imwrite(files[key], np.ascontiguousarray(arr), compression="zlib",
                         metadata={"software": "run_canon.py (optimized_inference mirror)"})
    INFO["outputs"] = files
    INFO["orientation"] = {
        "canon_pred_asinput": "same pixel grid as the input TIF layers (our vc_render_tifxyz "
                              "orientation = mirrored left-right vs the challenge's published layers)",
        "canon_pred_readable": "asinput[:, ::-1]: challenge orientation, text reads the right way",
        "network_saw": "challenge orientation (CANON_FLIP_INPUT=1)" if CFG["flip_input"]
                       else "the input TIFs as-is (mirrored orientation)",
    }
    for k, v in files.items():
        log(f"wrote {v}")
    log("ORIENTATION: canon_pred_asinput.* = same grid as your TIFs (mirrored vs the challenge); "
        "canon_pred_readable.* = flipped back [:, ::-1] (challenge orientation, text reads correctly)")


if __name__ == "__main__":
    status, err = "ok", None
    try:
        main()
    except BaseException as e:  # noqa: BLE001 -- always report, always print CANON_DONE
        status = "FAILED"
        err = f"{type(e).__name__}: {e}"
        traceback.print_exc()
        sys.stderr.flush()
    INFO["status"] = status
    INFO["error"] = err
    INFO["timings_s"]["total"] = round(time.time() - T0, 1)
    try:
        os.makedirs(CFG["out_dir"], exist_ok=True)
        with open(os.path.join(CFG["out_dir"], "canon_run_info.json"), "w") as f:
            json.dump(INFO, f, indent=2, default=str)
    except Exception as e:  # noqa: BLE001
        print(f"could not write canon_run_info.json: {e}", flush=True)
    print(f"CANON_DONE status={status} total={INFO['timings_s']['total']}s"
          + (f" error={err}" if err else "") + f" out={CFG['out_dir']}", flush=True)
    if status != "ok":
        sys.exit(1)
