# APP Conference Runway: AI Handoff

**Audience:** the global APP community.
**Purpose:** to show how this site was built, where every claim on it comes from, and how to reproduce or challenge it. Read it before running anything.
**Governance:** MBK Governance v5.0 (2026-09-21; trial through the 2026-10-04 review). Invoked for this project and confirmed active at 2026-09-23 21:26:33 -04:00 (EDT).
**Live site:** https://mbkarasin.github.io/app-conference-runway/ (kept out of search engines on purpose)
**Source code:** https://github.com/MBKarasin/app-conference-runway. It is public, so anyone can read every file and its full change history. Only the curator can change the site; others can suggest changes through GitHub issues.
**Curator and accountable owner:** Dr. Mark Karasin, DNP, APN, AGACNP-BC
**Document date:** 2026-09-23

---

## 1. Why this exists

Advanced practice providers (NPs, PAs, CRNAs, CNSs, CNMs) and their students have no single place to see where their colleagues meet, present and publish. Meetings are scattered across hundreds of organizer sites in many languages. Abstract deadlines come and go unseen, and student and DNP project venues are hard to find.

The Runway is a single, open, source-traced calendar of those opportunities. The goal is to help clinicians exchange ideas toward a shared aim: advancing the discipline and improving human health outcomes. Visitors search or filter the calendar, then open an entry to review its source wording and confirm details with the organizer.

The site is independent. It is not an official publication of, or endorsement by, Rutgers University or RWJBarnabas Health.

## 2. How it came together

- **Human role.** The curator conceived and directed the instrument's purpose, information architecture, visual representation, interface behavior, navigation, filters, taxonomy and hierarchy. He designed the List, Calendar and Orbit graph concepts, determined their ordering and interaction rules, selected the visual and color direction, made every decision on hosting and visibility, and reviewed the output. Data corrections that serve the stated objective are executed by the AI and reported. The curator's approval is reserved for new destinations, accounts, cost or scope changes.
- **AI role.** An AI assistant (Claude, by Anthropic) researched organizer pages, compiled the data, wrote the build and check scripts, and walked organizer sites to confirm dates. ChatGPT (OpenAI) red-teamed the public-facing design, translated the curator's interface and visualization direction into code, tested and refined the List, Calendar, Orbit and filtering behavior, and generated the selected APP Conference Runway logo under Dr. Mark Karasin's direction. The AI systems served as research, implementation and review tools; public product and design decisions remained with the curator.
- **Lineage.** The site began as a single-page "Conference Runway" artifact (dataset compiled 2026-09-16, kept verbatim as `sources/runway_2026-09-16.json`). On 2026-09-21 and 2026-09-22 it was rebuilt as this static site with a nightly checker.
- **Failures found during the build, and the controls added for each.** They are recorded here so reviewers can test whether the controls hold.
  - **Coverage drawn from memory.** Observances were missing (for example, National APP Week). Control: build a source-universe inventory before searching, and report coverage as a table.
  - **A checker that could not pass.** Ended meetings were re-read against pages that had moved on to the next edition, which produced 133 false "needs review" flags. Control: once a meeting ends, its record is frozen at what the page said when it was captured.
  - **One page fetched and treated as unfindable.** Dates were sitting in a site's menus. Control: walk the organizer's event index, the pages under its menus, program and registration pages, and any linked PDFs before calling a date unresolved.
  - **Dates inside images went unread.** Dates were published only in banners or flyers. Control: read the images, and link the image in the record.
  - **Unchecked absence claims.** Control: the build gate rejects absence language (see `scripts/validate.py`).
  - **"Reviewed" labels without a recorded quote.** Control: every upcoming dated record must carry verbatim organizer wording plus the exact URL, PDF or image it came from.

## 3. Content architecture (the core of the site)

### 3.1 Entities

