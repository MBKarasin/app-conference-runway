# APP Conference Runway: AI Handoff

**Audience:** the global APP community.
**Purpose:** to show how this site was built, how its factual calendar claims are sourced, where projections and curator judgments enter, and how to reproduce or challenge it. Read it before running anything.
**Governance:** MBK Governance v5.0 (2026-09-21; trial through the 2026-10-04 review). Invoked for this project and confirmed active at 2026-09-23 21:26:33 -04:00 (EDT).
**Live site:** https://mbkarasin.github.io/app-conference-runway/ (requests exclusion from search indexing on purpose)
**Source code:** https://github.com/MBKarasin/app-conference-runway. It is public, so anyone can read every file and its full change history. Only the curator can change the site; others can suggest changes through GitHub issues.
**Curator and accountable owner:** Dr. Mark Karasin, DNP, APN, AGACNP-BC
**Document date:** 2026-09-24 (revised after the overnight repopulation audit, §3.6, and again for the same day's interface revision: Scope and Focus rows, Orbit labels and separators, verification badges, contact address, §§3.4, 5, 7.4 and 8)

---

## 1. Why this exists

Advanced practice providers (NPs, PAs, CRNAs, CNSs, CNMs) and their students currently piece together opportunities across many organizer sites, languages and publication formats. Abstract deadlines can be easy to miss, and student and DNP project venues can be difficult to find.

The Runway is an open, source-traced calendar intended to reduce the effort required to discover and verify those opportunities. Its broader professional and health-outcome aims are aspirational; user-task, educational, clinical and population outcomes have not yet been evaluated. Visitors search or filter the calendar, then open an entry to review its source wording and confirm details with the organizer.

The site is independent. It is not an official publication of, or endorsement by, Rutgers University or RWJBarnabas Health.

## 2. How it came together

- **Human role.** The curator conceived and directed the instrument's purpose, information architecture, visual representation, interface behavior, navigation, filters, taxonomy and hierarchy. He designed the intentional four-view model of List, Calendar, Orbit and Directory, determined its ordering and interaction rules, selected the visual and color direction, made every decision on hosting and visibility, and reviewed the output. Data corrections that serve the stated objective are executed by the AI and reported. The curator's approval is reserved for new destinations, accounts, cost or scope changes.
- **AI role.** An AI assistant (Claude, by Anthropic) researched organizer pages, compiled the data, wrote the build and check scripts, and walked organizer sites to confirm dates. ChatGPT (OpenAI) red-teamed the public-facing design, translated the curator's interface and visualization direction into code, tested and refined the four views and filtering behavior, and generated the selected APP Conference Runway logo under Dr. Mark Karasin's direction. The AI systems served as research, implementation and review tools; public product and design decisions remained with the curator.
- **Lineage.** The site began as a single-page "Conference Runway" artifact (dataset compiled 2026-09-16, kept verbatim as `sources/runway_2026-09-16.json`). On 2026-09-21 and 2026-09-22 it was rebuilt as this static site with a nightly checker.
- **Failures found during the build, and the controls added for each.** They are recorded here so reviewers can test whether the controls hold.
  - **Coverage drawn from memory.** Observances were missing (for example, National APP Week). Control: build a source-universe inventory before searching, and report coverage as a table.
  - **A checker that could not pass.** Ended meetings were re-read against pages that had moved on to the next edition, which produced 133 false "needs review" flags. Control: once a meeting ends, its record is frozen at what the page said when it was captured.
  - **One page fetched and treated as unfindable.** Dates were sitting in a site's menus. Control: walk the organizer's event index, the pages under its menus, program and registration pages, and any linked PDFs before calling a date unresolved.
  - **Dates inside images went unread.** Dates were published only in banners or flyers. Control: read the images, and link the image in the record.
  - **Unchecked absence claims.** Control: the build gate rejects absence language (see `scripts/validate.py`).
  - **"Reviewed" labels without a recorded quote.** Control: every upcoming dated record must carry verbatim organizer wording plus the exact URL, PDF or image it came from.
  - **A rewrite that dropped working details.** The 2026-09-24 01:40 interface commit replaced the stylesheet and script whole; it removed the separators between the display buttons and left eleven of the twelve Orbit months without a year. Control: every interface push is diffed against the previous commit with each removed rule accounted for, and `scripts/ui_check.py` asserts the separators, the year on every Orbit month, the filter rows, the landmark celebration weeks in every view and each Focus in each view (§7.4).

For this project, **fidelity** means remaining faithful to organizer material and clearly identifying interpretation; **reliability** means that outputs can be reproduced, checked and challenged with failures made visible; and **utility** means helping an APP find, compare, verify and act on a relevant opportunity with low avoidable effort. These are evaluation standards the project pursues, not qualities it claims to have proven. The complete personal governance schema is not included in this repository, so an external reviewer can audit the stated boundaries and resulting artifacts but cannot independently reproduce the governance process from this repository alone. The Governance status above must be updated after its scheduled 2026-10-04 review.

## 3. Content architecture (the core of the site)

### 3.1 Entities

| Entity | What it is | Key fields |
|---|---|---|
| **Series** | A recurring meeting or observance run by one organizer | `id` (organizer slug + name slug), `name`, `org`, `org_url`, `professions`, `specialty`, `audience`/`focus`, `kind` (conference, symposium, summit, course, congress, observance), `region`, `recurrence`, `np_pa_basis` (why an NP/PA audience is justified), `archive_url` |
| **Edition** | One dated occurrence of a series | `id` = first 12 hex of SHA-1(`series` + "\|" + `start`), `start`, `end`, `location`, `format`, `theme`, `call` (abstract call: status, opens, closes, text, url), `source_url`, `evidence`, `evidence_image`, `compiled`, `reviewed_on`, `verify` |
| **Observance** | A celebration week or day with a published rule (for example, "PA Week, October 6–12") | `sources/observances.json`: the rule is stored with its evidence and computed per year |
| **Student opportunity** | A student session, poster or DNP project venue attached to one edition | `sources/student_opportunities.json`: `category` (student or project), `kind`, `detail`, `roles`, `url`, `deadline` |
| **Expected edition** | A projection of a meeting's usual month, up to three years ahead | Never given a day, and always labeled "Expected month" |

At the `site/data/runway.json` build of 2026-09-24: 328 series; 1,592 editions (367 dated records confirmed against organizer material, 2 carrying an organizer date conflict, 1 organizer save-the-date; 521 past editions frozen as published; 36 set by rule; 665 expected months); 318 upcoming non-projected records (a count that moves with the calendar date); organizers placed in 37 countries; 25 upcoming student and DNP opportunities; horizon through 2029. The counts change nightly.

### 3.2 The evidence rule

The intended publication rule for an upcoming, non-projected dated record is that it carries all three of:
1. the organizer's own material as the source: its event page, a page under its menus, a program PDF, or a banner or flyer image;
2. **verbatim** wording from that source that contains the dates (`evidence`, normally 200 characters or fewer and never paraphrased; translated titles are recorded in English, and the original-language wording is kept);
3. the exact location of that wording (`source_url`, plus `evidence_image` when the dates are in an image).

Aggregator listings are never treated as the source. A social post counts only when it comes from the organizer's own account (for example, AAAA 2027 on LinkedIn).

### 3.3 Provenance layers and precedence

`sources/runway_2026-09-16.json` (original) → `sources/group_*.json` (research batches) → `sources/archive/*` (past editions and archive links) → `sources/observances.json` → **`sources/overrides.json`** (curator corrections, which win over everything). The authoring policy requires each correction to carry a `_why`, although the current validation gap and legacy exceptions are disclosed in §3.5. Duplicate series are folded through `aliases`. A wrong or duplicate edition is removed with `"removed": true` and a reason. It is never silently deleted.

`data/ledger.json` is intended as a permanent record of every edition emitted by the build. `data/snapshots/<year>/<date>.json.gz` stores the generated data candidate for a New York calendar day; a second run that day replaces it. The 2026-09-21 and 2026-09-22 files hold a smaller field set, and the current `data/snapshots/MANIFEST.csv` lists 2026-09-23 and 2026-09-24 while four daily files exist (2026-09-21 through 2026-09-24), so the manifest still trails the directory. A snapshot hash proves the bytes of that candidate when it is listed; the present workflow does not bind a snapshot to a successful Pages deployment.

### 3.4 Verification pipeline

| Stage | Script | What it proves | What it cannot prove |
|---|---|---|---|
| Nightly re-read (scheduled 06:00 UTC; GitHub may start it late) | `scripts/check.py` | That the start date (in English, Portuguese, Spanish, French, German, Dutch, Italian, Japanese or Chinese 年/月/日 formats; numeric day-first and month-first; day lists such as "24th, 25th & 26th September" or "19 y 20 de noviembre"; for titles translated into English or pages in CJK script, the date and year decide), its year, and a distinctive name word still appear on the source page | End dates; pages that block automated readers, need JavaScript, or show dates only in images |
| Frozen past | `check.py` | Nothing: an ended meeting is kept as it was captured | — |
| Manual walk | done by the AI assistant in a real browser, under the curator's direction; the curator confirms disputed dates himself | Dates on pages the checker cannot read. The walk covers menus, sub-pages, PDFs, images and translation | Anything not walked (recorded in each override's `_why`) |
| Link check | `scripts/linkcheck.py` | Which source links now return 4xx | A 403 block says nothing about whether the link is live |
| Build gate | `scripts/validate.py` | Rejects bad dates, non-HTTPS sources, private-looking strings in generated record data, projections past the horizon, days on expected rows, and unsupported absence claims | Semantic truth of a quote |

