#!/bin/bash
# Survey pipeline, one batch at a time: render (63 layers, affine_1203.json) -> tar -> private dataset -> wait READY ->
# remove the batch's local tars (verified copy on Kaggle; keeps box A disk use ~3 GB) -> push the batch's GPU job.
cd; H=https://vesuvius-challenge-open-data.s3.amazonaws.com/; Zv=PHerc1203/volumes/20260319130212-2.403um-0.2m-77keV-masked.zarr/
set -a; source ~/.kaggle/token.env; set +a
NB=$(./venv/bin/python -c "import json; print(max(w['batch'] for w in json.load(open('p1203_survey/windows.json'))) + 1)")
for k in $(seq 0 $((NB - 1))); do
  B=kds/p1203survey_b$k; mkdir -p $B
  for d in $(./venv/bin/python -c "import json; print(' '.join(w['name'] for w in json.load(open('p1203_survey/windows.json')) if w['batch'] == $k))"); do
    [ -f $B/$d.tar ] && continue
    t0=$(date +%s); out=p1203_survey/${d}_L0_63; rm -rf $out; mkdir -p $out
    villa-src/volume-cartographer/build/bin/vc_render_tifxyz --volume $H$Zv --remote-url $H$Zv -s p1203_survey/$d --affine p1203_fine/affine_1203.json \
       --auto-crop --scale 1 -g 0 --num-slices 63 --slice-step 1 --tif-output $out --timeout 120 --cache-gb 8 > p1203_survey/$d.render.log 2>&1
    rc=$?; n=$(ls $out | wc -l)
    if [ $rc -eq 0 ] && [ $n -eq 63 ]; then tar -cf $B/$d.tar -C p1203_survey --transform "s,^${d}_L0_63,$d," ${d}_L0_63 && rm -rf $out; fi
    echo "b$k $d rc=$rc slices=$n $(( $(date +%s) - t0 ))s"
  done
  echo "{\"title\": \"p1203 survey b$k\", \"id\": \"<kaggle-user>/p1203-survey-b$k\", \"licenses\": [{\"name\": \"other\"}]}" > $B/dataset-metadata.json
  timeout 1800 ./kagenv/bin/kaggle datasets create -p $B 2>&1 | tail -1
  s=""; for i in $(seq 1 60); do s=$(./kagenv/bin/kaggle datasets status <kaggle-user>/p1203-survey-b$k 2>&1 | tail -1); [ "$s" = "ready" ] && break; sleep 20; done
  echo "b$k dataset status: $s"
  if [ "$s" = "ready" ]; then rm -f $B/*.tar; ./venv/bin/python make_survey_nb.py $k && timeout 300 ./kagenv/bin/kaggle kernels push -p kag/survey_b$k --accelerator NvidiaTeslaT4 2>&1 | tail -1; fi
  echo "BATCH_DONE b$k $(date +%H:%M:%S)"; df -h ~ | tail -1
done
echo "SURVEY_PIPELINE_DONE $(date +%H:%M:%S)"
