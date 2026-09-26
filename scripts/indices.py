"""Recompute the header's Fidelity Index and Reliability Index from the published data, with every term shown.

    python scripts/indices.py                       # site/data/runway.json, today in New York, now
    python scripts/indices.py --data <file|URL>     # another copy, such as the live site's data/runway.json
    python scripts/indices.py --today 2026-09-26 --now 2026-09-26T12:00:00Z   # reproduce a given moment
    python scripts/indices.py --json                # the same numbers as JSON

Standard library only. The definitions are those of site/AI-HANDOFF.md §3.4 and site/assets/app.js
(fidelityIndex, reliabilityIndex); scripts/ui_check.py asserts that the page shows exactly these numbers.
The page takes "today" from the visitor's own calendar day, so a visitor in another time zone near
midnight can see a different day's figures.

Beyond the two indices, the report prints sensitivity figures that are NOT part of either index. They show
how the Fidelity Index would read under other defensible treatments of the audit history (§3.5).
"""
import argparse, datetime as dt, json, math, re, sys, urllib.request
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
GOOD = {"verified", "rule", "announced", "archived"}   # confirmed, set by rule, save the date, recorded when published
Z95 = 1.959964


def wilson(x, n, z=Z95):
    """95% Wilson score interval for x/n, as (low, high); (0, 0) when n is 0 (app.js wilsonInterval)."""
    if not n:
        return (0.0, 0.0)
    p = x / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    r = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (max(0.0, (c - r) / d), min(1.0, (c + r) / d))


def _days(a, b):
    return (dt.date.fromisoformat(b) - dt.date.fromisoformat(a)).days


def compute(data, today, now=None):
    """Both indices exactly as the page computes them.

    data  the parsed runway.json
    today 'YYYY-MM-DD', the visitor's calendar day
    now   an aware datetime for the 36-hour freshness test (default: the current time)
    """
    now = now or dt.datetime.now(dt.timezone.utc)
    series = {s["id"] for s in data["series"]}
    eds = [e for e in data["editions"] if e["series"] in series]
    state = lambda e: (e.get("verify") or {}).get("state")
    past = lambda e: (e.get("end") or e["start"]) < today
    dated = [e for e in eds if state(e) != "expected" and not e.get("month_only")]

    def covered(e):
        v = e.get("verify") or {}
        if not (e.get("evidence") or v.get("state") == "rule"):
            return False
        if v.get("state") not in GOOD:
            return False
        if not e.get("source_url"):
            return False
        if not past(e):
            if e.get("link_dead"):
                return False
            if v.get("state") != "rule":
                seen = str(v.get("last_verified") or v.get("checked") or "")[:10]
                if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", seen):
                    return False      # an unreadable stamp fails, as in app.js
                if _days(seen, today) > 90:
                    return False
        return True

    ok = sum(1 for e in dated if covered(e))
    audits = data.get("audits") or []
    audited = sum(int(a.get("audited") or 0) for a in audits)
    wrong = sum(len(a["wrong"]) if isinstance(a.get("wrong"), list) else int(a.get("wrong") or 0) for a in audits)
    rate = wrong / audited if audited else 0.0
    lo, hi = wilson(wrong, audited)
    coverage = ok / len(dated) if dated else 0.0

    up = [e for e in dated if not past(e)]
    checked = data.get("sources_checked")
    hours = (now - dt.datetime.fromisoformat(checked.replace("Z", "+00:00"))).total_seconds() / 3600 if checked else math.inf
    fresh = hours <= 36
    rule = sum(1 for e in up if state(e) == "rule")
    machine = sum(1 for e in up if e.get("machine") and state(e) != "rule") if fresh else 0
    other = [e for e in up if not (state(e) == "rule" or (fresh and e.get("machine")))]

    return {
        "today": today, "now": now.isoformat(timespec="seconds"), "built": data.get("built"),
        "sources_checked": checked, "hours_since_check": round(hours, 2) if checked else None, "fresh": fresh,
        "fidelity": {
            "pct": 100 * coverage * (1 - rate),
            "coverage_pct": 100 * coverage, "covered": ok, "dated": len(dated),
            "dated_past": sum(1 for e in dated if past(e)), "dated_upcoming": len(up),
            "correct_pct": 100 * (1 - rate), "wrong": wrong, "audited": audited, "audits": len(audits),
            "low_pct": 100 * coverage * (1 - hi), "high_pct": 100 * coverage * (1 - lo),
        },
        "reliability": {
            "pct": 100 * (machine + rule) / len(up) if up else 0.0,
            "machine": machine, "rule": rule, "ok": machine + rule, "upcoming_dated": len(up),
            "not_counted": len(other),
            "not_counted_states": _tally(state(e) or "none" for e in other),
        },
        "audit_list": [{k: a.get(k) for k in ("id", "date", "audited", "wrong")} for a in audits],
    }