The page header shows one **Updated** timestamp: the time of the last nightly source read (or, when that is unavailable, the latest data build). Manual reviews are dated per record (`reviewed_on` in `sources/overrides.json`). As of 2026-09-22 those reviews were carried out by the AI assistant under the curator's direction. The curator personally confirmed two dates that appear only in images: ENRS 2027 and PNAA 2027. Since 2026-09-24 (curator decision after the ChatGPT audit) every List card shows its verification state beside its discipline badges: **Start found** (the nightly text match found the start date, its year and a name word on the organizer page), **Source reviewed** (the dates were confirmed by a manual review of the organizer's own source, the Manual walk above, rather than by the text match), **Save the date** (the organizer has published only a save-the-date), **Set by rule**, or an exception. The record dialog and the Directory still show exceptions only. An exception is a record whose latest automated check did not confirm it and has no curator evidence on file; it shows a note ("Date needs review", "Source not re-checked", "Organizer dates conflict" or "Source wording changed"), and "Needs review only" in Filters lists just those (deep link `#review=1`). Each record links its source and quotes its wording.

### 3.5 Known limits (attack these first)

- The checker is a text match. A start date, the year and one name word anywhere on a page will pass, even when the page lists other events.
- End dates are recorded from the source but are not re-checked automatically.
- Discipline tags (NP, PA, and the others) are curator judgments backed by `np_pa_basis`. The AGACNP filter is a curated topic view. It does not claim an AGACNP-specific track or credit.
- "Students & DNP projects" is one public discipline: organizer-documented opportunities for APP students (NP, PA, CRNA, CNS, CNM) together with venues that accept DNP project posters or abstracts. The underlying records retain their more specific student or project categories.
- Scope → **Students** (added 2026-09-24) selects the same documented student and DNP project opportunities for the edition shown, plus meetings the curator tagged as organized for students. Combined with a Discipline it keeps that discipline's meetings that have such an opportunity; it does not read the opportunity's own list of eligible roles.
- Coverage is concentrated in the United States and is incomplete globally.
- "Advanced practice provider" is a United States-origin umbrella term here. It does not imply that professional titles, education, credentials or scopes of practice are equivalent across countries.
- The intended evidence and override conventions are not all validation gates. Since 2026-09-24 `validate.py` fails the build when an upcoming, non-projected record lacks a quote or a source URL; 64 of the 324 upcoming records satisfy that gate with the wording the nightly checker captured (`evidence_auto`) rather than a curator-entered quote. The validator still does not enforce quote length, `_why` on every override (16 of 100 edition overrides and both alias mappings lack one), or `reviewed_on` completeness.
- Of 106 current or upcoming editions using a manual verification method, 44 lack a distinct `reviewed_on` value and fall back to another recorded date. Across all 180 `source_reviewed` editions, 118 lack `reviewed_on`. `compiled`, `verify.checked` and `reviewed_on` should not be treated as interchangeable without inspecting the source record.