| Entity | What it is | Key fields |
|---|---|---|
| **Series** | A recurring meeting or observance run by one organizer | `id` (organizer slug + name slug), `name`, `org`, `org_url`, `professions`, `specialty`, `audience`/`focus`, `kind` (conference, symposium, summit, course, congress, observance), `region`, `recurrence`, `np_pa_basis` (why an NP/PA audience is justified), `archive_url` |
| **Edition** | One dated occurrence of a series | `id` = first 12 hex of SHA-1(`series` + "\|" + `start`), `start`, `end`, `location`, `format`, `theme`, `call` (abstract call: status, opens, closes, text, url), `source_url`, `evidence`, `evidence_image`, `compiled`, `reviewed_on`, `verify` |
| **Observance** | A celebration week or day with a published rule (for example, "PA Week, October 6–12") | `sources/observances.json`: the rule is stored with its evidence and computed per year |
| **Student opportunity** | A student session, poster or DNP project venue attached to one edition | `sources/student_opportunities.json`: `category` (student or project), `kind`, `detail`, `roles`, `url`, `deadline` |
| **Expected edition** | A projection of a meeting's usual month, up to three years ahead | Never given a day, and always labeled "Expected month" |

At this snapshot: 328 series; 1,593 editions (370 dated records confirmed against organizer material, 298 of them still upcoming; 521 past editions frozen as published; 36 set by rule, 1 organizer save-the-date and 665 expected months); organizers in 38 countries; 58 student and DNP opportunities; horizon through 2029.

### 3.2 The evidence rule

A dated record is published only with all three of:
1. the organizer's own material as the source: its event page, a page under its menus, a program PDF, or a banner or flyer image;
2. **verbatim** wording from that source that contains the dates (`evidence`, 200 characters or fewer, never paraphrased; translated titles are recorded in English, and the original-language wording is kept);
3. the exact location of that wording (`source_url`, plus `evidence_image` when the dates are in an image).

Aggregator listings are never treated as the source. A social post counts only when it comes from the organizer's own account (for example, AAAA 2027 on LinkedIn).

### 3.3 Provenance layers and precedence

`sources/runway_2026-09-16.json` (original) → `sources/group_*.json` (research batches) → `sources/archive/*` (past editions and archive links) → `sources/observances.json` → **`sources/overrides.json`** (curator corrections, which win over everything; each entry carries a `_why`). Duplicate series are folded through `aliases`. A wrong or duplicate edition is removed with `"removed": true` and a reason. It is never silently deleted.

`data/ledger.json` is a permanent record of every edition ever published. `data/snapshots/<year>/<date>.json.gz` keeps the full published data file for each New York calendar day (from 2026-09-23; the 2026-09-21 and 2026-09-22 files hold a smaller field set), and `data/snapshots/MANIFEST.csv` records the SHA-256 of each day's uncompressed file.

### 3.4 Verification pipeline

| Stage | Script | What it proves | What it cannot prove |
|---|---|---|---|
| Nightly re-read (scheduled 06:00 UTC; GitHub may start it late) | `scripts/check.py` | That the start date (in English, Portuguese, Spanish, French, German, Dutch, Italian, Japanese or Chinese 年/月/日 formats; numeric day-first and month-first; day lists such as "24th, 25th & 26th September" or "19 y 20 de noviembre"; for titles translated into English or pages in CJK script, the date and year decide), its year, and a distinctive name word still appear on the source page | End dates; pages that block automated readers, need JavaScript, or show dates only in images |
| Frozen past | `check.py` | Nothing: an ended meeting is kept as it was captured | — |
| Manual walk | done by the AI assistant in a real browser, under the curator's direction; the curator confirms disputed dates himself | Dates on pages the checker cannot read. The walk covers menus, sub-pages, PDFs, images and translation | Anything not walked (recorded in each override's `_why`) |
| Link check | `scripts/linkcheck.py` | Which source links now return 4xx | A 403 block says nothing about whether the link is live |
| Build gate | `scripts/validate.py` | Rejects bad dates, non-HTTPS sources, private-looking strings, projections past the horizon, days on expected rows, and unsupported absence claims | Semantic truth of a quote |

The page header shows one **Updated** timestamp: the time of the last nightly source read (or, when that is unavailable, the latest data build). Manual reviews are dated per record (`reviewed_on` in `sources/overrides.json`). As of 2026-09-22 those reviews were carried out by the AI assistant under the curator's direction. The curator personally confirmed two dates that appear only in images: ENRS 2027 and PNAA 2027. Confirmed records carry no status badge. A record whose latest automated check did not confirm it, and has no curator evidence on file, shows a note ("Date needs review", "Source not re-checked", "Organizer dates conflict" or "Source wording changed"); "Needs review only" in Filters lists just those (deep link `#review=1`). Each record links its source and quotes its wording.

### 3.5 Known limits (attack these first)

