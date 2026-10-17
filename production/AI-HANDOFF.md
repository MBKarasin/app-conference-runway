# APP Conference Runway: AI Handoff

**Live site:** https://appconferencerunway.org/\
**Owner and curator:** Dr. Mark Karasin, DNP, APN, AGACNP-BC\
**Contact and corrections:** mark.karasin@protonmail.com\
**Document date:** 2026-09-26

This page is written for people and for AI systems that need to understand, check or challenge the Runway. It describes only what runs; where a part is staged but not yet running, it says so.

## 1. What this is

Advanced practice providers (NPs, PAs, CRNAs, CNSs, CNMs) and their students must search many organizer sites for meetings, abstract deadlines and student and DNP project venues. The Runway gathers them in one calendar that traces each upcoming record to the organizer's own material, re-reads those sources by machine, and helps a visitor plan attendance: dates, travel, lodging and the price of attendance by category. It is global in scope and incomplete; coverage is concentrated in the United States.

The site is independent. It is not an official publication of, or endorsement by, Rutgers University, RWJBarnabas Health or any organizer listed.

## 2. Ownership and roles

The Runway, this site and the appconferencerunway.org domain are owned and operated by the curator, who decides what is published and is accountable for it. Its source files, pipeline code and evidence archive are kept by the owner and are not published.

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

| Part | Status (2026-09-26) |
|---|---|
| A: re-read of dates, links and cited prices | Runs as described; first run 2026-09-26 |
| B: independent second read | Runs for plain pages; rendered and image pages, and a local-model reader, are staged |
| C: new editions of known series | Runs as an internal queue; automatic publication and a weekly open search are staged |
| Publish, verify, archive | Runs as described; publication is by the owner's account on the host |
| Schedule | The first run was started by hand. An automatic nightly schedule is being set up; until it runs, the **Updated** stamp shows the latest run, and after 36 hours without one, re-read records count as Medium confidence (§4.1). |

## 6. Price of attendance and door-to-door planning

Every meeting still ahead opens a **Plan your attendance** panel.

- **Registration** prices are shown by category (member, non-member, student and the like; early, regular, late; full meeting, one day, online) exactly as the organizer states them, each with the organizer's link, the date read, and its confidence. A price is never estimated. Where an organizer has not published prices the panel says **Not posted**; where they have not been read yet, **Not captured yet**; where the organizer's site refuses automated reading, **Not captured**, with a link to the organizer's page in every case.
- **Getting there** uses straight-line distance from the visitor's ZIP code, city or country (a country alone is represented by its most populous listed city, and the panel says so): up to 80 km is a commute; up to 400 km, a drive or rail trip; beyond, a flight, with airports that have scheduled service within 160 km of each end (OurAirports, public domain). Drive times are approximations and are labeled so. Fares are not estimated; the panel links out to search them.
- **Door-to-door dates:** a commute is a day trip on each meeting day. A drive of more than 2.5 hours arrives the day before, and one of more than 4 hours returns the day after. A flight arrives the day before and returns the day after when the trip is international or longer than 1,500 km. Nights follow from those dates.
- **Lodging:** the organizer's official hotel block first, with its rate, booking cut-off and link. An estimate is shown only when a per-night block rate is posted: that rate times the nights, before taxes, labeled as an estimate.
- **Ways to take part at lower cost** lists, in the organizer's terms, online options, student, one-day and early rates still open, and published scholarships, grants or volunteer roles, and then meetings for the same disciplines nearer the visitor in the next twelve months. The wording is factual and never asks whether someone can afford a meeting.
- **Privacy:** the place a visitor types stays in the browser; it reaches another site only if the visitor opens a link out.

## 7. Architecture