### 3.6 Repopulation audit of 2026-09-24 (printed so it can be checked)

Every upcoming, non-projected record (325 at the time) was independently re-derived from organizer material overnight on 2026-09-24, without reference to the stored fields, and then compared. Method limits, stated plainly: 313 records were read by AI agents through a cloud page reader (a model reading the page text and returning the date wording), so "confirmed" means model-read agreement with the organizer page, not a human reading; 12 records whose sites block cloud readers, or publish dates only in images or PDFs, were walked in a real browser on the curator's computer and read by the AI assistant; images were opened for 4 records (ENRS, PNAA, NNAK, SEOC). No human re-read the 325 records.

| Result | Records | What was done |
|---|---|---|
| Confirmed, no change | 297 | Dates, location and format matched organizer wording |
| Re-read in a browser, confirmed | 8 | ONAN, DelVal NAPNAP, TNA District 9, CBEn, AVA, V&VN VS, IAPACON, SEOC (PDF) |
| Confirmed from an image | 3 | ENRS 2027 (banner), PNAA 2027 (flyer), NNAK 2026 (flyer; its original page now returns 404, source replaced) |
| Corrected: format | 5 | ACG, ICCM Summit, EBPOM Ireland, OAPA, PINC recorded as hybrid per the organizer |
| Corrected: dates | 1 | PINC 2026 moved to November 7–8 per the organizer's current page |
| Corrected: abstract call | 5 | UFRO Temuco (closed 2026-08-29), ELSO LATAM (set to tba; the stored "Closed Jul 14" had no evidence), ACS Innovation Summit (open), Peking University forum (deadline 2026-09-30), AAAA 2027 poster deadline added |
| Organizer date conflict recorded | 2 | AAAA 2027 (event site April 14–18 vs organizer LinkedIn April 15–18); NANN 2027 (October 5–8 vs 6–8 on two NANN pages; a duplicate record was removed) |
| Rule-based observances, not individually published for the year | 6 | International Day of the Midwife 2027–2029, National Midwifery Week 2027–2029 (already labeled "Set by rule") |
| Source offline at check time | 1 | ANNA National Symposium 2027 (site in maintenance); left as captured |

Every change is in `sources/overrides.json` with `_why`, `reviewed_on: 2026-09-24`, the verbatim wording and the exact URL or image. The same night, an axe-core WCAG 2.2 AA pass, a horizontal-overflow check at 1440 px and 390 px, a console-error check and a landmark-record test (National APP Week and the NP, PA and CRNA weeks in every view) were run against the candidate before it was published.

## 4. Website architecture

- **Static site** in `site/`: `index.html`, `assets/app.js` (all behavior, no framework), `assets/app.css`, `assets/app-conference-runway-logo.png`, the APP-only browser and installed-app icons, `assets/config.js` (curator details and request address), `data/runway.json`, `runway.ics` (calendar feed), and self-hosted fonts.
- **No third-party requests at runtime.** No cookies, analytics or trackers. The Content-Security-Policy is `default-src 'self'`.
- **Search visibility:** `noindex, nofollow, noarchive` and `robots.txt`, by decision. These request exclusion but cannot guarantee it. The intended distribution is peer to peer among APPs.
- **Hosting:** GitHub Pages, deployed by GitHub Actions (`.github/workflows/runway.yml`).
  - Every push to `main` builds, validates and deploys.
  - A nightly schedule (06:00 UTC, which is 2 a.m. EDT or 1 a.m. EST; there is no clock gate, so a late start still runs) runs build, check, link check, build and validate, then archives and commits the run's generated candidate before applying the final failure gate. A failed check or validation prevents deployment in that run, but the candidate can remain on `main`; publication and archiving are therefore not one transaction. The review digest is a later best-effort step and can be stale if an earlier stage fails. No credentials or private operational material are recorded in this handoff.
  - Workflow permissions default to none. Each job requests only what it needs. Third-party actions are pinned to commit SHAs.
