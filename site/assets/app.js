/* APP Conference Runway — client. No dependencies, no third-party requests. */
(function () {
  "use strict";
  const CONFIG = window.RUNWAY_CONFIG || {};
  const REPO = CONFIG.repo || "";

  /* ---------- helpers ---------- */
  const $ = (s, r = document) => r.querySelector(s);
  const esc = s => String(s == null ? "" : s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const MONTH = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
  const DOW = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
  const iso = d => d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") + "-" + String(d.getDate()).padStart(2, "0");
  const D = s => new Date(s + "T12:00:00");
  const TODAY = iso(new Date());
  const addDays = (s, n) => { const d = D(s); d.setDate(d.getDate() + n); return iso(d); };
  const daysBetween = (a, b) => Math.round((D(b) - D(a)) / 864e5);
  const longDate = s => { const d = D(s); return MONTH[d.getMonth()] + " " + d.getDate() + ", " + d.getFullYear(); };
  const md = s => MON[D(s).getMonth()] + " " + D(s).getDate();
  function range(e) {
    if (e.month_only) { const d = D(e.start); return "~" + MON[d.getMonth()] + " " + d.getFullYear(); }
    const a = D(e.start), b = D(e.end || e.start), y = b.getFullYear();
    if (e.start === e.end || !e.end) return md(e.start) + ", " + a.getFullYear();
    if (a.getMonth() === b.getMonth() && a.getFullYear() === y) return md(e.start) + "–" + b.getDate() + ", " + y;
    return md(e.start) + (a.getFullYear() !== y ? ", " + a.getFullYear() : "") + " – " + md(e.end) + ", " + y;
  }
  function stampET(isoz) {
    try {
      return new Intl.DateTimeFormat("en-US", { timeZone: "America/New_York", month: "short", day: "numeric", year: "numeric", hour: "numeric", minute: "2-digit", timeZoneName: "short" }).format(new Date(isoz));
    } catch (e) { return isoz; }
  }
  const miles = (a, b, c, d) => { const R = 3958.8, r = x => x * Math.PI / 180; const h = Math.sin(r(c - a) / 2) ** 2 + Math.cos(r(a)) * Math.cos(r(c)) * Math.sin(r(d - b) / 2) ** 2; return 2 * R * Math.asin(Math.sqrt(h)); };
  const ICON = {
    check: '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M3 8.5l3 3 7-7" fill="none" stroke="currentColor" stroke-width="2"/></svg>',
    warn: '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M8 2l7 12H1z" fill="none" stroke="currentColor" stroke-width="1.6"/><path d="M8 6.5v3.5M8 11.8v.4" stroke="currentColor" stroke-width="1.6"/></svg>',
    dash: '<svg viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="6" fill="none" stroke="currentColor" stroke-width="1.6" stroke-dasharray="3 2"/></svg>',
    cal: '<svg viewBox="0 0 16 16" aria-hidden="true"><rect x="2" y="3" width="12" height="11" rx="1.5" fill="none" stroke="currentColor" stroke-width="1.5"/><path d="M2 6.5h12M5 1.5v3M11 1.5v3" stroke="currentColor" stroke-width="1.5"/></svg>',
    list: '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M2 4h12M2 8h12M2 12h12" stroke="currentColor" stroke-width="1.6"/></svg>',
    ext: '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M9 2h5v5M14 2L7 9M12 9.5V14H2V4h4.5" fill="none" stroke="currentColor" stroke-width="1.5"/></svg>',
    link: '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M6.5 9.5l3-3M7 4.5l1.5-1.5a2.8 2.8 0 014 4L11 8.5M9 11.5L7.5 13a2.8 2.8 0 01-4-4L5 7.5" fill="none" stroke="currentColor" stroke-width="1.5"/></svg>',
    archive: '<svg viewBox="0 0 16 16" aria-hidden="true"><rect x="1.5" y="2.5" width="13" height="3" fill="none" stroke="currentColor" stroke-width="1.4"/><path d="M2.5 5.5v8h11v-8M6 8.5h4" fill="none" stroke="currentColor" stroke-width="1.4"/></svg>'
  };

  /* ---------- vocabulary ---------- */
  const PROF_COLOR = { NP: "--np", AGACNP: "--np", PA: "--pa", CRNA: "--crna", CAA: "--caa", RNFA: "--rnfa", CNM: "--cnm", CNS: "--cns", Nursing: "--nursing", Multidisciplinary: "--multi" };
  const PROF_CHIPS = [["", "All APPs"], ["NP", "NP"], ["AGACNP", "AGACNP"], ["PA", "PA"], ["CRNA", "CRNA"], ["CAA", "CAA"], ["CNS", "CNS"], ["CNM", "CNM"], ["RNFA", "NP-RNFA"]];
  const AGACNP_TOPICS = new Set(["Acute Care", "Critical Care", "Emergency", "Emergency Medicine", "Hospital Medicine", "Cardiology", "Cardiothoracic Surgery", "Pulmonary", "Neuroscience", "Neurosurgery", "Trauma", "Resuscitation", "ECMO & Perfusion", "Surgery", "Vascular Surgery", "Infectious Diseases", "Toxicology", "Nephrology"]);
  const PLABEL = { RNFA: "NP-RNFA" };
  const FOCUS_CHIPS = [["", "All"], ["clinical", "Clinical"], ["academic", "Academic"], ["executive", "Executive"]];
  const KIND_CHIPS = [["", "All"], ["conference", "Conferences"], ["symposium", "Symposiums"], ["summit", "Summits"], ["course", "Courses"], ["observance", "Celebrations"]];
  const US_REGIONS = ["Northeast", "Midwest", "South", "West"];
  const CONTINENTS = ["North America", "South America", "Europe", "Asia", "Oceania", "Africa"];
  const TABS = [["upcoming", "Upcoming"], ["deadlines", "Abstract deadlines"], ["students", "Students & DNP projects"], ["past", "Past"], ["directory", "Directory"]];
  const VSTATE = {
    verified: ["Start found", "check"], conflict: ["Organizer dates conflict", "warn"], not_found: ["Needs review", "warn"], unreachable: ["Not re-checked", "dash"],
    unchecked: ["Not re-checked", "dash"], expected: ["Expected", "dash"], rule: ["Set by rule", "dash"],
    archived: ["Recorded when published", "check"], announced: ["Save the date", "check"]
  };

  /* ---------- state, mirrored in the URL ---------- */
  const DEF = () => ({ view: "upcoming", display: "list", q: "", prof: "", focus: "", kind: "", where: "", area: "", nearQ: "", near: null, radius: 100, spec: "", openOnly: false, verifiedOnly: true, expected: false, within: 0, cal: TODAY.slice(0, 7), more: 1 });
  const st = DEF();
  let filtersOpen = false;
  function readHash() {
    const h = new URLSearchParams(location.hash.slice(1));
    Object.assign(st, DEF());
    if (TABS.some(t => t[0] === h.get("view"))) st.view = h.get("view");
    if (h.get("display") === "calendar") st.display = "calendar";
    if (st.view === "students") st.display = "list";
    ["q", "prof", "focus", "kind", "where", "area", "spec"].forEach(k => { if (h.get(k)) st[k] = h.get(k); });
    if (h.get("near")) st.nearQ = h.get("near");
    if (+h.get("r")) st.radius = +h.get("r");
    st.openOnly = h.get("open") === "1"; st.verifiedOnly = h.get("ver") !== "0"; st.expected = h.get("exp") === "1";
    if (st.expected) st.verifiedOnly = false;
    st.within = +(h.get("within") || 0);
    if (/^\d{4}-\d{2}$/.test(h.get("cal") || "")) st.cal = h.get("cal");
    return h.get("e");
  }
  function writeHash(extra) {
    const h = new URLSearchParams();
    if (st.view !== "upcoming") h.set("view", st.view);
    if (st.display === "calendar") h.set("display", "calendar");
    ["q", "prof", "focus", "kind", "where", "area", "spec"].forEach(k => st[k] && h.set(k, st[k]));
    if (st.near) { h.set("near", st.nearQ); h.set("r", st.radius); }
    if (st.openOnly) h.set("open", "1");
    if (!st.verifiedOnly) h.set("ver", "0");
    if (st.expected) h.set("exp", "1");
    if (st.within) h.set("within", st.within);
    if (st.display === "calendar" && st.cal !== TODAY.slice(0, 7)) h.set("cal", st.cal);
    if (extra) Object.entries(extra).forEach(([k, v]) => h.set(k, v));
    const s = h.toString();
    history.replaceState(null, "", s ? "#" + s : location.pathname + location.search);
  }

  /* ---------- data ---------- */
  let DATA, SERIES, EDS, SPECS, COUNTRIES = [], CITIES = null;
  function callOf(e) {
    const c = e.call || {}, closes = c.closes, opens = c.opens;
    if (closes && closes < TODAY) return { k: "closed", label: "Closed " + md(closes) };
    if (opens && opens > TODAY) return { k: "soon", label: "Opens " + md(opens), opens };
    if (closes && (c.status === "open" || c.status === "soon" || (opens && opens <= TODAY))) {
      const n = daysBetween(TODAY, closes);
      // the organizer's cut-off time is usually not published in machine form, so the last day is never called "open now"
      if (n <= 0) return { k: "urgent", label: "Closes today · check the organizer's cut-off time", closes, n: 0, today: true };
      return { k: n <= 14 ? "urgent" : "open", label: "Closes " + md(closes), closes, n };
    }
    if (c.status === "open") return { k: "open", label: "Call listed · confirm with the organizer", n: null, undated: true };
    const short = (t, dflt) => t && t.length <= 30 ? t : dflt;
    if (c.status === "soon") return { k: "soon", label: short(c.text && c.text.split("·")[0].trim(), "Opening soon") };
    if (c.status === "closed") return { k: "closed", label: "Call closed" };
    if (c.status === "none") return { k: "none", label: short(c.text && c.text !== "—" ? c.text : "", "No call") };
    return { k: "tba", label: short(c.text, "Call not posted") };
  }
  function wireSkip() {
    const a = document.querySelector("a.skip");
    if (!a) return;
    a.addEventListener("click", ev => {
      ev.preventDefault();                       // a hash jump here would be read as new filter state
      const m = $("#view");
      if (!m) return;
      m.setAttribute("tabindex", "-1");
      m.focus({ preventScroll: true });
      m.scrollIntoView({ block: "start" });
    });
  }
  function prep(d) {
    DATA = d;
    SERIES = new Map(d.series.map(s => [s.id, s]));
    EDS = d.editions.filter(e => SERIES.has(e.series)).map(e => {
      const s = SERIES.get(e.series);
      e.s = s; e.end = e.end || e.start;
      e.past = e.end < TODAY;
      e.expectedRow = e.verify && e.verify.state === "expected";
      e.c = callOf(e);
      e.hay = [s.name, s.org_display || s.org, s.org, e.location, (s.specialty || []).join(" "), e.theme, (e.sessions || []).join(" "), (e.daily || []).map(x => x.title).join(" "), s.professions.join(" "), e.student && e.student.kind, e.student && e.student.detail, e.geo && e.geo.country].join(" ").toLowerCase();
      return e;
    });
    const upcoming = EDS.filter(e => !e.past && !e.expectedRow && e.verify.state !== "rule");
    const mapped = upcoming.filter(e => e.geo && e.geo.country);
    const countries = new Set(mapped.map(e => e.geo.country));
    COUNTRIES = [...countries].sort((a, b) => a.localeCompare(b));
    const continents = new Set(mapped.map(e => e.geo.continent));
    const coverage = $("#coverageCount");
    if (coverage) coverage.textContent = `Of ${upcoming.length} upcoming dated entries, ${mapped.length} have mapped locations in ${countries.size} countries across ${continents.size} continents.`;
    SPECS = [...new Set(d.series.flatMap(s => s.specialty || []))].sort();
  }

  /* ---------- matching ---------- */
  function agacnpFit(s) {
    if (s.name === "National APP Week") return true;
    const p = s.professions || [];
    if (!p.some(x => ["NP", "Nursing", "Multidisciplinary"].includes(x)) || (p.includes("CRNA") && !p.includes("NP") && !p.includes("Multidisciplinary"))) return false;
    return (s.specialty || []).some(x => AGACNP_TOPICS.has(x));
  }
  function profMatch(s) {
    const P = s.professions;
    switch (st.prof) {
      case "": return true;
      case "NP": return P.some(p => ["NP", "Multidisciplinary", "Nursing", "CNS", "CNM"].includes(p));
      case "AGACNP": return agacnpFit(s);
      case "PA": return P.some(p => ["PA", "Multidisciplinary"].includes(p));
      case "CRNA": return P.includes("CRNA");
      case "CAA": return P.includes("CAA");
      case "CNS": return P.includes("CNS");
      case "CNM": return P.includes("CNM");
      case "RNFA": return P.includes("RNFA") || !!s.rnfa_inferred;
    }
    return true;
  }
  function seriesMatch(s, ignoreProf = false) {
    if (!ignoreProf && !profMatch(s)) return false;
    if (st.focus && !(s.focus || []).includes(st.focus)) return false;
    if (st.kind && s.kind !== st.kind) return false;
    if (st.spec && !(s.specialty || []).includes(st.spec)) return false;
    return true;
  }
  function placeMatch(e) {
    const g = e.geo || {};
    const online = !!g.online || e.format === "virtual";
    if (st.where === "online") return online || e.format === "hybrid";
    if (st.area) {
      const [k, v] = [st.area.slice(0, 1), st.area.slice(2)];
      if (k === "r" && !(g.cc === "US" && g.region === v)) return false;
      if (k === "c" && g.continent !== v) return false;
      if (k === "n" && g.country !== v) return false;
    }
    if (st.near) {
      if (g.lat == null) return false;
      if (miles(st.near.lat, st.near.lon, g.lat, g.lon) > st.radius) return false;
    }
    return true;
  }
  function verMatch(e) {
    if (!st.verifiedOnly) return true;
    return e.verify.state === "rule" || e.verify.state === "archived" || e.verify.state === "announced"
      || (e.verify.state === "verified" && e.verify.evidence_match !== false);
  }
  function edMatch(e) {
    if (!seriesMatch(e.s, st.view === "students") || !placeMatch(e) || !verMatch(e)) return false;
    if (st.view === "students" && st.prof && !(e.student && (e.student.roles || []).includes(st.prof))) return false;
    if (st.q && !st.q.toLowerCase().split(/\s+/).every(w => e.hay.includes(w))) return false;
    if (st.openOnly && !(st.view === "students" ? e.student && e.student.deadline && e.student.deadline >= TODAY : ["open", "urgent"].includes(e.c.k))) return false;
    return true;
  }

  /* ---------- pieces ---------- */
  const colorOf = s => s.kind === "observance" ? "var(--obs)" : "var(" + (PROF_COLOR[s.professions[0]] || "--multi") + ")";
  const profTags = s => s.professions.map(p => `<span class="tag p" style="--c:var(${PROF_COLOR[p] || "--multi"})">${esc(PLABEL[p] || p)}</span>`).join("") + (s.rnfa_inferred ? `<span class="tag p" style="--c:var(--rnfa)" title="Surgical or perioperative meeting relevant to NP first assistants; curator tag">NP-RNFA</span>` : "");
  function vBadge(e, exceptionsOnly = false) {
    const v = e.verify || { state: "unchecked" };
    const [baseLabel, icon] = VSTATE[v.state] || VSTATE.unchecked;
    const drift = v.state === "verified" && v.method !== "manual" && v.evidence_match === false;
    if (exceptionsOnly && ((v.state === "verified" && !drift) || v.state === "rule" || v.state === "archived")) return "";
    if (v.state === "announced" && exceptionsOnly) return `<span class="vf verified" title="The organizer has published a save-the-date for these days; the detailed programme is still to come.">${ICON.check}Save the date</span>`;
    const label = v.state === "verified" && v.method === "manual" ? "Source reviewed" : drift ? "Source wording changed" : baseLabel;
    const when = "";   // the page header carries the check time; repeating it on every record only adds noise
    const tip = v.state === "verified" && v.method === "manual" ? "The organizer's source was manually reviewed for this date range. Review date appears on this label; confirm details before booking." :
      drift ? "The start date and a meeting-name word remain on the organizer page, but the original source excerpt no longer matches. Review the full range before relying on it." :
      v.state === "verified" ? "Start date, year and a distinctive meeting-name word were found on the organizer page. Confirm the end date there before booking." :
      v.state === "not_found" ? "The nightly check could not find these dates on the organizer page. Confirm before relying on them." :
      v.state === "conflict" ? (v.why || "The organizer publishes conflicting dates; confirm the final date before relying on it.") :
      v.state === "expected" ? "Projected from this meeting's usual month. No date has been published." :
      v.state === "announced" ? "The organizer has published a save-the-date for these days. Treat the range as theirs and the programme as still to come." :
      v.state === "archived" ? "The meeting has ended. The date is kept as the organizer's page read when it was recorded, and is not re-checked, because organizers replace the page with the next edition." :
      v.state === "rule" ? "Computed from the organizer's published rule for this observance." :
      "The organizer page could not be read automatically" + (v.why ? " (" + v.why + ")" : "") + ". Shown as compiled on " + (e.compiled || "") + ".";
    if (exceptionsOnly) {
      const plain = drift ? "Source wording changed" : v.state === "not_found" ? "Date needs review" :
        v.state === "conflict" ? "Organizer dates conflict" : v.state === "expected" ? "Expected month" : "Source not re-checked";
      const tone = drift || v.state === "not_found" || v.state === "conflict" ? "warn" : "muted";
      return `<span class="source-note ${tone}" title="${esc(tip)}">${esc(plain)}</span>`;
    }
    return `<span class="vf ${drift ? "not_found" : esc(v.state)}" title="${esc(tip)}">${ICON[drift ? "warn" : icon]}${esc(label + when)}</span>`;
  }
  function callPill(e) {
    if (e.s.kind === "observance" || e.expectedRow || e.past) return "";
    return `<span class="pill ${e.c.k}" title="${esc((e.call && e.call.text) || e.c.label)}">${esc(e.c.label)}</span>`;
  }
  function evRow(e, studentMode = false) {
    const s = e.s, d = D(e.start), b = D(e.end);
    const same = b.getMonth() === d.getMonth() && b.getFullYear() === d.getFullYear();
    const day = e.month_only ? MON[d.getMonth()] : e.start === e.end ? String(d.getDate()) : same ? d.getDate() + "–" + b.getDate() : d.getDate() + "→";
    const sub = e.month_only ? d.getFullYear() + " · expected" : (same || e.start === e.end ? MON[d.getMonth()] : MON[d.getMonth()] + "–" + MON[b.getMonth()] + " " + b.getDate()) + " " + d.getFullYear();
    const kindTag = s.kind === "observance" ? '<span class="tag">Celebration</span>' : s.kind !== "conference" ? `<span class="tag">${esc(s.kind[0].toUpperCase() + s.kind.slice(1))}</span>` : "";
    const dist = st.near && e.geo && e.geo.lat != null ? `<span>${Math.round(miles(st.near.lat, st.near.lon, e.geo.lat, e.geo.lon))} mi away</span>` : "";
    const appWeekNow = s.name === "National APP Week" && e.start <= TODAY && e.end >= TODAY;
    return `<article class="ev${e.expectedRow ? " expected" : ""}${e.past ? " past" : ""}${appWeekNow ? " app-week-now" : ""}" data-e="${e.id}" tabindex="0" role="button" aria-label="${esc(s.name + ", " + range(e))}">
      <div class="when" style="--c:${colorOf(s)}"><span class="d">${esc(day)}</span><span class="m">${esc(sub)}</span></div>
      <div class="body">${appWeekNow ? `<div class="live-label">OUR WEEK · HAPPENING NOW THROUGH ${esc(md(e.end))}</div>` : ""}<div class="title">${esc(s.name)}</div><div class="org">${esc(s.org_display || s.org)}</div>
        <div class="meta">${e.location ? `<span class="loc">${esc(e.location)}</span>` : ""}${dist}${e.format && e.format !== "in person" ? `<span>${esc(e.format[0].toUpperCase() + e.format.slice(1))}</span>` : ""}${e.theme ? `<span><i>${esc(e.theme)}</i></span>` : ""}</div>
        <div class="badges">${profTags(s)}${kindTag}</div>${studentMode && e.student ? `<p class="student-line"><b>${esc(e.student.kind)}</b> · ${esc(e.student.detail)}</p>` : ""}</div>
      <div class="side">${studentMode ? (e.student && e.student.deadline && e.student.deadline >= TODAY ? `<span class="student-due">Submit by ${esc(md(e.student.deadline))}</span>` : "") : callPill(e)}${vBadge(e, true)}</div></article>`;
  }
  const empty = msg => `<div class="empty">${esc(msg)} <button class="linkbtn" data-act="clear">Clear all filters</button>${st.verifiedOnly ? ` or <button class="linkbtn" data-act="showall">include dates awaiting a source check</button>` : ""}</div>`;

  /* ---------- views ---------- */
  function vList() {
    let L = EDS.filter(e => !e.past && edMatch(e) && (st.expected || !e.expectedRow));
    if (st.within) L = L.filter(e => e.start <= addDays(TODAY, st.within));
    if (st.near) L.sort((a, b) => a.start.localeCompare(b.start));
    if (!L.length) return empty("No upcoming meetings match these filters.");
    const cap = 120 * st.more, shown = L.slice(0, cap), groups = new Map();
    shown.forEach(e => { const k = e.start.slice(0, 7); if (!groups.has(k)) groups.set(k, []); groups.get(k).push(e); });
    let h = "";
    for (const [k, arr] of groups) { const d = D(k + "-01"); h += `<section class="month"><h2>${MONTH[d.getMonth()]} ${d.getFullYear()} <span>${arr.length}</span></h2><div class="list">${arr.map(e => evRow(e)).join("")}</div></section>`; }
    if (L.length > cap) h += `<button class="btn more" data-act="more">Show ${Math.min(120, L.length - cap)} more of ${L.length - cap} remaining</button>`;
    return h;
  }
  function vStudents() {
    const L = EDS.filter(e => e.student && !e.past && !e.expectedRow && edMatch(e));
    if (!L.length) return empty("No student or DNP project opportunities match these filters.");
    const projects = L.filter(e => e.student.category === "project");
    const meetings = L.filter(e => e.student.category !== "project");
    const deadlines = projects.filter(e => e.student.deadline && e.student.deadline >= TODAY).sort((a, b) => a.student.deadline.localeCompare(b.student.deadline));
    let h = `<div class="student-intro"><h2>Student opportunities and DNP project dissemination</h2><p>Organizer-documented student sessions, posters, project venues and registration. A meeting may welcome student work even when this year's submission window has closed. Open a record for its exact source and eligibility details.</p></div>`;
    if (deadlines.length) h += `<section class="student-deadlines"><h2>Student submissions ahead</h2><div class="student-deadline-list">${deadlines.map(e => `<button data-e="${esc(e.id)}"><b>${esc(md(e.student.deadline))}</b><span>${esc(e.student.kind)} · ${esc(e.s.name)}</span></button>`).join("")}</div></section>`;
    if (projects.length) h += `<section class="sec"><h2>DNP projects, posters and abstracts <span class="student-count">${projects.length}</span></h2><div class="list">${projects.map(e => evRow(e, true)).join("")}</div></section>`;
    if (meetings.length) h += `<section class="sec"><h2>Student meetings and pathways <span class="student-count">${meetings.length}</span></h2><div class="list">${meetings.map(e => evRow(e, true)).join("")}</div></section>`;
    return h;
  }
  function vCalendar() {
    const [y, m] = st.cal.split("-").map(Number);
    const first = new Date(y, m - 1, 1), start = new Date(first); start.setDate(1 - first.getDay());
    const M = EDS.filter(e => edMatch(e) && !e.expectedRow), byDay = new Map();
    const push = (k, v) => { if (!byDay.has(k)) byDay.set(k, []); byDay.get(k).push(v); };
    const mode = st.view;
    M.forEach(e => {
      const meeting = mode === "upcoming" || mode === "directory" || (mode === "past" && e.past);
      if (meeting && !(mode === "upcoming" && e.past)) {
        const from = e.start > iso(start) ? e.start : iso(start);
        const until = e.end < addDays(iso(start), 41) ? e.end : addDays(iso(start), 41);
        for (let day = from; day <= until; day = addDays(day, 1)) push(day, { e, dl: false, ongoing: day !== e.start });
      }
      if ((mode === "upcoming" || mode === "deadlines") && e.s.kind !== "observance") {
        if (e.c.closes) push(e.c.closes, { e, dl: true });
        if (mode === "deadlines" && e.c.opens) push(e.c.opens, { e, op: true });
      }
    });
    const expected = st.expected && mode !== "past" ? EDS.filter(e => e.expectedRow && edMatch(e) && e.start.slice(0, 7) === st.cal) : [];
    let cells = DOW.map(d => `<div class="dow">${d}</div>`).join("");
    for (let i = 0; i < 42; i++) {
      const d = new Date(start); d.setDate(start.getDate() + i);
      if (i >= 35 && d.getMonth() !== m - 1) break;
      const k = iso(d), items = (byDay.get(k) || []).sort((a, b) =>
        (a.e.s.name === "National APP Week" ? -10 : a.dl ? -5 : a.e.s.kind === "observance" ? -3 : 0) -
        (b.e.s.name === "National APP Week" ? -10 : b.dl ? -5 : b.e.s.kind === "observance" ? -3 : 0));
      cells += `<div class="cell${d.getMonth() !== m - 1 ? " out" : ""}${k === TODAY ? " today" : ""}"><span class="num">${d.getDate()}</span>
        ${items.map(({ e, dl, op, ongoing }, j) => { const daily = (e.daily || []).find(x => x.date === k); const label = e.s.name === "National APP Week" ? `<strong>National APP Week</strong>${daily ? `<small>${esc(daily.title)}</small>` : ""}` : (dl ? "Deadline: " : op ? "Opens: " : "") + esc(e.s.name); return `<button class="ce${dl ? " dl" : ""}${op ? " op" : ""}${ongoing ? " ongoing" : ""}${e.s.name === "National APP Week" ? " appweek" : ""}${e.past && !dl ? " was" : ""}${j >= 4 ? " extra" : ""}" style="--c:${colorOf(e.s)}" data-e="${e.id}" title="${esc((dl ? "Abstract deadline: " : op ? "Abstract call opens: " : ongoing ? "Continues: " : "") + e.s.name + (daily ? " · " + daily.title : "") + " — " + range(e))}">${label}</button>`; }).join("")}
        ${items.length > 4 ? `<button class="overflow" data-day="${k}" data-extra="${items.length - 4}" aria-expanded="false">+${items.length - 4} more</button>` : ""}</div>`;
    }
    const Y0 = +TODAY.slice(0, 4), years = []; for (let yy = Y0 - 3; yy <= DATA.horizon; yy++) years.push(yy);
    const title = { upcoming: "Meetings and abstract deadlines", deadlines: "Abstract calls: openings and deadlines", past: "Past meetings", directory: "Every edition on file" }[mode];
    return `<div class="calhead">
        <button class="btn" data-act="prevY" aria-label="Previous year">«</button><button class="btn" data-act="prev" aria-label="Previous month">‹</button>
        <h2>${MONTH[m - 1]} ${y}</h2>
        <button class="btn" data-act="next" aria-label="Next month">›</button><button class="btn" data-act="nextY" aria-label="Next year">»</button>
        <label class="sr" for="calM">Month</label><select id="calM" class="sel">${MONTH.map((n, i) => `<option value="${i + 1}" ${i + 1 === m ? "selected" : ""}>${n}</option>`).join("")}</select>
        <label class="sr" for="calY">Year</label><select id="calY" class="sel">${years.map(yy => `<option ${yy === y ? "selected" : ""}>${yy}</option>`).join("")}</select>
        <button class="btn" data-act="today">Today</button></div>
      <p class="fine">${esc(title)}</p>
      <div class="legend"><span><i style="--c:var(--np)"></i>NP</span><span><i style="--c:var(--pa)"></i>PA</span><span><i style="--c:var(--crna)"></i>CRNA</span><span><i style="--c:var(--caa)"></i>CAA</span><span><i style="--c:var(--cns)"></i>CNS</span><span><i style="--c:var(--cnm)"></i>CNM</span><span><i style="--c:var(--rnfa)"></i>NP-RNFA</span><span><i style="--c:var(--multi)"></i>Multidisciplinary</span><span><i style="--c:var(--nursing)"></i>Nursing</span><span><i style="--c:var(--obs)"></i>Celebration</span>${mode === "upcoming" || mode === "deadlines" ? `<span class="dlkey">Red = abstract deadline</span>` : ""}</div>
      ${expected.length ? `<div class="expectedrow"><b>Expected this month, no date posted yet:</b> ${expected.map(e => `<button class="chip" data-e="${e.id}">${esc(e.s.name)}</button>`).join("")}</div>` : ""}
      <div class="calwrap"><div class="cal" role="grid" aria-label="${MONTH[m - 1]} ${y}">${cells}</div></div>`;
  }
  function vPast() {
    const L = EDS.filter(e => e.past && !e.expectedRow && edMatch(e)).sort((a, b) => b.start.localeCompare(a.start));
    if (!L.length) return empty("No past meetings match these filters.");
    const by = new Map();
    L.forEach(e => { const y = e.start.slice(0, 4); if (!by.has(y)) by.set(y, []); by.get(y).push(e); });
    let h = `<p class="fine">Past editions stay on the Runway permanently. Open any meeting for its full history and the organizer's own archive of programs, abstracts and recordings.</p>`;
    for (const [y, arr] of by) h += `<section class="yr"><h2>${y} <span>${arr.length} meeting${arr.length === 1 ? "" : "s"}</span></h2><div class="list">${arr.map(e => evRow(e)).join("")}</div></section>`;
    return h;
  }
  function vDeadlines() {
    const L = EDS.filter(e => !e.expectedRow && !e.past && e.s.kind !== "observance" && edMatch(e));
    const open = L.filter(e => ["open", "urgent"].includes(e.c.k)).sort((a, b) => (a.c.closes || "9999").localeCompare(b.c.closes || "9999"));
    const soon = L.filter(e => e.c.k === "soon").sort((a, b) => (a.c.opens || "9999").localeCompare(b.c.opens || "9999"));
    const row = (e, big, small, u) => `<div class="dlrow" data-e="${e.id}" tabindex="0" role="button">
        <div class="count${u ? " u" : ""}">${esc(big)}<small>${esc(small)}</small></div>
        <div class="body"><div class="title">${esc(e.s.name)}</div><div class="org">${esc(e.s.org_display || e.s.org)} · meeting ${esc(range(e))}</div><div class="meta">${esc((e.call && e.call.text) || "")}</div></div>
        <div class="side">${vBadge(e, true)}</div></div>`;
    let h = `<section class="sec"><h2>Open now · ${open.length}</h2><div class="list">`;
    h += open.length ? open.map(e => e.c.today ? row(e, "Today", "organizer's cut-off time applies", true)
      : e.c.closes ? row(e, e.c.n, e.c.n === 1 ? "day left" : "days left", e.c.n <= 14)
      : row(e, "Listed", "no closing date posted")).join("") : `<div class="empty">No open calls match these filters.</div>`;
    h += `</div></section><section class="sec"><h2>Opening soon · ${soon.length}</h2><div class="list">`;
    h += soon.length ? soon.map(e => row(e, e.c.opens ? md(e.c.opens) : "Soon", "opens")).join("") : `<div class="empty">Nothing announced as opening soon.</div>`;
    return h + `</div></section><p class="fine">Deadlines are shown as each organizer publishes them. A deadline closing today shows the day only: the cut-off hour and time zone are the organizer's, so open their page before you submit. Calls with no closing date are shown as listed, not as open.</p>`;
  }
  function directorySeries() {
    const editionFilters = st.where || st.area || st.near || st.openOnly;
    return DATA.series.filter(s => seriesMatch(s) &&
      (!st.q || (s.name + " " + (s.org_display || s.org) + " " + s.org + " " + (s.specialty || []).join(" ")).toLowerCase().includes(st.q.toLowerCase())) &&
      (!editionFilters || EDS.some(e => e.series === s.id && edMatch(e) && (st.expected || !e.expectedRow))));
  }
  function vDirectory() {
    const S = directorySeries();
    if (!S.length) return empty("No meetings match these filters.");
    const eds = new Map();
    EDS.forEach(e => { if (!eds.has(e.series)) eds.set(e.series, []); eds.get(e.series).push(e); });
    const letters = [...new Set(S.map(s => s.name[0].toUpperCase()))];
    let h = `<nav class="alpha" aria-label="Jump to letter">${letters.map(l => `<a href="#" data-letter="${esc(l)}">${esc(l)}</a>`).join("")}</nav><div class="dir">`, cur = "";
    S.forEach(s => {
      const L = (eds.get(s.id) || []).sort((a, b) => a.start.localeCompare(b.start));
      const next = L.find(e => !e.past && !e.expectedRow && verMatch(e));
      const hidden = !next && L.some(e => !e.past && !e.expectedRow);
      const anchor = s.name[0].toUpperCase() !== cur ? (cur = s.name[0].toUpperCase(), ` id="letter-${esc(cur)}"`) : "";
      h += `<button class="srs"${anchor} data-s="${esc(s.id)}"><span class="title">${esc(s.name)}</span><span class="org">${esc(s.org_display || s.org)}</span>
        <span class="badges">${profTags(s)}${(s.specialty || []).slice(0, 2).map(x => `<span class="tag">${esc(x)}</span>`).join("")}</span>
        <span class="meta">${next ? "Next: " + esc(range(next)) : hidden ? "Next date awaiting a source check" : esc(s.status_note || "Next date not posted")}${s.archive_url ? " · past-meetings archive" : ""}</span>
        <span class="hist">${L.filter(e => !e.expectedRow).map(e => `<span class="${e.past ? "" : "fut"}" title="${esc(range(e))}">${e.start.slice(0, 4)}</span>`).join("")}</span></button>`;
    });
    return h + "</div>";
  }

  function spotlight() {
    const el = $("#spotlight");
    const current = EDS.filter(e => e.s.kind === "observance" && !e.expectedRow && e.start <= TODAY && e.end >= TODAY && ["verified", "rule"].includes(e.verify.state))
      .sort((a, b) => (a.s.name === "National APP Week" ? -1 : 0) - (b.s.name === "National APP Week" ? -1 : 0))[0];
    if (!current) { el.hidden = true; return; }
    el.hidden = false;
    el.innerHTML = `<div class="live-ribbon"><span class="live-flag">${current.s.name === "National APP Week" ? `OUR WEEK · DAY ${daysBetween(current.start, TODAY) + 1} OF ${daysBetween(current.start, current.end) + 1}` : "HAPPENING NOW"}</span><strong>${esc(current.s.name)}</strong><span class="live-dates">${esc(range(current))} · through ${esc(MON[D(current.end).getMonth()] + " " + D(current.end).getDate())}</span><button class="live-source" data-e="${esc(current.id)}">View official source and details ↗</button></div>`;
  }

  /* ---------- controls ---------- */
  const chipRow = (key, list) => list.map(([v, l]) => `<button class="chip${v ? "" : " all"}" data-f="${key}" data-v="${esc(v)}" aria-pressed="${st[key] === v}"${key === "prof" && v === "AGACNP" ? ' title="Curated adult acute care topic relevance; organizer eligibility and intended audience may vary."' : ""}>${key === "prof" && v ? `<span class="dot" style="--c:var(${PROF_COLOR[v]})"></span>` : ""}${esc(l)}</button>`).join("");
  function controls() {
    $("#tabs").innerHTML = TABS.map(([v, l]) => `<button id="tab-${v}" role="tab" aria-controls="view" aria-selected="${st.view === v}" tabindex="${st.view === v ? 0 : -1}" data-view="${v}">${esc(l)}</button>`).join("");
    $("#view").setAttribute("aria-labelledby", "tab-" + st.view);
    $("#quickprof").innerHTML = `<span class="flabel">Profession</span>${chipRow("prof", PROF_CHIPS)}`;
    $("#viewtools").innerHTML = `${st.view === "students" ? "" : `<div class="seg" role="group" aria-label="Display">
        <button data-display="list" aria-pressed="${st.display === "list"}">${ICON.list}List</button>
        <button data-display="calendar" aria-pressed="${st.display === "calendar"}">${ICON.cal}Calendar</button></div>`}
      <label class="switch"><input type="checkbox" id="verOnly" ${st.verifiedOnly ? "checked" : ""}><span class="track" aria-hidden="true"></span>Source checked dates</label>
      <button class="linkbtn" data-act="clear">Clear all</button>`;
    $("#geoquick").innerHTML = `<span class="flabel">Location</span>
      <button class="chip all" data-act="where-all" aria-pressed="${!st.where && !st.area && !st.near}">Anywhere</button>
      <button class="chip" data-act="where-online" aria-pressed="${st.where === "online"}">Online</button>
      <label class="geo-label" for="area">Continent / country / US region</label>
      <select id="area" class="sel"><option value="">All regions</option>
        <optgroup label="Continent">${CONTINENTS.map(c => `<option value="c:${c}" ${st.area === "c:" + c ? "selected" : ""}>${c}</option>`).join("")}</optgroup>
        <optgroup label="Country">${COUNTRIES.map(c => `<option value="n:${esc(c)}" ${st.area === "n:" + c ? "selected" : ""}>${esc(c)}</option>`).join("")}</optgroup>
        <optgroup label="United States">${US_REGIONS.map(r => `<option value="r:${r}" ${st.area === "r:" + r ? "selected" : ""}>US ${r}</option>`).join("")}</optgroup></select>
      <span class="geo-divider" aria-hidden="true"></span>
      <label class="geo-label" for="nearq">Near ZIP / city</label><input id="nearq" list="citylist" placeholder="US ZIP or city" value="${esc(st.nearQ)}" autocomplete="off" inputmode="search"><datalist id="citylist"></datalist>
      <label class="geo-label" for="radius">within</label><select id="radius" class="sel">${[25, 50, 100, 250, 500, 1000, 2000].map(r => `<option value="${r}" ${st.radius === r ? "selected" : ""}>${r} miles</option>`).join("")}</select>
      ${st.nearQ && !st.near ? `<span class="nearmsg">No match for “${esc(st.nearQ)}”</span>` : st.near ? `<span class="nearmsg">${esc(st.near.label)}</span>` : ""}`;
    $("#filters").innerHTML = `
      <div class="fgroup"><span class="flabel">Focus</span>${chipRow("focus", FOCUS_CHIPS)}</div>
      <div class="fgroup"><span class="flabel">Type</span>${chipRow("kind", KIND_CHIPS)}</div>
      <div class="fgroup"><label class="flabel" for="spec">Specialty</label><select id="spec" class="sel"><option value="">All specialties</option>${SPECS.map(s => `<option ${s === st.spec ? "selected" : ""}>${esc(s)}</option>`).join("")}</select>
        <label class="toggle"><input type="checkbox" id="openOnly" ${st.openOnly ? "checked" : ""}> Abstract call open</label>
        <label class="toggle"><input type="checkbox" id="exp" ${st.expected ? "checked" : ""}> Show expected dates through ${DATA.horizon}</label></div>`;
    $("#filters").classList.toggle("open", filtersOpen);
    $("#geoquick").classList.toggle("open", filtersOpen);
    $("#fbtn").setAttribute("aria-expanded", String(filtersOpen));
    $("#q").value = st.q;
  }
  const activeCount = () => [st.prof, st.focus, st.kind, st.where, st.area, st.near, st.spec, st.openOnly, st.expected, st.q, st.within].filter(Boolean).length;

  /* ---------- render ---------- */
  function render(keepFocus) {
    const active = document.activeElement;
    const f = keepFocus && active && active.id;
    const replaced = active && active.closest && active.closest("#tabs,#quickprof,#geoquick,#filters,#viewtools");
    const restore = replaced ? { id: active.id, view: active.dataset.view, display: active.dataset.display, filter: active.dataset.f, value: active.dataset.v } : null;
    spotlight(); controls();
    const v = st.view === "students" ? vStudents : st.display === "calendar" ? vCalendar : { upcoming: vList, deadlines: vDeadlines, past: vPast, directory: vDirectory }[st.view];
    $("#view").innerHTML = v();
    let summary;
    if (st.view === "directory") {
      const n = directorySeries().length;
      summary = `${n} of ${DATA.series.length} meeting series`;
    } else if (st.view === "students") {
      const n = EDS.filter(e => e.student && !e.past && !e.expectedRow && edMatch(e)).length;
      summary = `${n} student and DNP project opportunit${n === 1 ? "y" : "ies"}`;
    } else if (st.view === "past") {
      const n = EDS.filter(e => e.past && !e.expectedRow && edMatch(e)).length;
      summary = `${n} past edition${n === 1 ? "" : "s"}`;
    } else if (st.view === "deadlines") {
      const n = EDS.filter(e => !e.expectedRow && !e.past && e.s.kind !== "observance" && edMatch(e) && ["open", "urgent", "soon"].includes(e.c.k)).length;
      summary = `${n} open or upcoming abstract call${n === 1 ? "" : "s"}`;
    } else {
      const n = EDS.filter(e => !e.past && !e.expectedRow && edMatch(e) && (!st.within || e.start <= addDays(TODAY, st.within))).length;
      summary = `${n} upcoming meeting${n === 1 ? "" : "s"}`;
    }
    const applied = [];
    if (st.prof) applied.push("Role: " + (st.prof === "AGACNP" ? "AGACNP (curated topic fit)" : PLABEL[st.prof] || st.prof));
    if (st.area) applied.push((st.area.startsWith("n:") ? "Country: " : st.area.startsWith("c:") ? "Continent: " : "US region: ") + st.area.slice(2));
    if (st.where === "online") applied.push("Location: online");
    if (st.near) applied.push(`Within ${st.radius} miles of ${st.near.label}`);
    if (st.spec) applied.push("Specialty: " + st.spec);
    if (st.q) applied.push("Search: " + st.q);
    if (st.openOnly) applied.push(st.view === "students" ? "Student submissions open" : "Abstract call open");
    const stamp = DATA && DATA.built ? stampET(DATA.built).replace(/^Data snapshot /, "") : "";
    $("#summary").innerHTML = esc(summary + (applied.length ? " · " + applied.join(" · ") : ""))
      + (st.verifiedOnly && st.view !== "directory" ? ` · <span class="okstamp">source checked ${esc(stamp)}</span>` : "");
    $("#fbtn").textContent = "Filters" + (activeCount() ? " (" + activeCount() + ")" : "");
    writeHash();
    if (f && document.getElementById(f)) { const el = document.getElementById(f); el.focus(); if (el.setSelectionRange && el.value) el.setSelectionRange(el.value.length, el.value.length); }
    else if (restore) {
      const el = (restore.id && document.getElementById(restore.id)) ||
        [...document.querySelectorAll("#tabs button,#quickprof button,#geoquick button,#filters button,#viewtools button")].find(x =>
          (restore.view && x.dataset.view === restore.view) ||
          (restore.display && x.dataset.display === restore.display) ||
          (restore.filter && x.dataset.f === restore.filter && x.dataset.v === restore.value));
      if (el) el.focus({ preventScroll: true });
    }
  }

  /* ---------- near: ZIP or city ---------- */
  async function zipLookup(z) {
    const k = z.slice(0, 3);
    if (window.RUNWAY_ZIP) return window.RUNWAY_ZIP[z] || null;
    try { const r = await fetch("geo/zip/" + k + ".json"); if (!r.ok) return null; const j = await r.json(); return j[z] || null; } catch (e) { return null; }
  }
  async function cities() {
    if (CITIES) return CITIES;
    let base = window.RUNWAY_CITIES;
    if (!base) { try { const r = await fetch("geo/cities.json"); base = await r.json(); } catch (e) { base = []; } }
    const seen = new Set(base.map(c => (c[0] + "|" + c[1]).toLowerCase()));
    const venueCities = EDS.filter(e => e.geo && e.geo.place && e.geo.country && e.geo.lat != null)
      .map(e => [e.geo.place, e.geo.country, e.geo.lat, e.geo.lon]);
    for (const c of venueCities) { const key = (c[0] + "|" + c[1]).toLowerCase(); if (!seen.has(key)) { base.push(c); seen.add(key); } }
    CITIES = base;
    return CITIES;
  }
  async function resolveNear() {
    const q = st.nearQ.trim();
    st.near = null;
    if (!q) return;
    if (/^\d{5}$/.test(q)) { const ll = await zipLookup(q); if (ll) st.near = { lat: ll[0], lon: ll[1], label: "ZIP " + q }; return; }
    const C = await cities(), ql = q.toLowerCase().replace(/\s*,\s*/g, ", ");
    const hit = C.find(c => (c[0] + ", " + c[1]).toLowerCase() === ql) || C.find(c => c[0].toLowerCase() === ql.split(",")[0].trim()) || C.find(c => c[0].toLowerCase().startsWith(ql));
    if (hit) st.near = { lat: hit[2], lon: hit[3], label: hit[0] + ", " + hit[1] };
  }
  async function fillCityList(q) {
    if (!q || /^\d/.test(q)) { $("#citylist").innerHTML = ""; return; }
    const C = await cities(), ql = q.toLowerCase();
    $("#citylist").innerHTML = C.filter(c => c[0].toLowerCase().startsWith(ql)).slice(0, 12).map(c => `<option value="${esc(c[0] + ", " + c[1])}">`).join("");
  }

  /* ---------- detail dialog ---------- */
  const byId = id => EDS.find(e => e.id === id);
  const host = u => { try { return new URL(u).hostname.replace(/^www\./, ""); } catch (e) { return u; } };
  function openDetail(e) {
    const s = e.s, v = e.verify || {};
    $("#dlg").dataset.cur = e.id;
    const L = EDS.filter(x => x.series === s.id).sort((a, b) => a.start.localeCompare(b.start));
    const Y0 = +TODAY.slice(0, 4), older = L.filter(x => +x.start.slice(0, 4) < Y0 - 3 && !x.expectedRow).reverse();
    const fix = REPO ? `${REPO}/issues/new?template=fix.yml&title=${encodeURIComponent("Fix: " + s.name + " " + e.start.slice(0, 4))}` : "";
    const li = x => `<li class="${x.id === e.id ? "cur" : ""}"><span class="y">${esc(range(x))}</span><span>${esc(x.location || (x.expectedRow ? "Expected; not yet announced" : ""))}${x.detail_url ? ` · <a href="${esc(x.detail_url)}" target="_blank" rel="noopener noreferrer">Program & materials</a>` : ""}</span>${vBadge(x)}</li>`;
    $("#dlg").innerHTML = `<div class="dlg"><button class="x" data-act="close" aria-label="Close">×</button>
      <header><p class="eyebrow">${esc(s.org_display || s.org)}</p><h3>${esc(s.name)}</h3><div class="badges">${profTags(s)}${(s.specialty || []).map(x => `<span class="tag">${esc(x)}</span>`).join("")}</div></header>
      <dl class="kv">
        <dt>When</dt><dd><b>${esc(range(e))}</b> ${vBadge(e)}</dd>
        ${e.location ? `<dt>Where</dt><dd>${esc(e.location)}${e.format && e.format !== "in person" ? " · " + esc(e.format) : ""}</dd>` : ""}
        ${e.theme ? `<dt>Theme</dt><dd><i>${esc(e.theme)}</i></dd>` : ""}
        ${s.kind !== "observance" && !e.expectedRow && !e.past ? `<dt>Call for abstracts</dt><dd>${callPill(e)} ${esc((e.call && e.call.text) || "")}${e.call && e.call.url ? ` · <a href="${esc(e.call.url)}" target="_blank" rel="noopener noreferrer">Submission page</a>` : ""}</dd>` : ""}
        ${e.note ? `<dt>Note</dt><dd>${esc(e.note)}</dd>` : ""}
        ${e.student ? `<dt>Student & DNP opportunity</dt><dd><b>${esc(e.student.kind)}</b> · ${esc(e.student.detail)} <a href="${esc(e.student.url)}" target="_blank" rel="noopener noreferrer">Organizer's student details</a></dd>` : ""}
        ${s.recurrence ? `<dt>Recurs</dt><dd>${esc(s.recurrence)}</dd>` : ""}
        <dt>Focus</dt><dd>${(s.focus || []).map(a => esc(a[0].toUpperCase() + a.slice(1))).join(", ")} <span class="fine">(curator tags)</span></dd>
        ${s.np_pa_basis ? `<dt>Why it's here</dt><dd>${esc(s.np_pa_basis)}</dd>` : ""}
        <dt>${esc(e.start.slice(0, 4))} source</dt><dd>${e.source_url ? `<a href="${esc(e.source_url)}" target="_blank" rel="noopener noreferrer">${esc(host(e.source_url))} · ${esc(e.start.slice(0, 4))} organizer record</a>` : "—"} · ${v.last_verified ? esc((v.method === "manual" ? "reviewed by the curator " : "start checked ") + longDate(v.last_verified.slice(0, 10))) : "recorded " + esc(longDate(e.compiled || ""))}${e.link_dead ? ` · <span class="fine">the organizer has since removed this page (${esc(e.link_dead)}); the date above is what it said when recorded</span>` : ""}${v.why && v.state !== "verified" ? ` · <span class="fine">${esc(v.why)}</span>` : ""}${e.evidence_image ? ` · <a href="${esc(e.evidence_image)}" target="_blank" rel="noopener noreferrer">dates published in this image</a>` : ""}${e.source_language ? ` · <span class="fine">Original organizer source in ${esc(e.source_language)}; English navigation labels are curator translations where used.</span>` : ""}</dd>
      </dl>
      ${e.evidence && v.evidence_match !== false && ["verified", "archived", "announced", "rule"].includes(v.state)
        ? `<blockquote class="quote" title="${esc(e.evidence_auto ? "The sentence the date was found in at the last check." : "The wording recorded from the organizer's page.")}">“${esc(e.evidence)}”${e.evidence_auto ? ` <span class="fine">· found on the page at the last check</span>` : ""}</blockquote>` : ""}
      ${e.sessions && e.sessions.length ? `<div><p class="flabel">Sessions & courses</p><ul class="sessions">${e.sessions.map(x => `<li>${esc(x)}</li>`).join("")}</ul></div>` : ""}
      ${e.daily && e.daily.length ? `<div><p class="flabel">Daily program · organizer calendar</p><ul class="sessions">${e.daily.map(x => `<li><b>${esc(md(x.date))}</b> · ${esc(x.title)}</li>`).join("")}</ul></div>` : ""}
      <div><p class="flabel">Seven-year view · ${Y0 - 3}–${Y0 + 3}</p><ol class="timeline years">${yearRows(s, L)}</ol>
        ${older.length ? `<details class="older"><summary>Earlier editions (${older.length})</summary><ol class="timeline">${older.map(li).join("")}</ol></details>` : ""}
        <div class="archive">${s.archive_url ? `<a class="btn" href="${esc(s.archive_url)}" target="_blank" rel="noopener noreferrer">${ICON.archive}Organizer's past-meetings archive</a>` : ""}${s.proceedings_url ? `<a class="btn" href="${esc(s.proceedings_url)}" target="_blank" rel="noopener noreferrer">${ICON.ext}Abstracts & proceedings</a>` : ""}${!s.archive_url && !s.proceedings_url ? `<span class="fine">No organizer archive link found yet.</span>` : ""}</div></div>
      <div class="dlg-actions">
        ${!e.expectedRow && !e.past ? `<button class="btn primary" data-act="ics">${ICON.cal}Add to calendar</button>` : ""}
        ${e.source_url ? `<a class="btn" href="${esc(e.source_url)}" target="_blank" rel="noopener noreferrer">${ICON.ext}Organizer page</a>` : ""}
        <button class="btn" data-act="copy">${ICON.link}Copy link</button>
        ${fix ? `<a class="btn" href="${esc(fix)}" target="_blank" rel="noopener noreferrer">Suggest a fix</a>` : ""}
      </div>
      <p class="fine">Details change. Confirm on the organizer's page before registering, submitting or booking travel.</p></div>`;
    $("#dlg").dataset.e = e.id;
    if (!$("#dlg").open) $("#dlg").showModal();
    writeHash({ e: e.id });
  }
  function yearRows(s, L) {
    const Y0 = +TODAY.slice(0, 4), rows = [];
    for (let y = Y0 - 3; y <= Y0 + 3; y++) {
      const inY = L.filter(x => +x.start.slice(0, 4) === y);
      const dated = inY.filter(x => !x.expectedRow), exp = inY.filter(x => x.expectedRow);
      const tag = y < Y0 ? "past" : y === Y0 ? "now" : "next";
      if (dated.length) dated.forEach(x => rows.push(`<li class="${tag}${x.id === $("#dlg").dataset.cur ? " cur" : ""}"><span class="y">${esc(range(x))}</span><span>${esc(x.location || "")}${x.detail_url ? ` · <a href="${esc(x.detail_url)}" target="_blank" rel="noopener noreferrer">${y} program</a>` : ""}${x.source_url && x.source_url !== s.org_url ? ` · <a href="${esc(x.source_url)}" target="_blank" rel="noopener noreferrer">${y} organizer record</a>` : ""}</span>${vBadge(x)}</li>`));
      else if (exp.length) rows.push(`<li class="${tag} gap"><span class="y">${esc(range(exp[0]))}</span><span>Expected; not yet announced</span>${vBadge(exp[0])}</li>`);
      else if (y < Y0 || (y === Y0 && !L.some(x => +x.start.slice(0, 4) > y))) rows.push(`<li class="${tag} gap"><span class="y">${y}</span><span class="nodata">No data available; manual review pending</span><span></span></li>`);
      else rows.push(`<li class="${tag} gap"><span class="y">${y}</span><span class="nodata">Not yet announced</span><span></span></li>`);
    }
    return rows.join("");
  }
  function icsFor(e) {
    const s = e.s, stamp = new Date().toISOString().replace(/[-:]/g, "").slice(0, 15) + "Z";
    const x = t => String(t || "").replace(/\\/g, "\\\\").replace(/[;,]/g, m => "\\" + m).replace(/\n/g, "\\n");
    const L = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//APP Conference Runway//EN", "CALSCALE:GREGORIAN", "BEGIN:VEVENT", `UID:${e.id}@app-conference-runway`, `DTSTAMP:${stamp}`,
      `DTSTART;VALUE=DATE:${e.start.replace(/-/g, "")}`, `DTEND;VALUE=DATE:${addDays(e.end, 1).replace(/-/g, "")}`, `SUMMARY:${x(s.name)} (${x(s.org)})`, `LOCATION:${x(e.location)}`,
      `URL:${e.source_url || ""}`, `DESCRIPTION:${x("Confirm details on the organizer page. Listed on APP Conference Runway.")}`, "END:VEVENT"];
    if (e.c.closes && e.c.closes >= TODAY) L.push("BEGIN:VEVENT", `UID:${e.id}-call@app-conference-runway`, `DTSTAMP:${stamp}`, `DTSTART;VALUE=DATE:${e.c.closes.replace(/-/g, "")}`,
      `DTEND;VALUE=DATE:${addDays(e.c.closes, 1).replace(/-/g, "")}`, `SUMMARY:Abstract deadline: ${x(s.name)}`, "END:VEVENT");
    L.push("END:VCALENDAR");
    const encoder = new TextEncoder();
    const fold = line => {
      const chunks = []; let chunk = "", bytes = 0;
      for (const ch of line) {
        const width = encoder.encode(ch).length;
        if (bytes + width > 75) { chunks.push(chunk); chunk = " " + ch; bytes = 1 + width; }
        else { chunk += ch; bytes += width; }
      }
      return [...chunks, chunk].join("\r\n");
    };
    const a = document.createElement("a");
    const objectUrl = URL.createObjectURL(new Blob([L.map(fold).join("\r\n") + "\r\n"], { type: "text/calendar;charset=utf-8" }));
    a.href = objectUrl;
    a.download = s.name.replace(/[^A-Za-z0-9]+/g, "-").slice(0, 60) + "-" + e.start.slice(0, 4) + ".ics";
    document.body.appendChild(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(objectUrl), 30000);
    toast("Calendar file downloaded");
  }
  function toast(msg) { const t = document.createElement("div"); t.className = "toast"; t.setAttribute("role", "status"); t.textContent = msg; document.body.appendChild(t); setTimeout(() => t.remove(), 2400); }
  async function copy(text, msg) { try { await navigator.clipboard.writeText(text); toast(msg); } catch (e) { prompt("Copy this link:", text); } }

  /* ---------- events ---------- */
  function bind() {
    document.addEventListener("click", ev => {
      const t = ev.target.closest("[data-view],[data-display],[data-f],[data-act],[data-e],[data-s],[data-letter],[data-day]");
      if (!t) return;
      if (t.dataset.view) { st.view = t.dataset.view; if (st.view === "students") st.display = "list"; st.more = 1; render(); return; }
      if (t.dataset.display) { st.display = t.dataset.display; render(); return; }
      if (t.dataset.f) { st[t.dataset.f] = st[t.dataset.f] === t.dataset.v && t.dataset.v ? "" : t.dataset.v; st.more = 1; render(); return; }
      const act = t.dataset.act;
      if (act === "clear") { const keep = { view: st.view, display: st.display, cal: st.cal }; Object.assign(st, DEF(), keep); render(); return; }
      if (act === "share") {
        const note = `APP Conference Runway — conferences, abstract deadlines and celebration weeks for advanced practice providers worldwide, checked nightly against the organizers' own pages.\n${location.origin + location.pathname}\n(Not listed in search engines; pass it on to colleagues.)`;
        copy(note, "Note and link copied — paste it into an email or message.");
        return;
      }
      if (act === "showall") { st.verifiedOnly = false; render(); return; }
      if (act === "where-all") { st.where = ""; st.area = ""; st.near = null; st.nearQ = ""; render(); return; }
      if (act === "where-online") { st.where = st.where === "online" ? "" : "online"; st.area = ""; st.near = null; st.nearQ = ""; render(); return; }
      if (act === "more") { st.more++; render(); return; }
      if (act === "prev" || act === "next") { const [y, m] = st.cal.split("-").map(Number); st.cal = iso(new Date(y, m - 1 + (act === "next" ? 1 : -1), 1)).slice(0, 7); render(); return; }
      if (act === "prevY" || act === "nextY") { const [y, m] = st.cal.split("-").map(Number); st.cal = (y + (act === "nextY" ? 1 : -1)) + "-" + String(m).padStart(2, "0"); render(); return; }
      if (act === "today") { st.cal = TODAY.slice(0, 7); render(); return; }
      if (act === "close") { $("#dlg").close(); return; }
      if (act === "ics") { icsFor(byId($("#dlg").dataset.e)); return; }
      if (act === "copy") { copy(location.href, "Link copied"); return; }
      if (act === "copyview") { copy(location.href, "Link to this view copied"); return; }
      if (act === "filters") { filtersOpen = !filtersOpen; $("#filters").classList.toggle("open", filtersOpen); $("#geoquick").classList.toggle("open", filtersOpen); t.setAttribute("aria-expanded", String(filtersOpen)); return; }
      if (t.dataset.letter) { ev.preventDefault(); const el = document.getElementById("letter-" + t.dataset.letter); if (el) window.scrollTo({ top: el.getBoundingClientRect().top + scrollY - 170 }); return; }
      if (t.dataset.day) {
        const cell = t.closest(".cell"), expanded = cell.classList.toggle("expanded");
        t.setAttribute("aria-expanded", String(expanded));
        t.textContent = expanded ? "Show fewer" : `+${t.dataset.extra} more`;
        return;
      }
      if (t.dataset.s) { const L = EDS.filter(e => e.series === t.dataset.s).sort((a, b) => a.start.localeCompare(b.start)); const pick = L.find(e => !e.past && !e.expectedRow) || [...L].reverse().find(e => !e.expectedRow) || L[0]; if (pick) openDetail(pick); return; }
      if (t.dataset.e) { const e = byId(t.dataset.e); if (e) openDetail(e); }
    });
    document.addEventListener("keydown", ev => { if ((ev.key === "Enter" || ev.key === " ") && ev.target.matches("[role=button][data-e]")) { ev.preventDefault(); ev.target.click(); } });
    $("#tabs").addEventListener("keydown", ev => {
      if (!ev.target.matches('[role="tab"]')) return;
      const i = TABS.findIndex(([v]) => v === ev.target.dataset.view);
      const next = ev.key === "ArrowRight" ? (i + 1) % TABS.length : ev.key === "ArrowLeft" ? (i + TABS.length - 1) % TABS.length : ev.key === "Home" ? 0 : ev.key === "End" ? TABS.length - 1 : -1;
      if (next < 0) return;
      ev.preventDefault(); st.view = TABS[next][0]; if (st.view === "students") st.display = "list"; st.more = 1; render();
      $("#tab-" + st.view).focus();
    });
    document.addEventListener("change", async ev => {
      const id = ev.target.id;
      if (id === "spec") st.spec = ev.target.value;
      if (id === "openOnly") st.openOnly = ev.target.checked;
      if (id === "exp") { st.expected = ev.target.checked; if (st.expected) st.verifiedOnly = false; }
      if (id === "verOnly") { st.verifiedOnly = ev.target.checked; if (st.verifiedOnly) st.expected = false; }
      if (id === "area") { st.area = ev.target.value; st.where = ""; }
      if (id === "radius") st.radius = +ev.target.value;
      if (id === "calY" || id === "calM") { st.cal = $("#calY").value + "-" + String($("#calM").value).padStart(2, "0"); render(); return; }
      if (id === "nearq") { st.nearQ = ev.target.value.trim(); st.where = ""; await resolveNear(); }
      if (["spec", "openOnly", "exp", "verOnly", "area", "radius", "nearq"].includes(id)) { st.more = 1; render(); }
    });
    document.addEventListener("input", ev => { if (ev.target.id === "nearq") fillCityList(ev.target.value); });
    document.addEventListener("keydown", async ev => { if (ev.target.id === "nearq" && ev.key === "Enter") { ev.preventDefault(); ev.target.blur(); } });
    let tmr; $("#q").addEventListener("input", ev => { clearTimeout(tmr); tmr = setTimeout(() => { st.q = ev.target.value.trim(); st.more = 1; render(true); }, 180); });
    $("#dlg").addEventListener("close", () => writeHash());
    window.addEventListener("hashchange", async () => { const e = readHash(); await resolveNear(); render(); if (e && byId(e)) openDetail(byId(e)); });
  }

  /* ---------- boot ---------- */
  async function boot() {
    const want = readHash();
    let d = window.RUNWAY_DATA;
    if (!d) {
      try { const r = await fetch("data/runway.json", { cache: "no-cache" }); d = await r.json(); }
      catch (e) { $("#view").innerHTML = `<div class="empty">The meeting data could not be loaded. Check your connection and refresh.</div>`; return; }
    }
    prep(d);
    $("#updated").textContent = "Data snapshot " + stampET(d.built);
    $("#updated").setAttribute("datetime", d.built);
    await resolveNear();
    bind(); wireSkip(); render();
    if (want && byId(want)) openDetail(byId(want));
  }
  boot();
})();