- The checker is a text match. A start date, the year and one name word anywhere on a page will pass, even when the page lists other events.
- End dates are recorded from the source but are not re-checked automatically.
- Discipline tags (NP, PA, and the others) are curator judgments backed by `np_pa_basis`. The AGACNP filter is a curated topic view. It does not claim an AGACNP-specific track or credit.
- "Students & DNP projects" is one public discipline: organizer-documented opportunities for APP students (NP, PA, CRNA, CNS, CNM) together with venues that accept DNP project posters or abstracts. The underlying records retain their more specific student or project categories.
- Coverage is concentrated in the United States and is incomplete globally.

## 4. Website architecture

- **Static site** in `site/`: `index.html`, `assets/app.js` (all behavior, no framework), `assets/app.css`, `assets/app-conference-runway-logo.png`, `assets/config.js` (curator details and request address), `data/runway.json`, `runway.ics` (calendar feed), and self-hosted fonts.
- **No third-party requests at runtime.** No cookies, analytics or trackers. The Content-Security-Policy is `default-src 'self'`.
- **Search visibility:** `noindex, nofollow, noarchive` and `robots.txt`, by decision. The site spreads hand to hand among APPs.
- **Hosting:** GitHub Pages, deployed by GitHub Actions (`.github/workflows/runway.yml`).
  - Every push to `main` builds, validates and deploys.
  - A nightly schedule (06:00 UTC, which is 2 a.m. EDT or 1 a.m. EST; there is no clock gate, so a late start still runs) runs build, check, link check, build and validate, then archives the day's data even if the check failed. It commits the stamps and rewrites the "Runway: dates to review" issue from `data/check_report.md` on every run (closing it when nothing is open), so the issue and the report cannot disagree.
  - Workflow permissions default to none. Each job requests only what it needs. Third-party actions are pinned to commit SHAs.
- **Geography:** `scripts/geocode.py` places venues using the U.S. Census Gazetteer and GeoNames (CC BY 4.0), with manual pins in `sources/geo/manual.json`.

## 5. Design and navigation

- **Design authority and implementation:** The curator is the design authority for the site's visual representation, information architecture, user interface, List and Calendar presentations, Orbit graph, record grouping, filter model and public wording. AI assistants implemented and tested those decisions in the static site and documented material revisions here.
- **Header:** image logo (returns to the landing page), tagline, Copy link, Share, Make a request, AI Handoff, a two-line explanation of what the instrument does and how to use it, and a right-aligned automated re-check timestamp on the same bottom header row.
- **Logo and Rutgers reference:** The selected logo was generated by ChatGPT under Dr. Mark Karasin's direction. Its runway metaphor, navy field, white lettering and `#CC0033` scarlet accent were selected for this project. Scarlet is used as a restrained color reference to Rutgers; the logo does not reproduce the Rutgers block R, wordmark, seal or another institutional mark, and it does not imply Rutgers endorsement.
- **Tabs:** Upcoming · Abstract deadlines · Students & DNP projects · Directory.
- **Abstract deadlines:** mutually exclusive groups appear in this order: Due within 30 days · Opening within 30 days · Open now. A call is shown only once, with imminent closing dates taking priority.
- **Discipline filter:** All APPs, NP, AGACNP, CRNA, NP-RNFA, CNS, CNM, PA, Students & DNP. Student and DNP records share one discipline. Location type (All, Live, Online or Hybrid) can be combined with Global Region; distance and search remain independent filters.
- **Focus filter:** Clinical, Academic, Research and Leadership can be selected singly or in combination; All clears the focus selection. Focus sits directly to the right of Discipline on wide screens and becomes its own horizontally scrollable row on phones. The interface derives these tags from audience, specialty, organizer and meeting-name metadata, and every display uses the same match.
- **List view:** one card per edition, with discipline badges, the abstract-call state and the organizer.
- **Display switch:** List, Calendar and Orbit are alternate presentations of the same filtered records. Scarlet internal dividers make the three choices distinct. On wide screens the location controls sit immediately to the right of this switch under the label **Location**, followed by format and **Global Region** controls; the row stacks at narrow breakpoints. **Clear all** sits with the search and Filters controls so it cannot displace location.
- **Calendar view:** each consecutive run of days is one bar per week, not one entry per day. Colors show record type only: meeting, open abstract call (a bar running to the due date, with a scarlet end on the due day), abstract due and celebration. Dark navy borders carry the grid; scarlet is reserved for the current date, deadline ends, selected controls and a restrained accent on APP Week. The visible month is centered between paired month/year navigation arrows, while the two-row color key sits beside the Today control. When a week has hidden lanes, a dark-navy-topped, scarlet-accented raised disclosure bar says **+XX more this week** and lifts on hover before expanding in place. Filtered weeks with no matching records say so explicitly. Clicking a day number opens every record for that day.
- **Footer:** the compact provenance block begins with scarlet **Curated by**, keeps each affiliation and title on curator-specified lines, and uses the remaining width for one left-aligned explanation of source checking and coverage. The former Curator's note label and duplicated narrative were removed.
- **Orbit view:** the selected year and active filters float at the center of a circular month arrangement. Three rising columns on every month encode filtered meeting, abstracts-due and open-abstract density, with a plain count below each column. Choosing a month refreshes three initially open, collapsible sections in this order: Abstracts Due, Meetings & Conferences, Open Abstracts. The records open the same evidence detail used everywhere else. Logo navy marks meetings, scarlet marks due dates and a deeper green marks open calls. Location type, Global Region, distance, discipline, Focus, type, specialty, source-review status, abstract-call status, tab and search all use the same shared matcher as List and Calendar. Upcoming excludes past editions, Abstract deadlines admits only current or announced calls, Directory can show the full selected year, and projected records enter Orbit only when **Show expected dates** is enabled. These scopes live in interface logic rather than the current dataset, so subsequent source rebuilds retain them. If a new location filter leaves the selected month empty, Orbit moves within the displayed year to the first month that has a match; for example, Qatar reveals Qatar Health Congress in November 2026.
- **Record detail:** dates, location, abstract call, student opportunity, a seven-year view (three years back to three ahead), the organizer's archive, the source link, the quoted wording, a calendar file, and "Suggest a fix" (opens a GitHub issue).
- **Every view is a URL.** Filters and views live in the address hash, so a view can be shared as a link.
- **Dark mode** follows the device. The layout works at phone width.

