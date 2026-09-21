"""Published matrix against the best affine fit to its own landmarks, for every catalogue transform
that publishes landmarks. Reads only audit/results.txt (written by audit_landmarks.py from the public
catalogue); writes landmark_fit.png next to it.

  python3 plot_landmark_fit.py [results.txt] [out.png]
"""
import os, re, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "results.txt")
out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "landmark_fit.png")
rows = []
for line in open(src):
    c = [x.strip() for x in line.strip().strip("|").split("|")]
    if len(c) == 6 and re.match(r"^[\d.]+", c[3].replace("*", "").strip()):
        rows.append(dict(obj=c[0].replace("*", "").strip(), pair=c[1], n=int(c[2]),
                         rms=float(c[3].replace("*", "")), best=float(c[5].replace("*", ""))))
assert len(rows) == 25, len(rows)
off = [r for r in rows if r["rms"] - r["best"] > 1.0]           # published matrix is not the fit
assert len(off) == 1, off

fig, ax = plt.subplots(figsize=(7.5, 6.2), dpi=150)
top = 135
ax.plot([0, top], [0, top], color="#999999", lw=1, zorder=1,
        label="on this line, the published matrix is already the best fit")
on = [r for r in rows if r not in off]
ax.scatter([r["best"] for r in on], [r["rms"] for r in on], s=34, color="#4c72b0", zorder=3,
           label="24 transforms: published matrix = best fit (within 0.1 um)")
o = off[0]
ax.scatter([o["best"]], [o["rms"]], s=80, color="#c44e52", zorder=4, label="the one that is not")
ax.annotate("%s %s um\npublished matrix misses its landmarks by %.1f um\nthe best fit to the same %d landmarks: %.1f um"
            % (o["obj"], o["pair"], o["rms"], o["n"], o["best"]),
            xy=(o["best"], o["rms"]), xytext=(18, 108), fontsize=9, color="#c44e52",
            arrowprops=dict(arrowstyle="->", color="#c44e52", lw=1))
for r in sorted(on, key=lambda r: -r["rms"])[:3]:
    ax.annotate("%s %s" % (r["obj"], r["pair"]), xy=(r["best"], r["rms"]), xytext=(6, -12),
                textcoords="offset points", fontsize=7.5, color="#333333")
ax.set_xlim(0, top); ax.set_ylim(0, top)
ax.set_xlabel("best affine fit to the transform's own landmarks, RMS (um)")
ax.set_ylabel("published matrix, RMS at its own landmarks (um)")
ax.set_title("25 catalogue transforms that publish landmarks", fontsize=11)
ax.legend(loc="lower right", fontsize=8, frameon=False)
ax.text(0.99, -0.13, "data: audit/results.txt in kadenpool/scroll-lineup, from the catalogue's metadata.json",
        transform=ax.transAxes, fontsize=7, color="#777777", ha="right")
fig.tight_layout()
fig.savefig(out)
print("wrote %s: %d transforms, outlier %s %s (%.1f vs %.1f um)" % (out, len(rows), o["obj"], o["pair"], o["rms"], o["best"]))
