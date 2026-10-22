#!/usr/bin/env python3
"""Post-conference content monitor (curator decision 2026-10-21).

After a meeting ends, watch the organizer's pages for what the meeting produced: program and agenda,
abstracts and proceedings, posters, speakers and faculty, recordings, slides and handouts, recaps.
The record of when each item first appeared is the signal for how ideas enter and spread among APPs.

Scope: every dated edition on the Runway that ended in the last WINDOW_DAYS (collect everything; topics
are tagged later, never filtered here). Reads site/data/runway.json; never writes to site/.

What is stored (public repository): URLs, the link text, category, HTTP status, content type, page
title, byte length, SHA-256 and first/last-seen dates. Organizer text is NOT republished; the hash
proves what was seen and when, and the URL lets an analyst re-read it.

Outputs: data/postconf/state.json (current inventory), data/postconf/events.csv (append-only:
one row per item the first time it is seen, or when its content changes), data/postconf/report.md.
"""
import csv, datetime as dt, hashlib, html.parser, json, pathlib, re, sys, time, urllib.parse, urllib.request
from zoneinfo import ZoneInfo

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "postconf"
WINDOW_DAYS = 365          # keep watching a meeting for a year after it ends
MAX_LINKS = 15             # candidate links followed per edition per run
TIMEOUT = 20
UA = "Mozilla/5.0 (compatible; APP-Conference-Runway-postconf/1.0; +https://appconferencerunway.org/)"
TODAY = dt.datetime.now(ZoneInfo("America/New_York")).date()
NOW = dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")

# Category rules: matched against link text and URL path (case-insensitive). Order matters: first match wins.
CATEGORIES = [
    ("posters", r"poster|e-?poster"),
    ("abstracts", r"abstract|proceeding|supplement|accepted (papers|presentations)"),
    ("recordings", r"recording|on[- ]?demand|webcast|video|watch|youtube|vimeo|replay"),
    ("slides", r"slide|handout|presentation(s)? (download|pdf)|download (the )?presentation|syllab"),
    ("speakers", r"speaker|faculty|presenter|keynote|panelist"),
    ("program", r"(final|conference|meeting|summit|event|full|preliminary|printed|digital|online|interactive) program(me)?|program(me)?[ -](book|guide|at[- ]a[- ]glance|pdf|schedule)|agenda|schedule|at[- ]a[- ]glance|itinerary|educational sessions|session (list|catalog|schedule)|eventscribe|confex|pathable|sched\.com|whova|cvent"),
    ("recap", r"recap|highlight|photo|gallery|wrap[- ]?up|thank you for attending|post[- ]?(conference|event)|award winner"),
]
RULES = [(c, re.compile(p, re.I)) for c, p in CATEGORIES]
# Site-wide navigation that matches a rule but is not meeting content.
EXCLUDE = re.compile(r"(policy|legislative|strategic|research) agenda|board (meeting )?agenda|youtube\.com/(@|c/|channel/|user/)[^/]+/?$|vimeo\.com/[^/0-9]+/?$", re.I)


