#!/usr/bin/env python3
"""Re-check every dated edition against its organizer page.

For each edition the page is fetched (robots.txt honored, one request at a time per host) and reduced to text.
  verified     the start date (any common spelling) AND its year AND a distinctive word of the meeting name
               all appear on the organizer page
  not_found    page read fine, but the date/year/name is no longer there  -> needs human review
  unreachable  blocked, timed out, robots-disallowed, or too little text (JavaScript-only page)
Second readers: when the organizer's server delivered the page but the plain reader found too
little text or no match, the page is rendered in headless Chromium (Playwright), and a record that links the
organizer's own image (evidence_image) has that image read by OCR (tesseract). Both identify themselves with
the same user agent and obey the same robots.txt. A page that refused the reader (HTTP 403 and the like) is
never retried with a browser, so nothing here disguises the checker. Either reader is skipped when its tool is
not installed, which leaves the plain reader's verdict.
Nothing here edits dates. It only writes data/verification.json and data/check_report.md.
"""
import os, json, re, sys, html, time, datetime as dt, pathlib, threading, calendar, urllib.parse, urllib.robotparser
from concurrent.futures import ThreadPoolExecutor
import urllib.request, ssl

ROOT = pathlib.Path(__file__).resolve().parent.parent
UA = "APPConferenceRunwayChecker/1.0 (+https://github.com/; weekly date check, one request per page)"
# The same calendar day as build.py and snapshot.py (New York). On the UTC clock a run after 8 p.m.
# Eastern would freeze meetings ending that day as past before they had ended in the US.
from zoneinfo import ZoneInfo
TODAY = dt.datetime.now(ZoneInfo("America/New_York")).date().isoformat()
NOW = dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
STOP = {"annual", "conference", "meeting", "national", "the", "and", "for", "with", "association", "society",
        "american", "international", "congress", "summit", "symposium", "week", "day", "nurses", "nursing"}

CHALLENGE = re.compile(r"whether you are a human|verify (?:that )?you are (?:a )?human|are you a robot|checking your browser|enable javascript and cookies to continue|what code is in the image", re.I)

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
            rf"(?<!\d){d.month}\s*月\s*{d.day}\s*日",
            rf"(?<!\d){day}(?:st|nd|rd|th)?(?:\s*(?:,|&|and|y|e|et|und|-|–)\s*\d{{1,2}}(?:st|nd|rd|th)?)+,?\s+(?:de\s+)?{mon}\b",   # 24th, 25th & 26th September; 19 y 20 de noviembre
            rf"(?<!\d){d.year}\s*年\s*0?{d.month}\s*月\s*0?{d.day}\s*日?",
            rf"(?<!\d)0?{d.month}[ .]0?{d.day}[ .]{str(d.year)[2:]}(?!\d)"]
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
    if not r["ok"] and not r["why"].startswith(("robots", "page has", "the site asked")):
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
            if len(text) < 1500 and CHALLENGE.search(text):
                # a bot challenge (a short CAPTCHA or "are you human" page) is a refusal: it is reported, never answered
                return {"ok": False, "why": "the site asked the reader to prove it is human; not attempted"}
            if len(text) < 400:
                return {"ok": False, "why": f"page has almost no readable text ({len(text)} chars; likely JavaScript-only)"}
            return {"ok": True, "http": st, "text": text}
        except urllib.error.HTTPError as e:
            return {"ok": False, "why": f"HTTP {e.code}"}
        except Exception as e:
            return {"ok": False, "why": type(e).__name__ + ": " + str(e)[:80]}

def render_pages(urls):
    """Rendered text of pages the organizer's server delivered but the plain reader could not use.
    One browser, one page at a time, the checker's own user agent, robots.txt obeyed."""
    out = {}
    if not urls:
        return out
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        return out
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            ctx = browser.new_context(user_agent=UA, locale="en-US")
            for u in urls:
                try:
                    if not allowed(u):
                        continue
                    page = ctx.new_page()
                    resp = page.goto(u, wait_until="domcontentloaded", timeout=45000)
                    if resp is None or resp.status >= 400:
                        page.close(); continue
                    page.wait_for_timeout(4000)
                    t = page.evaluate("document.body ? document.body.innerText : ''") or ""
                    page.close()
                    if len(t) < 1500 and CHALLENGE.search(t):
                        continue
                    t = re.sub(r"\s+", " ", t.replace("–", "-").replace("—", "-").replace(" ", " "))
                    if len(t) >= 400:
                        out[u] = t
                except Exception:
                    pass
                time.sleep(1.0)
            browser.close()
    except Exception:
        pass
    return out

