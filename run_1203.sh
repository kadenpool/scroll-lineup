#!/bin/bash
# The README's worked example: PHerc1203 (no official transform exists for this pair).
# 1. scroll-lineup on the 2.403 um scan onto the 9.362 um scan  (~200 s, ~1.3 GB read)
# 2. compare1203.py against the two public PHerc1203 registrations, fetched from their own repos
#    (~4 min more, reads another ~1 GB for the held-out image check)
# Usage:  bash run_1203.sh            (set PY=... to choose an interpreter, OUT=... for the folder)
set -e
cd "$(dirname "$0")"
PY=${PY:-python3}
OUT=${OUT:-out_1203}; mkdir -p "$OUT"
B=s3://vesuvius-challenge-open-data/PHerc1203/volumes

$PY scroll_lineup.py $B/20260319130212-2.403um-0.2m-77keV-masked.zarr \
                     $B/20250820131727-9.362um-1.2m-113keV-masked.zarr \
                     --out "$OUT" --write-inverse > "$OUT/log.txt" 2>&1
echo "scroll-lineup exit $?"; grep -E "CONFIDENCE|wrote" "$OUT/log.txt"

# The two public transforms for this pair, from their authors' repositories (about 1 MB together).
mkdir -p _public1203
[ -f _public1203/flummox.json ] || curl -fsSL -o _public1203/flummox.json \
  https://raw.githubusercontent.com/flummoxjr/measure-before-you-hunt/master/hunt/pherc1203_2403um_to_9362um.json
[ -f _public1203/seven_pass3_final.npz ] || curl -fsSL -o _public1203/seven_pass3_final.npz \
  https://raw.githubusercontent.com/7jycwjmbfn-eng/pherc0139-physical-audit/master/results/1203/pass3_final.npz

$PY compare1203.py "$OUT/transform.json" _public1203/flummox.json _public1203/seven_pass3_final.npz \
    --out "$OUT/compare1203.json" --datacheck > "$OUT/compare1203.txt" 2>&1
echo "compare exit $?"; grep -v Warn "$OUT/compare1203.txt"
