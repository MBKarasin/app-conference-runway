#!/usr/bin/env python3
"""Build gate. Fails (exit 1) on anything that should never reach the public site."""
import json, re, sys, pathlib, datetime as dt
ROOT = pathlib.Path(__file__).resolve().parent.parent
d = json.load(open(ROOT / "site/data/runway.json", encoding="utf-8"))
S = {s["id"]: s for s in d["series"]}
errs = []
TODAY = dt.date.today().isoformat()
ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")
ABSENCE = ["the only", "no published", "not published", "none found", "no public", "does not exist", "no source"]
PRIVATE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[a-z]{2,}|Rosenkvist|\b\d{3}[-.]\d{3}[-.]\d{4}\b")
for e in d["editions"]:
    tag = f'{e["series"]} {e.get("start")}'
    if e["series"] not in S: errs.append(f"{tag}: unknown series")
    if not ISO.match(e.get("start") or ""): errs.append(f"{tag}: bad start date")
    if not ISO.match(e.get("end") or ""): errs.append(f"{tag}: bad end date")
    elif e["end"] < e["start"]: errs.append(f"{tag}: ends before it starts")
    elif (dt.date.fromisoformat(e["end"]) - dt.date.fromisoformat(e["start"])).days > 430: errs.append(f"{tag}: runs more than 14 months")
    for field in ("source_url", "detail_url"):
        u = e.get(field) or ""
        if u and not u.startswith("https://"): errs.append(f"{tag}: {field} is not https")
    if e.get("source_url") and e["end"] >= "2026-09-21" and e.get("verify", {}).get("state") not in ("expected", "rule"):
        years = set(re.findall(r"(?<!\d)20(?:2[3-9]|30)(?!\d)", e["source_url"]))
        if years and e["start"][:4] not in years:
            errs.append(f"{tag}: source URL names a different edition year")
    if int(e["start"][:4]) > d["horizon"] and e.get("verify", {}).get("state") in ("expected", "rule"): errs.append(f"{tag}: projection beyond horizon")
    c = e.get("call") or {}
    if c.get("url") and not c["url"].startswith("https://"): errs.append(f"{tag}: call URL is not https")
    for k in ("opens", "closes"):
        if c.get(k) and not ISO.match(c[k]): errs.append(f"{tag}: call {k} not a date")
    if e.get("verify", {}).get("state") == "expected" and not e.get("month_only"): errs.append(f"{tag}: expected row carries a day")
    daily = e.get("daily") or []
    if len({x.get("date") for x in daily}) != len(daily): errs.append(f"{tag}: repeated daily-program date")
    for item in daily:
        if not ISO.match(item.get("date") or "") or not e["start"] <= item["date"] <= e["end"] or not item.get("title"):
            errs.append(f"{tag}: invalid daily-program entry")
    student = e.get("student")
    if student:
        if student.get("category") not in ("project", "student") or not student.get("kind") or not student.get("detail") or not student.get("roles"):
            errs.append(f"{tag}: incomplete student opportunity")
        if not (student.get("url") or "").startswith("https://"):
            errs.append(f"{tag}: student opportunity lacks an organizer source")
        if student.get("deadline") and not ISO.match(student["deadline"]):
            errs.append(f"{tag}: bad student deadline")
# organizer quotes (evidence) are verbatim publisher text and are exempt from the wording gate
blob = json.dumps({**d, "editions": [{k: v for k, v in e.items() if k != "evidence"} for e in d["editions"]]}, ensure_ascii=False)
for w in ABSENCE:
    for m in re.finditer(re.escape(w), blob, re.I):
        errs.append(f'absence/superlative wording "{w}" in data: …{blob[max(0,m.start()-60):m.end()+40]}…')
for m in PRIVATE.finditer(blob):
    errs.append(f"private-looking string in data: {m.group(0)}")
# Upcoming, non-projected records must carry verbatim organizer wording and its source (the evidence rule in AI-HANDOFF §3.2)
for e in d["editions"]:
    if e["end"] >= TODAY and e.get("verify", {}).get("state") not in ("expected", "rule") and not e.get("removed"):
        if not (e.get("evidence") or "").strip(): errs.append(f'{e["series"]} {e["start"]}: upcoming record has no evidence quote')
        if not e.get("source_url"): errs.append(f'{e["series"]} {e["start"]}: upcoming record has no source URL')
