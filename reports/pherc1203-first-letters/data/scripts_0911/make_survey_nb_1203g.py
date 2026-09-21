"""Make the Kaggle notebook for the 1203 new-surface survey batch K: run_canon on every window folder of dataset <kaggle-user>/p1203g-survey-bK
(109-layer renders), each window with its own centred 62-layer window from layer_windows.json (default 24-85), C as rendered and D reversed, 2 GPUs."""
import json, sys, os
k = int(sys.argv[1]); R = "<run-dir>"; D = f"{R}/kag/s1203g_b{k}"; os.makedirs(D, exist_ok=True)
src = open(f"{R}/run_canon_cal.py").read()
cell1 = r'''import os, glob, tarfile, subprocess, time, json, re
t0 = time.time()
for t in sorted(glob.glob("/kaggle/input/**/*.tar", recursive=True)):
    tarfile.open(t).extractall("/tmp/x"); print("extracted", t, flush=True)
def nlayers(d): return sum(1 for f in os.listdir(d) if re.fullmatch(r"\d+\.tif", f))
dirs = sorted({d.rstrip("/") for d in glob.glob("/kaggle/input/**/", recursive=True) + glob.glob("/tmp/x/**/", recursive=True) if os.path.isdir(d) and nlayers(d) >= 100})
wins = {}
for d in dirs: wins.setdefault(os.path.basename(d), d)
names = sorted(wins); print(len(names), "windows", flush=True)
LW = {}
for f in glob.glob("/kaggle/input/**/layer_windows.json", recursive=True): LW.update(json.load(open(f)))
print("layer windows:", LW, flush=True)
def senses(n):
    st, en = str(LW.get(n, {}).get("start", 24)), str(LW.get(n, {}).get("end", 86))
    return {"C": {"CANON_START_LAYER": st, "CANON_END_LAYER": en}, "D": {"CANON_START_LAYER": st, "CANON_END_LAYER": en, "CANON_REVERSE": "1"}}
SENSES = {"C": None, "D": None}
jobs = [(n, s) for n in names for s in SENSES]; summary = {}
def launch(n, s, gpu, extra):
    out = f"/kaggle/working/{n}/{s}"; os.makedirs(out, exist_ok=True)
    env = dict(os.environ, CANON_LAYERS_DIR=wins[n], CANON_OUT_DIR=out, CUDA_VISIBLE_DEVICES=str(gpu), **senses(n)[s], **extra)
    return subprocess.Popen(["python", "-u", "/kaggle/working/run_canon.py"], env=env, stdout=open(f"{out}/run.log", "w"), stderr=subprocess.STDOUT), out
def collect(n, s, out, rc):
    txt = open(f"{out}/run.log").read(); m = re.search(r"mean on covered pixels ([0-9.eE+-]+), >0.5 on ([0-9.eE+-]+)", txt)
    summary[f"{n}/{s}"] = {"exit": rc, "mean": float(m.group(1)) if m else None, "frac_gt_0.5": float(m.group(2)) if m else None}
    print(n, s, summary[f"{n}/{s}"], f"[{time.time()-t0:.0f}s]", flush=True); json.dump(summary, open("/kaggle/working/survey_summary.json", "w"), indent=1)
n, s = jobs[0]; p, out = launch(n, s, 0, {}); collect(n, s, out, p.wait())
ck = sorted(glob.glob("/tmp/canon_models/**/*.ckpt", recursive=True)); extra = {"CANON_CKPT_PATH": ck[0]} if ck else {}
pending = jobs[1:]; running = {}
while pending or running:
    for g in (0, 1):
        if g not in running and pending:
            n, s = pending.pop(0); p, out = launch(n, s, g, extra); running[g] = (p, n, s, out)
    time.sleep(5)
    for g, (p, n, s, out) in list(running.items()):
        if p.poll() is not None: collect(n, s, out, p.returncode); del running[g]
print("ALL_DONE", f"[{time.time()-t0:.0f}s]", flush=True)
'''
nb = {"cells": [{"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": ["%%writefile /kaggle/working/run_canon.py\n" + src]},
                {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": [cell1]}],
      "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}}, "nbformat": 4, "nbformat_minor": 4}
json.dump(nb, open(f"{D}/nb.ipynb", "w"))
json.dump({"id": f"<kaggle-user>/vesuvius-s1203g-b{k}", "title": f"vesuvius s1203g b{k}", "code_file": "nb.ipynb", "language": "python", "kernel_type": "notebook",
           "is_private": True, "enable_gpu": True, "enable_internet": True, "dataset_sources": [f"<kaggle-user>/p1203g-survey-b{k}"],
           "competition_sources": [], "kernel_sources": []}, open(f"{D}/kernel-metadata.json", "w"), indent=1)
print("notebook", D)