- **Geography:** `scripts/geocode.py` places venues using the U.S. Census Gazetteer and GeoNames (CC BY 4.0), with manual pins in `sources/geo/manual.json`.

## 5. Design and navigation

- **Design authority and implementation:** The curator is the design authority for the site's visual representation, information architecture, user interface, List, Calendar, Orbit and Directory presentations, record grouping, filter model and public wording. AI assistants implemented and tested those decisions in the static site and documented material revisions here.
- **Header:** image logo (returns to the landing view, Orbit), tagline, Copy link, Share, Make a request, AI Handoff, a two-line explanation of what the instrument does and how to use it, and a right-aligned automated re-check timestamp on the same bottom header row.
- **Logo and Rutgers reference:** The selected logo was generated by ChatGPT under Dr. Mark Karasin's direction. Its runway metaphor, navy field, white lettering and `#CC0033` scarlet accent were selected for this project. Browser and installed-app icons use the standalone APP portion of that logo, without the Conference Runway wordmark. Scarlet is used as a restrained color reference to Rutgers; the logo does not reproduce the Rutgers block R, wordmark, seal or another institutional mark, and it does not imply Rutgers endorsement.
- **Primary controls:** Search starts the first control row; the former Upcoming, Abstract deadlines, Students and Directory tab block is not part of the current interface.
- **Discipline filter:** All APPs, NP, AGACNP, CRNA, NP-RNFA, CNS, CNM, PA, Students & DNP projects. Any combination can be selected, with OR logic within Discipline and AND logic between Discipline and the other filters. Stable color dots identify disciplines and selected chips carry a check; color is not the only selection indicator. All APPs clears the selection. Student and DNP records share one discipline. Location type (All, Live, Online or Hybrid) can be combined with Global Region; distance and search remain independent filters.
- **Scope filter** (labeled Focus until 2026-09-24): Clinical, Academic, Research, Leadership and Students can be selected singly or in combination; All clears the selection. Scope sits on its own row under Discipline. The interface derives the first four tags from audience, specialty, organizer and meeting-name metadata; Students is defined in §3.5. Every display uses the same match. Links made before the rename (`focus=clinical`) open the matching Scope.
- **Focus filter** (added 2026-09-24): All, Abstracts Due, Open Abstracts, Conferences and Celebrations. It shows one record type at a time; choosing the active type again returns to All, and All is the site as it was before the row existed. Focus sits to the right of Scope on wide screens, wraps under it at medium widths and becomes its own horizontally scrollable row on phones. **Abstracts Due** means a dated abstract call that is open, closing soon or opening later, with its due date still ahead. **Open Abstracts** means a call open today, with or without a published due date. **Conferences** means conferences, symposiums, summits, congresses and courses. **Celebrations** means celebration weeks and days such as National APP Week. In List, Abstracts Due and Open Abstracts group records by the month the abstracts are due, show the due date in the date block and move the meeting's dates into the record line; calls open with no posted due date sit last, under "Open, no due date posted". In Calendar, Abstracts Due marks only the due day, Open Abstracts shows calls with a known open window, and Conferences and Celebrations show only their own bars. Orbit shows the matching column and rail group (§5, Orbit). Directory keeps the series that have a matching edition. Focus replaced two older controls: the "Abstract call open" switch in Filters (old `open=1` links open Focus → Open Abstracts) and the Celebrations chip in the Filters panel's Type row (old `kind=observance` links open Focus → Celebrations). Type keeps Conferences, Symposiums, Summits and Courses as a refinement within meetings.
- **List view:** one card per edition, with discipline badges, the abstract-call state, the verification state (§3.4) and the organizer. Records are grouped into native, keyboard-operable month disclosures separated by a scarlet rule (by due month under Focus → Abstracts Due or Open Abstracts). Each month visibly says **Expand ↓** or **Collapse ↑**, and List also provides **Expand all ↓** and **Collapse all ↑**. A month chosen in Calendar or monthly Orbit becomes the List context, remains in the shared URL and is opened and scrolled below the sticky controls. If no upcoming record starts in that month, List keeps the requested month and explains the zero result instead of jumping to today's month.
- **Display switch:** List, Calendar and Orbit are alternate presentations of the same filtered records, and Directory is the fourth choice. The buttons read **List**, **Calendar**, **Orbit** (with its orbit symbol) and **Directory**, with a vertical scarlet rule between every pair. The two-line "Schedule / Orbit" label and the loss of the List | Calendar and Calendar | Orbit rules were both corrected on 2026-09-24. On wide screens the location controls sit immediately to the right of this switch under the label **Location**, followed by format and **Global Region** controls; the row stacks at narrow breakpoints. **Clear all** sits with the search and Filters controls so it cannot displace location.
- **Four-view intent:** the four views are deliberate, not interchangeable decoration. List supports chronological scanning, Calendar shows timing and collisions, Orbit reveals annual pattern and density, and Directory supports series-level discovery and history.
- **Global-first geography:** the Global Region selector deliberately presents Continent and Country before United States subregions. Coverage is currently United States-heavy, but the control does not put the United States at the top. The ordering is intended to encourage global discovery and counterbalance the dataset's present United States concentration; whether it changes discovery behavior has not been measured.
- **Transparency and personal governance:** visible organizer evidence, quoted wording, known limits, public source and change history, snapshots, and the distinction among curator decisions, AI work, machine observations and organizer claims are intentional. This inspectability was the only strategy that met the curator's integrity threshold for pursuing fidelity, reliability and utility within his personal governance schema. It is not a guarantee of correctness; it makes claims, uncertainty and accountability open to challenge. For this project, the governance boundary reserves objectives, public representation, new features, scope, cost and external actions to the curator while allowing reported implementation and corrections within an approved objective.
- **Calendar view:** each consecutive run of days is one bar per week, not one entry per day. Colors show record type only: meeting, open abstract call (a bar running to the due date, with a scarlet end on the due day), abstract due and celebration. Dark navy borders carry the grid; scarlet is reserved for the current date, deadline ends, selected controls and a restrained accent on APP Week. The visible month is centered between paired month/year navigation arrows, while the two-row color key sits beside the Today control. When a week has hidden lanes, a dark-navy-topped, scarlet-accented raised disclosure bar says **+XX more this week** and lifts on hover before expanding in place. Filtered weeks with no matching records say so explicitly. Clicking a day number opens every record for that day.
- **Directory view:** an alphabetical, series-level index showing recurring opportunities, next recorded dates, source exceptions and recorded history. It answers "what series exist?" rather than presenting another edition-level timeline.
- **Footer:** the compact provenance block begins with scarlet **Curated by**, keeps each affiliation and title on curator-specified lines, and uses the remaining width for one left-aligned explanation of source checking and coverage. The former Curator's note label and duplicated narrative were removed.
- **Orbit view (the landing view since 2026-09-24):** twelve consecutive months, starting with the current month, form the ring, and every month carries its year (for example **Sep ’26** through **Aug ’27**; on phones the year sits under the month). The center shows the window (for example 2026–27) and the active location, Discipline, Scope and Focus. The arrows move the window a year at a time, and a window other than the current one is carried in the address (`from=YYYY-MM`). Choosing the center label shows every matching record in the twelve months (`span=year` in the address; older links used `scope=year` and still work). With Focus on All, four rising columns on every month encode filtered meeting, abstracts-due, open-abstract and celebration density, with a plain count below each column. Choosing a Focus leaves one column. The top-right caption says, **Choose a month for a focused view, or choose the center label for all twelve months. The arrows move the window by a year.** Choosing a month refreshes the rail's upcoming-focused sections in this order: Abstracts Due, Meetings & Conferences, Open Abstracts, Celebrations. With Focus on All they start collapsed; with a Focus chosen only that section shows, already open. Celebration weeks moved from Meetings & Conferences to their own column and section on 2026-09-24. Choosing the center label instead titles the rail with the window (for example **September 2026 – August 2027**), changes **Records in focus** to the full filtered window, keeps the same sections and removes the per-section month-view cap; choosing a month returns to month scope. The records open the same evidence detail used everywhere else. Logo navy marks meetings, scarlet marks due dates, a deeper green marks open calls and amber (the calendar's celebration color) marks celebrations. Location type, Global Region, distance, Discipline, Scope, Focus, type, specialty, source-review status and search all use the same shared matcher as List and Calendar. Projected records enter Orbit only when **Show expected dates** is enabled. If a new location, Discipline, Scope or Focus choice leaves the selected month empty, Orbit moves within the window to the first month that has a match; for example, Qatar reveals Qatar Health Congress in November 2026.
- **Record detail:** dates, location, abstract call, student opportunity, a seven-year view (three years back to three ahead), the organizer's archive, the source link, the quoted wording, a calendar file, and "Suggest a fix" (opens a GitHub issue).
- **Every view is a URL.** Filters and views live in the address hash, so a view can be shared as a link: `display`, `from`, `span`, `cal`, `prof`, `scope`, `focus`, `where`, `area`, `near` and `r`, `spec`, `kind`, `exp`, `review`, `q` and `e` (an open record). Links from before 2026-09-24 still open the view they described: `focus=clinical` (and the other scope values) → Scope, `scope=year` → the twelve-month Orbit, `open=1` → Focus → Open Abstracts, `kind=observance` → Focus → Celebrations, `view=deadlines` → Focus → Abstracts Due.
- **Color:** the site renders its light palette regardless of device theme (`color-scheme: light`). The earlier device-following dark mode was removed on 2026-09-24 because an unguarded light skin left record dates, the masthead and the footer unreadable or inconsistent in dark mode; a reviewed dark palette is a roadmap item. The layout works at phone width.