## 6. Tools used

| Layer | Tool |
|---|---|
| AI assistant (build, research, verification) | Claude (Anthropic), in the Claude desktop app's Cowork mode, including its sub-agents, web search and fetch, and built-in browser. The session that wrote this document was configured for model `claude-opus-5-5`; per-session models are not recorded in the repository. |
| Independent reviewer and logo production | ChatGPT (OpenAI): independent red-team review; selected logo generated under Dr. Mark Karasin's direction; logo/header, two-line introduction and calendar visual hierarchy implemented in the GitHub web editor |
| AI sandbox tooling (review only, not in the pipeline) | Linux container; Python 3.11; Playwright 1.56 with Chromium (renders sites and walks organizer pages); Tesseract OCR (image dates); pypdf (PDF dates); Node 22 (syntax checks) |
| Browser on the curator's computer | The Claude desktop app's built-in browser and the Codex in-app browser, driven by the respective AI assistants, to walk sites that block cloud readers and to commit through GitHub's web editor |
| Pipeline | GitHub Actions on ubuntu-latest; Python 3.12; pypdf 5; the official `actions/checkout`, `setup-python`, `configure-pages`, `upload-pages-artifact` and `deploy-pages` |
| Hosting | GitHub Pages |
| Data references | U.S. Census Bureau Gazetteer; GeoNames (CC BY 4.0) |
| Fonts | Barlow Condensed and Source Sans 3 (SIL Open Font License) |
| Curator hardware | A personal desktop computer. Specifications are not recorded here. |

## 7. Reproduce it

This section is the replication contract. A future maintainer or AI should be able to recreate the public instrument, its data build and its maintenance workflow from the repository alone. Do not infer behavior from a screenshot when the rule is recorded here or in the source.

### 7.1 Choose the level being reproduced

1. **Visual and interaction replica.** Copy `site/` and serve it as static files. This preserves the published data snapshot, logo, fonts, List, Calendar, Orbit and filters, but it does not refresh records.
2. **Deterministic data replica.** Copy the whole repository and run the build and validation steps below. This regenerates the public data from the committed source files and verification state.
3. **Maintained public replica.** Fork the whole repository, configure GitHub Pages and workflow permissions, and retain the scheduled source check, snapshot and issue-reporting jobs. This is the level needed to reproduce the operating project rather than only its appearance.

### 7.2 Required environment and authoritative inputs

