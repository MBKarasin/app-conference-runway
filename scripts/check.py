#!/usr/bin/env python3
"""Re-check every dated edition against its organizer page.

For each edition the page is fetched (robots.txt honored, one request at a time per host) and reduced to text.
  verified     the start date (any common spelling) AND its year AND a distinctive word of the meeting name
               all appear on the organizer page
  not_found    page read fine, but the date/year/name is no longer there  -> needs human review
  unreachable  blocked, timed out, robots-disallowed, or too little text (JavaScript-only page)
Nothing here edits dates. It only writes data/verification.json and data/check_report.md.
"""
import json, re, sys, html, time, datetime as dt, pathlib, threading, calendar, urllib.parse, urllib.robotparser
from concurrent.futures import ThreadPoolExecutor
import urllib.request, ssl

ROOT = pathlib.Path(__file__).resolve().parent.parent
UA = "APPConferenceRunwayChecker/1.0 (+https://github.com/; weekly date check, one request per page)"
TODAY = dt.date.today().isoformat()
NOW = dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
STOP = {"annual", "conference", "meeting", "national", "the", "and", "for", "with", "association", "society",
        "american", "international", "congress", "summit", "symposium", "week", "day", "nurses", "nursing"}

def fetch(url, timeout=25):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,application/xhtml+xml,application/pdf;q=0.8,*/*;q=0.5"})
    with urllib.request.urlopen(req, timeout=timeout, context=ssl.create_default_context()) as r:
        ctype = r.headers.get("Content-Type", "")
        body = r.read(6_000_000)
        return r.status, ctype, body

def to_text(ctype, body):
    if "pdf" in ctype:
        try:
            import io
            from pypdf import PdfReader
            return " ".join((p.extract_text() or "") for p in PdfReader(io.BytesIO(body)).pages)
        except Exception:
            return ""
    t = body.decode("utf-8", "replace")
    t = re.sub(r"(?is)<(script|style|noscript|svg)[^>]*>.*?</\1>", " ", t)
    t = re.sub(r"(?s)<[^>]+>", " ", t)
    t = html.unescape(t)
    t = t.replace("–", "-").replace("—", "-").replace(" ", " ")
    return re.sub(r"\s+", " ", t)

# Month names in the organizer languages the catalog carries (pt, es, fr, de, nl, it)
INTL_MONTHS = ["janeiro|enero|janvier|Januar|januari|gennaio", "fevereiro|febrero|février|Februar|februari|febbraio",
    "março|marzo|mars|März|maart", "abril|avril|april|aprile", "maio|mayo|mai|mei|maggio", "junho|junio|juin|Juni|juni|giugno",
    "julho|julio|juillet|Juli|juli|luglio", "agosto|août|August|augustus", "setembro|septiembre|septembre|September|settembre",
    "outubro|octubre|octobre|Oktober|oktober|ottobre", "novembro|noviembre|novembre|November", "dezembro|diciembre|décembre|Dezember|december|dicembre"]

def date_regex(iso):
    d = dt.date.fromisoformat(iso)
    full, abbr = calendar.month_name[d.month], calendar.month_abbr[d.month]
    names = {full, abbr} | ({"Sept"} if d.month == 9 else set()) | set(INTL_MONTHS[d.month - 1].split("|"))
    mon = "(?:" + "|".join(sorted(names, key=len, reverse=True)) + ")"
    day = rf"0?{d.day}"
    pats = [rf"\b{mon}\.?,?\s+{day}(?:st|nd|rd|th)?(?!\d)",
            rf"(?<!\d){day}(?:st|nd|rd|th)?(?:\s+of)?\s+{mon}\b",
            rf"(?<!\d){day}(?:st|nd|rd|th)?\s*(?:-|to|&|and)\s*\d{{1,2}}(?:st|nd|rd|th)?,?\s+{mon}\b",
            rf"(?<!\d)0?{d.month}[/.-]{day}[/.-](?:{d.year}|{str(d.year)[2:]})(?!\d)",
            rf"{d.year}-{d.month:02d}-{d.day:02d}",
            rf"(?<!\d){day}\.?\s*(?:-|a|al|bis|au|tot|t/m)\s*\d{{1,2}}\.?\s+(?:de\s+)?{mon}\b",   # 25 a 27 de novembro, 4. bis 5. September
            rf"(?<!\d){day}\.?\s+(?:de\s+)?{mon}\b",
            rf"(?<!\d)0?{d.day}[/.]0?{d.month}[/.](?:{d.year}|{str(d.year)[2:]})(?!\d)",   # day-first (Europe, Latin America, Asia)
            rf"(?<!\d){d.month}\s*月\s*{d.day}\s*日"]
    return re.compile("|".join(pats), re.I)

def name_words(s):
    words = [w for w in re.findall(r"[A-Za-z]{4,}", s["name"]) if w.lower() not in STOP]
    acr = re.findall(r"\b[A-Z]{3,}\b", s["name"] + " " + s["org"])
    return words + acr

_robots, _locks, _lk = {}, {}, threading.Lock()
def allowed(url):
    p = urllib.parse.urlsplit(url); base = f"{p.scheme}://{p.netloc}"
    if base not in _robots:
        rp = urllib.robotparser.RobotFileParser()
        try:
            st, _, body = fetch(base + "/robots.txt", timeout=10)
            rp.parse(body.decode("utf-8", "replace").splitlines())
        except Exception:
            rp.parse([])            # no robots file reachable -> no restriction
        _robots[base] = rp
    return _robots[base].can_fetch(UA, url)

def host_lock(url):
    h = urllib.parse.urlsplit(url).netloc
    with _lk:
        return _locks.setdefault(h, threading.Lock())

def get_page(url):
    r = _get_page(url)
    if not r["ok"] and not r["why"].startswith(("robots", "page has")):
        time.sleep(5)
        r = _get_page(url)          # one retry: resets and timeouts are usually transient
    return r

def _get_page(url):
    with host_lock(url):
        try:
            if not allowed(url):
                return {"ok": False, "why": "robots.txt disallows"}
            st, ctype, body = fetch(url)
            text = to_text(ctype, body)
            time.sleep(1.0)
            if len(text) < 400:
                return {"ok": False, "why": f"page has almost no readable text ({len(text)} chars; likely JavaScript-only)"}
            return {"ok": True, "http": st, "text": text}
        except urllib.error.HTTPError as e:
            return {"ok": False, "why": f"HTTP {e.code}"}
        except Exception as e:
            return {"ok": False, "why": type(e).__name__ + ": " + str(e)[:80]}

def main():
    data = json.load(open(ROOT / "site" / "data" / "runway.json", encoding="utf-8"))
    series = {s["id"]: s for s in data["series"]}
    eds = [e for e in data["editions"] if e["verify"]["state"] not in ("expected", "rule") and e.get("source_url")]
    vfile0 = ROOT / "data" / "verification.json"
    old0 = json.load(open(vfile0, encoding="utf-8")) if vfile0.exists() else {}
    # A meeting that has already happened is not re-read: organizers move their page on to the next
    # edition, which would flip a correct historical record to "needs review". The record is frozen
    # at what the page said when it was captured or last confirmed.
    ended = lambda e: (e.get("end") or e["start"]) < TODAY
    frozen = [e for e in eds if ended(e) and (old0.get(e["id"], {}).get("last_verified") or e.get("evidence") or e.get("source_reviewed"))]
    eds = [e for e in eds if e not in frozen]
    urls = sorted({e["source_url"] for e in eds})
    print(f"checking {len(eds)} editions on {len(urls)} pages", file=sys.stderr)
    with ThreadPoolExecutor(12) as ex:
        pages = dict(zip(urls, ex.map(get_page, urls)))
    vfile = vfile0
    old = old0
    ver, flips = {}, []
    for e in frozen:
        prev = old.get(e["id"], {})
        ver[e["id"]] = {"checked": prev.get("checked") or NOW, "url": e["source_url"], "state": "archived",
                        "last_verified": prev.get("last_verified"), "evidence_match": prev.get("evidence_match"),
                        "why": "meeting has ended; the record is kept as the organizer's page read at the time",
                        "fails": prev.get("fails", 0)}
    for e in eds:
        pg, s = pages[e["source_url"]], series[e["series"]]
        prev = old.get(e["id"], {})
        rec = {"checked": NOW, "url": e["source_url"], "last_verified": prev.get("last_verified")}
        if not pg["ok"]:
            rec.update(state="unreachable", why=pg["why"])
        else:
            t = pg["text"]
            date_ok = bool(date_regex(e["start"]).search(t))
            year_ok = e["start"][:4] in t
            words = name_words(s)
            name_ok = (not words) or any(re.search(r"\b" + re.escape(w) + r"\b", t, re.I) for w in words)
            ev = e.get("evidence")
            ev_ok = None
            if ev:
                frags = [f.strip(" .\"'") for f in re.split(r"\.\.\.|…|\n", ev) if len(f.strip()) > 12]
                norm = lambda x: re.sub(r"\s+", " ", x.replace("–", "-").replace("—", "-")).lower()
                ev_ok = all(norm(f)[:80] in norm(t) for f in frags) if frags else None
            if date_ok and year_ok and name_ok:
                rec.update(state="verified", last_verified=NOW)
                m = date_regex(e["start"]).search(t)   # keep the sentence the date was found in, so every record can show its source wording
                if m:
                    a, b = max(0, m.start() - 90), min(len(t), m.end() + 90)
                    snip = re.sub(r"\s+", " ", t[a:b]).strip()
                    snip = re.sub(r"[\w.+-]+@[\w.-]+\.\w+", "", snip)            # never carry a contact address into the record
                    snip = re.sub(r"\+?\d[\d ().-]{7,}\d", "", snip)
                    rec["snippet"] = re.sub(r"\s{2,}", " ", snip).strip(" .,;|-")
            else:
                miss = [k for k, v in (("date", date_ok), ("year", year_ok), ("name", name_ok)) if not v]
                rec.update(state="not_found", why="not on page: " + ", ".join(miss))
            rec["evidence_match"] = ev_ok
        rec["fails"] = 0 if rec["state"] == "verified" else prev.get("fails", 0) + 1
        # a page that merely could not be read is only escalated after two runs in a row
        if prev.get("state") == "verified" and (rec["state"] == "not_found" or rec["fails"] >= 2):
            flips.append((e, rec))
        ver[e["id"]] = rec
    vfile.parent.mkdir(exist_ok=True)
    json.dump(ver, open(vfile, "w", encoding="utf-8"), indent=1, sort_keys=True)
    # human report
    from collections import Counter
    c = Counter(v["state"] for v in ver.values())
    L = [f"# Weekly source check — {NOW[:10]}", "",
         f"Editions re-checked: {len(eds)} · verified {c['verified']} · not found {c['not_found']} · unreachable {c['unreachable']}",
         f"Past editions frozen (not re-read): {len(frozen)}", ""]
    if flips:
        L += ["## Newly failing (were verified last run) — review these first", ""]
        L += [f"- [ ] **{series[e['series']]['name']}** ({e['start']}): {r.get('why')} — {e['source_url']}" for e, r in flips] + [""]
    for st, title in (("not_found", "Date not found on the organizer page"), ("unreachable", "Could not read the page")):
        rows = [(e, ver[e["id"]]) for e in eds if ver[e["id"]]["state"] == st]
        if rows:
            L += [f"## {title} ({len(rows)})", ""]
            L += [f"- {series[e['series']]['name']} — {e['start']} — {r.get('why')} — {e['source_url']}" for e, r in rows] + [""]
    (ROOT / "data" / "check_report.md").write_text("\n".join(L), encoding="utf-8")
    print(f"archived {c['archived']} | verified {c['verified']} | not_found {c['not_found']} | unreachable {c['unreachable']} | newly failing {len(flips)}")

if __name__ == "__main__":
    main()
