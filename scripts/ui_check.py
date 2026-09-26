"""Scripted interface check for the Runway.

    python scripts/ui_check.py                  # serves ./site locally
    python scripts/ui_check.py --url <site>     # checks a deployed site

Needs Playwright for Python with a Chromium browser (`pip install playwright && playwright install chromium`).
Every line printed is one assertion; the exit code is non-zero if any assertion failed. It checks the display
switch, the Orbit ring, the filter rows, the header's Fidelity and Reliability indices (values re-derived from
the published data), the landmark celebration weeks in every view, each Focus in each view, older links, the
request address and footer links, the AI Handoff page (opened as a signed-out visitor would, at desktop and
phone widths), the header tagline and icon URLs, phone, tablet and desktop layouts, the calendar feed, and
console errors. Date-dependent cases run at a fixed clock (FIXED_NOW) so they reproduce.
"Visible" means rendered with a real box and not inside a closed <details>; text in the DOM is not enough.
"""
import argparse, functools, hashlib, http.server, re, socketserver, sys, threading
from pathlib import Path
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright

LANDMARKS = ["National APP Week", "PA Week", "National Nurse Practitioner Week", "National CRNA Week"]
TAGLINE = "Independently curated for advanced practice providers worldwide"   # the header tagline, verbatim
# An item counts as visible only if it is rendered with a real box and is not inside a closed <details>.
VISIBLE_JS = """name => [...document.querySelectorAll('#view button, #view a, #view article')].some(x => {
  if (!x.textContent.includes(name)) return false;
  const d = x.closest('details'); if (d && !d.open) return false;
  const r = x.getBoundingClientRect(); return r.width > 0 && r.height > 0; })"""
FIXED_NOW = "2026-09-24T12:00:00-04:00"   # a fixed clock (New York) so the date-dependent cases below are reproducible
SCOPE = ["All", "Clinical", "Academic", "Research", "Leadership", "Students"]
FOCUS = ["All", "Abstracts Due", "Open Abstracts", "Conferences", "Celebrations"]
SCARLET = "rgb(204, 0, 51)"
results = []