- Use Python 3.12. The build, validation, geocoding, link-check and snapshot scripts otherwise use the Python standard library. Install `pypdf==5.*` before the web source check so evidence in PDFs can be read. There is no Node, bundler, package manager, database, server framework or runtime API.
- Treat `sources/runway_2026-09-16.json`, `sources/group_*.json`, `sources/archive/`, `sources/observances.json` and `sources/student_opportunities.json` as the curated content inputs. Follow `sources/SCHEMA.md` when adding records.
- `sources/overrides.json` is the final authority for corrections and removals; its entries must retain `_why`. Series aliases are resolved before editions are emitted. `data/verification.json` and `data/link_status.json` are machine-written observations, not replacements for the curated inputs.
- `sources/geo/manual.json` is the authority for locations that automatic geocoding cannot place. Generated geography is written to `sources/geo/locations.json`, `site/geo/cities.json` and the ZIP shards under `site/geo/zip/`.
- The public interface is defined by `site/index.html`, `site/assets/app.js`, `site/assets/app.css` and `site/assets/config.js`. The logo and self-hosted fonts in `site/assets/` are part of the visual system. Preserve the independence statement when personalizing affiliations.

### 7.3 Rebuild and preview locally

From the repository root, run:

```text
python scripts/build.py
python scripts/validate.py
python -m http.server 8000 --directory site
```

Open `http://localhost:8000/`. The build writes `site/data/runway.json` and `site/runway.ics` and updates the permanent `data/ledger.json`. A clean build must be followed by a passing validation before publication.

The following maintenance steps require network access and change their documented output files:

```text
python -m pip install "pypdf==5.*"
python scripts/check.py
python scripts/linkcheck.py
python scripts/build.py
python scripts/validate.py
python scripts/snapshot.py
```

`check.py` writes `data/verification.json` and `data/check_report.md`; `linkcheck.py` writes `data/link_status.json` and `data/link_report.md`; the second build incorporates those observations; `snapshot.py` archives the exact resulting public data. `geocode.py` is separate because it downloads Census and GeoNames reference files and rewrites the geography outputs; run it when a new or corrected venue needs placement, then rebuild and validate. The web is not deterministic, so record the run date and preserve the resulting git diff rather than expecting a later check to return byte-for-byte identical observations.

### 7.4 Interface invariants and acceptance test

A replica is not complete until these behaviors are checked in a browser at desktop and phone widths:

- List, Calendar and Orbit apply the same search, location type, Global Region, distance, discipline, Focus, type, specialty, abstract-call and source-review filters. Address hashes must restore the same selection after reload and be safe to share.
- Location type partitions the applicable records into All, Live, Online and Hybrid without losing or duplicating a record. ZIP-radius filtering appears in the Orbit center only when used.
- Upcoming excludes past editions; Abstract deadlines contains current or announced calls; Directory may show the full selected year. Expected editions remain absent unless **Show expected dates** is enabled.
- Orbit uses the selected year and active filters at the center. Month columns use logo navy for meetings, scarlet for abstracts due and deep green for open calls, with plain counts below the zero line. The detail rail is initially open, remains collapsible, and is ordered **Abstracts Due → Meetings & Conferences → Open Abstracts**. When a location-only result exists outside the selected month, Orbit advances to the first matching month in that year.
- Calendar bars retain navy structural borders and type colors. Deadline items precede other expanded records for the day or week instead of falling below "more" content.
- Opening a record in any view reaches the same evidence detail, organizer source and verbatim date wording. Keyboard navigation, visible focus, device dark mode and narrow-screen layout must remain usable.
- Public discipline labels use CRNA and do not expose legacy source taxonomy. The public ordering is NP, AGACNP, CRNA, NP-RNFA, CNS, CNM, PA, Students & DNP.
- With browser developer tools open, the static site should produce no application errors and no third-party runtime requests.

### 7.5 Publish and operate a GitHub replica

1. Fork or clone the complete repository, including the hidden `.github/` directory. No secrets are required.
2. Edit `site/assets/config.js` for the curator, affiliations, role labels, request address and repository URL. Replace the logo only if intentionally redesigning the identity; keep its accessible text and responsive sizing.
3. In repository settings, set Pages **Source** to **GitHub Actions**. In Actions → General, give workflows **Read and write permissions** so the scheduled checker can commit verification files and maintain the review issue.
4. Run **Check sources and publish** manually once. Thereafter, `.github/workflows/runway.yml` rebuilds and validates every push to `main`, deploys `site/`, and performs the scheduled check, link report, snapshot and review-issue update.
5. `.github/workflows/bootstrap.yml` exists only to unpack the original bundled distribution. A normal clone or fork that already contains the full repository must not run it.
6. Confirm the deployed URL, the Updated timestamp, a source-detail dialog, the calendar feed and at least one filtered URL in each of List, Calendar and Orbit.

