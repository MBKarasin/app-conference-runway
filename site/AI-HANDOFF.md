# APP Conference Runway: AI Handoff

**Live site:** https://appconferencerunway.org/\
**Owner and curator:** Dr. Mark Karasin, DNP, APN, AGACNP-BC\
**Contact and corrections:** mark.karasin@protonmail.com\
**Document date:** 2026-10-19

**Purpose.** A curated resource connecting advanced practice providers worldwide with opportunities to exchange ideas, advance their disciplines, and improve human health outcomes.

This page is written for people and for AI systems that need to understand, check or challenge the Runway. It describes only what runs; where a part is staged but not yet running, it says so.

## 1. What this is

Advanced practice providers (NPs, PAs, CRNAs, CNSs, CNMs) and their students must search many organizer sites for meetings, abstract deadlines and student and DNP project venues. The Runway gathers them in one calendar that traces each upcoming record to the organizer's own material, re-reads those sources by machine, and helps a visitor plan attendance: dates, travel, lodging and the price of attendance by category. It is global in scope and incomplete; coverage is concentrated in the United States.

The site is independent. It is not an official publication of, or endorsement by, Rutgers University, RWJBarnabas Health or any organizer listed.

## 2. Ownership and roles

The Runway, this site and the appconferencerunway.org domain are owned and operated by the curator, who decides what is published and is accountable for it. Its source files and pipeline code are public in the repository (https://github.com/MBKarasin/app-conference-runway); captured organizer pages stay with the owner.

| Actor | Role | No authority to |
|---|---|---|
| Deterministic pipeline | Re-read sources, test quotes, build, validate, compute the indices, package and archive each release | Invent or approve facts |
| AI systems (Claude by Anthropic; ChatGPT by OpenAI; local models) | Research, extraction, translation, implementation and independent review, as bounded workers | Publish on their own judgment, or change a fact without organizer evidence |
| Curator | Examine evidence, resolve conflicts, approve or reject semantic changes, decide policy | — |

No model is a source of truth. The organizer's own page is.

## 3. The evidence rule

### 3.1 Records

| Record | What it is |
|---|---|
| Series | A recurring meeting or observance of one organizer; `np_pa_basis` says why it serves APPs |
| Edition | One dated occurrence, with `source_url`, verbatim `evidence` and a `verify` state |
| Observance | A celebration week or day, dated by the organizer or by its published rule |
| Student opportunity | A student session, poster or DNP project venue at one edition |
| Expected edition | A meeting's usual month, projected up to three years ahead; never a day |
| Attendance | Registration prices, online option, official hotel block and support for one edition (§6) |

### 3.2 What counts as evidence

An upcoming dated record, unless computed from a published rule, carries the organizer's own material as its source (an event page or sub-page, a program PDF, or a banner or flyer), **verbatim** wording from it that contains the dates (normally 200 characters or fewer) and the exact location of that wording. Aggregators never count; a social post counts only from the organizer's own account. The build gate refuses a record without a quote and a source link. The same rule applies to every price (§6).

### 3.3 Corrections and precedence

Curator corrections win over every other input. Each carries a reason, a review date, the organizer's verbatim wording and the exact URL or image; the build gate refuses one without them (16 corrections made before review dates were kept carry none, and none is invented). A wrong edition is marked removed, never silently deleted. A ledger keeps every edition ever published, and each night's release is archived (§5.4).

## 4. Confidence and the indices

### 4.1 Confidence on each record

- **High confidence carries no label:** the latest automated re-read confirmed the record from the organizer's own page or image (start date, its year and a word of the meeting's name), or the date comes from the organizer's published rule, or the meeting has ended and is kept as recorded when published.
- **Confidence: Medium** marks a dated record not yet ended that the latest re-read did not confirm, with its reason inside the record: the organizer's site did not let the automated reader in (the record rests on a review by hand, dated), the dates were not found on the page, the organizer's own pages disagree, or no re-read has completed in 36 hours. The record stays listed. **Medium confidence only** lists these records.
- **Expected month** is a projection and never carries a day.

