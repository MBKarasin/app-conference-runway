# APP Conference Runway

A source-traced calendar of conferences, abstract deadlines, student and DNP project venues, and observances for advanced practice providers (NPs, PAs, CRNAs, CNSs, CNMs). Every upcoming dated entry links to the organizer's own material and, unless computed from a published rule, quotes the wording its date came from, so a visitor can confirm it before registering, submitting or traveling. The project is global in scope and incomplete; current coverage remains concentrated in the United States.

**Live site:** https://mbkarasin.github.io/app-conference-runway/. It is kept out of search engines by design (a `noindex` tag and `robots.txt`) and is shared directly among APPs.

The site is independent. It is not an official publication of, or endorsement by, Rutgers University or RWJBarnabas Health. It is curated by Dr. Mark Karasin, DNP, APN, AGACNP-BC, who decides what is published. Deterministic software and AI systems—including local models, Claude by Anthropic and ChatGPT by OpenAI—may assist research, implementation and independent review; no model decides what is published.

Documentation, limitations, and instructions for reproducing or challenging the project: the [AI Handoff](https://mbkarasin.github.io/app-conference-runway/ai-handoff.html), which opens on the site itself with no account; its source is [`site/AI-HANDOFF.md`](site/AI-HANDOFF.md). Terms of reuse: [`LICENSE`](LICENSE) (CC0 for the curator's own work). Contact: mark.karasin@protonmail.com.

## What a visitor sees

- Four views of the same filtered records: **List** (upcoming records by month), **Calendar** (a month grid), **Orbit** (the landing view: twelve months with the count of each record type) and **Directory** (every recurring series with its history).
- Filters: **Discipline**, **Focus** (one record type at a time), **Scope**, **Location** and search. Every view is a shareable link. **Near City** takes a ZIP code or a place such as "Springfield, IL", "Portland ME" or "London, ON", and says so when it does not know a place.
- Each record shows its source link and the organizer's quoted wording. Phones get a mobile layout, with a link to the desktop layout.

## How it stays current

- Every night a GitHub Action attempts the organizer pages of records that have not ended, writes `data/verification.json` and `data/check_report.md`, archives the day's generated data under `data/snapshots/`, and redeploys if the check and validation pass. Unreadable sources are reported rather than silently treated as corrections.
- Dates that no longer match are listed in the issue **"Runway: dates to review"**. Corrections go in `sources/overrides.json` with a `_why`, a `reviewed_on` date, the organizer's verbatim wording and the exact URL or image; the build gate rejects a correction without them.
- Meetings that have ended are kept as captured and are not re-read.
- New meetings enter a `sources/group_*.json` file, following `sources/SCHEMA.md`, only after the organizer evidence has been reviewed. The governed expansion will generate candidates outside the publication files first.

## Repository map

| Path | What it is |
|---|---|
| `sources/` | Curated inputs; `overrides.json` (curator corrections) wins over everything |
| `scripts/build.py` | Builds `site/data/runway.json`, the calendar feed `site/runway.ics` and the handoff page `site/ai-handoff.html` |
| `scripts/handoff_page.py` | Renders `site/AI-HANDOFF.md` as the handoff page (standard library only; run by `build.py`) |
| `scripts/check.py` | Re-reads organizer pages (robots.txt obeyed) |
| `scripts/linkcheck.py` | Reports links that now fail |
| `scripts/validate.py` | Build gate |
| `scripts/ui_check.py` | Scripted browser check of the interface |
| `scripts/icon_versions.py` | Stamps icon URLs with a content version |
| `scripts/snapshot.py` | Archives the day's generated data |
| `scripts/geocode.py` | Places venues for the location filters |
| `site/` | The static website: no framework, cookies, analytics or third-party requests |
| `.github/workflows/runway.yml` | Build, validate and deploy on push; nightly check on schedule |

## Run it yourself

Python 3.12; the build uses only the standard library. From the repository root:

```text
python scripts/build.py
python scripts/validate.py
python -m http.server 8000 --directory site
```

The maintenance run, the interface check and hosting a copy are in §6 of the handoff.

## Header indices

Both are recomputed in the browser from `site/data/runway.json` and defined in full in [§3.4 of the handoff](site/AI-HANDOFF.md#34-nightly-verification-and-admission-pipeline).

- **Fidelity Index:** evidence coverage (the share of dated records that carry the organizer's wording or a published rule, a good verification state and a current source link) multiplied by projected correctness (one minus the error rate pooled from independent audits).
- **Reliability Index:** the share of dated records not yet ended that the latest automated check re-confirmed from the organizer's own page or image, plus dates computed from a published rule. Manual reviews never count.

## Verification labels

A record that passed its check carries no label. Otherwise:

- **Save the date:** the organizer has published only a save-the-date.
- **Set by rule:** an observance computed from its organizer's published rule.
- **Recorded when published:** a meeting that has ended, kept as captured.
- **Expected month:** projected from a meeting's usual month; never given a day.
- **Needs review** or **Not re-checked** ("Date needs review" or "Source not re-checked" inside the record): the latest automated check did not confirm the record and no current manual review covers it. The **Needs review only** switch lists these.

Where an organizer's own pages disagree, the record follows the organizer's primary event page and states the disagreement inside the record.
