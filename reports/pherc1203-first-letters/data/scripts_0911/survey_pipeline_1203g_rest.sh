#!/bin/bash
# 1203 NEW-BAND SURVEY, REMAINING SURFACES (12 Sep): the 36 surfaces grown after the first selector run, with the CORRECTED
# transform (affine_1203_v2.json). Only the batches listed in windows_rest.json are rendered (the first 5 batches were done on 11 Sep).
# Per batch of 8: sharp render (109 layers) + coarse (29) -> offset_generic.py -> centred window -> dataset -> Kaggle job.
cd "<run-dir>"; H=https://vesuvius-challenge-open-data.s3.amazonaws.com/
C=PHerc1203/volumes/20250820131727-9.362um-1.2m-113keV-masked.zarr/; F=PHerc1203/volumes/20260319130212-2.403um-0.2m-77keV-masked.zarr/
set -a; source ~/.kaggle/token.env; set +a
NB=$(./venv/bin/python -c "import json; print(max(w['batch'] for w in json.load(open('p1203g_survey/windows_rest.json'))) + 1)")
for k in $(./venv/bin/python -c "import json; print(' '.join(sorted({str(w['batch']) for w in json.load(open('p1203g_survey/windows_rest.json'))}, key=int)))"); do   # only the new batches
  B=kds/p1203gsurvey_b$k; mkdir -p $B; echo "{}" > $B/layer_windows.json
  for d in $(./venv/bin/python -c "import json; print(' '.join(w['name'] for w in json.load(open('p1203g_survey/windows_rest.json')) if w['batch'] == $k))"); do
    t0=$(date +%s); S=p1203g_survey/${d}_S109; Q=p1203g_survey/${d}_C29; rm -rf $S $Q; mkdir -p $S $Q
    villa-src/volume-cartographer/build/bin/vc_render_tifxyz --volume $H$F --remote-url $H$F -s p1203g_survey/$d --affine p1203_fine/affine_1203_v2.json \
       --auto-crop --scale 1 -g 0 --num-slices 109 --slice-step 1 --tif-output $S --timeout 120 --cache-gb 8 > p1203g_survey/$d.sharp.log 2>&1
    villa-src/volume-cartographer/build/bin/vc_render_tifxyz --volume $H$C --remote-url $H$C -s p1203g_survey/$d \
       --auto-crop --scale 1 -g 0 --num-slices 29 --slice-step 1 --tif-output $Q --timeout 120 --cache-gb 4 > p1203g_survey/$d.coarse.log 2>&1
    mkdir -p p1203g_survey/_off_$d; ./venv/bin/python offset_generic.py $Q $S 9.362 2.403 p1203g_survey/_off_$d > p1203g_survey/_off_$d/offset.log 2>&1 || echo "!!! OFFSET FAILED for $d (see _off_$d/offset.log) -> default window"
    ./venv/bin/python - "$d" "$B/layer_windows.json" "p1203g_survey/_off_$d/offset.json" <<"PY"
import json, sys
name, jf, of = sys.argv[1:4]
lw = json.load(open(jf))
try: o = json.load(open(of)); dw = o["dw_fine_layers"]; ncc = o["best_ncc"]
except Exception: dw, ncc = 0.0, None
start = int(round(24 + dw)) if (ncc or 0) > 0.15 else 24      # centred 62-layer window on the measured sheet
if not (ncc or 0) > 0.15: print("!!! FALLBACK default window 24-86 for", name, "(ncc", ncc, ")", flush=True)   # L44: loud, counted below
start = max(0, min(109 - 62, start))
lw[name] = {"start": start, "end": start + 62, "dw_fine_layers": dw, "ncc": ncc}
json.dump(lw, open(jf, "w"), indent=1); print(name, lw[name])
PY
    n=$(ls $S | wc -l)
    if [ $n -eq 109 ]; then tar -cf $B/$d.tar -C p1203g_survey --transform "s,^${d}_S109,$d," ${d}_S109 && rm -rf $S $Q; fi
    echo "b$k $d slices=$n $(( $(date +%s) - t0 ))s"
  done
  echo "{\"title\": \"p1203g survey b$k\", \"id\": \"${KAGGLE_USER}/p1203g-survey-b$k\", \"licenses\": [{\"name\": \"other\"}]}" > $B/dataset-metadata.json
  cp $B/layer_windows.json p1203g_survey/layer_windows_b$k.json
  ./venv/bin/python -c "import json; w = json.load(open('$B/layer_windows.json')); f = [n for n, v in w.items() if not (v['ncc'] or 0) > 0.15]; print('b$k depth-corrected', len(w) - len(f), 'of', len(w), '| FALLBACKS:', len(f), f)"
  timeout 1800 ./kagenv/bin/kaggle datasets create -p $B 2>&1 | tail -1
  s=""; for i in $(seq 1 60); do s=$(./kagenv/bin/kaggle datasets status ${KAGGLE_USER}/p1203g-survey-b$k 2>&1 | tail -1); [ "$s" = "ready" ] && break; sleep 20; done
  echo "b$k dataset status: $s"
  if [ "$s" = "ready" ]; then rm -f $B/*.tar; ./venv/bin/python make_survey_nb_1203g.py $k && for try in $(seq 1 12); do   # retry: 2 GPU sessions per account
    r=$(timeout 300 ./kagenv/bin/kaggle kernels push -p kag/s1203g_b$k --accelerator NvidiaTeslaT4 2>&1 | tail -1); echo "push try $try: $r"
    echo "$r" | /usr/bin/grep -q "successfully pushed" && break; sleep 300; done; fi
  echo "BATCH_DONE b$k $(date +%H:%M:%S)"; df -h ~ | tail -1
done
echo "SURVEY1203G_REST_DONE $(date +%H:%M:%S)"