class Links(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(); self.links = []; self._href = None; self._text = []; self.title = ""; self._in_title = False
    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self._href = dict(attrs).get("href"); self._text = []
        elif tag == "title":
            self._in_title = True
    def handle_endtag(self, tag):
        if tag == "a" and self._href:
            self.links.append((self._href, " ".join("".join(self._text).split())[:160])); self._href = None
        elif tag == "title":
            self._in_title = False
    def handle_data(self, data):
        if self._href is not None: self._text.append(data)
        if self._in_title: self.title += data


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,application/pdf;q=0.9,*/*;q=0.5"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            body = r.read(5_000_000)
            return {"status": r.status, "type": (r.headers.get("Content-Type") or "").split(";")[0].strip(), "body": body, "final": r.geturl()}
    except urllib.error.HTTPError as e:
        return {"status": e.code, "type": "", "body": b"", "final": url}
    except Exception as e:                                   # timeouts, DNS, TLS: recorded, never fatal
        return {"status": type(e).__name__, "type": "", "body": b"", "final": url}


def classify(href, text):
    hay = f"{text} {urllib.parse.urlparse(href).path}"
    if EXCLUDE.search(f"{text} {href}"):
        return None
    for cat, rx in RULES:
        if rx.search(hay):
            return cat
    return None


def main():
    d = json.load(open(ROOT / "site/data/runway.json", encoding="utf-8"))
    names = {s["id"]: s["name"] for s in d["series"]}
    start = (TODAY - dt.timedelta(days=WINDOW_DAYS)).isoformat()
    eds = [e for e in d["editions"] if e.get("end") and start <= e["end"] < TODAY.isoformat()
           and e.get("verify", {}).get("state") not in ("expected", "rule") and e.get("source_url")]
    OUT.mkdir(parents=True, exist_ok=True)
    state_f, events_f = OUT / "state.json", OUT / "events.csv"
    state = json.load(open(state_f, encoding="utf-8")) if state_f.exists() else {}
    new_events = []
    eds = sorted(eds, key=lambda x: x["end"], reverse=True)
    if len(sys.argv) > 1 and sys.argv[1].isdigit():         # optional cap for a trial run: postconf.py 5
        eds = eds[:int(sys.argv[1])]
    for i, e in enumerate(eds):
        rec = state.setdefault(e["id"], {"series": e["series"], "name": names.get(e["series"], e["series"]),
                                         "start": e["start"], "end": e["end"], "items": {}})
        rec.update({"end": e["end"], "last_checked": NOW})
        pages = [u for u in (e.get("source_url"), e.get("detail_url")) if u]
        cands = {}
        for page in dict.fromkeys(pages):
            r = fetch(page); rec["source_status"] = r["status"]
            if not r["body"] or "html" not in r["type"]:
                continue
            p = Links()
            try: p.feed(r["body"].decode("utf-8", "replace"))
            except Exception: continue
            for href, text in p.links:
                if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
                    continue
                url = urllib.parse.urljoin(r["final"], href).split("#")[0]
                cat = classify(url, text)
                if cat and url not in cands:
                    cands[url] = (cat, text)
        for url, (cat, text) in list(cands.items())[:MAX_LINKS]:
            r = fetch(url)
            title = ""
            if r["body"] and "html" in r["type"]:
                p = Links()
                try: p.feed(r["body"].decode("utf-8", "replace")); title = " ".join(p.title.split())[:200]
                except Exception: pass
            sha = hashlib.sha256(r["body"]).hexdigest() if r["body"] else None
            item = rec["items"].get(url)
            if item is None:
                item = rec["items"][url] = {"category": cat, "text": text, "first_seen": NOW}
                if isinstance(r["status"], int) and r["status"] < 400:
                    new_events.append([NOW, e["id"], e["series"], e["end"], cat, "new", url, text, r["status"], sha])
            elif sha and item.get("sha256") and sha != item["sha256"]:
                new_events.append([NOW, e["id"], e["series"], e["end"], cat, "changed", url, text, r["status"], sha])
            item.update({"last_seen": NOW, "status": r["status"], "type": r["type"], "title": title,
                         "bytes": len(r["body"]), "sha256": sha or item.get("sha256")})
            time.sleep(0.5)                                  # polite to organizer servers
        print(f"[{i + 1}/{len(eds)}] {e['end']} {rec['name'][:60]}: {len(rec['items'])} items", flush=True)
    json.dump(state, open(state_f, "w", encoding="utf-8"), ensure_ascii=False, indent=1, sort_keys=True)
    write_header = not events_f.exists()
    with open(events_f, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if write_header:
            w.writerow(["seen_utc", "edition_id", "series", "edition_end", "category", "event", "url", "link_text", "status", "sha256"])
        w.writerows(new_events)
    # Report
    by_cat = {c: 0 for c, _ in CATEGORIES}
    with_any = 0
    for rec in state.values():
        live = [it for it in rec["items"].values() if isinstance(it.get("status"), int) and it["status"] < 400]
        with_any += bool(live)
        for it in live: by_cat[it["category"]] += 1
    lines = [f"# Post-conference content monitor", "", f"Run: {NOW}. Meetings watched (ended in the last {WINDOW_DAYS} days): {len(eds)}.",
             f"Meetings with any post-conference item found: {with_any}. New or changed items this run: {len(new_events)}.", "",
             "| Category | Live items |", "|---|---|"] + [f"| {c} | {n} |" for c, n in by_cat.items()] + ["",
             "Method and limits: link discovery from the organizer pages the Runway already cites; category by link text and URL. "
             "Pages that need JavaScript, sign-in or members-only access are not read and are recorded only by status. "
             "Organizer text is not stored; URL, hash and dates are."]
    (OUT / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines[:4]))


if __name__ == "__main__":
    sys.exit(main())