### 7.6 Definition of successful replication

The result is a faithful replica only when (a) the same committed inputs produce a validation-passing public dataset and calendar feed; (b) all three views preserve the filter and evidence rules above; (c) every published factual record remains traceable to its organizer material; (d) the scheduled workflow can update verification, snapshots and the review digest without a private service; and (e) a new maintainer can distinguish curator decisions, AI implementation, machine observations and organizer evidence from the repository history alone.

## 8. How to challenge it

- Pick any upcoming record. Open its source link and look for the quoted wording. If it is missing or does not support the dates, file "Suggest a fix" on that record or open an issue.
- Diff `sources/overrides.json` against its git history. Every manual change carries a `_why`.
- Run `scripts/check.py` and compare your results with `data/check_report.md`.
- Test the known limits in §3.5.

Corrections are welcome. The curator decides what is published.

## 9. Limits of the data

This is a curated directory, not a study, and it makes no accuracy or completeness claim. If you treat it as a dataset, these are the threats to validity as the builders understand them.

- **Construct.** An "APP opportunity" is operationalized as an organizer-published meeting, abstract call, student or DNP project venue, or observance. For NP and PA relevance, the justification is recorded per series in `np_pa_basis`. Inclusion is a judgment made by one curator, with no formal codebook beyond `sources/SCHEMA.md`.
- **Sampling frame.** The universe was assembled by AI-assisted web search seeded by the curator's knowledge and by organizer lists (national and state NP and PA associations, specialty societies, schools). Some sweeps, including DNP programs, are not verified as complete at this date. Organizers with little web presence are under-represented, and so is non-English content.
- **Measurement.** The truth criterion is agreement with the organizer's own published material. It is not attendance, and it is not whether the event actually took place. The automated check matches text and can produce false positives (another event on the same page) and false negatives (dates held in images, scripts or blocked pages). End dates are not re-checked.
- **Reliability.** There is one curator and one primary AI builder. No inter-rater agreement has been measured. A second model family reviewed the public-facing design and documentation, but it did not independently re-audit the full dataset. The primary AI both compiled and verified most records. That is self-verification, reduced but not removed by the verbatim-evidence rule and the curator's spot confirmation.
- **AI-specific risks.** Fabricated dates or organizers (a hallucination risk) are constrained because nothing is published without a verbatim quote and an exact URL. Automation bias, meaning trust in the checker's status, is reduced by removing per-record status badges from the public view.
- **Reproducibility.** The build is deterministic from `sources/`. The web is not deterministic: pages change. Nightly snapshots, the permanent ledger and the git history allow any past state to be reconstructed.
- **Suggested evaluation.**
  - A stratified random audit of upcoming records by independent human coders, reporting the share of dates supported by the source, with 95% confidence intervals.
  - A capture–recapture comparison against an independently built list, to estimate coverage.
  - The staleness rate over time, taken from the nightly check history.

## 10. Use and reuse

- **Permission.** To the extent the curator holds rights in this project's code, data compilation, design, AI-generated logo and documentation (including this handoff), he dedicates them to the public domain under [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/). Anyone may copy, modify, redistribute or build on them for any purpose, commercial or not, without asking and without attribution. Attribution is appreciated but not required.
- **What this dedication does not cover:**
  - **Organizer material.** Event names, the short verbatim quotes kept as evidence, linked pages and images, and any organizer marks belong to their organizers. They are reproduced only to show where a date came from.
  - **Third-party components**, which keep their own licenses: Barlow Condensed and Source Sans 3 (SIL Open Font License); GeoNames data (CC BY 4.0, attribution required); U.S. Census Bureau Gazetteer data (public domain).
  - **Institutional names and marks.** Rutgers University and RWJBarnabas Health names and logos are not licensed. Nothing here implies their endorsement.
- **No warranty.** The site and its data are provided as is, without warranty of any kind. Dates change. Confirm with the organizer before registering, submitting or traveling.
