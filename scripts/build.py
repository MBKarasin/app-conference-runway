#!/usr/bin/env python3
"""Merge curated sources + verification results into site/data/runway.json and site/runway.ics.

Sources (never edited by the checker):
  sources/runway_2026-09-16.json   the original Conference Runway dataset (compiled 2026-09-16)
  sources/group_*.json             organizer-page research batches (schema in sources/SCHEMA.md)
  sources/observances.json         celebration weeks/days with published rules
  sources/overrides.json           curator corrections (wins over everything)
Verification (written by scripts/check.py):
  data/verification.json
"""
import json, re, glob, hashlib, datetime as dt, pathlib, calendar

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC, SITE = ROOT / "sources", ROOT / "site"
TODAY_ = dt.date.today()
HORIZON = TODAY_.year + 3          # rolling: current year plus three
LOOKBACK = 3                        # years of history every meeting should show
RULES = {}
TODAY = dt.date.today()

MONTHS = {m.lower(): i for i, m in enumerate(calendar.month_name) if m}
MONTHS.update({m.lower(): i for i, m in enumerate(calendar.month_abbr) if m})

def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")

def series_key(org, name):
    n = re.sub(r"\(\s*\d+(st|nd|rd|th)\s*\)|\(\s*[IVXLC]+\s*\)|\b20\d\d\b|\b\d+(st|nd|rd|th)\b", "", name)
    n = re.sub(r"\s+", " ", n).strip(" -–()")
    return slug(org)[:40] + "__" + slug(n)[:50]

# ---------- curator tags for the migrated dataset ----------
SPEC_RULES = [
    (r"ELSO|ExtraCorporeal|AmSECT", ["ecmo & perfusion"]),
    (r"Thoracic|STS|AATS|Heart and Lung", ["cardiothoracic surgery"]),
    (r"Cardiology|Heart Rhythm|Heart Failure", ["cardiology"]),
    (r"Neurocritical|Neuroscience", ["neuroscience"]),
    (r"Toxicology|Poison", ["toxicology"]),
    (r"Surgeons|AORN|Perioperative", ["surgery"]),
    (r"Hospital Medicine", ["hospital medicine"]),
    (r"Emergency|EMT|Ambulance", ["emergency"]),
    (r"Vascular", ["vascular"]),
    (r"Resuscitation", ["resuscitation"]),
    (r"Pulmonary|CHEST", ["pulmonary"]),
    (r"Critical Care|Critical-Care|AACN Central|ICCM|Institute for Critical", ["critical care"]),
    (r"Women's Health|Obstetric|Midwi", ["women's health"]),
    (r"Anesthe", ["anesthesia"]),
    (r"Pediatric|Neonatal|Pediatrics", ["pediatrics"]),
    (r"Psychiatric", ["psychiatric-mental health"]),
    (r"Palliative|Hospice", ["palliative care"]),
    (r"Pain", ["pain"]),
    (r"Informatics", ["informatics"]),
    (r"Simulation|INACSL", ["simulation"]),
    (r"Research|Science|Academy of Medicine", ["research"]),
    (r"Leader|Leadership|Deans|Executive", ["leadership"]),
    (r"Education|League for Nursing|Colleges of Nursing|Faculties|Students?", ["education"]),
]
def spec_for(text, track):
    out = []
    for pat, tags in SPEC_RULES:
        if re.search(pat, text, re.I):
            out += [t for t in tags if t not in out]
    if not out:
        out = {"acute": ["critical care"], "app": ["advanced practice"], "edu": ["education"], "spec": ["nursing specialty"]}[track]
    return out[:3]