- **Static site:** no framework, cookies, analytics, advertising or third-party requests; a strict content security policy. The data are public files on the site: `data/runway.json` (records), `data/attendance.json` (prices and hotel blocks), `runway.ics` (calendar feed), `geo/` (city, ZIP and airport coordinates).
- **Hosting:** Cloudflare Pages, under the owner's account; the domain is registered to the owner. The host keeps standard access logs and may collect browsers' network-error reports; the site's own code sets no cookies and runs no analytics. The site asks the host not to rewrite its pages (`Cache-Control: no-transform`), so the host inserts no analytics tag and leaves email addresses as written, and after every publication each served file is compared with the release, byte for byte.
- **Search engines:** the owner requested public access and search discovery on October 17, 2026. Robots permit crawling and sitemap.xml lists the main public pages. Indexing is controlled by search engines and is not guaranteed.
- **Ownership of code and evidence:** the source files, the pipeline and the captured organizer pages stay with the owner. Only short quotes, links and hashes are published.

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


## 11. Site notes

Moved from the main-page footer on October 17, 2026. The single Updated timestamp describes the most recent actual source check.

Website is an independent resource. It is not an official publication of, or endorsement by, either Rutgers University or RWJBarnabas Health.

**How dates are checked.** Every dated entry comes from the organizer's own material and links the exact page, PDF, banner or flyer where its date was published. Organizer pages for meetings still ahead are re-read by an automated check, and ended meetings are kept as recorded when published; the Updated timestamp records the latest automated source check, the Fidelity and Reliability indices beneath it are defined in the [AI Handoff (§4)](#4-confidence-and-the-indices), and a record the latest re-read did not confirm says “Confidence: Medium” with its reason (see “Medium confidence only”).

**Price of attendance.** Registration prices, online options, official hotel blocks and support come only from the organizer's own pages, each with its link and the date it was read; what an organizer has not published reads “Not posted”. Travel fares are not estimated.

**Coverage.** Coverage snapshot on October 17, 2026: of 239 upcoming dated entries, 218 have mapped locations in 25 countries across 6 continents. A proprietary, curator-directed global research process proposes additions, but publication still requires organizer evidence, validation and human review. This remains an incomplete global calendar; [suggest a missing meeting or organizer](mailto:mark.karasin@protonmail.com?subject=APP%20Conference%20Runway%20request).

**Expected months** are projections, never assigned a day, and appear only when enabled.

