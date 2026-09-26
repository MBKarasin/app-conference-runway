# APP Conference Runway: AI Handoff

**Live site:** https://mbkarasin.github.io/app-conference-runway/\
**Source code:** https://github.com/MBKarasin/app-conference-runway\
**Owner and curator:** Dr. Mark Karasin, DNP, APN, AGACNP-BC, CNOR(E)\
**Contact and corrections:** mark.karasin@protonmail.com\
**Document date:** 2026-09-26

This page is written for people and for AI systems that need to understand, check or challenge the Runway. It describes what runs; where a part is planned, it says so.

## 1. Why this exists

Advanced practice providers (nurse practitioners, physician assistants and associates, nurse anesthetists, clinical nurse specialists and nurse-midwives) and their students must search many organizer sites for meetings, abstract deadlines, and student and DNP project venues. The Runway gathers them in one calendar that traces each upcoming record to the organizer's own material and re-reads those sources every night.

The Runway is global in scope. It is curated by a private individual, and the curator acknowledges the limits that come with that. They include, but are not limited to, geopolitical and technical barriers to web access and differences in language and publishing practice, which, together with the curator's place of residence, inherently risk over-representing the United States relative to APP activity worldwide. On 2026-09-26, 253 of the 315 upcoming dated records (80%) were in the United States. The curator does not treat this as a stopping point but as a building block: naming the limits openly is a step toward widening the vision of all APPs to include a global professional identity.

The curator shares the Runway for critique with colleagues in academic nursing, research, clinical practice, artificial intelligence and data science; their feedback informs his scholarly inquiry. Reviewers are named only with their written permission, and naming implies no endorsement by them or their institutions.

The site is independent. It is not an official publication of, or endorsement by, Rutgers University, RWJBarnabas Health or any organizer listed.

## 2. Ownership, roles and governance

The Runway and this repository are owned by the curator, who decides what is published and is accountable for it. Every actor below works under the curator's **MBK AI Governance Protocol**.

