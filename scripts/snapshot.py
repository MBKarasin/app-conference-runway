#!/usr/bin/env python3
"""Daily archive: the exact published data file (site/data/runway.json), gzipped, one file per New York calendar day.
data/snapshots/<YYYY>/<YYYY-MM-DD>.json.gz  (~220 KB a day). A second run on the same day replaces that day's file,
so the archive keeps the day's last published state. data/snapshots/MANIFEST.csv records the SHA-256 of the
uncompressed bytes, so any later change to an archived day is detectable."""
import csv, gzip, hashlib, pathlib, datetime as dt
from zoneinfo import ZoneInfo
ROOT = pathlib.Path(__file__).resolve().parent.parent
raw = (ROOT / "site/data/runway.json").read_bytes()
day = dt.datetime.now(ZoneInfo("America/New_York")).date().isoformat()
out = ROOT / "data" / "snapshots" / day[:4] / f"{day}.json.gz"
out.parent.mkdir(parents=True, exist_ok=True)
with open(out, "wb") as fh, gzip.GzipFile(fileobj=fh, mode="wb", mtime=0, compresslevel=9) as gz:
    gz.write(raw)
man = ROOT / "data" / "snapshots" / "MANIFEST.csv"
rows = list(csv.DictReader(open(man, encoding="utf-8"))) if man.exists() else []
rows = [r for r in rows if r["date"] != day] + [{"date": day, "file": str(out.relative_to(ROOT)),
        "sha256_json": hashlib.sha256(raw).hexdigest(), "bytes_json": len(raw), "archived_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}]
with open(man, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["date", "file", "sha256_json", "bytes_json", "archived_utc"]); w.writeheader(); w.writerows(sorted(rows, key=lambda r: r["date"]))
print(out, out.stat().st_size // 1024, "KB")