## 6. Tools used

| Layer | Tool |
|---|---|
| AI assistant (initial build, research, verification and handoff draft) | Claude (Anthropic), in the Claude desktop app's Cowork mode, including its sub-agents, web search and fetch, and built-in browser. The initial handoff-writing session was configured for model `claude-opus-5-5`; per-session models are not recorded in the repository. |
| Independent review, interface implementation and logo production | ChatGPT (OpenAI): independent red-team and implementation passes in Codex Work mode and the local repository; selected logo generated under Dr. Mark Karasin's direction; interface, navigation, icon and documentation revisions tested before handoff |
| AI implementation and review sandbox (not the deployed runtime) | Linux container; Python project validation; Node syntax and behavioral harnesses; Inkscape and ImageMagick icon rendering. Earlier recorded review sessions also used browser automation, Tesseract OCR and pypdf where relevant. Since 2026-09-24 the scripted interface check `scripts/ui_check.py` runs in Playwright with headless Chromium. |
| Browser on the curator's computer | The Claude desktop app's built-in browser and the Codex in-app browser, driven by the respective AI assistants, to walk sites that block cloud readers and to commit through GitHub's web editor |
| Pipeline | GitHub Actions on ubuntu-latest; Python 3.12; pypdf 5; the official `actions/checkout`, `setup-python`, `configure-pages`, `upload-pages-artifact` and `deploy-pages` |
| Hosting | GitHub Pages |
| Data references | U.S. Census Bureau Gazetteer; GeoNames (CC BY 4.0) |
| Fonts | Barlow Condensed and Source Sans 3 (SIL Open Font License) |
| Curator hardware | A personal desktop computer. Specifications are not recorded here. |