for s in d["series"]:
    if not s.get("professions"): errs.append(f'{s["id"]}: no profession tag')
    for field in ("org_url", "archive_url", "proceedings_url"):
        u = s.get(field) or ""
        if u and not u.startswith("https://"): errs.append(f'{s["id"]}: {field} is not https')
# A narrow coverage gate protects high-relevance recognition weeks from disappearing
# when source batches are refreshed. It makes no claim that the full catalog is exhaustive.
anchors = {
    "National APP Week": "2026-09-21",
    "Clinical Nurse Specialist Recognition Week": "2026-09-01",
    "National Midwifery Week": "2026-10-04",
    "National Nurse Practitioner Week": "2026-11-08",
    "National CRNA Week": "2027-01-17",
    "Emergency Nurses Week": "2026-10-11",
    "Perioperative Nurses Week": "2026-11-08",
    "Ambulatory Care Nurses Week": "2026-02-09",
    "Neonatal Nurses Week": "2026-09-12",
    "Advanced Practice Provider Symposium": "2026-09-23",
    "Stony Brook Medicine Advanced Practice Provider Symposium": "2026-09-24",
    # 2026-09-24: reconciled from 2027-04-15 to 2027-04-14 against AAAA's own official event page
    # (the one anesthetist.org links as "AAAA 2027"), which states April 14 - 18, 2027.
    "AAAA Annual Conference": "2027-04-14",
    "ACNP National Conference": "2027-09-09",
    "RCN Advanced Nurse Practitioner Conference": "2026-10-02",
    "ICN NP/APN Network Conference": "2026-09-14",
    "4th BRICS+ Nursing Conference": "2026-10-21",
    "II Simpósio Internacional de Enfermagem – Práticas Avançadas": "2026-11-25",
}
for name, start in anchors.items():
    if not any(S[e["series"]]["name"] == name and e["start"] == start
               and e.get("verify", {}).get("state") in ("verified", "rule", "conflict", "announced") for e in d["editions"]):
        errs.append(f"missing or unreviewed anchor: {name} {start}")
app_week = next((e for e in d["editions"] if S[e["series"]]["name"] == "National APP Week" and e["start"] == "2026-09-21"), None)
if app_week:
    if app_week["end"] != "2026-09-25" or {x["date"] for x in (app_week.get("daily") or [])} != {f"2026-09-{n:02d}" for n in range(21, 26)}:
        errs.append("National APP Week must span September 21–25 with all five daily programs")
    if not {"NP", "PA", "CRNA", "CAA", "CNS", "CNM"}.issubset(S[app_week["series"]]["professions"]):
        errs.append("National APP Week must include all six APP role categories")
if not any(s["name"] == "AAAA Annual Conference" and "CAA" in s["professions"] for s in d["series"]):
    errs.append("CAA conference must retain its profession tag")
student_eds = [e for e in d["editions"] if e.get("student") and e["end"] >= "2026-09-21"]
if len(student_eds) < 12 or not any("DNP" in e["student"]["kind"] for e in student_eds):
    errs.append("student and DNP project coverage is missing")
npwh = [e for e in d["editions"] if e["series"].endswith("__npwh-annual-women-s-healthcare-conference")]
if not any(e["start"] == "2026-09-23" and e["end"] == "2026-09-25" and "id=1984651" in (e.get("source_url") or "") for e in npwh):
    errs.append("NPWH 2026 must link to its own 2026 organizer event")
if any(e["start"] == "2024-09-25" and "2023-Annual-Conference" in (e.get("source_url") or "") for e in npwh):
    errs.append("NPWH 2024 must not link to the misleading 2023 slug")
if errs:
    print("\n".join(errs[:200])); print(f"\nFAILED: {len(errs)} problem(s)"); sys.exit(1)
print(f"validate ok: {len(d['series'])} series, {len(d['editions'])} editions")
