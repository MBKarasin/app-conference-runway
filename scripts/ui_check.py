"""Scripted interface check for the Runway.

    python scripts/ui_check.py                  # serves ./site locally
    python scripts/ui_check.py --url <site>     # checks a deployed site

Needs Playwright for Python with a Chromium browser (`pip install playwright && playwright install chromium`).
Every line printed is one assertion; the exit code is non-zero if any assertion failed. It checks the display
switch, the Orbit ring, the filter rows, the header's Fidelity and Reliability indices (values re-derived from
the published data), the landmark celebration weeks in every view, each Focus in each view, older links, the
request address and footer links, the header tagline and icon URLs, phone, tablet and desktop layouts, the
calendar feed, and console errors. Date-dependent cases run at a fixed clock (FIXED_NOW) so they reproduce.
"Visible" means rendered with a real box and not inside a closed <details>; text in the DOM is not enough.
"""
import argparse, functools, http.server, re, socketserver, sys, threading
from pathlib import Path
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

        # Header indices: labels, no "metric", and both values re-derived from the page's own data.
        head = page.inner_text("#updated")
        check("header shows Fidelity Index and Reliability Index", "Fidelity Index:" in head and "Reliability Index:" in head, head.replace("\n", " | "))
        check("header does not say 'metric'", "metric" not in head.lower())
        now_ms = page.evaluate("Date.now()")
        eds = [e for e in data["editions"] if e["series"] in {s["id"] for s in data["series"]}]
        state = lambda e: (e.get("verify") or {}).get("state")
        dated = [e for e in eds if state(e) != "expected" and not e.get("month_only")]
        past = lambda e: (e.get("end") or e["start"]) < today
        def days_since(d):
            y, m, dd = map(int, d[:10].split("-")); import datetime as _dt
            return (_dt.date(*map(int, today.split("-"))) - _dt.date(y, m, dd)).days
        def fid_ok(e):
            v = e.get("verify") or {}
            if not (e.get("evidence") or v.get("state") == "rule"): return False
            if v.get("state") not in ("verified", "rule", "announced", "archived"): return False
            if not e.get("source_url"): return False
            if not past(e):
                if e.get("link_dead"): return False
                if v.get("state") != "rule":
                    seen = v.get("last_verified") or v.get("checked")
                    if not seen or days_since(seen) > 90: return False
            return True
        coverage = sum(map(fid_ok, dated)) / len(dated)
        # Times the share projected correct from the pooled independent audits (§3.4). `wrong` is a count;
        # a list (one entry per record) is counted by its length, as app.js does for a stale cached file.
        aud = data.get("audits") or []
        audited = sum(a["audited"] for a in aud)
        wrong = sum(len(a["wrong"]) if isinstance(a.get("wrong"), list) else int(a.get("wrong") or 0) for a in aud)
        fid = 100 * coverage * (1 - (wrong / audited if audited else 0))
        import datetime as _dt
        chk = data.get("sources_checked")
        fresh = bool(chk) and (now_ms / 1000 - _dt.datetime.fromisoformat(chk.replace("Z", "+00:00")).timestamp()) / 3600 <= 36
        up = [e for e in dated if not past(e)]
        rule_n = sum(1 for e in up if state(e) == "rule")
        mach_n = sum(1 for e in up if e.get("machine") and state(e) != "rule") if fresh else 0
        rel = 100 * (rule_n + mach_n) / len(up)
        check("Fidelity Index matches its definition re-derived from the data", f"Fidelity Index: {fid:.2f}%" in head, f"derived {fid:.2f}% = {100*coverage:.2f}% evidence x {100*(1-wrong/audited):.2f}% projected correct ({wrong}/{audited} wrong in {len(aud)} audits)")
        fid_note = page.evaluate("[...document.querySelectorAll('#updated .idx')].map(x => x.title).find(x => x.includes('dated records carry')) || ''")
        check("Fidelity note states the audit basis", audited > 0 and f"found {wrong} of {audited} audited" in fid_note, fid_note[:120])
        check("Reliability Index matches its definition re-derived from the data", f"Reliability Index: {rel:.2f}%" in head, f"derived {rel:.2f}% = ({mach_n} machine + {rule_n} rule) / {len(up)}, fresh={fresh}")

        # 4. Landmark celebration weeks in every view (next dated edition of each).
        series = {s["id"]: s for s in data["series"]}
        for name in LANDMARKS:
            eds = sorted((e for e in data["editions"] if series[e["series"]]["name"] == name and (e.get("verify") or {}).get("state") != "expected" and (e.get("end") or e["start"]) >= today), key=lambda e: e["start"])
            if not eds:
                check(f"{name}: has an upcoming dated edition", False)
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
        go(f"display=calendar&cal={today[:7]}")
        check("National APP Week styled in the calendar", page.locator(".ce.appweek").count() >= 1 or today[:7] != "2026-09")

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
        # Fidelity is presumed: a record that passed its check carries no verification badge; a note appears
        # only for an exception, projection, rule or save-the-date.
        cards = page.evaluate("[...document.querySelectorAll('#view .ev')].map(c => [c.dataset.e, !!c.querySelector('.side .vf, .side .source-note')])")
        by_id = {e["id"]: e for e in data["editions"]}
        wrong = [i for i, has in cards if has and (by_id.get(i, {}).get("verify") or {}).get("state") == "verified"]
        check("verified records carry no verification badge on List cards", len(cards) > 0 and not wrong, f"{len(cards)} cards, {sum(h for _, h in cards)} with a note, {len(wrong)} verified with a note")
        mail = page.locator("[data-request]").first.get_attribute("href") or ""
        check("request address is mark.karasin@protonmail.com", mail.startswith("mailto:mark.karasin@protonmail.com"), mail[:60])
        html = page.content().lower()
        check("no Rutgers email address on the page", "@rutgers.edu" not in html and "rutgers.edu\"" not in html.replace("nursing.rutgers.edu", ""))
        handoff = page.locator("a.hbtn", has_text="AI Handoff").get_attribute("href")
        check("AI Handoff opens the rendered document on GitHub", handoff == "https://github.com/MBKarasin/app-conference-runway/blob/main/site/AI-HANDOFF.md", handoff)
        # A public index ships with its definition: the footer points to it (hover notes do not reach phones).
        defs = page.evaluate("[...document.querySelectorAll('footer a, .method-summary a')].map(a => a.href)")
        check("footer links the index definitions (AI Handoff §3.4)", any(u.endswith("/site/AI-HANDOFF.md#34-verification-pipeline") for u in defs))

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
        import hashlib, json as _json, xml.etree.ElementTree as ET
        from urllib.parse import urljoin, urlsplit, parse_qs
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
        fgo("focus=open&cal=2026-09")
        check("Orbit Open Abstracts keeps NACNS in September, the month it closes", "NACNS Annual Conference" in fpg.evaluate("[...document.querySelectorAll('.orbit-group.open .orbit-item')].map(x => x.textContent).join(' | ')"))
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
        fgo("display=list&near=23219&r=100")
        check("a record pinned only to a state is left out of distance results (VCNP)", "VCNP Annual Conference" not in vtext())
        # An ISO instant older than 90 days must fail the freshness test. The same data is served twice,
        # the second time with one upcoming record's stamp set to 2026-01-01T00:00:00Z.
        fid_count = lambda: fpg.evaluate("(() => { const t = [...document.querySelectorAll('#updated .idx')].map(x => x.title).find(x => x.includes('dated records carry')) || ''; const m = t.match(/(\\d+) of (\\d+)/); return m ? [+m[1], +m[2]] : null; })()")
        fgo("")
        before = fid_count()
        def stale(route):
            resp = route.fetch(); d = resp.json()
            for e in d["editions"]:
                if e.get("id") == "b9f577965d09":
                    e["verify"] = {**(e.get("verify") or {}), "last_verified": "2026-01-01T00:00:00Z", "checked": "2026-01-01T00:00:00Z"}
            route.fulfill(response=resp, body=_json.dumps(d))
        fpg.route("**/data/runway.json*", stale)
        fgo("")
        after = fid_count()
        fpg.unroute("**/data/runway.json*")
        check("an ISO stamp older than 90 days fails the Fidelity freshness test", bool(before and after) and after[0] == before[0] - 1 and after[1] == before[1], f"{before} → {after}")
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
