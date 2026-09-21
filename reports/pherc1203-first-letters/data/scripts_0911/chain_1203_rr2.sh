#!/bin/bash
# One-off (Kaden approved 12 Sep 09:42): hand-test the corrected 1203 transform on one window (L44 gate), then re-render the
# top 8 original-survey windows with it. Gate: |dw_fine_layers| <= 4 and ncc > 0.3 on the test window; else abort loudly.
cd "<run-dir>"
./test_offset_1203v2.sh auto_grown_20250930104534929_s_r42_c126 > test_offset_1203v2.log 2>&1
g=$(./venv/bin/python -c "
import json; o = json.load(open('p1203v2_test/_off_win/offset.json')); print('PASS' if abs(o['dw_fine_layers']) <= 4 and o['best_ncc'] > 0.3 else 'FAIL', round(o['dw_fine_layers'], 1), round(o['best_ncc'], 2))" 2>&1)
echo "GATE $g $(date -u +%H:%M)"; rm -rf p1203v2_test/win_S109 p1203v2_test/win_C29
case "$g" in PASS*) ./survey_pipeline_1203_rr2.sh > survey_pipeline_1203_rr2.log 2>&1; echo "CHAIN_DONE $(date -u +%H:%M) | $(tail -1 survey_pipeline_1203_rr2.log)";;
  *) echo "CHAIN_ABORT: corrected transform failed the hand test ($g) $(date -u +%H:%M)";; esac