A price or hotel detail is High when code found its quoted wording on the organizer's page, and Medium when it was read through a secondary reader or the page no longer shows it (§6).

### 4.2 Fidelity Index

**Fidelity Index = evidence coverage × projected correctness.**

- *Evidence coverage* = records passing every test below ÷ every dated record (past and upcoming; month-only projections excluded). A record passes if it carries the organizer's own wording or a published rule, holds a settled verification state (confirmed, set by rule, save the date, or recorded when published) and has a source link. A meeting not yet ended must also have a link not found gone and a confirmation no older than 90 days (rule dates excepted; an unreadable stamp fails).
- *Projected correctness* = 1 − (records found wrong ÷ records audited), summed over every independent audit on file. An audit counts a record wrong once if any action-critical field (dates, format, place, abstract call or deadline, eligibility) disagrees with the organizer. The index's note gives the counts and the 95% Wilson interval of that rate, scaled by coverage.
- *Worked example* (data built 2026-09-26, 07:32 UTC): coverage 924 ÷ 927 = 99.68% (614 ended, 313 not yet ended); correctness 1 − (10 + 9) ÷ (325 + 324) = 97.07%; Fidelity 99.68% × 97.07% = 96.76%, 95% range 95.2–97.8%.

### 4.3 Reliability Index

**Reliability Index = (records re-confirmed by the latest automated re-read + dates computed from a published rule) ÷ dated records not yet ended** (projections excluded). Reviews by hand never count. When no re-read has completed in 36 hours, re-confirmations stop counting and the index falls to the rule-computed share. The records it leaves out are exactly the records marked Confidence: Medium.

- *Worked example* (re-read of 2026-09-26, 06:51 UTC; data built 08:30 UTC): (250 + 29) ÷ 313 = 89.14%. The other 34 show Confidence: Medium; most are pages whose servers refused the automated reader that night and rest on a review by hand, and one was corrected that morning from the organizer's event page and waits for its first automated re-read there.

Both indices are recomputed in the visitor's browser from `data/runway.json` at every page load, for the visitor's own calendar day; the pipeline recomputes them with the same definitions and the interface check fails if the page disagrees.

### 4.4 What the indices do not show

- Neither measures completeness: meetings missing from the site.
- Evidence coverage is high largely by construction, since the build gate refuses an upcoming record without a quote and a source link; it falls mainly when confirmations age or organizer pages are removed.
- The two audits on file examined the same upcoming records as they stood on 2026-09-24, before the corrections that followed them. Pooling them treats 649 record audits as independent, which narrows the range; on the data of 2026-09-26, counting the shared sample once (n = 325) widens it to 94.3–98.1%, and the re-derivation alone gives 96.61% (94.1–98.0%).
- The first audit was a re-derivation of every upcoming record by AI agents without the stored values; the second was a review of the code, data and interface by another model family (ChatGPT) that, by its own report, re-derived no event in full. Neither was a human audit.
- Reliability measures whether a machine can re-read a record tonight, not whether it is right; some organizer servers refuse automated readers, and that varies night to night.
- The re-read is a text match anywhere on the page, so another event on the same page can pass it. End dates, venues and cut-off times are not re-checked automatically.

## 5. The re-read pipeline

Each run, in order. A run that fails a gate publishes nothing and the site stays on the last good release. The header's **Updated** stamp gives the time of the latest re-read; §5.5 says how often runs happen.

### 5.1 A: re-read

Every organizer source of a dated record not yet ended is re-read: the plain page, then a rendered page when it needs JavaScript, and a linked organizer image by OCR. It identifies itself, obeys robots.txt and reports a refusal instead of retrying with another reader. Every cited price and hotel detail is re-read the same way and its quote re-tested. Every outbound link is checked. Each page read leaves a receipt: URL, time, status and a SHA-256 of the text.

