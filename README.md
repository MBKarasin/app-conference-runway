# APP Conference Runway

A source-traced calendar of conferences, abstract deadlines, student and DNP project venues, and observances for advanced practice providers (NPs, PAs, CRNAs, CNSs, CNMs) worldwide. Every dated entry links to the organizer's own page and quotes the wording the date came from, so a visitor can confirm it before registering, submitting or traveling. Coverage is still concentrated in the United States and is not exhaustive.

Live site: https://mbkarasin.github.io/app-conference-runway/ (kept out of search engines on purpose; it is meant to travel from APP to APP).

How it was built, what it can and cannot prove, and how to challenge or reproduce it: [`site/AI-HANDOFF.md`](site/AI-HANDOFF.md). Terms of reuse: [`LICENSE`](LICENSE) (CC0 for the curator's own work; organizer material and third-party components keep their own rights).

## What a visitor sees

- **Orbit** (the landing view): twelve consecutive months starting with the current month, arranged in a ring, with the density of meetings, abstract deadlines and open calls on each month. Choose a month for its records, the center label for all twelve months, or the arrows to move the window a year at a time.
- **List**: upcoming records grouped by month. **Calendar**: a month grid with multi-day bars. **Directory**: every recurring series with its recorded history.
- Filters for discipline (NP, AGACNP, CRNA, NP-RNFA, CNS, CNM, PA, Students & DNP projects), focus, location type, global region and distance from a ZIP or city. Every view is a shareable link.
- A "Needs review only" switch lists the records whose last automated check did not confirm the date, and each record shows its source link, the quoted wording and, where the date was published only in an image, that image.

## How it stays current

- A GitHub Action scheduled nightly (06:00 UTC, about 2 a.m. Eastern; GitHub may start it late and it runs whenever it starts) re-reads every upcoming edition's organizer page, records what it found in `data/verification.json` and `data/check_report.md`, archives the day's generated data under `data/snapshots/`, and redeploys. The page header shows the time of the last source read.
- If a date stops matching its organizer page, the issue **"Runway: dates to review"** is refreshed from the report. Corrections go in `sources/overrides.json` with a `_why`, a verbatim quote and the exact URL or image; a push to `main` rebuilds and redeploys.
- Meetings that have ended are frozen as they were captured and are not re-read.
- New meetings are added to a `sources/group_*.json` file following `sources/SCHEMA.md`, from the organizer's own pages (including local-language pages, with titles translated into English and the original kept).

## Repository map

| Path | What it is |
|---|---|
| `sources/` | Curated inputs. Never edited by the checker. `overrides.json` holds the curator's corrections and wins over everything. |
| `scripts/build.py` | Merges sources and verification into `site/data/runway.json` and `site/runway.ics`; projects "expected" months up to three years ahead; maintains `data/ledger.json`, the permanent record of every edition ever published. |
| `scripts/check.py` | Re-reads organizer pages (robots.txt honored, one request per page, one site at a time). Writes `data/verification.json` and `data/check_report.md`. |
| `scripts/linkcheck.py` | Reports source links that now fail. |
| `scripts/validate.py` | Build gate: bad dates, non-HTTPS sources, private-looking strings, projections past the horizon, unsupported absence claims, missing landmark records, and upcoming records without a quote and source fail the build. |
| `scripts/snapshot.py` | Archives the generated data candidate for the day under `data/snapshots/<year>/` and lists its SHA-256 in `MANIFEST.csv`. |
| `scripts/geocode.py` | Places venues (U.S. Census Gazetteer; GeoNames, CC BY 4.0) for the region and distance filters; manual pins live in `sources/geo/manual.json`. |
| `site/` | The static website: no framework, no third-party requests at runtime, no cookies or analytics, self-hosted fonts (SIL Open Font License). |
| `.github/workflows/runway.yml` | Build, validate and deploy on push; nightly check, archive and review digest on schedule. |

## Run it yourself

Python 3.12, standard library only (plus `pypdf` for the checker). From the repository root:

```text
python scripts/build.py
python scripts/validate.py
python -m http.server 8000 --directory site
```

To host a copy: fork the repository (including `.github/`), set Pages → Source to **GitHub Actions**, give workflows read and write permission so the checker can commit, edit `site/assets/config.js` for your own name and request address, and run **Check sources and publish** once. The full replication contract is §7 of `site/AI-HANDOFF.md`.

## Verification states

- **Start found**: the start date, its year and a distinctive word of the meeting name were found on the organizer page at the last check. End dates are not re-checked automatically.
- **Source wording changed**, **Needs review**, **Not re-checked**, **Organizer dates conflict**: exceptions, shown with a plain note on the record and listed by "Needs review only".
- **Recorded when published**: a meeting that has ended, kept as captured.
- **Expected**: projected from a meeting's usual month; never given a day. **Set by rule**: an observance computed from its organizer's published rule.

## Roadmap

- A Leadership discipline (CNML, CENP, NE-BC, NEA-BC, CNL and leadership programs the curator has named for review, such as the AANP leadership academy, the Stanford APP leadership certificate and the Loretta Ford Visionary Leadership Program) is planned as a Focus and a program type; it will be added only with organizer-sourced records.
- A reviewed dark palette. The site currently renders its light palette regardless of device theme.
- Coverage outside the United States and non-English sources.
