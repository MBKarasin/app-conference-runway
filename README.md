# APP Conference Runway

A source-traced calendar of conferences, abstract deadlines, student and DNP project venues, and observances for advanced practice providers (NPs, PAs, CRNAs, CNSs, CNMs). Every upcoming dated entry links to the organizer's own material and, unless computed from a published rule, quotes the wording its date came from, so a visitor can confirm it before registering, submitting or traveling. The project is global in scope and incomplete: its reach is measured (see the Fidelity Index below), and current coverage remains concentrated in the United States.

**Live site:** https://mbkarasin.github.io/app-conference-runway/. Its pages carry a `noindex` tag, and it is shared directly among APPs.

The site is independent. It is not an official publication of, or endorsement by, Rutgers University or RWJBarnabas Health. It is owned and curated by Dr. Mark Karasin, DNP, APN, AGACNP-BC, CNOR(E), who decides what is published. Every AI actor works under his MBK AI Governance Protocol: Claude by Anthropic assists research and implementation, ChatGPT by OpenAI is the red team, and no model decides what is published. The curator shares the Runway for critique with colleagues in academic nursing, research, clinical practice, artificial intelligence and data science; their feedback informs his scholarly inquiry.

Documentation, limitations, and how to check or challenge the project: the [AI Handoff](https://mbkarasin.github.io/app-conference-runway/ai-handoff.html), which opens on the site itself with no account; its source is [`site/AI-HANDOFF.md`](site/AI-HANDOFF.md). Rights: [`LICENSE`](LICENSE) (all rights reserved; the name and logo are claimed as trademarks; the public receives transparency). Contact: mark.karasin@protonmail.com.

## What a visitor sees

- Four views of the same filtered records: **List** (upcoming records by month), **Calendar** (a month grid), **Orbit** (the landing view: twelve months with the count of each record type) and **Directory** (every recurring series with its history).
- Filters: **Discipline**, **Focus** (one record type at a time), **Scope**, **Location** and search. Every view is a shareable link. **Near City** takes a ZIP code or a place such as "Springfield, IL", "Portland ME" or "London, ON", and says so when it does not know a place.
- Each record shows its source link and the organizer's quoted wording. Phones get a mobile layout, with a link to the desktop layout.
- The header shows two time stamps, **Verified** (the latest nightly verification) and **Horizon scan** (the latest search for meetings not yet listed), and the two indices below.

## How it stays current

- Every night a GitHub Action attempts the organizer source of every dated record not yet ended (dates set by a published rule excepted) and checks every source link, writes `data/verification.json` and `data/check_report.md`, archives the day's generated data under `data/snapshots/`, and redeploys if the check and validation pass. Unreadable sources are reported rather than silently treated as corrections.
- Dates that no longer match are listed in the issue **"Runway: dates to review"**. Corrections go in `sources/overrides.json` with a `_why`, a `reviewed_on` date, the organizer's verbatim wording and the exact URL or image; the build gate rejects a correction without them.
- Meetings that have ended are kept as captured and are not re-read.
- New meetings enter a `sources/group_*.json` file, following `sources/SCHEMA.md`, only after the organizer evidence has been reviewed.

## Repository map

| Path | What it is |
|---|---|
| `sources/` | Curated inputs; `overrides.json` (curator corrections) wins over everything |
| `sources/probes.json` | Independent probes behind the Fidelity Index |
| `sources/audits.json` | Audits behind the Reliability Index's accuracy term |
| `scripts/build.py` | Builds `site/data/runway.json`, the calendar feed `site/runway.ics` and the handoff page `site/ai-handoff.html` |
| `scripts/handoff_page.py` | Renders `site/AI-HANDOFF.md` as the handoff page (standard library only; run by `build.py`) |
| `scripts/check.py` | Re-reads organizer pages (robots.txt obeyed) |
| `scripts/linkcheck.py` | Reports links that now fail |
| `scripts/validate.py` | Build gate |
| `scripts/indices.py` | Recomputes the header's Fidelity and Reliability indices, with every term; `--history` adds the readings from history |
| `scripts/ui_check.py` | Scripted browser check of the interface |
| `scripts/icon_versions.py` | Stamps icon URLs with a content version |
| `scripts/snapshot.py` | Archives the day's generated data |
| `scripts/geocode.py` | Places venues for the location filters |
| `site/` | The static website: no framework, cookies, analytics or third-party requests |
| `.github/workflows/runway.yml` | Build, validate and deploy on push; nightly check on schedule |

## Check it yourself

Python 3.12; the build uses only the standard library. From the repository root:

```text
python scripts/build.py
python scripts/validate.py
python scripts/indices.py --history
python -m http.server 8000 --directory site
```

`--history` reads the repository's own history, so it needs a git clone. The nightly checks and the interface check are in §6.1 of the handoff. Running the scripts to check the published data is part of the transparency the `LICENSE` grants; hosting a copy is not.

## Header indices

Both numbers are recomputed in the visitor's browser from `site/data/runway.json` at every page load. `python scripts/indices.py` recomputes them from the same file, or from the live copy with `--data https://mbkarasin.github.io/app-conference-runway/data/runway.json`, and prints every term; the interface check fails if the page shows anything else. Full definitions and limits: [§3.4 and §3.5 of the handoff](https://mbkarasin.github.io/app-conference-runway/ai-handoff.html#34-fidelity-and-reliability).

| Index | From history | Today (2026-09-26) |
|---|---|---|
| Fidelity (reach; the curator's team) | 30.0% (6 of 20) | 35.1% (20 of 57; 95% interval 24.0–48.1%) |
| Reliability (organizer display, as verified) | 87.9% (90.50% × 97.07%) | 70.3% (91.11% × 77.14%) |

**Fidelity Index = qualifying meetings found by the latest independent probe that the Runway already held ÷ all qualifying meetings the probe found** (capture–recapture; 95% Wilson interval). A probe starts from frames published by third parties (lists of organizations, or of meetings) and reads each organizer's own events page without looking at the Runway (`sources/probes.json`). Fidelity says nothing about whether a record is right.

**Reliability Index = confirmation × accuracy.** Confirmation = (records not yet ended that the latest nightly verification confirmed on the organizer's own material + dates set by a published rule) ÷ dated records not yet ended; only the rule dates count when no verification has been recorded in 36 hours. Accuracy = the share of records right in every action-critical field (dates, place, format, abstract call or deadline, eligibility) in the latest audit (`sources/audits.json`); it stands until the next audit.

**What they do not show.** Fidelity is only as wide as its probes, and its interval is wide. Reliability's accuracy term is a sample of 35 records (its own 95% interval is 61–88%). The audits and the probe were carried out by AI systems under the curator's direction, not by people. A confirmation does not re-check every field; the audit measures what it misses.

## Verification labels

A record that passed its check carries no label. Otherwise:

- **Save the date:** the organizer has published only a save-the-date.
- **Set by rule:** an observance computed from its organizer's published rule.
- **Recorded when published:** a meeting that has ended, kept as captured.
- **Expected month:** projected from a meeting's usual month; never given a day.
- **Needs review** or **Not re-checked** ("Date needs review" or "Source not re-checked" inside the record): the latest automated check did not confirm the record and no current manual review covers it. The **Needs review only** switch lists these.

Where an organizer's own pages disagree, the record follows the organizer's primary event page and states the disagreement inside the record.
