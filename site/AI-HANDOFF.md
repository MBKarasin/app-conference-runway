# APP Conference Runway: AI Handoff

**Audience:** the global APP community.
**Purpose:** to show how this site was built, where every claim on it comes from, and how to reproduce or challenge it. Read it before running anything.
**Governance:** MBK AI Governance v5.0 (2026-09-21) invoked.
**Live site:** https://mbkarasin.github.io/app-conference-runway/ (kept out of search engines on purpose)
**Source code:** https://github.com/MBKarasin/app-conference-runway. It is public, so anyone can read every file and its full change history. Only the curator can change the site; others can suggest changes through GitHub issues.
**Curator and accountable owner:** Dr. Mark Karasin, DNP, APN, AGACNP-BC
**Document date:** 2026-09-23

---

## 1. Why this exists

Advanced practice providers (NPs, PAs, CRNAs, CAAs, CNSs, CNMs) and their students have no single place to see where their colleagues meet, present and publish. Meetings are scattered across hundreds of organizer sites in many languages. Abstract deadlines come and go unseen, and student and DNP project venues are hard to find.

The Runway is a single, open, source-traced calendar of those opportunities. The goal is to help clinicians exchange ideas toward a shared aim: advancing the discipline and improving human health outcomes. Visitors search or filter the calendar, then open an entry to review its source wording and confirm details with the organizer.

The site is independent. It is not an official publication of, or endorsement by, Rutgers University or RWJBarnabas Health.

## 2. How it came together

- **Human role.** The curator set the scope and filters, made every decision on hosting, visibility and design, and reviewed the output. Data corrections that serve the stated objective are executed by the AI and reported. The curator's approval is reserved for new destinations, accounts, cost or scope changes.
- **AI role.** An AI assistant (Claude, by Anthropic) researched organizer pages, compiled the data, wrote the build and check scripts, walked organizer sites to confirm dates, and made the initial design changes. ChatGPT (OpenAI) then independently red-teamed the public-facing design, generated the selected APP Conference Runway logo under Dr. Mark Karasin's direction, implemented the logo and two-line introduction, and refined the calendar's visual hierarchy.
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
- "Students & DNP projects" is one public discipline: organizer-documented opportunities for APP students (NP, PA, CRNA, CAA, CNS, CNM) together with venues that accept DNP project posters or abstracts. The underlying records retain their more specific student or project categories.
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

- **Header:** image logo (returns to the landing page), tagline, Copy link, Share, Make a request, AI Handoff, a two-line explanation of what the instrument does and how to use it, and a right-aligned automated re-check timestamp on the same bottom header row.
- **Logo and Rutgers reference:** The selected logo was generated by ChatGPT under Dr. Mark Karasin's direction. Its runway metaphor, navy field, white lettering and `#CC0033` scarlet accent were selected for this project. Scarlet is used as a restrained color reference to Rutgers; the logo does not reproduce the Rutgers block R, wordmark, seal or another institutional mark, and it does not imply Rutgers endorsement.
- **Tabs:** Upcoming · Abstract deadlines · Students & DNP projects · Directory.
- **Abstract deadlines:** mutually exclusive groups appear in this order: Due within 30 days · Opening within 30 days · Open now. A call is shown only once, with imminent closing dates taking priority.
- **Discipline filter:** All APPs, NP, AGACNP, PA, CRNA / CAA, CNS, CNM, NP-RNFA, Students & DNP. CAA records are folded into the CRNA / CAA discipline; student and DNP records share one discipline. Further filters cover location (online, continent, country, US region, or within a radius of a ZIP code or city), focus, kind and specialty.
- **List view:** one card per edition, with discipline badges, the abstract-call state and the organizer.
- **Calendar view:** each consecutive run of days is one bar per week, not one entry per day. Colors show record type only: meeting, open abstract call (a bar running to the due date, with a scarlet end on the due day), and celebration. Dark navy borders carry the grid; scarlet is reserved for the current date, deadline ends, selected controls and a restrained accent on APP Week. Filtered weeks with no matching records say so explicitly. Clicking a day number opens every record for that day. Celebration color, meeting color and a possible yearly view remain open design decisions rather than implemented features.
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

1. Read `README.md`, `sources/SCHEMA.md` and the two workflows before running anything.
2. Fork or clone the repository. No secrets are required.
3. Run locally: `python scripts/build.py && python scripts/validate.py`, then serve `site/` with any static server (for example, `python -m http.server -d site`).
4. Optional: `python scripts/check.py` re-reads organizer pages (it honors robots.txt and sends one request at a time per host). `python scripts/geocode.py` places new venues.
5. To publish your own copy: set Pages to "GitHub Actions", allow workflow write permission, run "Check sources and publish" once, and edit `site/assets/config.js`.

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
