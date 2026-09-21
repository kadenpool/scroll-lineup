#!/bin/bash
# PHerc1203 (no official transform): scanreg, then the comparison with the two public transforms + image data check.
cd "$(dirname "$0")"
PY=${PY:-../venv/bin/python}
B=s3://vesuvius-challenge-open-data/PHerc1203/volumes
OUT=runs2/f1203; mkdir -p $OUT
$PY scanreg.py $B/20260319130212-2.403um-0.2m-77keV-masked.zarr $B/20250820131727-9.362um-1.2m-113keV-masked.zarr \
    --out $OUT --write-inverse > $OUT/log.txt 2>&1
echo "scanreg exit $?"; grep -E "CONFIDENCE|wrote" $OUT/log.txt
$PY compare1203.py $OUT/transform.json _public1203/flummox_pherc1203_2403um_to_9362um.json _public1203/seven_pass3_final.npz \
    --out $OUT/compare1203.json --datacheck > $OUT/compare1203.txt 2>&1
echo "compare exit $?"; grep -v Warn $OUT/compare1203.txt
