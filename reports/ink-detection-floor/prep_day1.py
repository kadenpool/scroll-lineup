"""Day 1 of the ink detection floor (PREREG.md): choose every window by the pre-registered rules, before any run.

  python3 prep_day1.py      # writes day1/{windows.json,masks.npz} beside this file

Version 2 (22 Sep, after the first independent review): every window is on a PHerc0139 segment whose native 9.362 um
scan is NOT in ink_9um's training data (the dataset card's native9 set is w035, w039, w040, w041 and w044 only).
Donor letters come from the team's published 2.4 um ink map, carried onto each 9.362 um window through the voxel ratio
plus a shift measured by matching the two scans' own surface images. Every core must show a clear papyrus sheet near
the middle of its 28 layers, and intact papyrus there (no large holes). Nothing here looks at any ink-model output of
ours.
"""
import io, json, os, re, ssl, sys, time, urllib.error, urllib.request, gzip
from concurrent.futures import ThreadPoolExecutor
import numpy as np, zarr
from PIL import Image
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "day1")
BUCKET = "vesuvius-challenge-open-data"
HTTP = "https://%s.s3.us-east-1.amazonaws.com/" % BUCKET
SCAN9, SCAN2 = "20250728140407", "20260102150214"
SV = "surface-volumes/9.362um-1.2m-113keV-volume-%s.zarr" % SCAN9
SV2 = "surface-volumes/2.399um-0.22m-78keV-volume-%s.zarr" % SCAN2
SEED, WIN, CORE = 20260922, 1024, 512
NATIVE9_TRAINED = {"w035", "w039", "w040", "w041", "w044"}          # ink_9um dataset card, native9 set
DONOR_SEGS, TARGET_SEGS = ("w025", "w026", "w027"), ("w036", "w042", "w045", "w046")
N_DONOR_PER_SEG, N_TARGET_PER_SEG = 2, 3
TEXT_SHARE, BLANK_SHARE = (0.15, 0.45), 0.005
BLANK_MARGIN = 16                    # 9.362 um px round a blank core that must be blank too, at its own measured shift
SHEET_LAYERS, SHEET_PROMINENCE = (10, 17), 7.0          # PREREG section 4
FLAT_MAX = 0.03                      # PREREG section 4: at most 3 % of the sheet plane without papyrus texture
F9_TO_L3 = 9.362 / (2.399 * 8)                                    # 9.362 um px -> the 2.399 um canvas at 1/8
Image.MAX_IMAGE_PIXELS = None
try:
    import certifi
    CTX = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    CTX = ssl.create_default_context()


def get(url, tries=6):
    """GET with retries for what the bucket answers when busy (5xx, dropped connections); a 4xx is final."""
    for i in range(tries):
        try:
            return urllib.request.urlopen(url, timeout=120, context=CTX).read()
        except urllib.error.HTTPError as e:
            if e.code < 500 or i == tries - 1:
                raise
        except (urllib.error.URLError, ConnectionError, TimeoutError, OSError):
            if i == tries - 1:
                raise
        time.sleep(2 * (i + 1))


def head_etag(url):
    req = urllib.request.Request(url, method="HEAD")
    return urllib.request.urlopen(req, timeout=60, context=CTX).headers.get("ETag", "").strip('"')


CATALOG_URL = "https://vesuvius-challenge-open-data.s3.amazonaws.com/metadata.json"
cat = json.loads(gzip.decompress(get(CATALOG_URL)))
SEG = {}
for sg in cat["samples"]["PHerc0139"]["segments"].values():
    m = re.search(r"-(w\d+)_", sg.get("long_id", ""))
    if m:
        SEG[m.group(1)] = "PHerc0139/segments/%s/" % sg["long_id"]


def listing(prefix):
    x = get(HTTP + "?list-type=2&prefix=" + urllib.request.quote(prefix)).decode()
    return re.findall(r"<Key>([^<]+)</Key>", x)


def arr(prefix, sv, level):
    try:
        return zarr.open_array("s3://%s/%s%s/%s" % (BUCKET, prefix, sv, level), mode="r", storage_options={"anon": True})
    except TypeError:       # an s3fs too old for zarr 3's async stores (Kaggle's image on 24 Sep): the same public
        return zarr.open_array("%s%s%s/%s" % (HTTP, prefix, sv, level), mode="r")   # array, read over HTTPS


def chunk(url):
    try:
        return get(url)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise


