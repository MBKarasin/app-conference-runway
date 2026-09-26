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
| `scripts/indices.py` | Recomputes the header's Fidelity and Reliability indices, with every term |
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

Both numbers are recomputed in the visitor's browser from `site/data/runway.json` at every page load. `python scripts/indices.py` recomputes them from the same file, or from the live copy with `--data https://mbkarasin.github.io/app-conference-runway/data/runway.json`, and prints every term; the interface check fails if the page shows anything else. Full definitions and caveats: [§3.4 and §3.5 of the handoff](https://mbkarasin.github.io/app-conference-runway/ai-handoff.html#34-nightly-verification-and-admission-pipeline).

**Fidelity Index = evidence coverage × projected correctness**

- *Evidence coverage* = dated records that pass every test ÷ all dated records (ended and upcoming; month-only projections excluded). A record passes if it carries the organizer's verbatim wording or a published rule, holds a settled state (confirmed, set by rule, save the date, recorded when published) and has a source link; a meeting not yet ended also needs a link not found gone and a confirmation no older than 90 days.
- *Projected correctness* = 1 − (records found wrong ÷ records audited), summed over the audits in `sources/audits.json`. A record counts wrong if any action-critical field (dates, format, place, abstract call or deadline, eligibility) disagreed with the organizer. The range shown is the 95% Wilson interval of that rate.
- *Worked example* (data built 2026-09-26): coverage 927 ÷ 927 = 100.00%; correctness 1 − (10 + 9) ÷ (325 + 324) = 97.07%; Fidelity 97.07%, range 95.5–98.1%.

**Reliability Index = (records re-confirmed by the latest automated check + dates set by a published rule) ÷ dated records not yet ended**

- *Re-confirmed* means the nightly check found the start date, its year and a word of the meeting's name on the organizer's own page (rendered when it needs JavaScript) or in the organizer's image the record links. Manual reviews never count. When no check has completed in 36 hours, re-confirmations stop counting.
- *Worked example* (check of 2026-09-25, 10:42 UTC): (256 + 29) ÷ 313 = 91.05%. Most of the other 28 are pages whose servers refused the cloud-hosted checker that night; each rests on a manual review of the organizer's source.

**What they do not show.** Neither measures completeness (meetings missing from the site). Coverage is high largely by construction, since the build gate refuses an upcoming record without a quote and source link. Both audits examined the same upcoming records on 2026-09-24, before the corrections that followed them, and were carried out by AI systems under the curator's direction; the second, a review of the code, data and interface, re-derived no event in full. Counting their shared sample once widens the range to 94.6–98.4%, and the re-derivation alone gives 96.92%. Reliability measures whether a machine can re-read a record tonight, not whether the record is right.

## Verification labels

A record that passed its check carries no label. Otherwise:

- **Save the date:** the organizer has published only a save-the-date.
- **Set by rule:** an observance computed from its organizer's published rule.
- **Recorded when published:** a meeting that has ended, kept as captured.
- **Expected month:** projected from a meeting's usual month; never given a day.
- **Needs review** or **Not re-checked** ("Date needs review" or "Source not re-checked" inside the record): the latest automated check did not confirm the record and no current manual review covers it. The **Needs review only** switch lists these.

Where an organizer's own pages disagree, the record follows the organizer's primary event page and states the disagreement inside the record.
