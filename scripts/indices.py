"""Recompute the header's Fidelity Index and Reliability Index from the published data, with every term shown.

    python scripts/indices.py                       # site/data/runway.json, today in New York, now
    python scripts/indices.py --data <file|URL>     # another copy, such as the live site's data/runway.json
    python scripts/indices.py --today 2026-09-26 --now 2026-09-26T12:00:00Z   # reproduce a given moment
    python scripts/indices.py --history             # add the readings from history (walks this clone's git log)
    python scripts/indices.py --json                # the same numbers as JSON

Standard library only (and git, for --history). The definitions are those of site/AI-HANDOFF.md §3.4 and
site/assets/app.js (fidelityIndex, reliabilityIndex); scripts/ui_check.py asserts that the page shows exactly these
numbers. The page takes "today" from the visitor's own calendar day, so a visitor in another time zone near
midnight can see a different day's figures.

Fidelity Index (reach; the curator's team) = distinct qualifying meetings the latest independent probe found that
  the Runway already held ÷ all the qualifying meetings it found (sources/probes.json), with the 95% Wilson interval.
Reliability Index (organizer display, as verified) = confirmation × accuracy.
  confirmation = (upcoming dated records the latest nightly verification confirmed on the organizer's own material
                  + dates set by a published rule) ÷ upcoming dated records; rule dates only when no verification
                  has finished in 36 hours.
  accuracy     = 1 − wrong ÷ audited in the latest audit (sources/audits.json).
Readings printed as "not part of either index" are sensitivity figures, never blended into the indices.
"""
import argparse, datetime as dt, json, math, subprocess, sys, urllib.request
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
Z95 = 1.959964
NY = ZoneInfo("America/New_York")


def wilson(x, n, z=Z95):
    """95% Wilson score interval for x/n, as (low, high); (0, 0) when n is 0 (app.js wilsonInterval)."""
    if not n:
        return (0.0, 0.0)
    p = x / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    r = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (max(0.0, (c - r) / d), min(1.0, (c + r) / d))


def _latest(xs):
    """The entry with the latest date; a later entry wins a tie (app.js latest)."""
    out = None
    for x in xs:
        if out is None or str(x.get("date")) >= str(out.get("date")):
            out = x
    return out


def _wrong(a):
    return len(a["wrong"]) if isinstance(a.get("wrong"), list) else int(a.get("wrong") or 0)


def _tally(xs):
    out = {}
    for x in xs:
        out[x] = out.get(x, 0) + 1
    return dict(sorted(out.items()))


