"""Redraw ctl_curve.png from ctl_curve.json: AUC against the depth window, forward and reversed.

usage: python depth/plot_ctl_curve.py depth/ctl_curve.json out.png

Needs matplotlib, which the tool itself does not, so it is not in requirements.txt. The picture is
committed, so nobody has to run this to see it."""
import json, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

curve = json.load(open(sys.argv[1]))
rows = sorted(curve["rows"], key=lambda r: r["start"])
x = [r["start"] + 10 for r in rows]                       # window centre, in layers of the 101-slice render
auc_f = [r.get("auc_forward") for r in rows]
auc_r = [r.get("auc_reverse") for r in rows]
ink = [r.get("share_on_ink_forward") for r in rows]
bg = [r.get("share_on_bg_forward") for r in rows]

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(7.6, 6.6), sharex=True, height_ratios=[1.25, 1])
ax1.axhline(0.5, color="0.75", lw=1, ls=":")
ax1.plot(x, auc_f, "o-", color="#1b5e20", lw=2, label="forward (the official depth order)")
ax1.plot(x, auc_r, "s--", color="#9e9e9e", lw=1.4, label="reverse")
ax1.axvline(50, color="#1565c0", lw=1, ls="--")
ax1.annotate("the peak, layers 40 to 61", xy=(50, max(v for v in auc_f if v)), xytext=(58, 0.80),
             color="#1565c0", fontsize=9, arrowprops=dict(arrowstyle="->", color="#1565c0", lw=1))
ax1.set_ylabel("reads the writing (pixel AUC)")
ax1.set_ylim(0.3, 1.0)
ax1.legend(loc="lower left", fontsize=9, frameon=False)
ax1.set_title("Known text at 9.362 um: what the ink model answers when shown different layers\n"
              "PHerc0139 w016, ink_9um seed43 step-060000, 21-layer window slid through a 101-layer render",
              fontsize=9.5, loc="left")

ax2.plot(x, [100 * v if v is not None else None for v in ink], "o-", color="#1b5e20", lw=2, label="called ink ON the labelled writing")
ax2.plot(x, [100 * v if v is not None else None for v in bg], "^-", color="#c62828", lw=1.6, label="called ink on labelled BACKGROUND")
ax2.axvline(50, color="#1565c0", lw=1, ls="--")
ax2.set_xlabel("centre of the 21-layer window, in layers of the render (1 layer = 9.362 um)")
ax2.set_ylabel("% of pixels called ink")
ax2.legend(loc="upper right", fontsize=9, frameon=False)
for ax in (ax1, ax2):
    ax.grid(alpha=0.25)
    ax.set_xticks(x)
fig.tight_layout()
fig.savefig(sys.argv[2], dpi=150)
print("wrote", sys.argv[2])