def prof_for(org, name, track):
    t = org + " " + name
    if re.search(r"Physician Assistant|Physician Associate|\bPAs?\b|NCCPA", t): return ["PA"]
    if re.search(r"Nurse Practitioner|NONPF|AANP|FNAP|APN|NP\b|Advanced Practice", t): return ["NP"]
    if re.search(r"Anesthe", t): return ["CRNA", "Nursing"]
    if re.search(r"Midwi", t): return ["CNM", "Nursing"]
    if track == "acute" and not re.search(r"Nurs", t): return ["Multidisciplinary"]
    if re.search(r"Nurs|AACN|Sigma|NLN|League|AWHONN|AORN", t): return ["Nursing"]
    return ["Multidisciplinary"]

AUD = {"acute": ["clinician"], "app": ["clinician", "leader"], "edu": ["academic", "leader"], "spec": ["clinician"]}
KIND_RULES = [(r"Summit|Assembly|Hill Day", "summit"),
              (r"Symposium", "symposium"), (r"course|FCCS|Review|Ultrasound", "course")]
def kind_for(name, tags):
    for pat, k in KIND_RULES:
        if re.search(pat, name + " " + " ".join(tags or []), re.I): return k
    return "conference"

ISO_D = re.compile(r"^\d{4}-\d{2}-\d{2}$")
def norm_call(c):
    c = c or {}
    c = {k: (v if k not in ("opens", "closes", "d", "odd", "df") or v is None or ISO_D.match(str(v)) else None) for k, v in c.items()}
    st = c.get("st") or c.get("status") or "tba"
    st = {"postponed": "tba"}.get(st, st)
    return {"status": st, "text": c.get("t") or c.get("text"),
            "opens": c.get("odd") or c.get("opens"), "closes": c.get("d") or c.get("closes"),
            "final": c.get("df"), "url": c.get("url")}

def migrate_runway():
    raw = json.load(open(SRC / "runway_2026-09-16.json", encoding="utf-8"))
    series, eds = {}, []
    for r in raw["rows"]:
        key = series_key(r["org"], r["name"])
        text = r["org"] + " " + r["name"]
        s = series.setdefault(key, {
            "id": key, "name": re.sub(r"\s*\((\d+(st|nd|rd|th)|[IVX]+)\)\s*|\s+20\d\d$", "", r["name"]).strip(),
            "org": r["org"], "org_url": r["url"], "professions": prof_for(r["org"], r["name"], r["track"]),
            "specialty": spec_for(text, r["track"]), "audience": AUD[r["track"]],
            "kind": kind_for(r["name"], r.get("tags")), "region": r["reg"], "recurrence": None,
            "origin": "runway-2026-09-16", "tags_by": "curator"})
        eds.append({"series": key, "start": r["s"], "end": r["e"], "location": r["where"],
                    "format": (r.get("fmt") or ("virtual" if r["reg"] == "virtual" else "in person")).lower(),
                    "theme": r.get("theme"), "note": r.get("note"), "sessions": r.get("sub"),
                    "call": norm_call(r["call"]), "source_url": r["url"], "evidence": None,
                    "compiled": "2026-09-16", "origin": "runway-2026-09-16"})
    for t in raw["tba"]:
        key = series_key(t["org"], t["name"])
        if key not in series:
            series[key] = {"id": key, "name": re.sub(r"\s+20\d\d$", "", t["name"]), "org": t["org"], "org_url": t["url"],
                           "professions": prof_for(t["org"], t["name"], t["track"]),
                           "specialty": spec_for(t["org"] + " " + t["name"], t["track"]),
                           "audience": AUD[t["track"]], "kind": kind_for(t["name"], None), "region": t["reg"],
                           "recurrence": None, "origin": "runway-2026-09-16", "tags_by": "curator"}
        series[key]["status_note"] = t["text"]
    return series, eds

def prof_from_agent(p):
    p = set(p or [])
    out = [x for x in ("NP", "PA", "CRNA", "CAA", "RNFA", "CNM", "CNS", "Nursing") if x in p]
    if "RN" in p and not out: out.append("Nursing")
    if "MD" in p and len(p - {"MD"}) and ("NP" in p or "PA" in p): out.append("Multidisciplinary")
    if not out: out = ["Multidisciplinary"]
    return out