def compute(data, today, now=None):
    """Both indices exactly as the page computes them.

    data  the parsed runway.json
    today 'YYYY-MM-DD', the visitor's calendar day
    now   an aware datetime for the 36-hour freshness test (default: the current time)
    """
    now = now or dt.datetime.now(dt.timezone.utc)
    # Fidelity: the latest probe.
    probes = [p for p in (data.get("probes") or []) if int(p.get("found") or 0) > 0]
    fid = None
    if probes:
        p = _latest(probes)
        held, found = int(p.get("held") or 0), int(p["found"])
        lo, hi = wilson(held, found)
        fid = {"pct": 100 * held / found, "held": held, "found": found, "low_pct": 100 * lo, "high_pct": 100 * hi,
               "probe": p.get("id"), "date": p.get("date"), "finished": p.get("finished"), "window": p.get("window") or {},
               "frames": p.get("frames") or [], "counted_twice": p.get("counted_twice") or 0,
               "series_held": p.get("series_held"), "series_found": p.get("series_found")}

    # Reliability: confirmation (census) x accuracy (latest audit).
    series = {s["id"] for s in data["series"]}
    eds = [e for e in data["editions"] if e["series"] in series]
    state = lambda e: (e.get("verify") or {}).get("state")
    past = lambda e: (e.get("end") or e["start"]) < today
    up = [e for e in eds if state(e) != "expected" and not e.get("month_only") and not past(e)]
    checked = data.get("sources_checked")
    hours = (now - dt.datetime.fromisoformat(checked.replace("Z", "+00:00"))).total_seconds() / 3600 if checked else math.inf
    fresh = hours <= 36
    rule = sum(1 for e in up if state(e) == "rule")
    machine = sum(1 for e in up if e.get("machine") and state(e) != "rule") if fresh else 0
    other = [e for e in up if not (state(e) == "rule" or (fresh and e.get("machine")))]
    conf = (machine + rule) / len(up) if up else 0.0
    audits = [a for a in (data.get("audits") or []) if int(a.get("audited") or 0) > 0]
    a = _latest(audits) if audits else None
    audited, wrong = (int(a["audited"]), _wrong(a)) if a else (0, 0)
    acc = 1 - wrong / audited if audited else 1.0
    wlo, whi = wilson(wrong, audited)
    rel = {"pct": 100 * conf * acc, "conf_pct": 100 * conf, "machine": machine, "rule": rule, "ok": machine + rule,
           "upcoming_dated": len(up), "not_counted": len(other), "not_counted_states": _tally(state(e) or "none" for e in other),
           "acc_pct": 100 * acc, "audited": audited, "wrong": wrong, "right": audited - wrong,
           "audit": a.get("id") if a else None, "audit_date": a.get("date") if a else None,
           "low_pct": 100 * conf * (1 - whi if audited else 1), "high_pct": 100 * conf * (1 - wlo if audited else 1)}
    # The Horizon scan dot (app.js): green within 8 days of the latest probe's finish, yellow within 14, red after or with
    # no probe. A probe recorded only by its date counts from noon that day in New York (16:00 UTC).
    scan_ref = (fid.get("finished") or (fid["date"] + "T16:00:00Z" if fid.get("date") else None)) if fid else None
    scan_days = (now - dt.datetime.fromisoformat(scan_ref.replace("Z", "+00:00"))).total_seconds() / 86400 if scan_ref else math.inf
    scan = {"finished": fid.get("finished") if fid else None, "age_days": round(scan_days, 3) if scan_ref else None,
            "tone": "ok" if scan_days <= 8 else "warn" if scan_days <= 14 else "bad"}
    return {
        "today": today, "now": now.isoformat(timespec="seconds"), "built": data.get("built"),
        "scan": scan, "verified_tone": "ok" if fresh else "bad",
        "sources_checked": checked, "hours_since_check": round(hours, 2) if checked else None, "fresh": fresh,
        "fidelity": fid, "reliability": rel,
        "audit_list": [{k: x.get(k) for k in ("id", "date", "audited", "wrong")} for x in data.get("audits") or []],
        "probe_history": data.get("probe_history") or [],
    }


