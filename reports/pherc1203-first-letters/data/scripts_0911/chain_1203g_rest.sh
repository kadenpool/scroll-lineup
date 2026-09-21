#!/bin/bash
# One-off (12 Sep 16:45): survey the 1203 new-band surfaces grown after the first selector run (36 of 60 never surveyed), with the
# corrected transform. Selector appends to windows.json (skips surveyed segments); the new windows (batch >= 5) go to
# windows_rest.json; the rest pipeline renders only those batches. Aborts loudly on a selector crash or zero new windows.
cd "<run-dir>"
n0=$(./venv/bin/python -c "import json; print(len(json.load(open('p1203g_survey/windows.json'))))")
./venv/bin/python survey_sel_1203g.py > survey_sel_1203g_rest.log 2>&1
/usr/bin/grep -q Traceback survey_sel_1203g_rest.log && { echo "CHAIN_ABORT selector crashed $(date -u +%H:%M)"; exit 1; }
./venv/bin/python - "$n0" <<'PY'
import json, sys
n0 = int(sys.argv[1]); w = json.load(open("p1203g_survey/windows.json")); rest = w[n0:]
json.dump(rest, open("p1203g_survey/windows_rest.json", "w"), indent=1)
print("new windows:", len(rest), "on", len({x["segment"] for x in rest}), "surfaces; batches", sorted({x["batch"] for x in rest}))
PY
nr=$(./venv/bin/python -c "import json; print(len(json.load(open('p1203g_survey/windows_rest.json'))))")
[ "$nr" -gt 0 ] || { echo "CHAIN_DONE nothing new to survey $(date -u +%H:%M)"; exit 0; }
./survey_pipeline_1203g_rest.sh > survey_pipeline_1203g_rest.log 2>&1
echo "CHAIN_DONE $(date -u +%H:%M) | $(tail -1 survey_pipeline_1203g_rest.log)"