def load_groups(series, eds):
    for f in sorted(SRC.glob("group_*.json")):
        g = json.load(open(f, encoding="utf-8"))
        for s in g["series"]:
            key = series_key(s["org"], s["name"])
            rec = {"id": key, "name": s["name"], "org": s["org"], "org_url": s.get("org_url"),
                   "professions": prof_from_agent(s.get("professions")),
                   "specialty": [x.lower() for x in (s.get("specialty") or [])][:3] or ["multispecialty"],
                   "audience": s.get("audience") or ["clinician"], "kind": s.get("kind") or "conference",
                   "region": s.get("region") or "us", "recurrence": s.get("recurrence"),
                   "np_pa_basis": s.get("np_pa_basis") or s.get("rnfa_basis"), "archive_url": s.get("archive_url"),
                   "origin": "research-" + g["group"], "tags_by": "curator"}
            # an existing migrated series with the same key keeps its tags but gains recurrence/basis
            if key in series:
                for k in ("recurrence", "np_pa_basis"):
                    if rec.get(k): series[key][k] = rec[k]
            else:
                series[key] = rec
            for e in s.get("editions", []):
                eds.append({"series": key, "start": e["start"], "end": e.get("end") or e["start"],
                            "location": e.get("location"), "format": (e.get("format") or "in person").lower(),
                            "theme": e.get("theme"), "note": e.get("note"), "sessions": None,
                            "call": norm_call(e.get("call")), "source_url": e.get("source_url"),
                            "evidence": e.get("evidence"), "compiled": e.get("checked") or "2026-09-21",
                            "detail_url": e.get("detail_url"), "source_language": e.get("source_language"), "student": e.get("student"), "origin": "research-" + g["group"],
                            "source_reviewed": bool(e.get("source_reviewed"))})

def load_archive(series, eds):
    """Past-meeting pages and earlier editions found on organizer sites (sources/archive/out_*.json)."""
    for f in sorted((SRC / "archive").glob("*out_*.json")):
        for x in json.load(open(f, encoding="utf-8")):
            s = series.get(x["id"])
            if not s: continue
            for k in ("archive_url", "archive_evidence", "proceedings_url"):
                if x.get(k) and not s.get(k): s[k] = x[k]
            if x.get("still_missing"):
                gn = s.setdefault("gap_notes", {})
                note = (x.get("note") or "").lower()
                why = ("not held" if re.search(r"bienn|not held|no .* in \d{4}|inaugural|started in|began in|launched in|cancel", note)
                       else "blocked" if re.search(r"403|blocked|robots", note) else "none")
                for y in x["still_missing"]:
                    gn[str(y)] = why
            for e in (x.get("past_editions") or []) + (x.get("found") or []):
                if not e.get("start") or e["start"] >= TODAY.isoformat(): continue
                eds.append({"series": x["id"], "start": e["start"], "end": e.get("end") or e["start"],
                            "location": e.get("location"), "format": (e.get("format") or "in person").lower(),
                            "theme": e.get("theme"), "note": None, "sessions": None, "call": {"status": "closed"},
                            "source_url": e.get("source_url"), "evidence": e.get("evidence"),
                            "detail_url": e.get("detail_url"), "compiled": "2026-09-21", "origin": "research-archive"})

SMALL = {"and", "of", "the", "for", "in", "&"}
UPPER = {"ecmo": "ECMO", "icu": "ICU", "hiv": "HIV", "ent": "ENT", "gi": "GI", "copd": "COPD", "app": "APP", "apps": "APPs", "np": "NP", "pa": "PA"}
def title(t):
    words = re.split(r"(\s+|-)", t)
    out = []
    for i, w in enumerate(words):
        lw = w.lower()
        if lw in UPPER: out.append(UPPER[lw])
        elif i and lw in SMALL: out.append(lw)
        else: out.append(w[:1].upper() + w[1:])
    return "".join(out)