def history(data, repo=ROOT):
    """The readings from history (§3.4): Fidelity from the sources brought up before the first probe; Reliability
    from every nightly verification recorded in this clone's git history, times the audits before the latest one."""
    out = {}
    H = data.get("probe_history") or []
    if H:
        held, found = sum(int(h["held"]) for h in H), sum(int(h["found"]) for h in H)
        lo, hi = wilson(held, found)
        out["fidelity"] = {"pct": 100 * held / found, "held": held, "found": found, "low_pct": 100 * lo, "high_pct": 100 * hi,
                           "dates": [h["date"] for h in H]}
    git = lambda *a: subprocess.run(["git", "-C", str(repo), *a], capture_output=True, text=True, check=True).stdout
    runs = []
    try:
        log = git("log", "--reverse", "--format=%h|%cI|%an|%s", "--", "data/verification.json")
    except (OSError, subprocess.CalledProcessError):
        out["reliability_unavailable"] = "the reading from history needs a git clone of the repository (git log of data/verification.json)"
        log = ""
    for line in log.splitlines():
        h, when, author, subject = line.split("|", 3)
        if author != "runway-checker" or not subject.startswith("Nightly source check"):
            continue
        try:
            ver = json.loads(git("show", f"{h}:data/verification.json"))
            d = json.loads(git("show", f"{h}:site/data/runway.json"))
        except (subprocess.CalledProcessError, json.JSONDecodeError):
            continue
        day = dt.datetime.fromisoformat(when).astimezone(NY).date().isoformat()
        st = lambda e: (e.get("verify") or {}).get("state") if isinstance(e.get("verify"), dict) else e.get("verify")
        up = [e for e in d["editions"] if st(e) != "expected" and not e.get("month_only") and (e.get("end") or e["start"]) >= day]
        rule = sum(1 for e in up if st(e) == "rule")
        mach = sum(1 for e in up if st(e) != "rule" and (ver.get(e["id"]) or {}).get("state") == "verified")
        runs.append({"commit": h, "at": when, "upcoming": len(up), "machine": mach, "rule": rule})
    audits = [a for a in (data.get("audits") or []) if int(a.get("audited") or 0) > 0]
    last = _latest(audits)["date"] if audits else None
    earlier = [a for a in audits if str(a["date"]) < str(last)]
    if runs and earlier:
        ok, n = sum(r["machine"] + r["rule"] for r in runs), sum(r["upcoming"] for r in runs)
        aud, wr = sum(int(a["audited"]) for a in earlier), sum(_wrong(a) for a in earlier)
        out["reliability"] = {"pct": 100 * (ok / n) * (1 - wr / aud), "conf_pct": 100 * ok / n, "confirmed": ok, "checked": n,
                              "runs": len(runs), "first": runs[0]["at"], "last": runs[-1]["at"],
                              "acc_pct": 100 * (1 - wr / aud), "audited": aud, "wrong": wr, "audits": [a["id"] for a in earlier]}
    return out


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
    ap.add_argument("--history", action="store_true", help="also print the readings from history (needs a git clone)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    today = a.today or dt.datetime.now(NY).date().isoformat()
    now = dt.datetime.fromisoformat(a.now.replace("Z", "+00:00")) if a.now else None
    data = load(a.data)
    r = compute(data, today, now)
    hist = history(data) if a.history else None
    if a.json:
        if hist is not None:
            r["history"] = hist
        print(json.dumps(r, indent=1))
        return
    f, l = r["fidelity"], r["reliability"]
    print(f"Data built {r['built']}; latest nightly verification {r['sources_checked']} ({r['hours_since_check']} h before {r['now']}); today {r['today']}")
    sc = r["scan"]
    print(f"Horizon scan {sc['finished'] or (f['date'] if f else 'not yet run')} ({sc['age_days']} days before now): dot {dict(ok='green', warn='yellow', bad='red')[sc['tone']]};"
          f" Verified dot {dict(ok='green', bad='red')[r['verified_tone']]}")
    print()
    if f:
        w = f["window"]
        print(f"Fidelity Index    {f['pct']:.2f}%   (95% interval {f['low_pct']:.1f}-{f['high_pct']:.1f}%)   reach")
        print(f"  probe {f['probe']} ({f['date']}): qualifying dated meetings starting {w.get('from')} to {w.get('to')}")
        for x in f["frames"]:
            print(f"    {x.get('id')} {x.get('label')}: {x.get('held')} of {x.get('found')} held")
        print(f"  distinct meetings: {f['held']} held of {f['found']} found" + (f" ({f['counted_twice']} found in two frames, counted once)" if f["counted_twice"] else ""))
        if f.get("series_found"):
            print(f"  not part of the index: by meeting series, {f['series_held']} of {f['series_found']} = {100 * f['series_held'] / f['series_found']:.2f}%")
    else:
        print("Fidelity Index    none: no probe is recorded")
    print()
    print(f"Reliability Index {l['pct']:.2f}%   (95% range {l['low_pct']:.1f}-{l['high_pct']:.1f}%)")
    print(f"  confirmation  ({l['machine']} confirmed by the latest nightly verification + {l['rule']} set by a published rule)"
          f" / {l['upcoming_dated']} upcoming dated records = {l['conf_pct']:.2f}%")
    print(f"    not counted: {l['not_counted']} {l['not_counted_states']}" + ("" if r["fresh"] else "   (no verification within 36 hours: only rule dates count)"))
    if l["audited"]:
        print(f"  accuracy      latest audit {l['audit']} ({l['audit_date']}): {l['right']} of {l['audited']} right in every action-critical field = {l['acc_pct']:.2f}%")
    else:
        print("  accuracy      no audit recorded (taken as 100%)")
    print(f"  = {l['conf_pct']:.2f}% x {l['acc_pct']:.2f}%")
    if hist is not None:
        print()
        print("From history")
        hf, hr = hist.get("fidelity"), hist.get("reliability")
        if hist.get("reliability_unavailable"):
            print(f"  Reliability  not computed: {hist['reliability_unavailable']}")
        if hf:
            print(f"  Fidelity     {hf['held']} of {hf['found']} held when sources not previously captured were brought up"
                  f" ({', '.join(hf['dates'])}) = {hf['pct']:.2f}%   (95% interval {hf['low_pct']:.1f}-{hf['high_pct']:.1f}%)")
        if hr:
            print(f"  Reliability  {hr['conf_pct']:.2f}% confirmed ({hr['confirmed']} of {hr['checked']} record checks, {hr['runs']} nightly verifications"
                  f" {hr['first'][:10]} to {hr['last'][:10]}) x {hr['acc_pct']:.2f}% right ({hr['audited'] - hr['wrong']} of {hr['audited']},"
                  f" audits {', '.join(hr['audits'])}) = {hr['pct']:.2f}%")


if __name__ == "__main__":
    sys.exit(main())
