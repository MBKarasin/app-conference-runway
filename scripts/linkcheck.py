"""Check every outbound link in the published data. Writes data/link_report.md.
Read-only: one polite request per URL, same user agent and robots handling as scripts/check.py."""
import json, pathlib, sys, collections
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import check as C
ROOT = pathlib.Path(__file__).resolve().parent.parent

def probe(u):
    try:
        if not C.allowed(u): return ("robots", None)
        st, ctype, body = C.fetch(u, timeout=25)
        return ("ok", st)
    except Exception as e:
        code = getattr(e, "code", None)
        return (f"HTTP {code}" if code else type(e).__name__, code)

def main():
    d = json.load(open(ROOT / "site/data/runway.json", encoding="utf-8"))
    where = collections.defaultdict(set)
    for s in d["series"]:
        for f in ("org_url", "archive_url", "proceedings_url"):
            if s.get(f): where[s[f]].add(f"{s['name']} ({f})")
    for e in d["editions"]:
        for f in ("source_url", "detail_url"):
            if e.get(f): where[e[f]].add(f"{e['series']} {e['start']} ({f})")
        if (e.get("call") or {}).get("url"): where[e["call"]["url"]].add(f"{e['series']} {e['start']} (call)")
        if (e.get("student") or {}).get("url"): where[e["student"]["url"]].add(f"{e['series']} {e['start']} (student)")
    urls = sorted(where)
    print(f"checking {len(urls)} links", file=sys.stderr)
    with ThreadPoolExecutor(12) as ex:
        res = dict(zip(urls, ex.map(probe, urls)))
    bad = {u: r for u, r in res.items() if r[0] not in ("ok", "robots")}
    c = collections.Counter(r[0] for r in res.values())
    L = [f"# Link check — {C.NOW[:10]}", "", f"Links: {len(urls)} · " + " · ".join(f"{k} {v}" for k, v in c.most_common()), ""]
    for u, (why, _) in sorted(bad.items()):
        L += [f"- {why} — {u}", "  - " + "; ".join(sorted(where[u])[:4])]
    (ROOT / "data" / "link_report.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(dict(c))
    json.dump({u: r[0] for u, r in res.items()}, open(ROOT / "data" / "link_status.json", "w"), indent=0, sort_keys=True)

if __name__ == "__main__":
    main()