FOCUS = {"clinician": "clinical", "academic": "academic", "leader": "executive"}
RNFA_SPEC = re.compile(r"surg|periop", re.I)
def present(series):
    for s in series.values():
        s["specialty"] = [title(x) for x in (s.get("specialty") or [])]
        s["focus"] = sorted({FOCUS.get(a, a) for a in (s.get("audience") or ["clinician"])})
        # RNFA: explicit tag, or perioperative/surgical meetings open to nurses (curator inference, labeled in the UI)
        if "RNFA" not in s["professions"] and any(RNFA_SPEC.search(x) for x in s["specialty"]) \
                and any(p in s["professions"] for p in ("Nursing", "Multidisciplinary", "NP")) and "CRNA" not in s["professions"]:
            s["rnfa_inferred"] = True

def orgroot(o):
    return re.sub(r"[^a-z]", "", re.sub(r"\(.*?\)", "", o.lower()))

STOP = {"annual", "conference", "meeting", "national", "the", "and", "of", "for", "in"}
def name_overlap(x, y):
    a = {w for w in re.findall(r"[a-z]+", x.lower()) if w not in STOP}
    b = {w for w in re.findall(r"[a-z]+", y.lower()) if w not in STOP}
    return len(a & b) / max(1, min(len(a), len(b)))

def merge_twins(series, eds):
    """Two series from the same organizer that share a start date are the same meeting under two names.
    Keep the older (Runway) key, re-point editions, and keep the research batch's recurrence/basis."""
    starts = {}
    for e in eds: starts.setdefault(e["series"], set()).add(e["start"])
    keys = sorted(series, key=lambda k: (series[k]["origin"] != "runway-2026-09-16", k))
    alias = {}
    for i, a in enumerate(keys):
        for b in keys[i + 1:]:
            if b in alias or a in alias: continue
            if (orgroot(series[a]["org"]) == orgroot(series[b]["org"]) and starts.get(a, set()) & starts.get(b, set())
                    and name_overlap(series[a]["name"], series[b]["name"]) >= 0.5):
                alias[b] = a
    for b, a in alias.items():
        for k in ("recurrence", "np_pa_basis"):
            if series[b].get(k) and not series[a].get(k): series[a][k] = series[b][k]
        del series[b]
    for e in eds:
        e["series"] = alias.get(e["series"], e["series"])
    return alias

def dedupe(eds):
    """Same series + same start date = one edition. Research batches (with evidence) win."""
    best = {}
    for e in eds:
        k = (e["series"], e["start"])
        cur = best.get(k)
        if cur is None or (not cur.get("evidence") and e.get("evidence")):
            best[k] = e
    return list(best.values())

def edition_id(e):
    return hashlib.sha1((e["series"] + "|" + e["start"]).encode()).hexdigest()[:12]

def typical_month(s, eds_for):
    if s.get("recurrence"):
        m = re.search(r"typically\s+([A-Za-z]+)", s["recurrence"])
        if m and m.group(1).lower() in MONTHS: return MONTHS[m.group(1).lower()]
    dated = [e for e in eds_for if e.get("status") != "expected"]
    if s["kind"] != "observance" and len(dated) >= 1:
        months = [int(e["start"][5:7]) for e in dated]
        return max(set(months), key=months.count)
    return None

