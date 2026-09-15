#!/usr/bin/env python3
"""summarize.py - one markdown table from runs*/<tag>/{report,validation,datacheck_*}.json.
Verdict rules were fixed before the first validation run (PREREG_0912.md): p95 error vs the official transform
<= 30 um PASS, <= 150 um WEAK, else FAIL.
Usage: python summarize.py results/v2_0139a results/v3_0009B ... > table.md"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from validate import load_meta, official  # noqa: E402
from scroll_lineup import decompose  # noqa: E402


def verdict(p95):
    if p95 is None:
        return "FAIL (no answer)"
    return "PASS" if p95 <= 30 else ("WEAK" if p95 <= 150 else "FAIL")


def dc(d, name):
    p = os.path.join(d, name)
    if not os.path.exists(p):
        return None
    r = json.load(open(p))["results"]
    o, f = r.get("ours", {}), r.get("official", {})
    if o.get("median_move_um") is None or f.get("median_move_um") is None:
        return f"n={o.get('n_common', 0)}"
    return f"{o['median_move_um']:.0f} / {f['median_move_um']:.0f} (n={o['n_common']})"


def main():
    meta = load_meta(os.environ.get("META"))  # unset: fetch metadata.json from the public bucket
    print("| run | scroll: moving -> fixed (um) | official geometry | G2 score: winner / runner-up | confidence | "
          "error vs official: median / p95 / max um | verdict | at official landmarks: ours / official RMS um | "
          "held-out image blocks must move: ours / official (median um) | image blocks at the official landmarks must move: ours / official (median um) | tool | min | MB |")
    print("|" + "---|" * 13)
    for d in sys.argv[1:]:
        tag = os.path.basename(d.rstrip("/"))
        rep = json.load(open(os.path.join(d, "report.json")))
        vp = os.path.join(d, "validation.json")
        val = json.load(open(vp)) if os.path.exists(vp) else None
        vm, vf = rep["volumes"]["moving"], rep["volumes"]["fixed"]
        sample = val["sample"] if val else "?"
        mid, fid = vm["url"].rstrip("/").split("/")[-1].split("-")[0], vf["url"].rstrip("/").split("/")[-1].split("-")[0]
        try:
            Toff, *_ = official(meta, sample, mid, fid)
            og = decompose(Toff[:3, :3] * vf["um"] / vm["um"])
            geo = (f"rot {og['rot_deg']:.0f}, tilt {og['tilt_deg']:.1f}" + (", mirror" if og["improper"] else "") +
                   (", upside down" if og["z_axis_flipped"] else ""))
        except SystemExit:
            geo = "-"
        res = rep.get("g2", {}).get("results", [])
        g2 = f"{res[0]['score']:.2f} / {res[1]['score']:.2f}" if len(res) > 1 else "-"
        conf = rep.get("confidence", {}).get("level", "(v0.1: none)")
        e = val["error"] if val else None
        err = f"{e['median_um']:.0f} / {e['p95_um']:.0f} / {e['max_um']:.0f}" if e else "-"
        lm = val.get("landmarks") if val else None
        lms = f"{lm['ours_rms_um']:.0f} / {lm['official_rms_um']:.0f} (n={lm['n']})" if lm else "-"
        print(f"| {tag} | {sample}: {vm['um']} -> {vf['um']} | {geo} | {g2} | {conf} | {err} | "
              f"{verdict(e['p95_um'] if e else None)} | {lms} | {dc(d, 'datacheck_heldout.json') or '-'} | "
              f"{dc(d, 'datacheck_landmarks.json') or '-'} | {rep.get('version')} | {rep.get('seconds', 0) / 60:.1f} | "
              f"{rep.get('downloaded_MB', 0):.0f} |")


if __name__ == "__main__":
    main()