## 7. Reproduce it

This section is the replication contract. A future maintainer or AI should be able to recreate the public instrument, its data build and its maintenance workflow from the repository alone. Do not infer behavior from a screenshot when the rule is recorded here or in the source.

### 7.1 Choose the level being reproduced

1. **Visual and interaction replica.** Copy `site/` and serve it as static files. This preserves the published data snapshot, logo, icons, fonts, List, Calendar, Orbit, Directory and filters, but it does not refresh records.
2. **Date-relative data replica.** Copy the whole repository and run the build and validation steps below. This regenerates public data from the committed source files, verification state and the execution date.
3. **Maintained public replica.** Fork the whole repository, configure GitHub Pages and workflow permissions, and retain the scheduled source check, snapshot and issue-reporting jobs. This is the level needed to reproduce the operating project rather than only its appearance.

### 7.2 Required environment and authoritative inputs

- Use Python 3.12. The build, validation, geocoding, link-check and snapshot scripts otherwise use the Python standard library. Install `pypdf==5.*` before the web source check so evidence in PDFs can be read. There is no Node, bundler, package manager, database, server framework or runtime API.
- Treat `sources/runway_2026-09-16.json`, `sources/group_*.json`, `sources/archive/`, `sources/observances.json` and `sources/student_opportunities.json` as the curated content inputs. Follow `sources/SCHEMA.md` when adding records.
- `sources/overrides.json` is the final authority for corrections and removals; its entries must retain `_why`. Series aliases are resolved before editions are emitted. `data/verification.json` and `data/link_status.json` are machine-written observations, not replacements for the curated inputs.
- `sources/geo/manual.json` is the authority for locations that automatic geocoding cannot place. Generated geography is written to `sources/geo/locations.json`, `site/geo/cities.json` and the ZIP shards under `site/geo/zip/`.
- The public interface is defined by `site/index.html`, `site/assets/app.js`, `site/assets/app.css`, `site/assets/config.js` and `site/manifest.webmanifest`. The masthead logo, APP-only favicon and installed-app icon family, and self-hosted fonts are part of the visual system. Preserve the independence statement when personalizing affiliations.

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

`check.py` writes `data/verification.json` and `data/check_report.md`; `linkcheck.py` writes `data/link_status.json` and `data/link_report.md`; the second build incorporates those observations; `snapshot.py` archives that generated data candidate. It does not attest that the same bytes were deployed. `geocode.py` is separate because it downloads Census and GeoNames reference files and rewrites the geography outputs; run it when a new or corrected venue needs placement, then rebuild and validate. The web is not deterministic, so record the run date and preserve the resulting git diff rather than expecting a later check to return byte-for-byte identical observations.

### 7.4 Interface invariants and acceptance test

A replica is not complete until these behaviors are checked in a browser at desktop and phone widths:

- List, Calendar, Orbit and Directory apply the same search, location type, Global Region, distance, Discipline, Scope, Focus, type, specialty and source-review filters where those fields apply. Discipline and Scope are multi-select controls; Focus shows one record type at a time. Their selections and the active display must survive a shared address-hash reload, and the pre-2026-09-24 links listed in §5 must still open the view they described.
- The display switch reads List, Calendar, Orbit and Directory, with a vertical scarlet rule between every pair of buttons. The filter rows are Discipline, then Scope with Focus to its right (wrapping below it at medium widths).
- Every List card shows its verification state.
- Location type partitions the applicable records into All, Live, Online and Hybrid without losing or duplicating a record. ZIP-radius filtering appears in the Orbit center only when used.
- List, Calendar and month-focused Orbit exclude past editions. The center-label Orbit view includes matching past and upcoming records within the twelve-month window. Directory remains a series-level view. Expected editions remain absent unless **Show expected dates** is enabled.
- List month groups use native disclosures, a scarlet divider directly below each month/year heading, correct **Expand ↓** / **Collapse ↑** cues and working Expand all / Collapse all controls. Manual disclosure state survives a filter re-render. Calendar → List and monthly Orbit → List preserve, open and scroll to the exact selected month without moving keyboard focus from the List control; a zero-match or past month remains visible with an explanation. Annual Orbit does not invent a month-level List landing.
- Orbit opens by default, shows twelve consecutive months from the current month, labels every month with its year, and uses the window label and active filters at the center. Month columns use logo navy for meetings, scarlet for abstracts due, deep green for open calls and amber for celebrations, with plain counts below the zero line. With Focus on All, all four detail-rail groups are initially collapsed and remain independently expandable in this order: **Abstracts Due → Meetings & Conferences → Open Abstracts → Celebrations**; with a Focus chosen, each month shows one column and the rail one open group. Activating the center label selects window scope, clears every month pressed-state, titles the rail with the window and lists every matching row in it; activating a month restores upcoming-focused month scope. The arrows shift the window by twelve months. The caption reads, **Choose a month for a focused view, or choose the center label for all twelve months. The arrows move the window by a year.** When a location-only result exists outside the selected month, Orbit advances to the first matching month in that year.
- Calendar bars retain navy structural borders and type colors. Deadline items precede other expanded records for the day or week instead of falling below "more" content.
- Opening a record in any view reaches the same evidence detail, organizer source and verbatim date wording. Keyboard navigation, visible focus, device dark mode and narrow-screen layout must remain usable.
- Public discipline labels use CRNA and do not expose legacy source taxonomy. The public ordering is NP, AGACNP, CRNA, NP-RNFA, CNS, CNM, PA, Students & DNP projects. Each discipline keeps a stable color dot, multi-selection is permitted, and a check provides a non-color selected-state indicator.
- Global Region retains the intentional Continent, Country, United States optgroup order. Browser tabs and installed shortcuts use the standalone APP logo mark, never the retired dark runway badge. Verify favicon changes in a fresh or private Edge profile on macOS and in a second Chromium- or Safari-family browser because icon caches can conceal a correct deployment.
- With browser developer tools open, the static site should produce no application errors and no third-party runtime requests.
- Run `python scripts/ui_check.py` before every interface push, and `python scripts/ui_check.py --url <deployed site>` after it. It needs Playwright for Python with Chromium and checks the site at 1440 px and 390 px. All of its checks must pass, and they were written so they can fail: on 2026-09-24, run against the previous commit, it failed on the missing separators, the months without a year and the old filter rows. Before the push, also diff `site/assets/` against the previous commit and account for every removed CSS rule and label.