def project(series, eds):
    """Expected editions through HORIZON for annual series: month only, tagged INFERRED."""
    by = {}
    for e in eds: by.setdefault(e["series"], []).append(e)
    out = []
    for key, s in series.items():
        mine = by.get(key, [])
        rule = RULES.get(key)
        if rule:
            have = {e["start"][:4] for e in mine}
            for y in range(TODAY.year, HORIZON + 1):
                if str(y) in have: continue
                st, en = rule_dates(rule, y)
                out.append({"series": key, "start": st, "end": en, "location": "Nationwide", "format": "virtual",
                            "theme": None, "note": "Date computed from the organizer's published rule", "sessions": None,
                            "call": {"status": "none"}, "source_url": s.get("org_url"), "evidence": None,
                            "compiled": TODAY.isoformat(), "origin": "rule", "status": "rule"})
            continue
        rec = (s.get("recurrence") or "").lower()
        if not rec:
            observed_years = {e["start"][:4] for e in mine}
            if len(observed_years) < 2 and not re.search(r"\bannual\b|\byearly\b", s["name"], re.I):
                continue  # one dated edition is not evidence of a recurring meeting
            rec = "annual"
        if "bienn" in rec or "every other" in rec: step = 2
        elif "annual" in rec: step = 1
        else: continue
        m = typical_month(s, mine)
        if not m: continue
        years = sorted({int(e["start"][:4]) for e in mine})
        last = max(years) if years else TODAY.year - 1
        y = last + step
        while y <= HORIZON:
            if (y, m) < (TODAY.year, TODAY.month):      # never project into the past
                y += step; continue
            out.append({"series": key, "start": f"{y}-{m:02d}-01", "end": f"{y}-{m:02d}-01",
                        "month_only": True, "location": None, "format": None, "theme": None, "note": None,
                        "sessions": None, "call": {"status": "tba"}, "source_url": s.get("org_url"),
                        "evidence": None, "compiled": TODAY.isoformat(), "origin": "projection",
                        "status": "expected"})
            y += step
    return out

def observances():
    f = SRC / "observances.json"
    if not f.exists(): return {}, []
    o = json.load(open(f, encoding="utf-8"))
    series, eds = {}, []
    for s in o:
        key = "obs__" + slug(s["name"])
        series[key] = {"id": key, "name": s["name"], "org": s["org"], "org_url": s["url"],
                       "professions": s["professions"], "specialty": ["celebration"],
                       "audience": ["clinician", "leader", "academic"], "kind": "observance",
                       "region": s.get("region", "us"), "recurrence": s["rule_text"], "origin": "observances", "tags_by": "curator"}
        published = {p["start"][:4]: p for p in s.get("published", [])}
        for y in range(TODAY.year - LOOKBACK, HORIZON + 1):
            if str(y) in published:
                p = published[str(y)]
                eds.append({"series": key, "start": p["start"], "end": p["end"], "location": "Nationwide",
                            "format": s.get("format"), "theme": p.get("theme"), "note": None, "sessions": None,
                            "daily": p.get("daily"),
                            "call": {"status": "none"}, "source_url": p["source_url"], "evidence": p.get("evidence"),
                            "compiled": p.get("checked", "2026-09-21"), "origin": "observances",
                            "source_reviewed": bool(p.get("source_reviewed"))})
            elif s.get("rule"):
                st, en = rule_dates(s["rule"], y)
                if st:
                    eds.append({"series": key, "start": st, "end": en, "location": "Nationwide", "format": s.get("format"),
                                "theme": None, "note": "Computed from the organizer's published rule",
                                "sessions": None, "call": {"status": "none"}, "source_url": s["url"],
                                "evidence": s.get("rule_evidence"), "compiled": TODAY.isoformat(),
                                "origin": "rule", "status": "rule"})
    return series, eds

def rule_dates(rule, y):
    kind = rule["type"]
    if kind == "fixed":
        a = dt.date(y, rule["month"], rule["day"]); b = dt.date(y, rule.get("end_month", rule["month"]), rule.get("end_day", rule["day"]))
        return a.isoformat(), b.isoformat()
    if kind == "weekday_after":
        d = dt.date(y, rule["month"], rule["day"]) + dt.timedelta(days=1)
        while d.weekday() != rule["weekday"]: d += dt.timedelta(days=1)
        return d.isoformat(), (d + dt.timedelta(days=rule.get("length", 1) - 1)).isoformat()
    if kind == "nth_weekday":
        c = calendar.Calendar()
        days = [d for d in c.itermonthdates(y, rule["month"]) if d.month == rule["month"] and d.weekday() == rule["weekday"]]
        d = days[rule["n"] - 1]
        return d.isoformat(), (d + dt.timedelta(days=rule.get("length", 1) - 1)).isoformat()
    return None, None

