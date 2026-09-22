#!/usr/bin/env python3
"""Write today's compact snapshot (gzip) of every dated edition and its verification state.
data/snapshots/<YYYY>/<YYYY-MM-DD>.json.gz  (~30 KB a day, ~11 MB a year)"""
import gzip, json, pathlib, datetime as dt
ROOT = pathlib.Path(__file__).resolve().parent.parent
d = json.load(open(ROOT / "site/data/runway.json", encoding="utf-8"))
day = dt.date.today().isoformat()
out = ROOT / "data" / "snapshots" / day[:4] / f"{day}.json.gz"
out.parent.mkdir(parents=True, exist_ok=True)
snap = {"built": d["built"], "editions": [{k: e.get(k) for k in ("id", "series", "start", "end", "location", "call", "source_url", "verify")}
                                          for e in d["editions"] if e["verify"]["state"] != "expected"]}
with gzip.open(out, "wt", encoding="utf-8") as f:
    json.dump(snap, f, separators=(",", ":"), ensure_ascii=False)
print(out, out.stat().st_size // 1024, "KB")