| Actor | Role | No authority to |
|---|---|---|
| Curator | Owns the Runway and the MBK AI Governance Protocol; examines evidence, resolves conflicts, approves or rejects changes of meaning, sets policy | — |
| Deterministic pipeline (GitHub Actions) | Re-reads sources and checks links every night; builds, validates, archives the day's data and deploys | Invent or approve facts |
| Claude (Anthropic) | Research, extraction, translation, implementation, audits and probes, as a bounded worker | Publish on its own judgment, or change a fact without organizer evidence |
| ChatGPT (OpenAI) | **Red team**: independent challenge of the method, data, interface and governance | Approve its own findings or bypass the release gates |
| Local model (LM Studio, on the curator's workstation) | Planned: a second reader of organizer pages, running around the clock with no tools or network access of its own, once it passes a blind pilot against published records | Hold credentials, reach the network or publish |

No model is a source of truth; the organizer's own page is. Captured organizer evidence supports research, and reviewed repository `main` is the published record. The Runway is kept separate from the curator's other projects and conversation history.

## 3. Content

### 3.1 Records

| Record | What it is |
|---|---|
| Series | A recurring meeting or observance of one organizer; `np_pa_basis` says why it serves APPs |
| Edition | One dated occurrence, with `source_url`, verbatim `evidence` and a `verify` state |
| Observance | A celebration week or day, dated by the organizer or by its published rule |
| Student opportunity | A student session, poster or DNP project venue at one edition |
| Expected edition | A meeting's usual month, projected up to three years ahead; never a day |

### 3.2 Evidence rule

An upcoming dated record, unless computed from a published rule, carries the organizer's own material as its source (an event page or sub-page, a program PDF, or a banner or flyer), **verbatim** wording from it that contains the dates (`evidence`) and the exact location of that wording (`source_url`, plus `evidence_image` for an image). Aggregators never count; a social post counts only from the organizer's own account. The build gate (`scripts/validate.py`) rejects a record without a quote and a source link, or with a quote over 200 characters.

The quote is limited to 200 characters because it is the organizer's copyrighted wording, reproduced only to show where a date came from. It is a pointer to the evidence, not the evidence itself: the nightly verification re-reads the organizer's whole page (§3.5), so the limit neither narrows what is checked nor lowers either index.

### 3.3 Corrections and precedence

`sources/runway_2026-09-16.json` → `sources/group_*.json` → `sources/archive/` → `sources/observances.json` → `sources/overrides.json` (curator corrections, which win). A correction carries a `_why`, a `reviewed_on` date, the verbatim wording and the exact URL or image; the build gate rejects one without a `_why`, and without a `reviewed_on` unless it predates review dates (16 listed in `validate.py`; none is invented for them). A wrong edition is marked `"removed": true`, never silently deleted. `call_patch` sets single call fields, such as a published cut-off time (`due_time`, `tz`); `uid` keeps a corrected edition's calendar-feed identity (`sources/SCHEMA.md`). `data/ledger.json` keeps every edition ever emitted; `data/snapshots/` keeps each day's generated data.

### 3.4 Fidelity and Reliability

The header reports two indices with different owners. **Fidelity** measures reach: how much of the APP meeting world the Runway holds. That is the curator's team's responsibility, and it says nothing about whether a record is right. **Reliability** measures how accurately and completely organizers display their own activity, as the Runway verifies it. Whether a record is true belongs here, and it rests on the organizer's own material.

Four numbers, from the data built on 2026-09-26 (nightly verification of 10:25 UTC):

| Index | From history | Today |
|---|---|---|
| Fidelity (reach) | 30.0% (6 of 20; 95% interval 14.5–51.9%) | 35.1% (20 of 57; 95% interval 24.0–48.1%) |
| Reliability (organizer display, as verified) | 87.9% (90.50% × 97.07%) | 70.3% (91.11% × 77.14%; 95% range 55.6–80.1%) |

**Fidelity = qualifying meetings found by the latest independent probe that the Runway already held ÷ all qualifying meetings the probe found**, with the 95% Wilson interval.

- No complete list of APP meetings exists, so reach is estimated the way epidemiologists estimate a population that no single register captures: by capture–recapture. A probe starts from frames published by third parties (lists of organizations, or of meetings) and reads each organizer's own events page without looking at the Runway (`sources/probes.json`).
- *Today* (probe of 2026-09-26): seven frames (published lists of U.S. state PA, NP and nurse anesthetist associations; PA specialty societies; national NP/APN and PA associations outside the United States; and independent editorial lists of NP conferences) found 57 qualifying dated meetings starting between 2026-09-26 and 2027-12-31. The Runway held 20.
- *From history:* when sources not previously captured were brought up before the probe (an outside conference index on 2026-09-23 and a single meeting on 2026-09-24), the Runway already held 6 of their 20 qualifying meetings.
- Every meeting a probe finds that the Runway lacks enters review. Fidelity changes only when a new probe is recorded.

**Reliability = confirmation × accuracy.**

- *Confirmation* (a census, every night) = (records not yet ended that the latest nightly verification confirmed on the organizer's own material + dates computed from a published rule) ÷ dated records not yet ended (projections excluded). Confirmed means the verification found the record's start date, with its year and a word of its name, on the organizer's page, rendered when it needs JavaScript, or in the organizer's image the record links. Manual reviews never count. When no verification has been recorded in 36 hours, only the rule dates count.
- *Accuracy* (a sample) = audited records right in every action-critical field (dates, place, format, abstract call or deadline, eligibility) ÷ records audited, in the latest audit of `sources/audits.json`. It stands until the next audit; the range shown is its 95% Wilson interval, scaled by confirmation.
- *Today:* confirmation (258 + 29) ÷ 315 = 91.11%. Accuracy 27 ÷ 35 = 77.14%, from a blind random sample of 40 confirmed records, 35 of them assessable, each re-derived from the organizer's own pages by auditors who never saw the stored values. Every audited date was right; the misses were 7 abstract calls and 1 host city, since corrected.
- *From history:* 3,506 of 3,874 record checks confirmed across the 12 automated verifications from 2026-09-22 to 2026-09-26 (90.50%), times the two audits of 2026-09-24 (630 of 649 right, 97.07%).

The page recomputes both indices in the visitor's browser from `site/data/runway.json` at every load; each opens its definition when clicked or tapped, and the footer links here. `python scripts/indices.py` recomputes both from the same file (or from the live copy, with `--data <URL>`) and prints every term; `--history` adds the readings from history, taken from this repository's own history. `scripts/ui_check.py` fails if the page shows a different value.

**Time stamps.** The header carries two:

- **Verified**: when the latest recorded nightly verification ran, in New York time. It drives Reliability's confirmation term and the record labels. Its dot is green when a verification was recorded within 36 hours and red otherwise.
- **Horizon scan**: when the latest probe for meetings the Runway does not yet list finished, in New York time. It sets Fidelity. Its dot reports the scan's reconciliation, not its age: green when everything the scan found has cleared (each meeting it found that the Runway lacked was added or set aside with a reason, and any error was checked and reconciled), yellow while anything is still to reconcile. On 2026-09-26 it is yellow: 35 of the 37 meetings the probe found that the Runway lacked await review, and 2 were added. The scan is to run weekly; so far it has been run by hand, on 2026-09-26.

**Labels.** A record that passed its check carries none; others read **Save the date**, **Set by rule**, **Recorded when published** or **Expected month** (never a day). A record confirmed by neither the latest check nor a current manual review is an exception ("Date needs review" or "Source not re-checked"), which **Needs review only** lists. Where an organizer's own pages disagree, the record follows the organizer's primary event page and states the disagreement inside it.

### 3.5 Nightly verification and known limits

- **Every night** (`scripts/check.py`, `scripts/linkcheck.py`), the organizer source of every dated record not yet ended is attempted, except dates computed from a published rule, and every source link is checked. A page that needs JavaScript is rendered; a linked organizer image is read by OCR. The reader identifies itself, obeys robots.txt and reports a page that refuses automated readers instead of reading it any other way.
- **Manual review** (`sources/overrides.json`) covers pages the checker cannot read. The **link check** marks a source link gone on a 4xx other than a refusal.
- **Ended meetings** are kept as recorded when published and are not re-read. A record's detail shows its series from three years back to three years ahead.
- **A confirmation is not a full admission test.** It shows that the record's start date and name appear on the organizer's material. On a page that lists several meetings, the match can belong to another of them, and other fields (end dates, venues, abstract calls and cut-off times) are not re-checked. The blind audit measures how often that matters: on 2026-09-26, 8 of 35 confirmed records carried a stale abstract call or host city. A verification result never rewrites a fact; a new or changed fact needs captured organizer evidence, a visible proposed change and the curator's approval.
- **Some organizer servers refuse cloud-hosted readers**, varying by night. Their records rest on a dated manual review and do not count toward confirmation.
- **A call's cut-off time** is known only where the organizer publishes one (`due_time`); otherwise its last day reads "Closes today · check the organizer's cut-off time".
- **Fidelity is only as wide as its probes.** Frames not yet probed (DNP programs, health-system APP conferences, national specialty nursing societies) may be covered better or worse, and with 57 meetings the interval is wide.
- **Reliability's accuracy term is a sample** of 35 records; its own 95% interval is 61–88%.
- **Who audited.** The re-derivation of 2026-09-24, the blind sample of 2026-09-26 and the probe of 2026-09-26 were carried out by AI agents of the builder's model family (Claude) without the stored values. The cross-model review of 2026-09-24 (ChatGPT, the red team) re-derived no event in full, by its own report. All worked under the curator's direction; none was a human audit.
- **The audits of 2026-09-24 overlap.** Both examined the same upcoming records, before the corrections that followed them, so pooling them in the reading from history treats 649 record audits as independent.

## 4. Architecture and public accountability

The operating contract is evidence-first: organizer material is captured within access limits; deterministic checks test the source and any proposed fact; AI systems work only as bounded workers that produce candidates or findings; the curator decides changes of meaning; GitHub then builds, validates, records and deploys the result.

### 4.1 Public and proprietary boundary

The Runway publishes what a reader needs to check it and keeps private what would let others game or imitate it.

- **Public in this repository:** the admitted records with their organizer links, quoted wording and verification states; the organizer source files behind them, including organizers checked where nothing qualified; the build, check, validation and index code; the audit and probe totals behind both indices; curator corrections with their reasons and review dates; daily snapshots and the full version history; and a public correction route.
- **Not published:** the discovery process (search queries, prompts, source prioritization, model routing), unpublished candidates, the probes' organization and meeting lists, credentials and security configuration.

The repository reproduces the published site and its checks from the admitted records. It does not reproduce the discovery process.

### 4.2 Current production and governed expansion

**Current production:** curated source files; nightly verification of every upcoming record and every source link; deterministic build and validation; daily snapshots; the two indices with their probe and audit ledgers; curator corrections; red-team review; GitHub Pages deployment.

**Governed expansion (planned, not yet running):**

- a weekly horizon scan that repeats the probes and proposes meetings not yet listed;
- the local model as an independent second reader, running around the clock on the curator's workstation after a blind pilot;
- a monthly blind audit by a different model family;
- stronger semantic checks, a candidate lifecycle separate from publication, and pull-request-only admission of changes of meaning.

Each must pass containment, privacy, prompt-injection, rollback and accuracy gates before activation. The Runway is intended to fit later into the curator's shared platform services for scheduling, evidence custody, policy, model adapters and audit receipts, as a separate tenant: no personal conversation archive, protected data, unrelated project files or cross-project credentials belong in its context.

### 4.3 Website and release architecture

- **Static site** in `site/`: no framework, cookies, analytics or third-party requests.
- **This handoff on the site:** `scripts/build.py` renders this file to `site/ai-handoff.html` (`scripts/handoff_page.py`, standard library only), the page the site's AI Handoff links open, so reading it needs no GitHub account or app. The build gate fails if that page no longer matches this file, a section link misses, or Markdown is left unrendered.
- **Search engines:** every page carries a `noindex` tag, and nothing stops a crawler from reading it. GitHub Pages cannot send that instruction as an HTTP header, and crawlers read robots.txt only at a host's root, so the data files (`data/runway.json`, `runway.ics`, `AI-HANDOFF.md`) can be listed if something links them, and the repository itself is public on GitHub. The Runway is shared by link; no instruction guarantees exclusion.
- **Hosting:** GitHub Pages via `.github/workflows/runway.yml`. Each push to `main` builds, validates and deploys; the nightly run (06:00 UTC, may start late) also verifies sources and links, archives the day's data and updates the review issue, deploying only if the check and validation pass.
- **Icons:** browser-tab and installed-app icons are the logo's mark without letters. Every icon URL carries `?v=` + the first 8 hex digits of its SHA-256, written by `python scripts/icon_versions.py`; `--check` exits 1 on a stale stamp.
- **Feed and clock:** `site/runway.ics` carries every dated record the site shows as settled (confirmed, set by rule, recorded when published, save the date) from 60 days before the build onward, plus each abstract deadline still ahead. An event's UID is the edition id, or its `uid` when a corrected edition keeps the identity it was published under. The build and the checker use New York's calendar day; an open page reloads itself when the visitor's calendar day changes.
- **Performance** (measured 2026-09-25): the data file is 1.5 MB, 240 KB as served (gzip); the city list (170 KB served) loads only when Near City is used. If the data cannot load, the page says so.

## 5. Interface

- **Header:** the **Verified** and **Horizon scan** stamps and the two indices (§3.4).
- **Views:** **List** (upcoming records by month), **Calendar** (month grid), **Orbit** (landing view: twelve months with each record type's density) and **Directory** (every series with its history), all filtered alike by Discipline, Focus, Scope, Location and search. A record opens the same detail everywhere: source link, quoted wording, calendar file, **Suggest a fix**.
- **Links:** each view is a URL whose hash carries its filters; older links still open the view they described.
- **Near City** takes a ZIP code or a place with its state, province or country ("Springfield, IL", "Portland ME", "London, ON"; the city list carries each city's state or province). An unknown place is reported above the results; distance is then not applied.
- **Calendar** lists abstract calls open now with no published due date above the current month's grid. A call with a published cut-off time closes at that instant, wherever the visitor is.
- **Accessibility:** a list card opens from its title button (no control sits inside another), and a record whose organizer page was removed says so and links the Internet Archive's copies.
- **Phones:** a phone (screen's shorter side ≤ 700 px) gets the mobile layout with a **Desktop layout** link at the top; choosing it fits the desktop layout to the screen, and **Switch to the mobile layout** returns. The choice is kept only in that browser (localStorage, no cookie). Tablets and desktops get the desktop layout; upright tablets (701–900 px) fit the month grid to the screen. On a phone held upright, the Calendar is a day-by-day agenda that opens at today, with records under way today listed above today, and Orbit's twelve months show as a grid.

## 6. Tools, models and infrastructure

- **AI systems:** Claude (Anthropic), through the Claude apps, for research, implementation, audits and probes; ChatGPT (OpenAI), as red team; a local model, Qwen 27B in LM Studio on the curator's workstation (staged as a second reader).
- **Protocols and skills used with the AI systems:** the MBK AI Governance Protocol; the curator's skills Pandora, anti-fabrication, checkpoint-clarification and communication style.
- **Software:** Python 3.12 and its standard library; pypdf; Playwright with Chromium, for pages that need JavaScript and for the interface check; Pillow and Tesseract, for OCR of organizer images; Git.
- **Services:** GitHub (repository, Actions, Pages, Issues); Proton Mail (contact).
- **Hardware:** the curator's Windows workstation (AMD Ryzen 7 7700X, 64 GB RAM, Intel Arc Pro B60 GPU with 24 GB) runs the local model and serves as a second vantage point for reading organizer pages; GitHub-hosted Ubuntu runners run the nightly verification, builds and deploys; Anthropic-hosted Linux workspaces run research and development.
- **Desktop tools:** the Claude desktop app, linked to the curator's workstation.
- **Data and fonts:** U.S. Census Bureau Gazetteer (public domain); GeoNames (CC BY 4.0); Barlow Condensed and Source Sans 3 (SIL Open Font License).

### 6.1 Check it yourself

The repository can be read, and downloaded as a ZIP, without a GitHub account. With Python 3.12 (standard library only), from the repository root (`--history` reads the repository's own history, so it needs a git clone):

```text
python scripts/build.py
python scripts/validate.py
python scripts/indices.py --history
python -m http.server 8000 --directory site
```

The nightly run adds `python scripts/check.py` and `python scripts/linkcheck.py` (network; `pypdf==5.*`, with Playwright and Chromium, Pillow and Tesseract as optional second readers). `python scripts/ui_check.py` (Playwright with Chromium) runs the scripted interface check against a local copy or, with `--url`, the deployed site. Running these to check the published data is part of the transparency §9 grants; hosting a copy is not.

## 7. Challenge and correct

Check any record against its source link. To correct one:

1. **Report** it with **Suggest a fix** (a prefilled GitHub issue, which needs a GitHub account) or **Make a request** (mark.karasin@protonmail.com), linking organizer material that shows the right detail.
2. **Re-read** the organizer's own material, translated where needed; aggregators do not count.
3. **Record** the fix in `sources/overrides.json` with a `_why`, a `reviewed_on` date, the verbatim wording and the exact URL or image.
4. **Publish:** a push to `main` rebuilds, validates and redeploys.

An organizer may ask at the same address for its material to be corrected or removed. Analysis of blind spots is welcome.

## 8. Limits of the data

- **Reach is measured, not assumed** (§3.4): most qualifying meetings in the frames probed on 2026-09-26 were not yet listed. Small organizers and non-English sources are the least covered.
- Discipline tags (`np_pa_basis`) are curator judgments (CAA meetings sit under CRNA, nursing-facing ones under NP). "Advanced practice provider" is a U.S. umbrella term; titles and scopes differ by country.
- AI systems contributed to research and review. The evidence rule, deterministic checks, the curator's authority and audits reduce error risk; they do not remove it.
- No label is itself a claim: a confirmed record can still carry a wrong end date, venue or abstract deadline (§3.5). Confirm with the organizer before registering, submitting or traveling.
- Builds depend on the day they run; a snapshot records a build, not a deployment.
- A city or ZIP used for distance stays in the page address; GitHub Pages may keep access logs.

## 9. Rights

- **© 2026 Mark Karasin. All rights reserved** (also in `LICENSE`). The APP Conference Runway name and logo, in every form (the mark alone, the mark with letters, and the mark with the name beside it), are claimed as the owner's trademarks and may not be used without his written permission. The site's text, design, data compilation and code, and this handoff, are the owner's; no license to copy, modify or redistribute them is granted.
- **What the public receives is transparency:** anyone may read the site and this repository, link to them, run the repository's scripts to check the published data and indices, and check any record against its organizer's source. GitHub's terms also let GitHub users view and fork a public repository on GitHub; that grants no other use.
- **Earlier versions:** from commit `ad9dd5f` (2026-09-22) until this change, versions of this repository carried a CC0 1.0 public-domain dedication for the curator's code, data compilation, design and documentation; from commit `c94aa5f` (2026-09-23) it also named the logo artwork. That dedication cannot be withdrawn for those versions and does not extend to later changes. It never waived trademark rights (CC0 1.0, §4(a)).
- **Not the owner's:** organizer and event names, organizer marks, quoted wording, linked pages and images belong to their organizers and appear only to show where a date came from. Third-party components keep their licenses: Barlow Condensed and Source Sans 3 (SIL Open Font License); GeoNames data (CC BY 4.0, attribution required); U.S. Census Bureau Gazetteer data (public domain). Institutional names and marks, including those of Rutgers University and RWJBarnabas Health, are not licensed and imply no endorsement.
- **No warranty.** The site and its data are provided as is, without warranty of any kind. Dates change; confirm with the organizer before registering, submitting or traveling.