def ics(eds, series):
    def esc(s): return (s or "").replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")
    def fold(line):
        parts, chunk, size = [], "", 0
        for char in line:
            width = len(char.encode("utf-8"))
            if size + width > 75:
                parts.append(chunk)
                chunk, size = " " + char, 1 + width
            else:
                chunk += char
                size += width
        return "\r\n".join(parts + [chunk])
    L = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//APP Conference Runway//EN", "CALSCALE:GREGORIAN",
         "X-WR-CALNAME:APP Conference Runway", "X-PUBLISHED-TTL:PT12H", "REFRESH-INTERVAL;VALUE=DURATION:PT12H"]
    stamp = dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ")
    for e in eds:
        if e.get("month_only") or e["end"] < (TODAY - dt.timedelta(days=60)).isoformat(): continue
        s = series[e["series"]]
        end = (dt.date.fromisoformat(e["end"]) + dt.timedelta(days=1)).strftime("%Y%m%d")
        L += ["BEGIN:VEVENT", f"UID:{e['id']}@app-conference-runway", f"DTSTAMP:{stamp}",
              f"DTSTART;VALUE=DATE:{e['start'].replace('-', '')}", f"DTEND;VALUE=DATE:{end}",
              f"SUMMARY:{esc(s['name'])} ({esc(s['org'])})", f"LOCATION:{esc(e.get('location'))}",
              f"URL:{e.get('source_url') or ''}",
              f"DESCRIPTION:{esc('Confirm details on the organizer page before registering or booking travel.')}",
              "END:VEVENT"]
        c = e.get("call") or {}
        if c.get("closes") and c["closes"] >= TODAY.isoformat():
            d = c["closes"].replace("-", "")
            nd = (dt.date.fromisoformat(c["closes"]) + dt.timedelta(days=1)).strftime("%Y%m%d")
            L += ["BEGIN:VEVENT", f"UID:{e['id']}-call@app-conference-runway", f"DTSTAMP:{stamp}",
                  f"DTSTART;VALUE=DATE:{d}", f"DTEND;VALUE=DATE:{nd}",
                  f"SUMMARY:Abstract deadline: {esc(s['name'])}", f"DESCRIPTION:{esc(c.get('text') or '')}",
                  f"URL:{c.get('url') or e.get('source_url') or ''}", "END:VEVENT"]
    L.append("END:VCALENDAR")
    return "\r\n".join(fold(line) for line in L) + "\r\n"