### 5.2 B: confirm

When the text of a page the first reader confirmed has changed since the last night, a second reader, written separately (its own fetch, its own HTML reader and its own date matcher), re-reads it. If the two disagree, the record shows Confidence: Medium until they agree. Today the second reader reads plain pages only: a record the first reader confirmed through the rendering browser or an organizer image is not second-read, and when the second reader cannot read a page, the first reader's result stands and the gap is logged. Prices are re-tested the same way (§5.1). A local model on the owner's machine is staged to become a further reader once it passes a blind pilot against published records.

### 5.3 C: discover

The pipeline reads the organizer's own pages for every series whose next date is not yet known, and queues any date in the next two years found near the series' name as a candidate, with the page, the passage and a hash of the page. Candidates are internal: one enters the Runway only after review against the organizer's evidence. Automatic publication of a candidate at Confidence: Medium after a second night's confirmation is staged, as is a wider weekly search for organizers the Runway does not yet list.

### 5.4 Publish, verify, archive

The pipeline builds the data, the calendar feed and this page; validates them; recomputes both indices; runs the scripted interface check; and packages the release with a SHA-256 manifest. After publication the live site is checked against that manifest and the interface check runs again. Only then is the release archived on the owner's machine, filed by year and date with its receipts, decisions and report; the live site is then verified once more. Nothing in the archive is ever deleted.

### 5.5 What runs today

| Part | Status (2026-10-19) |
|---|---|
| A: re-read of dates, links and cited prices | Runs nightly |
| B: independent second read | Runs for plain pages; rendered pages and organizer images are read when the optional readers install |
| C: new editions of known series | Runs as an internal queue; publication is by curator review |
| Schedule and publication | GitHub Actions runs the check nightly at 2 a.m. Eastern (GitHub may start it a few hours late) and commits the result; Cloudflare Pages publishes the domain from that commit. A separate daily check fails, and notifies the owner, if the live site has not updated in 30 hours. |
| Archive | Every published version stays in the repository's history; the day's data is also archived in `data/snapshots/` with a SHA-256 manifest. Nothing is deleted. |

## 6. Price of attendance and door-to-door planning

Every meeting still ahead opens a **Plan your attendance** panel.

- **Registration** prices are shown by category (member, non-member, student and the like; early, regular, late; full meeting, one day, online) exactly as the organizer states them, each with the organizer's link, the date read, and its confidence. A price is never estimated. Where an organizer has not published prices the panel says **Not posted**; where they have not been read yet, **Not captured yet**; where the organizer's site refuses automated reading, **Not captured**, with a link to the organizer's page in every case.
- **Getting there** uses straight-line distance from the visitor's ZIP code, city or country (a country alone is represented by its most populous listed city, and the panel says so): up to 80 km is a commute; up to 400 km, a drive or rail trip; beyond, a flight, with airports that have scheduled service within 160 km of each end (OurAirports, public domain). Drive times are approximations and are labeled so. Fares are not estimated; the panel links out to search them.
- **Door-to-door dates:** a commute is a day trip on each meeting day. A drive of more than 2.5 hours arrives the day before, and one of more than 4 hours returns the day after. A flight arrives the day before and returns the day after when the trip is international or longer than 1,500 km. Nights follow from those dates.
- **Lodging:** the organizer's official hotel block first, with its rate, booking cut-off and link. An estimate is shown only when a per-night block rate is posted: that rate times the nights, before taxes, labeled as an estimate.
- **Ways to take part at lower cost** lists, in the organizer's terms, online options, student, one-day and early rates still open, and published scholarships, grants or volunteer roles, and then meetings for the same disciplines nearer the visitor in the next twelve months. The wording is factual and never asks whether someone can afford a meeting.
- **Privacy:** the place a visitor types stays in the browser; it reaches another site only if the visitor opens a link out.