### 7.5 Publish and operate a GitHub replica

1. Fork or clone the complete repository, including the hidden `.github/` directory. No secrets are required.
2. Edit `site/assets/config.js` for the curator, affiliations, role labels, request address and repository URL. Replace the masthead logo only if intentionally redesigning the identity; update the complete favicon and installed-app icon family with it, and keep accessible text and responsive sizing.
3. In repository settings, set Pages **Source** to **GitHub Actions**. In Actions → General, give workflows **Read and write permissions** so the scheduled checker can commit verification files and maintain the review issue.
4. Run **Check sources and publish** manually once. Thereafter, `.github/workflows/runway.yml` rebuilds and validates every push to `main`, deploys `site/`, and performs the scheduled check, link report, snapshot and review-issue update.
5. `.github/workflows/bootstrap.yml` exists only to unpack the original bundled distribution. A normal clone or fork that already contains the full repository must not run it.
6. Confirm the deployed URL, the Updated timestamp, a source-detail dialog, the calendar feed and at least one filtered URL in each of List, Calendar, Orbit and Directory.

### 7.6 Definition of successful replication

The result is a faithful operational replica only when (a) the committed inputs and recorded execution date produce a validation-passing public dataset and calendar feed; (b) all four views preserve the applicable filter and evidence rules above; (c) current factual records remain traceable to organizer material, with known legacy exceptions disclosed; (d) the scheduled workflow can update verification, snapshots and the review digest without a private service; and (e) a new maintainer can distinguish curator decisions, AI implementation, machine observations and organizer evidence from the repository history alone. The current build does not accept an injectable `as_of` clock, and a committed snapshot is a generated candidate rather than deployment attestation. Exact reconstruction of historic public bytes would require the deployed commit or artifact to be recorded alongside that snapshot.

## 8. How to challenge it

- Pick any upcoming record. Open its source link and look for the quoted wording. If it is missing or does not support the dates, file "Suggest a fix" on that record or open an issue.
- Diff `sources/overrides.json` against its git history. Treat a missing `_why` as an open control gap, not proof that no rationale existed.
- Run `scripts/check.py` and compare your results with `data/check_report.md`.
- Test the known limits in §3.5.

Corrections are welcome. The curator decides what is published.

**A note to readers, developers, enthusiasts and AI agents reviewing this handoff:** after reading the known limits in §§3.5 and 9, the curator is explicitly interested in your analysis of the project's fidelity, reliability, utility, governance boundaries and blind spots. The intentional global-first region ordering, four-view model and source-level transparency are especially open to thoughtful challenge. Send analysis to [mark.karasin@protonmail.com](mailto:mark.karasin@protonmail.com), the curator's personal address for this project, and state the evidence, assumptions and uncertainty behind your conclusions.

### 8.1 Correction path

1. **Report.** Use **Suggest a fix** on the record (it opens a prefilled GitHub issue), open an issue directly, or use **Make a request** (email to the address above). Name the record and link the organizer page, PDF, image or official organizer post that shows the right date.
2. **Re-read the source.** The organizer's own material is walked again as in §3.4: its event index, the pages under its menus, program and registration pages, PDFs, banner and flyer images, and the translated page where the source is not in English. An aggregator listing is not treated as the source.
3. **Record the correction.** It goes into `sources/overrides.json` with a `_why`, a `reviewed_on` date, the verbatim wording and the exact URL or image. A wrong or duplicate edition is marked `"removed": true` with a reason and is never silently deleted. When the organizer's own pages disagree, the record shows "Organizer dates conflict" rather than choosing one silently.
4. **Publish.** A push to `main` rebuilds, validates and redeploys the site, and the change stays visible in the public commit history. The next nightly check re-reads the source.

The repository sets no response-time target for corrections (§9, Operations and continuity). The curator decides what is published.

