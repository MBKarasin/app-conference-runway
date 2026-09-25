# APP Conference Runway

A source-traced calendar of conferences, abstract deadlines, student and DNP project venues, and observances for advanced practice providers (NPs, PAs, CRNAs, CNSs, CNMs) worldwide. Every dated entry links to the organizer's own page and quotes the wording the date came from, so a visitor can confirm it before registering, submitting or traveling. Coverage is still concentrated in the United States and is not exhaustive.

Live site: https://mbkarasin.github.io/app-conference-runway/ (kept out of search engines on purpose; it is meant to travel from APP to APP).

How it was built, what it can and cannot prove, and how to challenge or reproduce it: [`site/AI-HANDOFF.md`](site/AI-HANDOFF.md). Terms of reuse: [`LICENSE`](LICENSE) (CC0 for the curator's own work; organizer material and third-party components keep their own rights).

## What a visitor sees

- **Orbit** (the landing view): twelve consecutive months starting with the current month, each labeled with its year (Sep ’26 … Aug ’27), arranged in a ring, with the density of meetings, abstract deadlines, open calls and celebrations on each month. Choose a month for its records, the center label for all twelve months, or the arrows to move the window a year at a time.
- **List**: upcoming records grouped by month. **Calendar**: a month grid with multi-day bars. **Directory**: every recurring series with its recorded history. The display switch reads List | Calendar | Orbit | Directory.
- Filters, in three rows under the display switch and search box: **Discipline** (NP, AGACNP, CRNA, NP-RNFA, CNS, CNM, PA) with **Focus** to its right, one record type at a time (All, Abstracts Due, Open Abstracts, Conferences, Celebrations; each chip wears its type's color); then **Scope** (Clinical, Academic, Research, Leadership, Students) with **Location** to its right (format, global region, distance from a city or ZIP). Abstracts Due and Open Abstracts list records by the month the abstracts are due. The badges on a List card are the same vocabulary, and choosing one applies that filter. Every view is a shareable link.
- On phones, the Calendar is a day-by-day agenda (opening at today in the current month, with records still under way listed above today), the header and filter rows are compact with swipeable chip rows, and turned sideways the filter bar scrolls away with the page. The desktop layout is unchanged.
- A List card carries a verification note only when there is something to say (below). A "Needs review only" switch lists the records whose last automated check did not confirm the date, and each record shows its source link, the quoted wording and, where the date was published only in an image, that image.

## How it stays current

- A GitHub Action scheduled nightly (06:00 UTC, about 2 a.m. Eastern; GitHub may start it late and it runs whenever it starts) re-reads every upcoming edition's organizer page, records what it found in `data/verification.json` and `data/check_report.md`, archives the day's generated data under `data/snapshots/`, and redeploys. The page header shows the time of the last source check with the Fidelity Index and Reliability Index beneath it (below).
- If a date stops matching its organizer page, the issue **"Runway: dates to review"** is refreshed from the report. Corrections go in `sources/overrides.json` with a `_why`, a verbatim quote and the exact URL or image; a push to `main` rebuilds and redeploys.
- Meetings that have ended are frozen as they were captured and are not re-read.
- New meetings are added to a `sources/group_*.json` file following `sources/SCHEMA.md`, from the organizer's own pages (including local-language pages, with titles translated into English and the original kept).

## Repository map

| Path | What it is |
|---|---|
| `sources/` | Curated inputs. Never edited by the checker. `overrides.json` holds the curator's corrections and wins over everything. |
| `scripts/build.py` | Merges sources and verification into `site/data/runway.json` and `site/runway.ics`; projects "expected" months up to three years ahead; maintains `data/ledger.json`, the permanent record of every edition ever published. |
| `scripts/check.py` | Re-reads organizer pages (robots.txt honored, one request per page, one site at a time). Where the organizer's server delivered the page but the plain reader found too little text or no match, it renders the page in headless Chromium and reads the organizer's own flyer or banner that the record links with OCR; a site that refuses automated readers is reported, never retried with a browser. Writes `data/verification.json` and `data/check_report.md`. |
| `scripts/linkcheck.py` | Reports source links that now fail. |
| `scripts/validate.py` | Build gate: bad dates, non-HTTPS sources, private-looking strings, projections past the horizon, unsupported absence claims, missing landmark records, and upcoming records without a quote and source fail the build. |
| `scripts/ui_check.py` | Scripted interface check (Playwright, Chromium): display switch and its separators, the year on every Orbit month, the Discipline/Scope/Focus rows, both header indices (labels, and values re-derived from the published data), phones held upright and sideways (touch-emulated), the landmark celebration weeks in every view, each Focus in each view, old links, the request address, layout at 1440 px and 390 px, console errors; since 2026-09-24 also the header tagline, content-versioned icon URLs and a letterless tab icon, and the red team's P1 cases replayed with the clock frozen at the audit's moment (each failed on `e4bbe92`). "Visible" means rendered and not inside a closed section. Run it before every interface push and with `--url` against the live site after. |
| `scripts/icon_versions.py` | Stamps every browser-tab and installed-app icon URL with its content version (`?v=` + the first 8 hex digits of its SHA-256). Run it after any icon change; `--check` exits 1 if a stamp is stale. |
| `scripts/snapshot.py` | Archives the generated data candidate for the day under `data/snapshots/<year>/` and lists its SHA-256 in `MANIFEST.csv`. |
| `scripts/geocode.py` | Places venues (U.S. Census Gazetteer; GeoNames, CC BY 4.0) for the region and distance filters; manual pins live in `sources/geo/manual.json`. |
| `scripts/preview.py` | Builds a self-contained local HTML preview with no network requests. Developer tool; not run by the workflow. |
| `site/` | The static website: no framework, no third-party requests at runtime, no cookies or analytics, self-hosted fonts (SIL Open Font License). |
| `.github/workflows/runway.yml` | Build, validate and deploy on push; nightly check, archive and review digest on schedule. |

## Run it yourself

Python 3.12, standard library only (plus `pypdf` for the checker; optionally Playwright with Chromium, Pillow and tesseract for its second readers). From the repository root:

```text
python scripts/build.py
python scripts/validate.py
python -m http.server 8000 --directory site
```

Before pushing an interface change, run `python scripts/ui_check.py` (it needs `pip install playwright` and `playwright install chromium`); every check must pass.

To host a copy: fork the repository (including `.github/`), set Pages → Source to **GitHub Actions**, give workflows read and write permission so the checker can commit, edit `site/assets/config.js` for your own name and request address, and run **Check sources and publish** once. The full replication contract is §7 of `site/AI-HANDOFF.md`.

## Header indices

Defined in full in §3.4 of [`site/AI-HANDOFF.md`](site/AI-HANDOFF.md#34-verification-pipeline); both are recomputed in the browser from `site/data/runway.json`.

- **Fidelity Index**: the share of dated records (past and upcoming) that carry the organizer's own wording or a published rule, hold a good verification state and a source link, and, for meetings still ahead, a working link confirmed within 90 days. It does not claim that end dates, venues or submission cut-off times were verified.
- **Reliability Index** (the curator's definition, a machine re-check rate): the share of dated records that have not ended which the latest automated check re-confirmed from the organizer's own page or image, plus dates computed from a published rule. Manual reviews never count as machine confirmations, and when no check has completed in 36 hours the index drops to the rule-computed share.

## Verification states

**A record that passed its check carries no label.** Fidelity is presumed: every dated record traces to the organizer, and a label appears only where the checks have something to say. ("Start found" and "Source reviewed" were retired on 2026-09-24; labelling the normal case told a reader nothing and buried the exceptions.)

- **Save the date**: the organizer has published only a save-the-date for these days.
- **Set by rule**: an observance computed from its organizer's published rule.
- **Recorded when published**: a meeting that has ended, kept as captured.
- **Expected**: projected from a meeting's usual month; never given a day.
- **Needs review** and **Not re-checked** (inside the record: "Date needs review" and "Source not re-checked"): exceptions, records whose latest automated check did not confirm them and that have no curator evidence on file; "Needs review only" lists them. Where an organizer's own pages disagree, the record follows the organizer's primary event page and states the disagreement inside the record.

## Roadmap

- A Leadership discipline (CNML, CENP, NE-BC, NEA-BC, CNL and leadership programs the curator has named for review, such as the AANP leadership academy, the Stanford APP leadership certificate and the Loretta Ford Visionary Leadership Program) is planned as a Scope and a program type; it will be added only with organizer-sourced records.
- A reviewed dark palette. The site currently renders its light palette regardless of device theme.
- Coverage outside the United States and non-English sources.
