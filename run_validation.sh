#!/bin/bash
# The validation batch behind the README table: the twelve pairs in pairs.txt, each against the
# official transform in the open-data metadata.json, plus the two held-out image checks.
# Reads about 15 GB from the public bucket in total and takes a few hours on 8 cores.
# Usage:  bash run_validation.sh [pairs.txt]        (set PY=... to choose an interpreter)
cd "$(dirname "$0")"
PY=${PY:-python3}
PAIRS=${1:-pairs.txt}
OUTROOT=${OUTROOT:-runs}
mkdir -p "$OUTROOT"
while read -r TAG SAMPLE MOV FIX; do
  [[ -z "$TAG" || "$TAG" == \#* ]] && continue
  OUT=$OUTROOT/$TAG; mkdir -p "$OUT"
  echo "=== $TAG $(date '+%F %T %Z')" | tee -a "$OUTROOT/batch.log"
  $PY scroll_lineup.py "$MOV" "$FIX" --out "$OUT" > "$OUT/log.txt" 2>&1
  echo "scroll-lineup exit $? $(date '+%T')" | tee -a "$OUTROOT/batch.log"
  grep -E "CONFIDENCE|wrote" "$OUT/log.txt" | tee -a "$OUTROOT/batch.log"
  MID=$(basename "$MOV"); MID=${MID%%-*}; FID=$(basename "$FIX"); FID=${FID%%-*}
  if [ -f "$OUT/transform.json" ]; then
    $PY validate.py "$SAMPLE" "$MID" "$FID" "$OUT/transform.json" --out "$OUT/validation.json" > "$OUT/validation.txt" 2>&1
    echo "validate exit $?" | tee -a "$OUTROOT/batch.log"
    grep -E "median_um|p95_um|max_um|landmarks" "$OUT/validation.txt" | tee -a "$OUTROOT/batch.log"
    $PY datacheck.py "$MOV" "$FIX" ours=$OUT/transform.json official=$OUT/official_transform.json \
        --out $OUT/datacheck_heldout.json --radius 10 > $OUT/datacheck_heldout.txt 2>&1
    $PY datacheck.py "$MOV" "$FIX" official=$OUT/official_transform.json ours=$OUT/transform.json \
        --at-landmarks official --out $OUT/datacheck_landmarks.json --radius 10 > $OUT/datacheck_landmarks.txt 2>&1
    grep -hv Warn $OUT/datacheck_heldout.txt $OUT/datacheck_landmarks.txt | sed 's/^/  dc /' | tee -a "$OUTROOT/batch.log"
  fi
done < "$PAIRS"
echo "=== BATCH DONE $(date '+%F %T %Z')" | tee -a "$OUTROOT/batch.log"
echo "Table:  $PY summarize.py $OUTROOT/*/ > table.md"