**Roadmap.** A Leadership discipline (CNML, CENP, NE-BC, NEA-BC, CNL and leadership programs the curator has named for review) is planned as a Scope and a program type and will be added only with organizer-sourced records; a reviewed dark palette is planned. The curator is also considering an optional estimate of approximate door-to-door conference cost. This feature is not implemented and is not part of the verified event data. A useful proposal would examine registration, travel, ground transportation, lodging, meals, taxes and fees while avoiding false precision and unnecessary collection of a visitor's home address. Any estimate should be a visibly separate derived planning layer, never organizer-verified event data, and should expose its range, component sources, observation dates, assumptions, exclusions, original currency and confidence. A privacy-preserving first version could calculate locally from a city, ZIP code or airport plus user-entered travel prices; live market quotes would require a new service architecture, provider agreements, protected credentials and a sustained operating commitment beyond the present static site. Cost must not reorder regions or quietly favor domestic opportunities. The curator welcomes views on whether the feature would materially improve utility, what source and refresh rules it would require, and whether its logistics can meet the same fidelity, reliability and personal-governance standards as the current date evidence.

## 9. Limits of the data

This is a curated directory, not a study, and it makes no accuracy or completeness claim. If you treat it as a dataset, these are the threats to validity as the builders understand them.

- **Construct.** An "APP opportunity" is operationalized as an organizer-published meeting, abstract call, student or DNP project venue, or observance. For NP and PA relevance, the justification is recorded per series in `np_pa_basis`. Inclusion is a judgment made by one curator, with no formal codebook beyond `sources/SCHEMA.md`.
- **Sampling frame.** The universe was assembled by AI-assisted web search seeded by the curator's knowledge and by organizer lists (national and state NP and PA associations, specialty societies, schools). Some sweeps, including DNP programs, are not verified as complete at this date. Organizers with little web presence are under-represented, and so is non-English content.
- **Measurement.** The truth criterion is agreement with the organizer's own published material. It is not attendance, and it is not whether the event actually took place. The automated check matches text and can produce false positives (another event on the same page) and false negatives (dates held in images, scripts or blocked pages). End dates are not re-checked.
- **Reliability.** There is one curator and one primary AI builder. No inter-rater agreement has been measured. A second model family reviewed the public-facing design and documentation, but it did not independently re-audit the full dataset. The primary AI both compiled and verified most records. That is self-verification, reduced but not removed by the verbatim-evidence rule and the curator's spot confirmation.
- **AI-specific risks.** Fabricated dates or organizers (a hallucination risk) are constrained by the intended verbatim-evidence and exact-URL rule, but current enforcement and legacy exceptions are disclosed in §3.5. Automation bias, meaning over-trust in the checker's status, is a live risk now that every List card shows a verification badge (since 2026-09-24). The badges name their method so a reader can weigh them: "Start found" is a text match and "Source reviewed" is a manual review. Exception notes remain visible.
- **Reproducibility.** The build is operationally reproducible but date-relative: it uses the current date and time for rolling horizons, projections, staleness and build stamps. The web also changes. Nightly snapshots preserve generated candidates, not deployment-attested public files; byte-identical reruns would require an injectable `as_of` clock and captured web observations, while exact deployed-state reconstruction also requires deployment-to-commit provenance.
- **Privacy and hosting.** The site code sets no cookies or analytics and a URL fragment is not sent to the web server, but a resolved city or ZIP may remain in the shareable fragment and local browser history. GitHub Pages may retain standard hosting logs outside this codebase.
- **Operations and continuity.** One curator controls publication. The repository does not yet define succession, account recovery, rollback, a last-known-good deployment reference, correction-response targets, failure notification, off-repository backup or snapshot retention. A failed scheduled candidate is committed before the failure gate; deployment later rebuilds `main` rather than consuming and attesting the snapshot, and the manifest currently omits two existing legacy snapshots. Scheduled runs can be delayed or dropped by the host, the workflow has no retry/rebase procedure, and an overlapping pending run can replace an earlier pending run. At roughly 220 KB per daily snapshot, archive growth is about 80 MB per year at the current dataset size.
- **Accessibility and international use.** Keyboard, focus and narrow layouts are tested as interface invariants; an axe-core WCAG 2.2 AA pass on 2026-09-24 found no violations after the record dialog gained a focus trap and the footer partner link a 24 px target, but no independent human audit is recorded. The interface is English-first, distance is miles-only, and the Near control is partly ZIP-oriented.
- **Reuse mechanics.** The CC0 dedication is recorded in this document and in the root `LICENSE` file (added 2026-09-24). Organizer and institutional marks are not covered.
- **Suggested evaluation.**
  - A stratified random audit of upcoming records by independent human coders, reporting the share of dates supported by the source, with 95% confidence intervals.
  - A capture–recapture comparison against an independently built list, to estimate coverage.
  - The staleness rate over time, taken from the nightly check history.

## 10. Use and reuse

- **Permission** (also in the root `LICENSE` file). To the extent the curator holds rights in this project's code, data compilation, design, AI-generated logo and documentation (including this handoff), he dedicates them to the public domain under [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/). Anyone may copy, modify, redistribute or build on them for any purpose, commercial or not, without asking and without attribution. Attribution is appreciated but not required.
- **What this dedication does not cover:**
  - **Organizer material.** Event names, the short verbatim quotes kept as evidence, linked pages and images, and any organizer marks belong to their organizers. They are reproduced only to show where a date came from.
  - **Third-party components**, which keep their own licenses: Barlow Condensed and Source Sans 3 (SIL Open Font License); GeoNames data (CC BY 4.0, attribution required); U.S. Census Bureau Gazetteer data (public domain).
  - **Institutional names and marks.** Rutgers University and RWJBarnabas Health names and logos are not licensed. Nothing here implies their endorsement.
- **No warranty.** The site and its data are provided as is, without warranty of any kind. Dates change. Confirm with the organizer before registering, submitting or traveling.