## 7. Architecture

- **Static site:** no framework, cookies, advertising or third-party requests from the site's own code; a strict content security policy that permits only the host's visitor-count beacon. The data are public files on the site: `data/runway.json` (records), `data/attendance.json` (prices and hotel blocks), `runway.ics` (calendar feed), `geo/` (city, ZIP and airport coordinates).
- **Hosting:** Cloudflare Pages, under the owner's account, built from the repository's `site/` folder; the domain is registered to the owner. The host keeps standard access logs and may collect browsers' network-error reports and aggregate visit counts.
- **Search engines:** the owner requested public access and search discovery on October 17, 2026. Robots permit crawling and sitemap.xml lists the main public pages. Indexing is controlled by search engines and is not guaranteed.
- **Evidence:** the captured organizer pages stay with the owner. Only short quotes, links and hashes are published.

## 8. Challenge and correct

Check any record against its source link. To correct one, use **Report a correction** in the record, or email mark.karasin@protonmail.com with the record's link and the organizer's page that shows the right detail. A correction is recorded with its reason, review date, the organizer's wording and the exact URL, and is published through the same gates as every other change. Analysis of blind spots is welcome at the same address.

## 9. Limits of the data

- A curated directory, not a study: no completeness claim. Small organizers and non-English sources are likely under-represented.
- Discipline tags are curator judgments. "Advanced practice provider" is a U.S. umbrella term; titles and scopes differ by country.
- AI systems contributed to research and review; the evidence rule, deterministic checks, human authority and audits reduce, not remove, error risk.
- No label is itself a claim: a High-confidence record can still have a wrong end date or venue. Confirm with the organizer before registering, submitting or traveling.
- Distances use ZIP or city centroids and are approximate. A place typed into the planner or Near City stays in the page address or the browser.

## 10. Rights

© 2026 Mark Karasin. The owner's code, original design, documentation and data compilation are released under the MIT license; see LICENSE.txt and THIRD_PARTY_NOTICES.md. Organizer names, marks, quoted wording, linked pages and images belong to their organizers and appear only to show where a date or price came from. Third-party components keep their licenses: Barlow Condensed and Source Sans 3 (SIL Open Font License), GeoNames (CC BY 4.0), U.S. Census Bureau Gazetteer and OurAirports (public domain). Institutional names are not licensed and imply no endorsement.


## 11. Daily update status

One header timestamp, **Updated**, shows the most recent actual source check; it does not move because the layout changed. The dot beside it is green when the latest nightly update checked, validated and published; amber while one is in progress or when checking reported an issue; red when no update has started in 30 hours. The workflow writes `data/update-status.json` with `status`, `started_at`, `sources_checked_at` and `published_at`. Confidence labels and the two indices are hidden from visitors at the curator's request; their evidence and calculations are retained.

## 12. Curator log

Short notes of curator decisions and corrections, newest first. Detail stays in the linked reports and the repository history.

- **2026-10-19** Publishing moved to a single route: the nightly check commits to GitHub and Cloudflare Pages publishes from it. Duplicate copies (the GitHub Pages copy, the hand-uploaded snapshot) retired and archived. The October 17 reconciliation is carried into every nightly build (`sources/curated.json`). Orientation guide restored; phone layout of the Orbit legend tidied.
- **2026-10-17** Manual reconciliation of 34 exceptions from the source check: 30 confirmed or corrected against organizer material, four unsupported future PAEA editions withheld pending organizer confirmation, four date ranges and six abstract calls corrected. Originals and automated results retained ([manual review](data/manual-review.json), [withheld records](data/withheld-editions.json)). Site opened to the public and to search engines; code and documentation released under the MIT license. Header simplified to one update stamp.
- **2026-10-06** Orientation guide ("What am I looking at?") and shared footer added.
- **2026-09-26** First automated re-read of every upcoming record.

---

How can I help?

*Do what's right, not what's easy.*