def read_box(prefix, box):
    """28 x h x w uint8 from the 9.362 um surface volume (zarr v2, uncompressed 28 x 128 x 128 chunks)."""
    y0, y1, x0, x1 = box
    base = f"{HTTP}{prefix}{SV}/0"
    cy, cx = range(y0 // 128, (y1 - 1) // 128 + 1), range(x0 // 128, (x1 - 1) // 128 + 1)
    keys = [(a, b) for a in cy for b in cx]
    with ThreadPoolExecutor(16) as ex:
        blobs = list(ex.map(lambda ab: chunk(f"{base}/0/{ab[0]}/{ab[1]}"), keys))
    out = np.zeros((28, len(cy) * 128, len(cx) * 128), np.uint8)
    for (a, b), blob in zip(keys, blobs):
        if blob is not None:
            out[:, (a - cy[0]) * 128:(a - cy[0] + 1) * 128, (b - cx[0]) * 128:(b - cx[0] + 1) * 128] = \
                np.frombuffer(blob, np.uint8).reshape(28, 128, 128)
    oy, ox = y0 - cy[0] * 128, x0 - cx[0] * 128
    return out[:, oy:oy + (y1 - y0), ox:ox + (x1 - x0)]


def sheet(v):
    """The layer where the papyrus sheet sits (peak of the mean-intensity profile) and how clear it is."""
    prof = ndimage.uniform_filter1d(v.reshape(v.shape[0], -1).mean(1).astype(np.float32), 3)
    pk = int(np.argmax(prof))
    return pk, float(prof[pk] - np.median(prof)), [round(float(p), 1) for p in prof]


def flat_share(v, pk):
    """Share of the sheet plane with almost no texture: air in a crack or gap, which the ink map calls blank. Local
    standard deviation over 9 px under a quarter of the plane's median local standard deviation."""
    pl = v[pk].astype(np.float32)
    m1, m2 = ndimage.uniform_filter(pl, 9), ndimage.uniform_filter(pl * pl, 9)
    ls = np.sqrt(np.maximum(m2 - m1 * m1, 0))
    return float((ls < 0.25 * np.median(ls)).mean())


def published(w):
    key = [k for k in listing(SEG[w] + "ink-detection/downsampled/") if "2.399um" in k and "new_canon" in k]
    if len(key) != 1:
        raise SystemExit("%s: expected one downsampled 2.399 um new_canon map, found %d" % (w, len(key)))
    url = HTTP + key[0]
    return np.asarray(Image.open(io.BytesIO(get(url))).convert("L")).astype(np.float32) / 255, key[0], head_etag(url)


def match_offset(ref, small, m):
    """Where `small` sits inside `ref` (which has m px of margin all round): a correlation search at 2 px steps, then
    1 px steps around the best, then a parabola through the peak on each axis for the sub-pixel part."""
    def r_at(dy, dx):
        c = ref[m + dy:m + dy + small.shape[0], m + dx:m + dx + small.shape[1]]
        return float(np.corrcoef(c.ravel(), small.ravel())[0, 1]) if c.shape == small.shape else -2.0
    coarse = max(((r_at(dy, dx), dy, dx) for dy in range(-m, m + 1, 2) for dx in range(-m, m + 1, 2)))
    fine = max(((r_at(dy, dx), dy, dx) for dy in range(coarse[1] - 2, coarse[1] + 3)
                for dx in range(coarse[2] - 2, coarse[2] + 3) if abs(dy) < m and abs(dx) < m))
    r, dy, dx = fine
    def vertex(a, b, c):                                  # peak of the parabola through (-1, a), (0, b), (1, c)
        den = a - 2 * b + c
        return 0.0 if den >= 0 else float(np.clip(0.5 * (a - c) / den, -0.5, 0.5))
    sy = vertex(r_at(dy - 1, dx), r, r_at(dy + 1, dx))
    sx = vertex(r_at(dy, dx - 1), r, r_at(dy, dx + 1))
    return r, dy + sy, dx + sx


def register(w, box9):
    """Shift (dy, dx), in 9.362 um px, that carries the 1/8 2.399 um canvas onto this 9.362 um window, found by
    matching the two scans' own surface planes (9.362 plane 14 against 2.399 level 3, middle plane 54)."""
    y0, y1, x0, x1 = box9
    p9 = read_box(SEG[w], box9)[14].astype(np.float32)
    small = ndimage.zoom(p9, F9_TO_L3, order=1)
    a3 = arr(SEG[w], SV2, 3)
    m = 24
    ly0, lx0 = int(round(y0 * F9_TO_L3)) - m, int(round(x0 * F9_TO_L3)) - m
    ly1, lx1 = ly0 + small.shape[0] + 2 * m, lx0 + small.shape[1] + 2 * m
    if ly0 < 0 or lx0 < 0 or ly1 > a3.shape[1] or lx1 > a3.shape[2]:
        return None
    ref = np.asarray(a3[54, ly0:ly1, lx0:lx1]).astype(np.float32)
    r, ty, tx = match_offset(ref, small, m)
    # the window's first pixel sits at level-3 coordinate round(y0 * F) + ty; express the shift in 9.362 um px
    ty += round(y0 * F9_TO_L3) - y0 * F9_TO_L3
    tx += round(x0 * F9_TO_L3) - x0 * F9_TO_L3
    return {"r": r, "shift_l3": [float(ty), float(tx)], "shift_9": [float(ty / F9_TO_L3), float(tx / F9_TO_L3)]}


def map_on_window(pub, box9, shift9):
    """The published map, sampled on the 9.362 um window's pixel grid (voxel ratio, shared origin, plus the shift)."""
    y0, y1, x0, x1 = box9
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    return ndimage.map_coordinates(pub, [(yy + shift9[0]) * F9_TO_L3, (xx + shift9[1]) * F9_TO_L3], order=1, mode="constant")


def candidates(w, pub, want):
    H, W = arr(SEG[w], SV, 0).shape[1:]
    plane = np.asarray(arr(SEG[w], SV, 3)[14]) > 0
    gy, gx = plane.shape[0] / H, plane.shape[1] / W
    out = []
    for y in range(0, H - CORE + 1, 64):
        for x in range(0, W - CORE + 1, 64):
            p = pub[int(y * F9_TO_L3):int((y + CORE) * F9_TO_L3), int(x * F9_TO_L3):int((x + CORE) * F9_TO_L3)]
            v = plane[int(y * gy):int((y + CORE) * gy), int(x * gx):int((x + CORE) * gx)]
            if not (p.size and v.size and v.mean() >= 0.99):
                continue
            share = float((p > 0.5).mean())
            if want == "blank":
                g = pub[int(max(y - BLANK_MARGIN, 0) * F9_TO_L3):int((y + CORE + BLANK_MARGIN) * F9_TO_L3),
                        int(max(x - BLANK_MARGIN, 0) * F9_TO_L3):int((x + CORE + BLANK_MARGIN) * F9_TO_L3)]
                if float((g > 0.5).mean()) >= BLANK_SHARE:
                    continue
            if (want == "blank" and share < BLANK_SHARE) or (want == "text" and TEXT_SHARE[0] <= share <= TEXT_SHARE[1]):
                out.append((y, x, share))
    return out, (H, W)


def pick(w, want, n, rng, taken, log, allow_short=False):
    pub, key, etag = published(w)
    cands, (H, W) = candidates(w, pub, want)
    rng.shuffle(cands)
    got = []
    for y, x, share in cands:
        wy, wx = min(max(y + CORE // 2 - WIN // 2, 0), H - WIN), min(max(x + CORE // 2 - WIN // 2, 0), W - WIN)
        if any(abs(wy - a) < WIN and abs(wx - b) < WIN for a, b in taken.get(w, [])):
            continue
        v = read_box(SEG[w], [y, y + CORE, x, x + CORE])
        pk, prom, prof = sheet(v)
        flat = flat_share(v, pk)
        ok = SHEET_LAYERS[0] <= pk <= SHEET_LAYERS[1] and prom >= SHEET_PROMINENCE and flat <= FLAT_MAX
        log.append({"seg": w, "want": want, "core": [y, x], "share": share, "sheet_layer": pk, "prominence": prom,
                    "flat_share": flat, "kept": ok})
        if not ok:
            continue
        rec = {"seg": w, "prefix": SEG[w], "core": [y, y + CORE, x, x + CORE], "box": [wy, wy + WIN, wx, wx + WIN],
               "published_ink_share_core": share, "sheet_layer": pk, "sheet_prominence": prom, "flat_share": flat,
               "profile": prof,
               "published_map": key, "published_map_etag": etag}
        if want == "text":
            reg = register(w, rec["box"])
            if reg is None or reg["r"] < 0.3:
                log[-1]["kept"] = False
                log[-1]["registration"] = reg
                continue
            rec["registration"] = reg
            m = map_on_window(pub, rec["box"], reg["shift_9"])
            cy0, cx0 = y - wy, x - wx
            rec["_map_core"] = m[cy0:cy0 + CORE, cx0:cx0 + CORE]
        else:
            # a blank core is registered like a donor, and must be blank where the map really is: at its own
            # measured shift, and that shift moved 3 px either way, over the core and a border round it
            reg = register(w, rec["box"])
            worst = None
            if reg is not None and reg["r"] >= 0.3:
                g = BLANK_MARGIN
                shares = []
                for dy in (-3, 0, 3):
                    for dx in (-3, 0, 3):
                        m = map_on_window(pub, [y - g, y + CORE + g, x - g, x + CORE + g],
                                          (reg["shift_9"][0] + dy, reg["shift_9"][1] + dx)) > 0.5
                        shares += [float(m.mean()), float(m[g:-g, g:-g].mean())]   # core with border; core alone
                worst = max(shares)
            log[-1]["registration"] = reg
            log[-1]["blank_share_registered_worst"] = worst
            if worst is None or worst >= BLANK_SHARE:
                log[-1]["kept"] = False
                continue
            rec["registration"] = reg
            rec["blank_share_registered_worst"] = worst
        got.append(rec)
        taken.setdefault(w, []).append((wy, wx))
        if len(got) == n:
            break
    if len(got) < n and not allow_short:
        raise SystemExit("%s: only %d %s cores qualify (of %d candidates)" % (w, len(got), want, len(cands)))
    return got


def pick_spread(segs, n_each, rng, taken, log, want):
    """n_each cores per segment; a segment that cannot supply n_each gives what it can, and the shortfall is drawn
    from the other segments in the listed order (PREREG section 4)."""
    got, short = [], {}
    for w in segs:
        g = pick(w, want, n_each, rng, taken, log, allow_short=True)
        got += g
        if len(g) < n_each:
            short[w] = n_each - len(g)
    need = n_each * len(segs)
    for w in segs:
        if len(got) >= need:
            break
        if w not in short:
            got += pick(w, want, need - len(got), rng, taken, log, allow_short=True)
    if len(got) < need:
        raise SystemExit("only %d of %d %s cores qualify across %s" % (len(got), need, want, ", ".join(segs)))
    return got, short


def main():
    os.makedirs(OUT, exist_ok=True)
    assert not (set(DONOR_SEGS) | set(TARGET_SEGS)) & NATIVE9_TRAINED
    rng = np.random.default_rng(SEED)
    taken, log, masks = {}, [], {}
    info = {"prereg": "PREREG.md", "version": 2, "seed": SEED, "window_px": WIN, "core_px": CORE, "scan": SCAN9,
            "surface_volume": SV, "native9_trained_excluded": sorted(NATIVE9_TRAINED),
            "catalog_etag": head_etag(CATALOG_URL), "sheet_rule": {"layers": SHEET_LAYERS, "prominence": SHEET_PROMINENCE},
            "blank_rule": {"share_below": BLANK_SHARE, "margin_px": BLANK_MARGIN, "registered": True,
                           "shift_tolerance_px": 3},
            "flat_max": FLAT_MAX,
            "donors": [], "targets": [], "shams": []}
    for w in DONOR_SEGS:
        for d in pick(w, "text", N_DONOR_PER_SEG, rng, taken, log):
            i = len(info["donors"])
            mp = d.pop("_map_core")
            ink = mp > 0.5
            neg = ~ndimage.binary_dilation(ink, iterations=3)          # a 3 px band around the letters is left out
            masks[f"donor{i}_ink"], masks[f"donor{i}_neg"] = ink, neg
            d["ink_px"], d["neg_px"] = int(ink.sum()), int(neg.sum())
            info["donors"].append(d)
    info["targets"], short_t = pick_spread(TARGET_SEGS, N_TARGET_PER_SEG, rng, taken, log, "blank")
    info["shams"], short_s = pick_spread(DONOR_SEGS, len(info["targets"]) // len(DONOR_SEGS), rng, taken, log, "blank")
    info["shortfall"] = {"targets": short_t, "shams": short_s}
    for i, t in enumerate(info["targets"]):
        t["name"] = "target%02d_%s" % (i, t["seg"])
        t["donor"] = i % len(info["donors"])
        t["sham"] = i
    info["selection_log"] = log
    np.savez_compressed(os.path.join(OUT, "masks.npz"), **masks)
    json.dump(info, open(os.path.join(OUT, "windows.json"), "w"), indent=1)
    for d in info["donors"]:
        print("donor", d["seg"], d["core"][:4:2], "share %.2f sheet %d (%.1f) reg r %.2f shift9 %s ink %d" % (
            d["published_ink_share_core"], d["sheet_layer"], d["sheet_prominence"], d["registration"]["r"],
            [round(s, 1) for s in d["registration"]["shift_9"]], d["ink_px"]))
    for t in info["targets"]:
        print(t["name"], t["core"][:4:2], "share %.4f sheet %d (%.1f) donor %d" % (
            t["published_ink_share_core"], t["sheet_layer"], t["sheet_prominence"], t["donor"]))
    print("shams:", [(s["seg"], s["sheet_layer"]) for s in info["shams"]])
    print("shortfall (filled from the other segments in order):", info["shortfall"])
    print("cores examined:", len(log), "kept:", sum(1 for l in log if l["kept"]))


if __name__ == "__main__":
    main()