def _tally(xs):
    out = {}
    for x in xs:
        out[x] = out.get(x, 0) + 1
    return dict(sorted(out.items()))


def sensitivity(r):
    """Other readings of the audit history. Reported beside the index, never blended into it."""
    f = r["fidelity"]
    cov = f["coverage_pct"] / 100
    rows = []
    for a in r["audit_list"]:
        n, x = int(a["audited"] or 0), (len(a["wrong"]) if isinstance(a["wrong"], list) else int(a["wrong"] or 0))
        if n:
            lo, hi = wilson(x, n)
            rows.append((f"audit {a['id']} alone ({x}/{n})", 100 * cov * (1 - x / n), 100 * cov * (1 - hi), 100 * cov * (1 - lo)))
    if len(r["audit_list"]) > 1 and f["audited"]:
        # The audits so far looked at the same upcoming records, so their samples are not independent. Keeping the
        # pooled rate but using the size of the largest single audit as the sample size widens the range honestly.
        n_eff = max(int(a["audited"] or 0) for a in r["audit_list"])
        p = f["wrong"] / f["audited"]
        lo, hi = wilson(p * n_eff, n_eff)
        rows.append((f"pooled rate, sample counted once (n = {n_eff})", 100 * cov * (1 - p), 100 * cov * (1 - hi), 100 * cov * (1 - lo)))
    return rows


def load(src):
    if src.startswith(("http://", "https://")):
        req = urllib.request.Request(src, headers={"User-Agent": "APPConferenceRunway-indices/1.0"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.load(resp)
    return json.loads(Path(src).read_text(encoding="utf-8"))


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--data", default=str(ROOT / "site" / "data" / "runway.json"))
    ap.add_argument("--today", help="YYYY-MM-DD (default: today in New York)")
    ap.add_argument("--now", help="ISO instant for the 36-hour freshness test (default: now)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    today = a.today or dt.datetime.now(ZoneInfo("America/New_York")).date().isoformat()
    now = dt.datetime.fromisoformat(a.now.replace("Z", "+00:00")) if a.now else None
    r = compute(load(a.data), today, now)
    if a.json:
        r["sensitivity"] = [{"reading": n, "pct": v, "low_pct": lo, "high_pct": hi} for n, v, lo, hi in sensitivity(r)]
        print(json.dumps(r, indent=1))
        return
    f, l = r["fidelity"], r["reliability"]
    print(f"Data built {r['built']}; last source check {r['sources_checked']} ({r['hours_since_check']} h before {r['now']}); today {r['today']}")
    print()
    print(f"Fidelity Index    {f['pct']:.2f}%   (95% range {f['low_pct']:.1f}-{f['high_pct']:.1f}%)")
    print(f"  evidence coverage   {f['covered']} of {f['dated']} dated records = {f['coverage_pct']:.2f}%"
          f"   ({f['dated_past']} ended, {f['dated_upcoming']} not yet ended)")
    print(f"  projected correct   1 - {f['wrong']}/{f['audited']} = {f['correct_pct']:.2f}%   (pooled over {f['audits']} audits)")
    for x in r["audit_list"]:
        print(f"      {x['id']}: {x['wrong']} wrong of {x['audited']} audited")
    print(f"  = {f['coverage_pct']:.2f}% x {f['correct_pct']:.2f}%")
    print()
    print(f"Reliability Index {l['pct']:.2f}%")
    print(f"  ({l['machine']} re-confirmed by the latest automated check + {l['rule']} set by a published rule) / {l['upcoming_dated']} dated records not yet ended")
    print(f"  not counted: {l['not_counted']} {l['not_counted_states']}" + ("" if r["fresh"] else "   (no check within 36 hours: machine confirmations do not count)"))
    print()
    print("Sensitivity (not part of either index):")
    for name, v, lo, hi in sensitivity(r):
        print(f"  {name:<52} {v:.2f}%   (95% range {lo:.1f}-{hi:.1f}%)")


if __name__ == "__main__":
    sys.exit(main())