Confirm details with the organizer before registering, submitting or booking travel. Distance results use ZIP or city centroids and are approximate. Independent of the organizers listed; the site code sets no cookies or analytics; its host, Cloudflare, may keep standard access logs and network-error reports. City data: U.S. Census Bureau Gazetteer and [GeoNames](https://www.geonames.org/) (CC BY 4.0); airports: [OurAirports](https://ourairports.com/data/) (public domain). This page asks search engines not to index it and is shared directly among APPs.

© 2026 Mark Karasin. APP Conference Runway and appconferencerunway.org are owned and operated by the curator. Organizer names, marks and quoted wording belong to their organizers.


## 12. Daily update status

The daily update is scheduled for 4 a.m. America/New_York. One header timestamp shows the most recent actual source-check time. It does not advance merely because the layout changed or a scheduled task woke up.

The dot describes the latest scheduled run: green means source checking, validation and publication succeeded; yellow means the run started but remains in progress or reported an issue; red means the latest scheduled run is missing. Confidence labels, confidence filtering, and the two data-quality indices are currently hidden from the visitor interface at the curator’s request. Their underlying evidence and calculations are retained.

The publishing workflow must maintain data/update-status.json with status, started_at, sources_checked_at and published_at. A success requires all three stages to finish. Until this is wired to the owning GitHub-to-Cloudflare publishing workflow, the preview correctly displays a red dot. A local chat follow-up has been scheduled; it is not evidence that an unattended GitHub-to-Cloudflare pipeline is operational.


## 13. October 17, 2026 refresh

A fresh deterministic source check attempted 239 current dated editions on 185 organizer pages: 205 matched, 8 did not match, and 26 could not be read. Those exceptions remain in the data and review report; a successful fetch is not a comprehensive validation of every meeting field. PDF text extraction was available; optional rendered-page and image-OCR readers were not available in this run.

A bounded organizer-source search also replaced two expected-month projections with dated 2027 records: Charter Oak, March 21–23; and NCAPA Summer, August 15–20. NCAPA’s updated October date image supersedes the older August 22–27 save-the-date. The reviewed organizer page still uses North Myrtle Beach in its general prose while its new image says Myrtle Beach; exact venue details remain to be announced. The Rutgers/RWJBarnabas cardiovascular meeting, October 16–17, was added from its official Rutgers CloudCME page. This was not an exhaustive global discovery sweep.

The header therefore shows a current check time with a yellow badge, reflecting completed work with unresolved source exceptions. Detailed results: [source check report](data/check_report.md).


## 14. October 17 manual reconciliation and daily follow-up

Completed 2026-10-17T08:57:46Z. Automated pass: 239 checked, 205 matched, 34 exceptions. Direct review: 30 confirmed or corrected (including one professional-association corroboration), four unsupported future PAEA editions withheld from public calendar with originals preserved. Four event date ranges corrected; six call records refreshed.

Original evidence and automated failures are retained. See [manual review report](data/manual-review-report.md), [structured manual review](data/manual-review.json), [withheld records](data/withheld-editions.json), and [daily follow-up ledger](data/follow-up.json). Taiwan was subsequently confirmed from an organizer-issued letter hosted by its recipient. CANO was resolved against the conference-specific landing page and newsletter. Its registration prose discrepancy remains documented for monitoring. Four unsupported PAEA editions remain withheld and tracked for daily follow-up. The badge represents successful completion of the update process, not a claim of perfect data or universal page readability. Four PAEA future editions have no current organizer support and are withheld rather than displayed as confirmed.

The next local chat heartbeat is October 18 at 4 a.m. Eastern. It must read the ledgers, follow up independently, refresh actual records, validate, publish and verify. The main Cloudflare site is not connected to GitHub publishing; a scheduled wakeup alone is not a successful publication. No credentials or expanded permissions were created.


## 15. Public access and source resolution

Organizer-issued letter dated February 3, ROC year 115, visually reviewed on October 17. It confirms October 18, 2026, 12:30–16:00, Greater Tainan Convention Center, and July 31 abstract deadline. Letter hosted by its recipient, Taiwan Midwives Association; original organizer website remains protected.

CANO dates remain October 22–25 based on conference-specific organizer materials and ISNCC. Four PAEA future editions remain withheld pending primary confirmation and are preserved in the daily follow-up ledger. Raw automated failures are retained for provenance; they are superseded by the documented manual dispositions, not silently erased.

Public search crawling is permitted as requested. Publishing a sitemap does not itself submit the site to Google Search Console or prove indexing.


## 16. Public publication and MIT licensing — October 17, 2026

The owner explicitly authorized public website access, public repository visibility, MIT licensing and search discovery to support the exchange of ideas and promotion of human health. His original code, design, artwork, documentation and data compilation throughout the repository are released under MIT. Preserve the copyright and license notice. Third-party content and components retain their rights and notices; no trademark rights or institutional endorsement are granted. See [MIT license](LICENSE.txt) and [scope and third-party notices](THIRD_PARTY_NOTICES.md).

Main public site: https://appconferencerunway.org/ . Public source: https://github.com/MBKarasin/app-conference-runway . `production/` in the repository is the approved main-domain snapshot; the existing `site/` build and GitHub Pages workflow are a separate variant. Do not replace the main site with that variant or claim the two deployments are synchronized. Current main-site changes include the subtitle beneath the logo, logo reduced by 15%, and three header actions with sharing removed, compact footer, hidden confidence layer, fresh source review and one daily update stamp.

Search robots permit crawling and the sitemap lists the main pages. The main domain is canonical. Search Console submission and actual indexing are separate states; only record them as completed after verification. No search-engine listing or ranking is guaranteed.

Carry forward the withheld PAEA records and source-resolution history in the daily ledgers. Never restore unsupported dates merely to improve a badge. Green describes a successfully checked, validated and published update with documented dispositions. The local daily 4 a.m. Eastern heartbeat is configured; unattended GitHub-to-Cloudflare publishing is not yet connected. A scheduled wakeup alone is not successful publication.


## 17. Final header direction

Restore the approved uppercase subtitle beneath the logo. Reduce logo artwork width by 15% relative to its containing logo area. Remove Share with a colleague; keep Copy link, Make a request and AI Handoff in their earlier header arrangement. Preserve the compact footer, source-check timestamp and badge.