def ocr_image(url):
    """Text of the organizer's own banner or flyer that a record links as its evidence (tesseract + Pillow)."""
    import io, shutil, subprocess
    if not shutil.which("tesseract"):
        return ""
    try:
        from PIL import Image, ImageOps
    except Exception:
        return ""
    try:
        if not allowed(url):
            return ""
        _, _, body = fetch(url, timeout=40)
        im = Image.open(io.BytesIO(body)); im.load()
    except Exception:
        return ""
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA"); bg = Image.new("RGB", im.size, "white"); bg.paste(im, mask=im.split()[-1]); im = bg
    g = ImageOps.grayscale(im.convert("RGB"))
    txt = []
    # sparse text at native size finds ribbons and badges; a doubled page-of-text pass finds small print
    for img, psm in ((g, "11"), (g.resize((g.width * 2, g.height * 2)), "6")):
        buf = io.BytesIO(); img.save(buf, "PNG")
        try:
            r = subprocess.run(["tesseract", "stdin", "stdout", "--psm", psm], input=buf.getvalue(), capture_output=True, timeout=120)
            txt.append(r.stdout.decode("utf-8", "replace"))
        except Exception:
            pass
    t = re.sub(r"\s+", " ", " ".join(txt).replace("™", "th").replace("–", "-").replace("—", "-"))   # a superscript "TH" reads as ™
    # letter-spaced type ("L O E W S") reads as single characters; add a copy with those runs joined
    return t + " " + re.sub(r"(?<![\w.])((?:[\w.] ){2,}[\w.])(?![\w.])", lambda m: m.group(1).replace(" ", ""), t)

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
    def judge(e, t):
        s = series[e["series"]]
        rx, year = date_regex(e["start"]), e["start"][:4]
        date_ok = bool(rx.search(t))
        # a numeric date that carries its own two-digit year (03.31.27) confirms the year as well
        year_ok = year in t or any(re.search(rf"(?<!\d)(?:{year}|{year[2:]})$", m.group(0)) for m in rx.finditer(t))
        words = name_words(s)
        name_ok = (not words) or any(re.search(r"\b" + re.escape(w) + r"\b", t, re.I) for w in words)
        # a page written mostly in CJK script cannot carry the English name words; date + year decide there
        if not name_ok and e.get("source_language") and e["source_language"] != "English":
            name_ok = True   # the listing carries an English translation of a title the organizer prints in another language
        if not name_ok and len(re.findall(r"[぀-ヿ一-鿿가-힯]", t)) > 0.2 * max(1, len(re.findall(r"\w", t))):
            name_ok = True
        return date_ok, year_ok, name_ok

    # The plain reader first; then, only where the organizer's server delivered the page, the second readers.
    results = {}
    for e in eds:
        pg = pages[e["source_url"]]
        if pg["ok"]:
            results[e["id"]] = ("page", pg["text"], judge(e, pg["text"]))
    served = lambda u: pages[u]["ok"] or pages[u]["why"].startswith("page has")
    confirmed = lambda e: e["id"] in results and all(results[e["id"]][2])
    need = [e for e in eds if served(e["source_url"]) and not confirmed(e)]
    rendered = render_pages(sorted({e["source_url"] for e in need}))
    for e in need:
        t = rendered.get(e["source_url"])
        if t:
            j = judge(e, t)
            if all(j) or e["id"] not in results:
                results[e["id"]] = ("rendered", t, j)
    for e in need:
        if e.get("evidence_image") and not confirmed(e):
            img = ocr_image(e["evidence_image"])
            if img:
                page_text = results[e["id"]][1] if e["id"] in results else ""
                j = judge(e, page_text + " " + img)
                if all(j):
                    results[e["id"]] = ("image", page_text, j)   # the image text is matched, never quoted

    for e in eds:
        pg = pages[e["source_url"]]
        prev = old.get(e["id"], {})
        rec = {"checked": NOW, "url": e["source_url"], "last_verified": prev.get("last_verified")}
        if e["id"] not in results:
            rec.update(state="unreachable", why=pg["why"])
            if prev.get("snippet"): rec["snippet"] = prev["snippet"]   # keep the last wording captured from the organizer
        else:
            via, t, (date_ok, year_ok, name_ok) = results[e["id"]]
            ev = e.get("evidence")
            ev_ok = None
            if ev and t:
                frags = [f.strip(" .\"'") for f in re.split(r"\.\.\.|…|\n", ev) if len(f.strip()) > 12]
                norm = lambda x: re.sub(r"\s+", " ", x.replace("–", "-").replace("—", "-")).lower()
                ev_ok = all(norm(f)[:80] in norm(t) for f in frags) if frags else None
            if date_ok and year_ok and name_ok:
                rec.update(state="verified", last_verified=NOW)
                if via != "page":
                    rec["via"] = via   # "rendered": read after the page's JavaScript ran; "image": the date was read from the organizer's own image
                m = date_regex(e["start"]).search(t) if via != "image" else None   # keep the sentence the date was found in, so every record can show its source wording
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
    on_file = lambda e: bool(e.get("source_reviewed") and e.get("evidence"))   # curator walked the source and kept a verbatim quote + URL
    failed = [e for e in eds if ver[e["id"]]["state"] in ("not_found", "unreachable")]
    open_ = [e for e in failed if not on_file(e)]
    sha = os.environ.get("GITHUB_SHA", "local")[:7]
    L = [f"# Nightly source check — {NOW[:10]}", "",
         f"Generated {NOW} from commit {sha}. This report is the canonical status; the review issue is rewritten from it on every run.", "",
         f"Editions re-checked: {len(eds)} · verified {c['verified']} · not found {c['not_found']} · unreachable {c['unreachable']}",
         f"Checker could not match: {len(failed)} · of these, curator evidence on file: {len(failed) - len(open_)} · open: {len(open_)}",
         f"Confirmed by the second readers: rendered after JavaScript {sum(1 for v in ver.values() if v.get('via') == 'rendered')} · read from the organizer's image {sum(1 for v in ver.values() if v.get('via') == 'image')}",
         f"Past editions frozen (not re-read): {len(frozen)}", ""]
    if flips:
        L += ["## Newly failing (were verified last run) — review these first", ""]
        L += [f"- [ ] **{series[e['series']]['name']}** ({e['start']}): {r.get('why')} — {e['source_url']}" for e, r in flips] + [""]
    for st, title in (("not_found", "Date not found on the organizer page"), ("unreachable", "Could not read the page")):
        rows = [(e, ver[e["id"]]) for e in eds if ver[e["id"]]["state"] == st and not on_file(e)]
        if rows:
            L += [f"## {title} — open ({len(rows)})", ""]
            L += [f"- {series[e['series']]['name']} — {e['start']} — {r.get('why')} — {e['source_url']}" for e, r in rows] + [""]
    kept = [e for e in failed if on_file(e)]
    if kept:
        L += [f"## Checker could not match, curator evidence on file ({len(kept)})", ""]
        L += [f"- {series[e['series']]['name']} — {e['start']} — reviewed {e.get('reviewed_on') or '?'} — {e['source_url']}" for e in kept] + [""]
    L += [f"OPEN_ITEMS={len(open_) + len(flips)}"]
    (ROOT / "data" / "check_report.md").write_text("\n".join(L), encoding="utf-8")
    print(f"archived {c['archived']} | verified {c['verified']} | not_found {c['not_found']} | unreachable {c['unreachable']} | newly failing {len(flips)}"
          f" | via rendered {sum(1 for v in ver.values() if v.get('via') == 'rendered')} | via image {sum(1 for v in ver.values() if v.get('via') == 'image')}")

if __name__ == "__main__":
    main()