def check(name, ok, detail=""):
    results.append((bool(ok), name, detail))
    print(("PASS " if ok else "FAIL ") + name + (f"  [{detail}]" if detail else ""))


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def serve(root):
    handler = functools.partial(QuietHandler, directory=str(root))
    class QuietServer(socketserver.TCPServer):
        def handle_error(self, request, client_address):
            pass   # a reload cancels the previous page's data request mid-transfer; that broken pipe is not a finding
    httpd = QuietServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, f"http://127.0.0.1:{httpd.server_address[1]}/"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", help="deployed site to check instead of ./site")
    args = ap.parse_args()
    httpd = None
    base = args.url
    if not base:
        httpd, base = serve(Path(__file__).resolve().parent.parent / "site")
    base = base if base.endswith("/") else base + "/"
    errors = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)

        def go(hash_=""):
            page.goto(base + ("#" + hash_ if hash_ else ""), wait_until="networkidle")
            page.reload(wait_until="networkidle")           # a hash-only change must re-read state from the URL
            page.wait_for_selector("#quickfocus .chip", timeout=15000)

        def texts(sel):   # DOM text, independent of CSS text-transform and of collapsed disclosures
            return page.evaluate("s => [...document.querySelectorAll(s)].map(x => x.textContent.trim())", sel)

        def text(sel):
            return " ".join(texts(sel))

        go()
        data = page.evaluate("fetch('data/runway.json').then(r => r.json())")
        today = page.evaluate("(() => { const d = new Date(); return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0'); })()")

        # 1. Display switch: four plain labels, a scarlet separator before every button after the first.
        labels = texts("#viewtools .seg button")
        check("display switch reads List | Calendar | Orbit | Directory", labels == ["List", "Calendar", "Orbit", "Directory"], " | ".join(labels))
        check("no 'Schedule' label in the display switch", "schedule" not in page.inner_text("#viewtools").lower())
        seps = page.evaluate("""[...document.querySelectorAll('#viewtools .seg button')].map(b => { const s = getComputedStyle(b); return [s.borderLeftWidth, s.borderLeftStyle, s.borderLeftColor]; })""")
        check("separator between every pair of display buttons",
              all(float(w[:-2]) >= 2 and st == "solid" and c == SCARLET for w, st, c in seps[1:]), str(seps))

        # 2. Orbit: landing view, twelve months, each with its year.
        check("Orbit is the landing view", page.locator("#viewtools [data-display='orbit']").get_attribute("aria-pressed") == "true")
        months = page.evaluate("[...document.querySelectorAll('.orbit-month-name')].map(x => x.textContent)")
        y, m = int(today[:4]), int(today[5:7])
        want = []
        for i in range(12):
            mm = (m - 1 + i) % 12
            want.append(["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][mm] + " ’" + str(y + (m - 1 + i) // 12)[2:])
        check("Orbit ring shows twelve months, each with its year", months == want, ", ".join(months))

        # 3. Filter rows: Discipline; Scope with Focus to its right.
        check("Scope row label and chips", texts("#quickscope .flabel") == ["Scope"] and texts("#quickscope .chip") == SCOPE, ", ".join(texts("#quickscope .chip")))
        check("Focus row label and chips", texts("#quickfocus .flabel") == ["Focus"] and texts("#quickfocus .chip") == FOCUS, ", ".join(texts("#quickfocus .chip")))
        # Filter bar: views beside search; Discipline with Focus to its right; Scope with Location to its
        # right. Each pair shares a row at 1440 px, rows in that order.
        box = lambda sel: page.locator(sel).bounding_box() if page.locator(sel).count() else None
        pairs = [("#viewtools", ".search"), ("#quickprof", "#quickfocus"), ("#quickscope", "#geoquick")]
        rows = []
        for a_sel, b_sel in pairs:
            a, b = box(a_sel), box(b_sel)
            ok = bool(a and b) and b["x"] >= a["x"] + a["width"] - 1 and abs(b["y"] - a["y"]) < 12
            rows.append(a["y"] if a else -1)
            check(f"{b_sel} sits to the right of {a_sel} at 1440 px", ok, f"{a} | {b}")
        check("filter rows run views/search, Discipline/Focus, Scope/Location", rows == sorted(rows) and len(set(rows)) == 3, str(rows))

        # Header: the two time stamps, the indices' labels, no "metric", and both values re-derived from the page's own data.
        head = page.inner_text("#updated")
        check("header shows the Verified and Horizon scan stamps", "Verified " in head and "Horizon scan " in head and "Updated " not in head, head.replace("\n", " | "))
        check("header shows Fidelity Index and Reliability Index", "Fidelity Index:" in head and "Reliability Index:" in head, head.replace("\n", " | "))
        check("header does not say 'metric'", "metric" not in head.lower())
        now_ms = page.evaluate("Date.now()")
        # Both values re-derived by scripts/indices.py (the definitions of AI-HANDOFF §3.4) for this page's day and clock.
        import datetime as _dt
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import indices
        ix = indices.compute(data, today, _dt.datetime.fromtimestamp(now_ms / 1000, _dt.timezone.utc))
        fx, rx = ix["fidelity"] or {}, ix["reliability"]
        fid, rel = fx.get("pct", -1), rx["pct"]
        check("Fidelity Index matches its definition re-derived from the data (latest probe: held / found)", bool(fx) and f"Fidelity Index: {fid:.2f}%" in head,
              f"derived {fid:.2f}% = {fx.get('held')} held / {fx.get('found')} found (probe {fx.get('probe')})")
        titles = page.evaluate("[...document.querySelectorAll('#updated .idx')].map(x => x.title)")
        fid_note = next((t for t in titles if t.startswith("Reach:")), "")
        check("Fidelity note states the probe basis", bool(fx) and f"Of the {fx['found']} qualifying dated meetings" in fid_note and f"the Runway already held {fx['held']}" in fid_note, fid_note[:160])
        # Horizon scan: when the latest probe finished, in New York time, formatted like the Verified stamp.
        from zoneinfo import ZoneInfo as _ZI
        norm = lambda t: re.sub(r"[\u202f\u00a0]", " ", t or "").strip()
        scan_txt = norm(page.evaluate("(document.querySelector('#updated .scan-line') || {}).textContent || ''"))
        want_scan = (_dt.datetime.fromisoformat(fx["finished"].replace("Z", "+00:00")).astimezone(_ZI("America/New_York")).strftime("%b %-d, %Y, %-I:%M:%S %p %Z")
                     if fx.get("finished") else None)
        check("Horizon scan shows when the latest probe finished (a timestamp, New York time)", bool(want_scan) and scan_txt == "Horizon scan " + want_scan, f"{scan_txt!r} vs {want_scan!r}")
        check("Reliability Index matches its definition re-derived from the data (confirmation x latest audit)", f"Reliability Index: {rel:.2f}%" in head,
              f"derived {rel:.2f}% = ({rx['machine']} machine + {rx['rule']} rule) / {rx['upcoming_dated']} x {rx['right']}/{rx['audited']}, fresh={ix['fresh']}")
        rel_note = next((t for t in titles if t.startswith("Confirmation:")), "")
        check("Reliability note states the confirmation and audit basis", f"{rx['ok']} of {rx['upcoming_dated']} upcoming dated records" in rel_note and (not rx["audited"] or f"found {rx['right']} of {rx['audited']} audited records" in rel_note), rel_note[:200])
        dots = page.evaluate("[...document.querySelectorAll('#updated .stat')].map(x => x.className + '|' + (x.getAttribute('aria-label') || ''))")
        check("Verified dot reports freshness only (green within 36 hours, red after), with a text label", bool(dots) and dots[0].startswith("stat " + ix["verified_tone"] + "|") and len(dots[0].split("|", 1)[1]) > 20, f"{dots}; fresh={ix['fresh']}")
        check("Horizon scan dot: green when everything the latest scan found is reconciled, yellow while anything is open (with a text label)", len(dots) == 2 and dots[1].startswith("stat " + ix["scan"]["tone"] + "|") and len(dots[1].split("|", 1)[1]) > 20, f"{dots}; scan={ix['scan']}")

        # 4. Landmark celebration weeks in every view (next dated edition of each).
        series = {s["id"]: s for s in data["series"]}
        for name in LANDMARKS:
            eds = sorted((e for e in data["editions"] if series[e["series"]]["name"] == name and (e.get("verify") or {}).get("state") != "expected" and (e.get("end") or e["start"]) >= today), key=lambda e: e["start"])
            if not eds:
                # Between editions (the next is not announced yet), the series must still be findable in the Directory.
                had = any(series[e["series"]]["name"] == name and (e.get("verify") or {}).get("state") != "expected" for e in data["editions"])
                go("display=directory")
                check(f"{name}: between editions, still listed in Directory", had and name in page.inner_text("#view"), "no upcoming dated edition yet")
                continue
            month = eds[0]["start"][:7]
            go(f"display=list&cal={month}")
            check(f"{name} in List ({month})", name in page.inner_text(f"#list-month-{month}"))
            go(f"display=calendar&cal={month}")
            check(f"{name} in Calendar ({month})", name in page.inner_text("#view .cal"))
            go(f"cal={month}")
            in_window = page.locator(f".orbit-month[data-orbit-month='{month}']").count() == 1
            check(f"{name} in Orbit Celebrations ({month})", in_window and name in text(".orbit-group.obs"))
            go("display=directory")
            check(f"{name} in Directory", name in page.inner_text("#view"))

        # 5. Each Focus, each view.
        go("display=list&focus=celebrations")
        ev = page.locator("#view .ev")
        check("Focus Celebrations → List shows only celebrations", ev.count() > 0 and all("Celebration" in t for t in texts("#view .ev .badges")), f"{ev.count()} rows")
        go("display=list&focus=conferences")
        check("Focus Conferences → List shows no celebrations", page.locator("#view .ev").count() > 0 and not any("Celebration" in t for t in texts("#view .ev .badges")))
        go("display=list&focus=due")
        due = page.evaluate("[...document.querySelectorAll('#view .ev')].map(x => x.classList.contains('by-due'))")
        check("Focus Abstracts Due → List rows are ordered by due date", len(due) > 0 and all(due), f"{len(due)} rows")
        go("display=list&focus=open")
        pills = page.evaluate("[...document.querySelectorAll('#view .ev .pill')].map(x => x.className)")
        check("Focus Open Abstracts → every row's call is open", len(pills) > 0 and all(re.search(r"\b(open|urgent)\b", c) for c in pills), f"{len(pills)} rows")
        for f, cat in [("due", "due"), ("open", "open"), ("conferences", "meet"), ("celebrations", "obs")]:
            go(f"focus={f}")
            bars = page.evaluate("[...document.querySelectorAll('.orbit-month')].map(m => [...m.querySelectorAll('.orbit-columns i')].map(i => i.className).join(','))")
            groups = page.evaluate("[...document.querySelectorAll('.orbit-group')].map(g => g.className + (g.open ? ':open' : ''))")
            check(f"Focus {f} → Orbit shows one bar per month and one open group", all(b == cat for b in bars) and groups == [f"orbit-group {cat}:open"], f"{set(bars)} {groups}")
        go("")
        check("Focus All → Orbit shows four bars and four collapsed groups",
              page.evaluate("[...document.querySelectorAll('.orbit-month')].every(m => m.querySelectorAll('.orbit-columns i').length === 4)")
              and page.evaluate("[...document.querySelectorAll('.orbit-group')].map(g => g.className.split(' ')[1] + (g.open ? ':open' : ''))") == ["due", "meet", "open", "obs"])
        go(f"display=calendar&focus=due&cal={today[:7]}")
        check("Focus Abstracts Due → Calendar shows only due-day marks", page.evaluate("[...document.querySelectorAll('#view .ce')].every(c => c.classList.contains('call') && c.classList.contains('due'))"))
        go(f"display=calendar&focus=conferences&cal={today[:7]}")
        check("Focus Conferences → Calendar shows no calls or celebrations", page.evaluate("[...document.querySelectorAll('#view .ce')].every(c => c.classList.contains('meet'))"))
        go("display=directory&focus=celebrations")
        check("Focus Celebrations → Directory lists celebration series", "National APP Week" in page.inner_text("#view") and page.locator("#view .srs").count() <= 25)

        # 6. Legacy links and URL round trip.
        go("focus=clinical")
        check("old focus=clinical link opens Scope → Clinical", page.locator("#quickscope [data-scope='clinical']").get_attribute("aria-pressed") == "true" and page.locator("#quickfocus [data-focus='']").get_attribute("aria-pressed") == "true")
        go("scope=year")
        check("old scope=year link opens the twelve-month Orbit", page.locator("[data-orbit-year]").get_attribute("aria-pressed") == "true")
        go("open=1")
        check("old open=1 link opens Focus → Open Abstracts", page.locator("#quickfocus [data-focus='open']").get_attribute("aria-pressed") == "true")
        go("kind=observance")
        check("old kind=observance link opens Focus → Celebrations", page.locator("#quickfocus [data-focus='celebrations']").get_attribute("aria-pressed") == "true")
        for old in ("prof=STU", "prof=DNP", "view=students"):
            go(old)
            check(f"old {old} link opens Scope → Students", page.locator("#quickscope [data-scope='students']").get_attribute("aria-pressed") == "true")
        go("")
        page.click("#quickscope [data-scope='students']")
        page.click("#quickfocus [data-focus='due']")
        h = page.evaluate("location.hash")
        check("Scope and Focus are written to the address", "scope=students" in h and "focus=due" in h, h)
        page.reload(wait_until="networkidle")
        check("Scope and Focus survive a reload", page.locator("#quickscope [data-scope='students']").get_attribute("aria-pressed") == "true" and page.locator("#quickfocus [data-focus='due']").get_attribute("aria-pressed") == "true")

        # 7. Records, contact and handoff.
        go("display=list")
        # A confirmed record is presumed right: a record that passed its check carries no verification badge; a note appears
        # only for an exception, projection, rule or save-the-date.
        cards = page.evaluate("[...document.querySelectorAll('#view .ev')].map(c => [c.dataset.e, !!c.querySelector('.side .vf, .side .source-note')])")
        by_id = {e["id"]: e for e in data["editions"]}
        wrong = [i for i, has in cards if has and (by_id.get(i, {}).get("verify") or {}).get("state") == "verified"]
        check("verified records carry no verification badge on List cards", len(cards) > 0 and not wrong, f"{len(cards)} cards, {sum(h for _, h in cards)} with a note, {len(wrong)} verified with a note")
        mail = page.locator("[data-request]").first.get_attribute("href") or ""
        check("request address is mark.karasin@protonmail.com", mail.startswith("mailto:mark.karasin@protonmail.com"), mail[:60])
        html = page.content().lower()
        check("no Rutgers email address on the page", "@rutgers.edu" not in html and "rutgers.edu\"" not in html.replace("nursing.rutgers.edu", ""))
        # The AI Handoff opens on this site for anyone: no GitHub page, account or app on the way (2026-09-26,
        # after the curator's phone met a GitHub sign-in page; the old check compared only the link's text).
        handoff = page.locator("a.hbtn", has_text="AI Handoff").get_attribute("href")
        check("AI Handoff opens the handoff on this site, not on GitHub", handoff == "ai-handoff.html", handoff)
        # A public index ships with its definition: the footer and each index note point to it (hover notes do not reach phones).
        defs = page.evaluate("[...document.querySelectorAll('footer a, .method-summary a')].map(a => a.href)")
        page.locator("#updated button.idx").first.click()
        notes = page.evaluate("[...document.querySelectorAll('#idx-note a')].map(a => a.href)")
        page.keyboard.press("Escape")
        hurl = urljoin(base, "ai-handoff.html")
        md = page.request.get(urljoin(base, "AI-HANDOFF.md")).body()
        want = [re.sub(r"[`*]", "", ln.split(" ", 1)[1]).strip() for ln in re.sub(r"(?ms)^```.*?^```", "", md.decode("utf-8")).splitlines() if re.match(r"#{1,3} ", ln)]
        herrs = []
        hctx = browser.new_context(viewport={"width": 1440, "height": 1000})   # a fresh browser: no cookies, not signed in anywhere
        hpg = hctx.new_page()
        hpg.on("console", lambda m: herrs.append(m.text) if m.type == "error" else None)
        resp = hpg.goto(hurl, wait_until="load")
        check("the AI Handoff page opens with no sign-in (HTTP 200, on this site, no password field)",
              resp is not None and resp.status == 200 and hpg.url.startswith(base) and hpg.locator("input[type=password]").count() == 0,
              f"{resp.status if resp else None} {hpg.url}")
        heads = hpg.evaluate("""[...document.querySelectorAll('#doc h1, #doc h2, #doc h3')].map(h => [h.id,
            [...h.childNodes].filter(n => !(n.nodeType === 1 && n.classList.contains('anchor'))).map(n => n.textContent).join('').trim()])""")
        check("the AI Handoff page shows every heading of AI-HANDOFF.md, in order", [t for _, t in heads] == want, f"{len(heads)} on the page, {len(want)} in the file")
        meta = lambda n: hpg.evaluate("n => (document.querySelector(`meta[name=${n}]`) || {}).content || ''", n)   # absent on a broken page: report, don't wait
        sha = meta("handoff-source-sha256")
        check("the AI Handoff page was rendered from the AI-HANDOFF.md this site serves", sha == hashlib.sha256(md).hexdigest(), sha[:12])
        robots = meta("robots")
        check("the AI Handoff page asks search engines not to index it", "noindex" in robots, robots)
        sec = next((hid for hid, t in heads if t.startswith("3.4 ")), None)
        target = urljoin(hurl, "#" + sec) if sec else None
        check("footer and index notes link the index definitions on this site (AI Handoff §3.4)", bool(target) and target in defs and target in notes, f"{target}; notes {notes}")
        if target:
            hpg.goto(target, wait_until="load")
            top = hpg.evaluate("id => document.getElementById(id).getBoundingClientRect().top", sec)
            check("a section link opens the AI Handoff at that section", 0 <= top < 200, f"{top:.0f}px from the top")
        hctx.close()
        UA_IPHONE = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
        hctx = browser.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, user_agent=UA_IPHONE)
        hpg = hctx.new_page()
        hpg.on("console", lambda m: herrs.append(m.text) if m.type == "error" else None)
        hpg.goto(hurl, wait_until="load")
        fit = hpg.evaluate("""() => ({over: document.scrollingElement.scrollWidth - window.innerWidth,
            wide: [...document.querySelectorAll('.table-wrap, pre')].filter(x => x.getBoundingClientRect().right > window.innerWidth + 1).length,
            h1: document.querySelector('#doc h1').getBoundingClientRect().top})""")
        check("phone: the AI Handoff page fits the screen (tables and code scroll inside their own box)", fit["over"] <= 0 and fit["wide"] == 0, str(fit))
        check("phone: the AI Handoff's title is on the first screen", 0 <= fit["h1"] < 844, f"{fit['h1']:.0f}px")
        hctx.close()
        check("the AI Handoff page loads with no console errors", not herrs, "; ".join(herrs[:3]))

        # 8. Layout at desktop and phone widths.
        for w in (1440, 390):
            page.set_viewport_size({"width": w, "height": 900})
            for hash_ in ("", "display=list&focus=due", "display=calendar"):
                go(hash_)
                over = page.evaluate("document.scrollingElement.scrollWidth - window.innerWidth")
                check(f"no horizontal page scroll at {w} px ({hash_ or 'Orbit'})", over <= 0, f"{over}px")
        # 9. Phones: upright and sideways, with touch, as a phone reports itself. The desktop
        #    layout must not change; that is checked by screenshot diff at release and guarded here.
        page.set_viewport_size({"width": 1440, "height": 1000})
        go("display=calendar")
        check("desktop Calendar keeps the month grid (no phone agenda)", page.locator("#view .calspan").count() == 1 and page.locator("#view .agenda").count() == 0)
        check("desktop header keeps the full action labels", page.evaluate("[...document.querySelectorAll('.hb-short')].every(x => getComputedStyle(x).display === 'none')"))
        UA_PHONE = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
        for (pw, ph, orient) in ((390, 664, "upright"), (844, 340, "sideways")):
            ctx = browser.new_context(viewport={"width": pw, "height": ph}, is_mobile=True, has_touch=True, user_agent=UA_PHONE)
            ph_page = ctx.new_page()
            ph_page.on("pageerror", lambda e: errors.append(str(e)))
            def pgo(hash_=""):
                ph_page.goto(base + ("#" + hash_ if hash_ else ""), wait_until="networkidle")
                ph_page.reload(wait_until="networkidle")
                ph_page.wait_for_selector("#quickfocus .chip", timeout=15000)
            pgo("display=calendar")
            tops = ph_page.evaluate("[...document.querySelectorAll('.viewtools .seg button')].map(b => Math.round(b.getBoundingClientRect().top))")
            check(f"phone {orient}: the four display buttons sit on one row", len(tops) == 4 and max(tops) - min(tops) <= 2, str(tops))
            over = ph_page.evaluate("document.scrollingElement.scrollWidth - window.innerWidth")
            check(f"phone {orient}: no sideways page scroll", over <= 0, f"{over}px")
            if orient == "upright":
                rows = ph_page.evaluate("""['#quickprof','#quickfocus','#quickscope'].map(s => { const e = document.querySelector(s), cs = getComputedStyle(e);
                    return {h: Math.round(e.getBoundingClientRect().height), more: e.scrollWidth > e.clientWidth, scrolls: cs.overflowX === 'auto',
                            fade: (cs.maskImage || cs.webkitMaskImage || 'none') !== 'none'}; })""")
                check("phone upright: each chip row is one line, and a row with more chips swipes and fades at the edge",
                      all(r["h"] < 45 and (not r["more"] or (r["scrolls"] and r["fade"])) for r in rows), str(rows))
                cal = ph_page.evaluate("""() => ({agenda: !!document.querySelector('#view .agenda'), grid: !!document.querySelector('#view .calspan'),
                    wide: [...document.querySelectorAll('#view .ag-item')].filter(x => x.getBoundingClientRect().right > innerWidth + 1).length,
                    items: document.querySelectorAll('#view .ag-item').length, viewTop: Math.round(document.querySelector('#view').getBoundingClientRect().top)})""")
                check("phone upright: Calendar is a day-by-day agenda that fits the screen", cal["agenda"] and not cal["grid"] and cal["items"] > 0 and cal["wide"] == 0, str(cal))
                check("phone upright: the view starts on the first screen", cal["viewTop"] < ph, f"view top {cal['viewTop']} px, screen {ph} px")
                series = {s["id"]: s for s in data["series"]}
                apw = sorted((e for e in data["editions"] if series[e["series"]]["name"] == "National APP Week" and (e.get("verify") or {}).get("state") != "expected" and (e.get("end") or e["start"]) >= today), key=lambda e: e["start"])
                if apw:
                    pgo(f"display=calendar&cal={apw[0]['start'][:7]}")
                    # Visible, not merely present: textContent also reads a collapsed <details>.
                    check("phone upright: National APP Week is visible in the Calendar agenda", ph_page.evaluate(VISIBLE_JS, "National APP Week"))
            else:
                pos = ph_page.evaluate("getComputedStyle(document.querySelector('.bar')).position")
                check("phone sideways: the filter bar scrolls away instead of covering the page", pos != "sticky", pos)
                grid = ph_page.evaluate("(() => { const g = document.querySelector('#view .calspan'); return g ? Math.round(g.getBoundingClientRect().right) : -1; })()")
                check("phone sideways: the Calendar month grid fits the screen", 0 < grid <= pw, f"grid right edge {grid} px, screen {pw} px")
            ctx.close()
        # 10. Header wording and the browser-tab icons.
        page.set_viewport_size({"width": 1440, "height": 1000})
        go("")
        eyebrow = page.evaluate("(document.querySelector('.headactions .eyebrow') || {}).textContent || ''").strip()
        check("header tagline is the curator's wording", eyebrow == TAGLINE, eyebrow)
        # Every icon URL carries ?v=<first 8 hex of its SHA-256>, so a changed icon is a new URL (browsers
        # keep an icon whose bytes change under the same URL).
        import json as _json, xml.etree.ElementTree as ET   # hashlib is imported at the top
        from urllib.parse import urlsplit, parse_qs   # urljoin is imported at the top
        links = page.evaluate("[...document.querySelectorAll('link[rel~=icon],link[rel=apple-touch-icon],link[rel=mask-icon],link[rel=manifest]')].map(l => [l.rel, l.getAttribute('href'), l.type || ''])")
        def stamp_ok(href, rel_to):
            url = urljoin(rel_to, href)
            body = page.request.get(url).body()
            v = (parse_qs(urlsplit(href).query).get("v") or [""])[0]
            return v == hashlib.sha256(body).hexdigest()[:8], body
        for rel, href, typ in links:
            ok, body = stamp_ok(href, base)
            check(f"{rel} {href.split('?')[0]} carries its content version", ok, href)
            if rel == "manifest":
                for ic in _json.loads(body)["icons"]:
                    ok2, _ = stamp_ok(ic["src"], urljoin(base, href))
                    check(f"manifest icon {ic['src'].split('?')[0]} carries its content version", ok2, ic["src"])
            if typ == "image/svg+xml":
                root = ET.fromstring(body)
                paths = [el for el in root.iter() if el.tag.endswith("path")]
                texts = [el for el in root.iter() if el.tag.endswith("text")]
                # the tab icon is the scarlet horizon and the three navy lanes, no letters
                check("tab icon draws only the horizon and three lanes (no letters)", len(paths) == 4 and not texts, f"{len(paths)} paths, {len(texts)} text")

        # 11. Date-dependent cases, run at a fixed clock (FIXED_NOW, New York).
        fctx = browser.new_context(viewport={"width": 1440, "height": 1000}, timezone_id="America/New_York")
        fpg = fctx.new_page()
        fpg.clock.set_fixed_time(FIXED_NOW)
        fpg.on("pageerror", lambda e: errors.append(str(e)))
        def fgo(hash_=""):
            fpg.goto(base + ("#" + hash_ if hash_ else ""), wait_until="networkidle")
            fpg.reload(wait_until="networkidle")
            fpg.wait_for_selector("#quickfocus .chip", timeout=15000)
        # Filter-logic checks read textContent: a collapsed month section must not hide a record from the test.
        vtext = lambda: fpg.evaluate("document.querySelector('#view').textContent")
        fgo("display=list&q=AAAA&prof=CRNA&scope=students")   # AAAA, filed under CRNA, with its student opportunity
        view = vtext()
        check("AAAA keeps the organizer's wording: CAA student posters", "CAA student posters" in view and "CRNA student posters" not in view)
        fgo("display=list&focus=open")
        check("VAM is not listed as open before its November 18 opening", "Vascular Annual Meeting" not in vtext())
        # Red team F03: NACNS's professional call closed Aug 13; only its student-poster call runs to Sep 27.
        check("NACNS is not listed as an open call after its professional deadline (Aug 13)", "NACNS Annual Conference" not in vtext())
        fgo("display=list&scope=students&q=NACNS")
        due = fpg.evaluate("[...document.querySelectorAll('#view article')].filter(a => a.textContent.includes('NACNS Annual Conference')).map(a => (a.querySelector('.student-due') || {}).textContent || '')")
        check("NACNS student posters stay listed under Students with their Sep 27 deadline", "Submit by Sep 27" in due, " | ".join(due))
        # Red team F04: every call open on the fixed day that closes in its month shows in Orbit's Open Abstracts for that month.
        day = FIXED_NOW[:10]
        def open_on(e):
            c = e.get("call") or {}; cl, op = c.get("closes"), c.get("opens")
            return bool(cl) and cl >= day and not (op and op > day) and (c.get("status") == "open" or bool(op and op <= day))
        names = {s["id"]: s["name"] for s in data["series"]}
        closing = sorted({names[e["series"]] for e in data["editions"] if e["series"] in names and open_on(e) and e["call"]["closes"][:7] == day[:7]})
        fgo("focus=open&cal=" + day[:7])
        orbit_open = fpg.evaluate("[...document.querySelectorAll('.orbit-group.open .orbit-item')].map(x => x.textContent).join(' | ')")
        gone = [n for n in closing if n not in orbit_open]
        check("Orbit Open Abstracts keeps every call in the month it closes", bool(closing) and not gone, f"{len(closing)} due this month; missing: {gone}")
        fgo("focus=conferences&cal=2026-10")
        n_all = int(fpg.evaluate("(document.querySelector('.orbit-group.meet summary b') || {}).textContent || '0'"))
        n_before = fpg.locator(".orbit-group.meet .orbit-item").count()
        if fpg.locator(".orbit-group.meet button.orbit-more").count():
            fpg.click(".orbit-group.meet button.orbit-more")
        n_after = fpg.locator(".orbit-group.meet .orbit-item").count()
        check("Orbit month shows every meeting after Show all", n_all > 12 and n_before == 12 and n_after == n_all, f"{n_before} → {n_after} of {n_all}")
        fgo("display=directory&q=cardiac%20surgery")
        check("Directory finds series for 'cardiac surgery', as List does", fpg.locator("#view .srs").count() > 0, f"{fpg.locator('#view .srs').count()} series")
        fgo("display=directory")
        dom = fpg.evaluate("""({stray: document.querySelectorAll('#view .dir > :not(.srs)').length, nested: document.querySelectorAll('#view button button').length,
            cards: document.querySelectorAll('#view .srs').length, whole: [...document.querySelectorAll('#view .srs')].every(c => c.querySelector('.badges') && c.querySelector('.meta') && c.querySelector('.srs-open'))})""")
        check("Directory cards hold their badges, dates and years (no nested buttons)", dom["cards"] > 0 and dom["stray"] == 0 and dom["nested"] == 0 and dom["whole"], str(dom))
        fgo("display=list&near=49690&r=50")
        check("a venue pinned to its town is found near it (MAPA, Williamsburg MI)", "MAPA Fall CME Conference" in vtext())
        # VCNP 2027 was pinned only to its state until its venue was announced (corrected 2026-09-26); Charter Oak's venue,
        # Westbrook CT, is a town the geocoder places only at its state, so it takes over the state-pin case.
        pinned = {e["id"]: (e.get("geo") or {}).get("precision") for e in data["editions"] if e["id"] in ("50a6bc48cd8f", "3eecefb90b41")}
        fgo("display=list&near=06498&r=50")
        check("a record pinned only to a state is left out of distance results (Charter Oak 2027, Westbrook CT)",
              pinned.get("50a6bc48cd8f") == "state" and "Charter Oak Conference" not in vtext(), str(pinned))
        fgo("display=list&near=24016&r=25")
        check("VCNP 2027 is found near Roanoke once its venue is announced", pinned.get("3eecefb90b41") == "city" and "VCNP Annual Conference" in vtext(), str(pinned))
        fgo("display=calendar&cal=2026-09")   # National APP Week 2026 (Sep 21-25) is under way at FIXED_NOW
        check("National APP Week styled in the calendar", fpg.locator(".ce.appweek").count() >= 1, f"{fpg.locator('.ce.appweek').count()} styled cells")
        # A verification older than 36 hours: the dot turns red and only rule dates count as confirmed. The same data is
        # served with its verification stamp set three days before the fixed clock; the page must show what
        # scripts/indices.py derives for that clock.
        stale_at = "2026-09-21T16:00:00Z"
        stale_d = {}
        def stale(route):
            resp = route.fetch(); d = resp.json()
            d["sources_checked"] = stale_at
            stale_d.update(d)
            route.fulfill(response=resp, body=_json.dumps(d))
        fpg.route("**/data/runway.json*", stale)
        fgo("")
        shown = fpg.evaluate("""({dot: (document.querySelector('#updated .stat') || {}).className || '', head: document.querySelector('#updated').innerText,
            note: [...document.querySelectorAll('#updated .idx')].map(x => x.title).find(x => x.startsWith('Confirmation:')) || ''})""")
        fpg.unroute("**/data/runway.json*")
        sx = indices.compute(stale_d, FIXED_NOW[:10], _dt.datetime.fromisoformat(FIXED_NOW))["reliability"] if stale_d else None
        check("a verification older than 36 hours turns the dot red and counts only rule dates",
              bool(sx) and shown["dot"] == "stat bad" and sx["machine"] == 0 and f"Reliability Index: {sx['pct']:.2f}%" in shown["head"] and "no nightly verification has been recorded in the last 36 hours" in shown["note"],
              f"{shown['dot']}; derived {sx['pct'] if sx else None}; {shown['note'][:90]}")
        # The Horizon scan dot reads the scan's reconciliation, not its age: a scan with nothing open is green, one with
        # findings still open is yellow, and one with no reconciliation recorded is yellow; never red.
        for label, rec, want in (("with nothing open", {"missing": 37, "added": 30, "rejected": 7, "open": 0, "as_of": "2026-09-20T12:00:00Z"}, "stat ok"),
                                 ("with findings open", {"missing": 37, "added": 2, "rejected": 0, "open": 35, "as_of": "2026-09-20T12:00:00Z"}, "stat warn"),
                                 ("with no reconciliation recorded", None, "stat warn")):
            def scan_rec(rec):   # a factory, not a default argument: Playwright passes a handler's second argument the request
                def h(route):
                    resp = route.fetch(); d = resp.json()
                    for pr in d.get("probes") or []:
                        pr["finished"] = "2026-08-01T12:00:00Z"   # an old scan: its age must not colour the dot
                        if rec is None: pr.pop("reconciliation", None)
                        else: pr["reconciliation"] = rec
                    route.fulfill(response=resp, body=_json.dumps(d))
                return h
            fpg.route("**/data/runway.json*", scan_rec(rec))
            fgo("")
            got = fpg.evaluate("[...document.querySelectorAll('#updated .stat')].map(x => x.className)")
            fpg.unroute("**/data/runway.json*")
            check(f"a horizon scan {label} shows a {'green' if want.endswith('ok') else 'yellow'} dot, whatever its age", got[1:2] == [want], str(got))
        fctx.close()
        # A phone at the fixed clock: a record that started earlier this month and is still running stays in view.
        pctx = browser.new_context(viewport={"width": 390, "height": 664}, is_mobile=True, has_touch=True, timezone_id="America/New_York",
                                   user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1")
        ppg = pctx.new_page(); ppg.clock.set_fixed_time(FIXED_NOW)
        ppg.goto(base + "#display=calendar", wait_until="networkidle"); ppg.reload(wait_until="networkidle")
        ppg.wait_for_selector("#view .agenda", timeout=15000)
        check("phone agenda shows National APP Week while it is under way", ppg.evaluate(VISIBLE_JS, "National APP Week"))
        pctx.close()
        # 12. Phones and tablets: Orbit months never overlap on a phone; a phone offers the desktop
        #     layout and back; tablets held upright see the whole month grid; desktops show no switch.
        mctx = browser.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, user_agent=UA_PHONE, timezone_id="America/New_York")
        mpg = mctx.new_page()
        mpg.goto(base, wait_until="networkidle"); mpg.wait_for_selector(".orbit-month")
        ov = mpg.evaluate("""(() => { const r=[...document.querySelectorAll('.orbit-month, .orbit-core')].map(m => m.getBoundingClientRect()); let n=0;
            for (let i=0;i<r.length;i++) for (let j=i+1;j<r.length;j++) { const a=r[i], b=r[j]; if (Math.min(a.right,b.right)-Math.max(a.left,b.left) > 1 && Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top) > 1) n++; } return n; })()""")
        check("phone: no Orbit month card overlaps another or the year control", ov == 0, f"{ov} overlapping pairs")
        label = mpg.inner_text(".layout-toggle") if mpg.locator(".layout-toggle").is_visible() else ""
        check("phone: a Desktop layout switch is offered", label == "Desktop layout", label)
        mpg.goto(base + "#display=calendar", wait_until="networkidle"); mpg.wait_for_selector("#view .agenda")
        mpg.click(".layout-toggle"); mpg.wait_for_timeout(600)
        st_d = mpg.evaluate("({w: innerWidth, scale: visualViewport.scale, grid: !!document.querySelector('#view .calspan'), label: document.querySelector('.layout-toggle').textContent})")
        check("phone: the switch shows the desktop layout, fitted to the screen", st_d["w"] >= 1270 and st_d["scale"] < 0.5 and st_d["grid"] and st_d["label"] == "Switch to the mobile layout", str(st_d))
        mpg.locator(".layout-toggle").dispatch_event("click"); mpg.wait_for_timeout(600)
        st_m = mpg.evaluate("({w: innerWidth, agenda: !!document.querySelector('#view .agenda'), label: document.querySelector('.layout-toggle').textContent})")
        check("phone: the switch returns to the mobile layout", st_m["w"] == 390 and st_m["agenda"] and st_m["label"] == "Desktop layout", str(st_m))
        mctx.close()
        for tw, th in ((768, 1024), (820, 1180)):
            tctx = browser.new_context(viewport={"width": tw, "height": th}, is_mobile=True, has_touch=True, timezone_id="America/New_York")
            tpg = tctx.new_page(); tpg.goto(base + "#display=calendar", wait_until="networkidle"); tpg.wait_for_selector("#view .cal")
            fit = tpg.evaluate("(() => { const w=document.querySelector('#view .calwrap'); return {inner: w ? w.scrollWidth - w.clientWidth : 0, sw: getComputedStyle(document.querySelector('.layout-strip')).display}; })()")
            check(f"tablet {tw} px upright: the month grid fits the screen, no layout switch", fit["inner"] <= 1 and fit["sw"] == "none", str(fit))
            tctx.close()
        check("desktop: no layout switch", not page.locator(".layout-toggle").is_visible())

        # 12b. Red-team fixes of 2026-09-25 (F05, F10, F11, F13, F16, F17, F20, F23), at the fixed clock.
        from urllib.parse import quote
        rctx = browser.new_context(viewport={"width": 1440, "height": 1000}, timezone_id="America/New_York")
        rpg = rctx.new_page(); rpg.clock.set_fixed_time(FIXED_NOW)
        rpg.on("pageerror", lambda e: errors.append(str(e)))
        def rgo(hash_=""):
            rpg.goto(base + ("#" + hash_ if hash_ else ""), wait_until="networkidle")
            rpg.reload(wait_until="networkidle")
            rpg.wait_for_selector("#quickfocus .chip", timeout=15000)
        day = FIXED_NOW[:10]
        # F16: each index opens its definition on click (tap) and closes with Escape.
        rgo("")
        n_idx = rpg.locator("#updated button.idx").count()
        shown = closed = False
        if n_idx:   # an older page has no index buttons: the check fails instead of stopping the run
            rpg.locator("#updated button.idx").first.click()
            shown = rpg.locator("#idx-note").is_visible() and "qualifying dated meetings" in rpg.inner_text("#idx-note")
            rpg.keyboard.press("Escape")
            closed = not rpg.locator("#idx-note").is_visible()
        check("F16: each index opens its definition on click or tap; Escape closes it", n_idx == 2 and shown and closed, f"{n_idx} index buttons, shown={shown}, closed={closed}")
        # F17: no control inside a control; a list card opens from its title button; the month grid claims no grid role.
        rgo("display=list")
        sem = rpg.evaluate("""({nested: document.querySelectorAll('#view button button, #view [role=button] button').length,
            cards: document.querySelectorAll('#view article.ev').length, open: document.querySelectorAll('#view article.ev .ev-open').length,
            rolebtn: document.querySelectorAll('#view article[role=button]').length})""")
        opened = False
        if sem["open"]:
            rpg.locator("#view article.ev .ev-open").first.click()
            opened = rpg.evaluate("document.querySelector('#dlg').open")
            rpg.keyboard.press("Escape")
        rgo("display=calendar")
        grid = rpg.locator("#view [role=grid]").count()
        check("F17: list cards hold no nested controls and open from their title button; the month grid claims no grid role",
              sem["cards"] > 0 and sem["open"] == sem["cards"] and sem["nested"] == 0 and sem["rolebtn"] == 0 and opened and grid == 0, f"{sem} dialog={opened} grid={grid}")
        # F11: every call open on the fixed day with no due date is listed above that month's grid.
        names = {s["id"]: s["name"] for s in data["series"]}
        want_undated = sorted({names[e["series"]] for e in data["editions"] if e["series"] in names and (e.get("end") or e["start"]) >= day
                               and (e.get("verify") or {}).get("state") != "expected" and (e.get("call") or {}).get("status") == "open" and not (e.get("call") or {}).get("closes")})
        undated = rpg.inner_text(".undatedrow") if rpg.locator(".undatedrow").count() else ""
        check("F11: calls open with no due date are listed above this month's grid", all(n in undated for n in want_undated), f"{len(want_undated)} expected: {undated[:160]}")
        rgo("display=list&focus=open")
        v = rpg.evaluate("document.querySelector('#view').textContent")
        check("calls the organizer has closed are not listed as open (NPAA, Feb 27; ACS Innovation Summit, Aug 10)", "NPAA Annual Conference" not in v and "Innovation Summit" not in v)
        # F13: a place filter judges the edition a Directory card offers (ISHLT: Prague in 2024, Sydney next).
        rgo("display=directory&area=c:Europe")
        eu = rpg.evaluate("[...document.querySelectorAll('#view .srs .title')].map(x => x.textContent)")
        rgo("display=directory&area=c:Oceania")
        oc = rpg.evaluate("[...document.querySelectorAll('#view .srs .title')].map(x => x.textContent)")
        check("F13: Directory place filters use the edition the card offers (ISHLT under Oceania, not Europe)", "ISHLT Annual Meeting" not in eu and "ISHLT Annual Meeting" in oc, f"{len(eu)} in Europe, {len(oc)} in Oceania")
        # F05: qualified place names resolve to that state or province; an unknown place is reported.
        def near_label(q):
            rgo("display=list&near=" + quote(q) + "&r=50")
            return rpg.inner_text("#geoquick .nearmsg") if rpg.locator("#geoquick .nearmsg").count() else ""
        probes = {"Springfield, IL": "Illinois", "Springfield IL": "Illinois", "Portland, ME": "Maine", "Columbus, GA": "Georgia", "Kansas City, KS": "Kansas", "London, ON": "Ontario"}
        got = {q: near_label(q) for q in probes}
        check("F05: 'City, ST' and 'City ST' resolve to that state or province", all(w in got[q] for q, w in probes.items()), "; ".join(f"{q} → {got[q]}" for q in probes))
        rgo("display=list&near=" + quote("Qwertyville, ZZ") + "&r=50")
        check("F05: an unknown place is reported above the results, not silently dropped", rpg.locator("#view .nearmiss").is_visible())
        # F20: a record whose organizer page was removed says so and offers the Internet Archive.
        dead = next((e["id"] for e in data["editions"] if e.get("link_dead") and e.get("source_url")), None)
        if dead:
            rgo("e=" + dead)
            dtext = rpg.inner_text("#dlg")
            rpg.keyboard.press("Escape")
        check("F20: a record whose organizer page was removed says so and links an archived copy", not dead or ("removed this page" in dtext and "archived copy" in dtext), dead or "no removed pages")
        rctx.close()
        # F10: a published cut-off time closes the call at that instant, wherever the visitor is. The served data is given
        # one call closing Oct 6 at 1 p.m. New York time; a visitor in Los Angeles loads the page 30 minutes before and after.
        def with_cutoff(route):
            resp = route.fetch(); d2 = resp.json()
            for e in d2["editions"]:
                if e.get("id") == "fff7c127c15a":
                    e["call"] = {"status": "open", "opens": None, "closes": "2026-10-06", "due_time": "13:00", "tz": "America/New_York", "text": "test", "url": None}
            route.fulfill(response=resp, body=_json.dumps(d2))
        seen = []
        for t in ("2026-10-06T09:30:00-07:00", "2026-10-06T10:30:00-07:00"):
            cctx = browser.new_context(viewport={"width": 1440, "height": 1000}, timezone_id="America/Los_Angeles")
            cpg = cctx.new_page(); cpg.clock.set_fixed_time(t); cpg.route("**/data/runway.json*", with_cutoff)
            cpg.goto(base + "#display=list&focus=open&q=ACC.27", wait_until="networkidle"); cpg.wait_for_selector("#quickfocus .chip")
            seen.append(cpg.evaluate("document.querySelector('#view').textContent"))
            cctx.close()
        check("F10: a call with a published cut-off closes at that time, wherever the visitor is",
              "Closes today, 1:00 PM EDT" in seen[0] and "ACC.27" not in seen[1], f"before: {'Closes today, 1:00 PM EDT' in seen[0]}; still listed after: {'ACC.27' in seen[1]}")
        # F23: when the calendar day has changed, a tab that is shown again reloads so statuses are recomputed.
        dctx = browser.new_context(viewport={"width": 1440, "height": 1000}, timezone_id="America/New_York")
        dpg = dctx.new_page(); dpg.clock.set_fixed_time(FIXED_NOW)
        dpg.goto(base + "#display=list", wait_until="networkidle"); dpg.wait_for_selector("#quickfocus .chip")
        dpg.evaluate("window.__sameDoc = 1")
        dpg.clock.set_fixed_time(day + "T23:59:59-04:00")
        dpg.evaluate("document.dispatchEvent(new Event('visibilitychange'))"); dpg.wait_for_timeout(400)
        same_day_kept = dpg.evaluate("window.__sameDoc === 1")
        dpg.clock.set_fixed_time("2026-09-25T09:00:00-04:00")
        try:
            with dpg.expect_navigation(timeout=8000):
                dpg.evaluate("document.dispatchEvent(new Event('visibilitychange'))")
            reloaded = dpg.evaluate("window.__sameDoc === undefined")
        except Exception:
            reloaded = False
        dctx.close()
        check("F23: a tab reloads when it is shown on a new calendar day, and not before", same_day_kept and reloaded, f"kept same day: {same_day_kept}; reloaded next day: {reloaded}")

        # 13. The calendar feed (runway.ics).
        ics = page.request.get(urljoin(base, "runway.ics")).text().replace("\r\n ", "")
        uids = set(re.findall(r"UID:([0-9a-f]{12})@", ics))
        # The feed's contract: every upcoming dated record the site shows as settled. A record in an exception
        # state (for example a page that timed out tonight) is one the site asks a reader to review, so it is left out.
        settled = {"verified", "rule", "archived", "announced"}
        shown = [e for e in data["editions"] if (e.get("verify") or {}).get("state") in settled and not e.get("month_only") and (e.get("end") or e["start"]) >= today]
        missing = [e["id"] for e in shown if e["id"] not in uids]
        check("calendar feed carries every upcoming record the site shows as settled", not missing, f"{len(shown)} shown, {len(missing)} missing")

        check("no console or page errors", not errors, "; ".join(errors[:3]))
        browser.close()
    if httpd:
        httpd.shutdown()
    failed = [r for r in results if not r[0]]
    print(f"\n{len(results) - len(failed)}/{len(results)} checks passed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