def main():
    series, eds = migrate_runway()
    load_groups(series, eds)
    load_archive(series, eds)
    os_, oe = observances(); series.update(os_); eds += oe
    ov = json.load(open(SRC / "overrides.json", encoding="utf-8")) if (SRC / "overrides.json").exists() else {}
    for b, a in ov.get("aliases", {}).items():
        if b in series and a in series:
            for k in ("recurrence", "np_pa_basis"):
                if series[b].get(k) and not series[a].get(k): series[a][k] = series[b][k]
            del series[b]
            for e in eds:
                if e["series"] == b: e["series"] = a
    merged = merge_twins(series, eds)
    eds = dedupe(eds)
    for e in eds: e["id"] = edition_id(e)
    for k, v in ov.get("series", {}).items():
        if k in series: series[k].update(v)
    for k, v in ov.get("editions", {}).items():
        for e in eds:
            if e["id"] == k: e.update(v)
    eds = [e for e in eds if not e.get("removed")]
    student_file = SRC / "student_opportunities.json"
    if student_file.exists():
        student_editions = json.load(open(student_file, encoding="utf-8")).get("editions", {})
        unknown = set(student_editions) - {e["id"] for e in eds}
        if unknown: raise ValueError("Student opportunities reference missing editions: " + ", ".join(sorted(unknown)))
        for e in eds:
            if e["id"] in student_editions: e["student"] = student_editions[e["id"]]
    global RULES
    RULES = ov.get("rules", {})
    led_f = ROOT / "data" / "ledger.json"
    ledger = json.load(open(led_f, encoding="utf-8")) if led_f.exists() else {}
    have = {e["id"] for e in eds}
    removed_ids = {k for k, patch in ov.get("editions", {}).items() if patch.get("removed")}
    for lid, le in ledger.items():
        if lid not in have and lid not in removed_ids and le["series"] in series:
            eds.append({**le["edition"], "id": lid, "origin": "ledger"})
    now = dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    for e in eds:
        rec = ledger.setdefault(e["id"], {"series": e["series"], "first_seen": now})
        rec["last_seen"] = now
        rec["edition"] = {k: e.get(k) for k in ("series", "start", "end", "location", "format", "theme", "note", "sessions",
                                               "call", "source_url", "evidence", "detail_url", "compiled", "student")}
    led_f.parent.mkdir(exist_ok=True)
    json.dump(ledger, open(led_f, "w", encoding="utf-8"), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    proj = project(series, eds)
    for e in proj: e["id"] = edition_id(e)
    present(series)
    geo = json.load(open(SRC / "geo" / "locations.json", encoding="utf-8")) if (SRC / "geo" / "locations.json").exists() else {}
    for e in eds + proj:
        e["geo"] = geo.get((e.get("location") or "").strip()) if e.get("location") else None
        if (e.get("format") == "virtual" or series[e["series"]]["region"] == "virtual") and not e["geo"]:
            e["geo"] = {"online": True}
    ver = json.load(open(ROOT / "data" / "verification.json", encoding="utf-8")) if (ROOT / "data" / "verification.json").exists() else {}
    for e in eds:
        v = ver.get(e["id"])
        # A check belongs to the page it read. A corrected source must be checked again.
        if v and v.get("url") != e.get("source_url"):
            v = None
        if e.get("status") == "rule":
            e["verify"] = {"state": "rule", "checked": e["compiled"]}
        elif e.get("date_conflict"):
            e["verify"] = {"state": "conflict", "method": "manual", "checked": e["compiled"],
                           "last_verified": e["compiled"], "url": e.get("source_url"),
                           "why": e.get("note") or "The organizer publishes conflicting dates."}
        elif e.get("source_reviewed") and not (v and v.get("state") == "not_found"):
            e["verify"] = {"state": "verified", "method": "manual", "checked": e["compiled"],
                           "last_verified": e["compiled"], "url": e.get("source_url")}
        elif v:
            e["verify"] = v
        else:
            e["verify"] = {"state": "unchecked", "checked": None}
    for e in proj:
        e["verify"] = {"state": "rule" if e.get("status") == "rule" else "expected", "checked": e["compiled"] if e.get("status") == "rule" else None}
    org_display = json.load(open(SRC / "org_display.json", encoding="utf-8"))
    for s in series.values():
        s["org_display"] = org_display.get(s["org"], s["org"])
    all_eds = sorted(eds + proj, key=lambda e: (e["start"], e["series"]))
    used = {e["series"] for e in all_eds}
    out = {"built": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"), "horizon": HORIZON,
           "series": sorted([s for s in series.values()], key=lambda s: s["name"].lower()),
           "editions": all_eds}
    (SITE / "data").mkdir(parents=True, exist_ok=True)
    json.dump(out, open(SITE / "data" / "runway.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    open(SITE / "runway.ics", "w", encoding="utf-8", newline="").write(ics(eds, series))
    n = lambda st: sum(1 for e in eds if e["verify"]["state"] == st)
    print(f"merged twins {len(merged)}: " + ", ".join(merged))
    print(f"series {len(series)} | dated editions {len(eds)} | expected {len(proj)} | "
          f"verified {n('verified')} changed {n('not_found')} unreachable {n('unreachable')} rule {n('rule')} unchecked {n('unchecked')}")

if __name__ == "__main__":
    main()
