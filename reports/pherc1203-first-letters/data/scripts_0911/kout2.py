"""Fetch a Kaggle kernel's outputs KEEPING folder structure, plus the full log. Never prints the token.
(kout.py saves every file under its basename, so same-named files in different folders overwrite each other.)
Retries each file 3 times and skips files already present at the right size, so it can be re-run to resume.
Usage: kout2.py <user> <slug> <token.env> <download_dir> [max_mb_per_file=200] [only_suffixes=all, e.g. .log,.json,.png]"""
import json, re, sys, os, time, urllib.request, urllib.parse
user, slug, envf, dl = sys.argv[1:5]
max_mb = float(sys.argv[5]) if len(sys.argv) > 5 else 200.0
only = tuple(s for s in (sys.argv[6] if len(sys.argv) > 6 else "").split(",") if s)
tok = re.search(r"KAGGLE_API_TOKEN\s*=\s*['\"]?([^\s'\"]+)", open(envf).read()).group(1)
Hd = {"Authorization": "Bearer " + tok}
base = f"https://www.kaggle.com/api/v1/kernels/output?userName={user}&kernelSlug={slug}"
r = json.loads(urllib.request.urlopen(urllib.request.Request(base, headers=Hd), timeout=120).read()); pages = 1
while r.get("nextPageToken") and pages < 100:   # the listing comes 500 files per page
    nxt = json.loads(urllib.request.urlopen(urllib.request.Request(
        base + "&pageToken=" + urllib.parse.quote(r["nextPageToken"]), headers=Hd), timeout=120).read())
    r["files"] = r.get("files", []) + nxt.get("files", []); r["nextPageToken"] = nxt.get("nextPageToken"); pages += 1
os.makedirs(dl, exist_ok=True)
log = r.get("log") or ""
try: text = "".join(e.get("data", "") for e in json.loads(log))
except Exception: text = log
open(os.path.join(dl, "kernel.log"), "w").write(text)
files = r.get("files", [])
json.dump([{k: v for k, v in f.items() if k != "url"} for f in files], open(os.path.join(dl, "_files.json"), "w"), indent=0)
print(f"{slug}: {len(files)} output files in {pages} page(s); log {len(text.splitlines())} lines -> {dl}/kernel.log; list -> {dl}/_files.json")
ok = have = 0; skipped = []; failed = []
for f in files:
    n = f.get("fileName", ""); u = f.get("url"); sz = int(f.get("size") or f.get("totalBytes") or 0)
    if not u or ".." in n or n.startswith("/") or (only and not n.endswith(only)): skipped.append(n); continue
    if sz and sz > max_mb * 1e6: skipped.append(f"{n} ({sz/1e6:.0f} MB)"); continue
    p = os.path.join(dl, n); os.makedirs(os.path.dirname(p) or dl, exist_ok=True)
    if sz and os.path.exists(p) and os.path.getsize(p) == sz: have += 1; continue
    for attempt in range(3):
        try:
            with urllib.request.urlopen(u, timeout=300) as resp, open(p + ".part", "wb") as out:
                while True:
                    b = resp.read(1 << 20)
                    if not b: break
                    out.write(b)
            if sz and os.path.getsize(p + ".part") != sz: raise IOError(f"short: {os.path.getsize(p + '.part')} of {sz}")
            os.replace(p + ".part", p); ok += 1; break
        except Exception as e:
            if attempt == 2: failed.append(f"{n}: {e}")
            time.sleep(3)
print(f"downloaded {ok}, already had {have}, skipped {len(skipped)}, FAILED {len(failed)}: {failed[:5]}")
