"""Scripted interface check for the Runway (run before every UI push, and against the live site after deploy).

    python scripts/ui_check.py                      # serves ./site locally
    python scripts/ui_check.py --url https://mbkarasin.github.io/app-conference-runway/

Needs Playwright for Python with a Chromium browser (`pip install playwright && playwright install chromium`).
It is a builder's tool; the GitHub workflow does not run it. Every line printed is one assertion; the exit code
is non-zero if any assertion failed. It checks what screenshots have missed before: the display-switch
separators, the year on every Orbit month, the Scope and Focus rows, the landmark celebration weeks in every
view, each Focus in each view, legacy links, the request address, and console errors.
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
        sb = page.locator("#quickscope").bounding_box() if page.locator("#quickscope").count() else None
        fb = page.locator("#quickfocus").bounding_box()
        check("Focus sits to the right of Scope at 1440 px", bool(sb and fb) and fb["x"] >= sb["x"] + sb["width"] and abs(fb["y"] - sb["y"]) < 8, f"scope {sb}, focus {fb}")
        check("Discipline row sits above Scope", bool(sb) and page.locator("#quickprof").bounding_box()["y"] < sb["y"])

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
        go("")
        page.click("#quickscope [data-scope='students']")
        page.click("#quickfocus [data-focus='due']")
        h = page.evaluate("location.hash")
        check("Scope and Focus are written to the address", "scope=students" in h and "focus=due" in h, h)
        page.reload(wait_until="networkidle")
        check("Scope and Focus survive a reload", page.locator("#quickscope [data-scope='students']").get_attribute("aria-pressed") == "true" and page.locator("#quickfocus [data-focus='due']").get_attribute("aria-pressed") == "true")

        # 7. Records, contact and handoff.
        go("display=list")
        sides = page.evaluate("[...document.querySelectorAll('#view .ev .side')].map(s => !!s.querySelector('.vf, .source-note'))")
        check("every List card shows its verification state", len(sides) > 0 and all(sides), f"{sum(sides)}/{len(sides)}")
        mail = page.locator("[data-request]").first.get_attribute("href") or ""
        check("request address is mark.karasin@protonmail.com", mail.startswith("mailto:mark.karasin@protonmail.com"), mail[:60])
        html = page.content().lower()
        check("no Rutgers email address on the page", "@rutgers.edu" not in html and "rutgers.edu\"" not in html.replace("nursing.rutgers.edu", ""))
        handoff = page.locator("a.hbtn", has_text="AI Handoff").get_attribute("href")
        check("AI Handoff opens the rendered document on GitHub", handoff == "https://github.com/MBKarasin/app-conference-runway/blob/main/site/AI-HANDOFF.md", handoff)

        # 8. Layout at desktop and phone widths.
        for w in (1440, 390):
            page.set_viewport_size({"width": w, "height": 900})
            for hash_ in ("", "display=list&focus=due", "display=calendar"):
                go(hash_)
                over = page.evaluate("document.scrollingElement.scrollWidth - window.innerWidth")
                check(f"no horizontal page scroll at {w} px ({hash_ or 'Orbit'})", over <= 0, f"{over}px")
        check("no console or page errors", not errors, "; ".join(errors[:3]))
        browser.close()
    if httpd:
        httpd.shutdown()
    failed = [r for r in results if not r[0]]
    print(f"\n{len(results) - len(failed)}/{len(results)} checks passed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
