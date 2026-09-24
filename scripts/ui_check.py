"""Scripted interface check for the Runway (run before every UI push, and against the live site after deploy).

    python scripts/ui_check.py                      # serves ./site locally
    python scripts/ui_check.py --url https://mbkarasin.github.io/app-conference-runway/

Needs Playwright for Python with a Chromium browser (`pip install playwright && playwright install chromium`).
It is a builder's tool; the GitHub workflow does not run it. Every line printed is one assertion; the exit code
is non-zero if any assertion failed. It checks what screenshots have missed before: the display-switch
separators, the year on every Orbit month, the filter rows, the header's Fidelity and Reliability indices
(labels, and values re-derived from the published data), the landmark celebration weeks in every view, each
Focus in each view, legacy links, the request address, the footer's link to the index definitions, phones
held upright and sideways (touch-emulated), and console errors.
"""
import argparse, functools, http.server, re, socketserver, sys, threading
from pathlib import Path
from playwright.sync_api import sync_playwright

LANDMARKS = ["National APP Week", "PA Week", "National Nurse Practitioner Week", "National CRNA Week"]
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
    httpd = socketserver.TCPServer(("127.0.0.1", 0), handler)
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
        # Filter bar since the 2026-09-24 reflow: views beside search; Discipline with Focus to its right;
        # Scope with Location to its right. Each pair shares a row at 1440 px, rows in that order.
        box = lambda sel: page.locator(sel).bounding_box() if page.locator(sel).count() else None
        pairs = [("#viewtools", ".search"), ("#quickprof", "#quickfocus"), ("#quickscope", "#geoquick")]
        rows = []
        for a_sel, b_sel in pairs:
            a, b = box(a_sel), box(b_sel)
            ok = bool(a and b) and b["x"] >= a["x"] + a["width"] - 1 and abs(b["y"] - a["y"]) < 12
            rows.append(a["y"] if a else -1)
            check(f"{b_sel} sits to the right of {a_sel} at 1440 px", ok, f"{a} | {b}")
        check("filter rows run views/search, Discipline/Focus, Scope/Location", rows == sorted(rows) and len(set(rows)) == 3, str(rows))

        # Header indices (2026-09-24): labels, no "metric", and both values re-derived from the page's own data.
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
        fid = 100 * sum(map(fid_ok, dated)) / len(dated)
        import datetime as _dt
        chk = data.get("sources_checked")
        fresh = bool(chk) and (now_ms / 1000 - _dt.datetime.fromisoformat(chk.replace("Z", "+00:00")).timestamp()) / 3600 <= 36
        up = [e for e in dated if not past(e)]
        rule_n = sum(1 for e in up if state(e) == "rule")
        mach_n = sum(1 for e in up if e.get("machine") and state(e) != "rule") if fresh else 0
        rel = 100 * (rule_n + mach_n) / len(up)
        check("Fidelity Index matches its definition re-derived from the data", f"Fidelity Index: {fid:.2f}%" in head, f"derived {fid:.2f}%")
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
        # Since the 2026-09-24 afternoon decision ("fidelity is presumed"), a record that passed its check
        # carries no verification badge; a note appears only for an exception, projection, rule or save-the-date.
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
        # 9. Phones (2026-09-24): upright and sideways, with touch, as a phone reports itself. The desktop
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
                    check("phone upright: National APP Week is in the Calendar agenda", "National APP Week" in ph_page.evaluate("document.querySelector('#view').textContent"))
            else:
                pos = ph_page.evaluate("getComputedStyle(document.querySelector('.bar')).position")
                check("phone sideways: the filter bar scrolls away instead of covering the page", pos != "sticky", pos)
                grid = ph_page.evaluate("(() => { const g = document.querySelector('#view .calspan'); return g ? Math.round(g.getBoundingClientRect().right) : -1; })()")
                check("phone sideways: the Calendar month grid fits the screen", 0 < grid <= pw, f"grid right edge {grid} px, screen {pw} px")
            ctx.close()
        check("no console or page errors", not errors, "; ".join(errors[:3]))
        browser.close()
    if httpd:
        httpd.shutdown()
    failed = [r for r in results if not r[0]]
    print(f"\n{len(results) - len(failed)}/{len(results)} checks passed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
