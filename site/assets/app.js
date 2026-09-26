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
  const DOWL = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
  const iso = d => d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") + "-" + String(d.getDate()).padStart(2, "0");
  const D = s => new Date(s + "T12:00:00");
  const TODAY = iso(new Date());
  const addDays = (s, n) => { const d = D(s); d.setDate(d.getDate() + n); return iso(d); };
  const daysBetween = (a, b) => Math.round((D(b) - D(a)) / 864e5);
  const longDate = s => { const d = D(s); return MONTH[d.getMonth()] + " " + d.getDate() + ", " + d.getFullYear(); };
  const md = s => MON[D(s).getMonth()] + " " + D(s).getDate();
  // Phones held upright (below 700 px) get the Calendar as a day-by-day agenda; see calAgenda.
  const PHONE_CAL = window.matchMedia ? window.matchMedia("(max-width: 700px)") : { matches: false };
  function range(e) {
    if (e.month_only) { const d = D(e.start); return "~" + MON[d.getMonth()] + " " + d.getFullYear(); }
    const a = D(e.start), b = D(e.end || e.start), y = b.getFullYear();
    if (e.start === e.end || !e.end) return md(e.start) + ", " + a.getFullYear();
    if (a.getMonth() === b.getMonth() && a.getFullYear() === y) return md(e.start) + "–" + b.getDate() + ", " + y;
    return md(e.start) + (a.getFullYear() !== y ? ", " + a.getFullYear() : "") + " – " + md(e.end) + ", " + y;
  }
  function stampET(isoz) {
    try {
      return new Intl.DateTimeFormat("en-US", { timeZone: "America/New_York", month: "short", day: "numeric", year: "numeric", hour: "numeric", minute: "2-digit", second: "2-digit", timeZoneName: "short" }).format(new Date(isoz));
    } catch (e) { return isoz; }
  }
  const miles = (a, b, c, d) => { const R = 3958.8, r = x => x * Math.PI / 180; const h = Math.sin(r(c - a) / 2) ** 2 + Math.cos(r(a)) * Math.cos(r(c)) * Math.sin(r(d - b) / 2) ** 2; return 2 * R * Math.asin(Math.sqrt(h)); };
  const ICON = {
    check: '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M3 8.5l3 3 7-7" fill="none" stroke="currentColor" stroke-width="2"/></svg>',
    warn: '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M8 2l7 12H1z" fill="none" stroke="currentColor" stroke-width="1.6"/><path d="M8 6.5v3.5M8 11.8v.4" stroke="currentColor" stroke-width="1.6"/></svg>',
    dash: '<svg viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="6" fill="none" stroke="currentColor" stroke-width="1.6" stroke-dasharray="3 2"/></svg>',
    cal: '<svg viewBox="0 0 16 16" aria-hidden="true"><rect x="2" y="3" width="12" height="11" rx="1.5" fill="none" stroke="currentColor" stroke-width="1.5"/><path d="M2 6.5h12M5 1.5v3M11 1.5v3" stroke="currentColor" stroke-width="1.5"/></svg>',
    list: '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M2 4h12M2 8h12M2 12h12" stroke="currentColor" stroke-width="1.6"/></svg>',
    orbit: '<svg viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="2.2" fill="currentColor"/><circle cx="8" cy="8" r="5.8" fill="none" stroke="currentColor" stroke-width="1.3" stroke-dasharray="2.4 1.8"/></svg>',
    directory: '<svg viewBox="0 0 16 16" aria-hidden="true"><rect x="3" y="2" width="11" height="12" rx="1.5" fill="none" stroke="currentColor" stroke-width="1.4"/><path d="M1.5 4.5h3M1.5 8h3M1.5 11.5h3M7 5h4M7 8h4M7 11h3" fill="none" stroke="currentColor" stroke-width="1.4"/></svg>',
    ext: '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M9 2h5v5M14 2L7 9M12 9.5V14H2V4h4.5" fill="none" stroke="currentColor" stroke-width="1.5"/></svg>',
    link: '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M6.5 9.5l3-3M7 4.5l1.5-1.5a2.8 2.8 0 014 4L11 8.5M9 11.5L7.5 13a2.8 2.8 0 01-4-4L5 7.5" fill="none" stroke="currentColor" stroke-width="1.5"/></svg>',
    archive: '<svg viewBox="0 0 16 16" aria-hidden="true"><rect x="1.5" y="2.5" width="13" height="3" fill="none" stroke="currentColor" stroke-width="1.4"/><path d="M2.5 5.5v8h11v-8M6 8.5h4" fill="none" stroke="currentColor" stroke-width="1.4"/></svg>'
  };

  /* ---------- vocabulary ---------- */
  const PROF_COLOR = { STU: "--stu", DNP: "--dnp", NP: "--np", AGACNP: "--np", PA: "--pa", CRNA: "--crna", RNFA: "--rnfa", CNM: "--cnm", CNS: "--cns", Multidisciplinary: "--multi" };
  // Students & DNP projects is a Scope, not a Discipline: it is a kind of work, not a credential.
  const PROF_CHIPS = [["", "All APPs"], ["NP", "NP"], ["AGACNP", "AGACNP"], ["CRNA", "CRNA"], ["RNFA", "NP-RNFA"], ["CNS", "CNS"], ["CNM", "CNM"], ["PA", "PA"]];
  const AGACNP_TOPICS = new Set(["Acute Care", "Critical Care", "Emergency", "Emergency Medicine", "Hospital Medicine", "Cardiology", "Cardiothoracic Surgery", "Pulmonary", "Neuroscience", "Neurosurgery", "Trauma", "Resuscitation", "ECMO & Perfusion", "Surgery", "Vascular Surgery", "Infectious Diseases", "Toxicology", "Nephrology"]);
  const PLABEL = { RNFA: "NP-RNFA", STU: "Students & DNP projects", DNP: "Students & DNP projects" };
  // Students = organizer-documented opportunities for APP students; DNP Projects = venues for DNP project posters/abstracts.
  const APP_ROLES = ["NP", "AGACNP", "PA", "CRNA", "CNS", "CNM"];
  const stuOK = e => !!(e && e.student && (e.student.roles || []).some(r => APP_ROLES.includes(r)));
  const dnpOK = e => !!(e && e.student && e.student.category === "project");
  // SCOPE: whom and what a meeting serves. Multi-select; All clears it.
  const SCOPE_CHIPS = [["", "All"], ["clinical", "Clinical"], ["academic", "Academic"], ["research", "Research"], ["leadership", "Leadership"], ["students", "Students"]];
  const SCOPE_VALUES = SCOPE_CHIPS.map(([v]) => v).filter(Boolean);
  const SCOPE_TIPS = { students: "Organizer-documented opportunities for APP students (sessions, posters, abstracts, DNP projects) and meetings organized for students." };
  // FOCUS: which record type to show. One at a time; All shows every type.
  const FOCUS_CHIPS = [["", "All"], ["due", "Abstracts Due"], ["open", "Open Abstracts"], ["conferences", "Conferences"], ["celebrations", "Celebrations"]];
  const FOCUS_VALUES = FOCUS_CHIPS.map(([v]) => v).filter(Boolean);
  const FOCUS_LABEL = { due: "Abstracts due", open: "Open abstracts", conferences: "Conferences", celebrations: "Celebrations" };
  const FOCUS_TIPS = { due: "Records with an upcoming abstract deadline, ordered by due date.", open: "Abstract calls open now, ordered by due date.", conferences: "Conferences, symposiums, summits, congresses and courses; no celebration weeks.", celebrations: "APP celebration weeks and days, such as National APP Week." };
  const PROF_TIPS = { NP: "NP-relevant: NP, nursing, CNS, CNM and multidisciplinary meetings (curator judgment)", PA: "PA-relevant: PA and multidisciplinary meetings (curator judgment)",
    STU: "One combined view for APP students and DNP project dissemination.",
    AGACNP: "Curated adult acute care topic relevance; organizer eligibility and intended audience may vary." };
  // Meeting type refines Focus → Conferences; celebrations are a Focus value (older kind=observance links map there).
  const KIND_CHIPS = [["", "All"], ["conference", "Conferences"], ["symposium", "Symposiums"], ["summit", "Summits"], ["course", "Courses"]];
  const US_REGIONS = ["Northeast", "Midwest", "South", "West"];
  const CONTINENTS = ["North America", "South America", "Europe", "Asia", "Oceania", "Africa"];
  const VSTATE = {
    verified: ["Start found", "check"], conflict: ["Organizer dates conflict", "warn"], not_found: ["Needs review", "warn"], unreachable: ["Not re-checked", "dash"],
    unchecked: ["Not re-checked", "dash"], expected: ["Expected", "dash"], rule: ["Set by rule", "dash"],
    archived: ["Recorded when published", "check"], announced: ["Save the date", "check"]
  };

  /* ---------- state, mirrored in the URL ---------- */
  const DEF = () => ({ display: "orbit", orbitFrom: TODAY.slice(0, 7), orbitScope: "month", q: "", prof: [], scope: [], focus: "", kind: "", where: "", area: "", nearQ: "", near: null, radius: 50, spec: "", review: false, expected: false, within: 0, cal: TODAY.slice(0, 7), more: 1 });
  const st = DEF();
  let filtersOpen = false;
  const listDisclosure = new Map();
  let listDefaultOpen = true;
  let listContextMonth = "";
  let pendingListMonth = "";
  function readHash() {
    const h = new URLSearchParams(location.hash.slice(1));
    Object.assign(st, DEF());
    listContextMonth = "";
    pendingListMonth = "";
    const legacyView = h.get("view");
    if (["list", "calendar", "orbit", "directory"].includes(h.get("display"))) st.display = h.get("display");
    if (/^\d{4}-\d{2}$/.test(h.get("from") || "")) st.orbitFrom = h.get("from");
    ["q", "kind", "where", "area", "spec"].forEach(k => { if (h.get(k)) st[k] = h.get(k); });
    const requestedProf = (h.get("prof") || "").split(",").map(x => x === "DNP" ? "STU" : x);
    if (legacyView === "students") requestedProf.push("STU");
    const requestedSet = new Set(requestedProf);
    st.prof = PROF_CHIPS.map(([v]) => v).filter(v => v && requestedSet.has(v));
    if (legacyView === "students") st.display = "list";
    if (legacyView === "directory") st.display = "directory";
    // Orbit window scope is span=year. Older links used scope=year for the twelve-month Orbit.
    if (st.display === "orbit" && (h.get("span") === "year" || h.get("scope") === "year")) st.orbitScope = "year";
    // Scope reads scope=…; older links carried the same values as focus=….
    const scopeIn = [...(h.get("scope") || "").split(","), ...(h.get("focus") || "").split(",")].map(x => x === "executive" ? "leadership" : x === "student" ? "students" : x);
    // Students & DNP projects is Scope → Students; older prof=STU, prof=DNP and view=students links open it there.
    if (requestedSet.has("STU")) scopeIn.push("students");
    st.scope = SCOPE_VALUES.filter(v => scopeIn.includes(v));
    st.focus = (h.get("focus") || "").split(",").find(x => FOCUS_VALUES.includes(x)) || "";
    if (!st.focus && st.kind === "observance") { st.focus = "celebrations"; st.kind = ""; }   // older kind=observance links
    if (!st.focus && h.get("open") === "1") st.focus = "open";                              // older open=1 links
    if (!st.focus && legacyView === "deadlines") st.focus = "due";                          // older view=deadlines links
    if (h.get("near")) st.nearQ = h.get("near");
    if (+h.get("r")) st.radius = +h.get("r");
    st.review = h.get("review") === "1"; st.expected = h.get("exp") === "1";
    st.within = +(h.get("within") || 0);
    if (/^\d{4}-\d{2}$/.test(h.get("cal") || "")) {
      st.cal = h.get("cal");
      if (st.display === "list") listContextMonth = pendingListMonth = st.cal;
    }
    if (st.display === "orbit") orbitClamp();
    return h.get("e");
  }
  function writeHash(extra) {
    const h = new URLSearchParams();
    if (st.display !== "orbit") h.set("display", st.display);
    if (st.display === "orbit" && st.orbitFrom !== TODAY.slice(0, 7)) h.set("from", st.orbitFrom);
    ["q", "kind", "where", "area", "spec"].forEach(k => st[k] && h.set(k, st[k]));
    if (st.prof.length) h.set("prof", PROF_CHIPS.map(([v]) => v).filter(v => v && st.prof.includes(v)).join(","));
    if (st.scope.length) h.set("scope", SCOPE_VALUES.filter(v => st.scope.includes(v)).join(","));
    if (st.focus) h.set("focus", st.focus);
    if (st.near) { h.set("near", st.nearQ); h.set("r", st.radius); }
    if (st.expected) h.set("exp", "1");
    if (st.review) h.set("review", "1");
    if (st.within) h.set("within", st.within);
    if (st.display === "orbit" && st.orbitScope === "year") h.set("span", "year");
    if (st.display === "list" && listContextMonth) h.set("cal", st.cal);
    else if (["calendar", "orbit"].includes(st.display) && st.cal !== TODAY.slice(0, 7)) h.set("cal", st.cal);
    if (extra) Object.entries(extra).forEach(([k, v]) => h.set(k, v));
    const s = h.toString();
    history.replaceState(null, "", s ? "#" + s : location.pathname + location.search);
  }

  /* ---------- data ---------- */
  let DATA, SERIES, EDS, SPECS, COUNTRIES = [], CITIES = null;
  // Red team F10: when the organizer publishes a cut-off time (call.due_time "HH:MM" in call.tz, an IANA zone), the
  // call closes at that instant, wherever the visitor is. cutoffAt turns the organizer's wall-clock time into an instant.
  function cutoffAt(date, time, tz) {
    try {
      const [Y, M, Dd] = date.split("-").map(Number), [h, mi] = time.split(":").map(Number), want = Date.UTC(Y, M - 1, Dd, h, mi);
      const fmt = new Intl.DateTimeFormat("en-US", { timeZone: tz, hourCycle: "h23", year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" });
      let t = want;
      for (let i = 0; i < 3; i++) {
        const p = Object.fromEntries(fmt.formatToParts(new Date(t)).map(x => [x.type, x.value]));
        t += want - Date.UTC(+p.year, +p.month - 1, +p.day, +p.hour % 24, +p.minute);
      }
      return Number.isFinite(t) ? t : null;
    } catch (err) { return null; }
  }
  const cutoffLabel = (t, tz) => { try { return new Intl.DateTimeFormat("en-US", { timeZone: tz, hour: "numeric", minute: "2-digit", timeZoneName: "short" }).format(new Date(t)); } catch (err) { return ""; } };
  function callOf(e) {
    const c = e.call || {}, closes = c.closes, opens = c.opens;
    const cut = closes && c.due_time && c.tz ? cutoffAt(closes, c.due_time, c.tz) : null;
    if (closes && closes < TODAY) return { k: "closed", label: "Closed " + md(closes) };
    if (opens && opens > TODAY) return { k: "soon", label: "Opens " + md(opens), opens };
    // "soon" means not yet open. Without a published opening date a "soon" call stays upcoming; it never
    // turns open just because its due date lies ahead.
    if (closes && (c.status === "open" || (opens && opens <= TODAY))) {
      if (cut && Date.now() > cut) return { k: "closed", label: "Closed " + md(closes) + ", " + cutoffLabel(cut, c.tz) };
      const n = daysBetween(TODAY, closes);
      // Without a published cut-off time the last day is never called "open now".
      if (n <= 0) return cut
        ? { k: "urgent", label: "Closes today, " + cutoffLabel(cut, c.tz), closes, n: 0, today: true }
        : { k: "urgent", label: "Closes today · check the organizer's cut-off time", closes, n: 0, today: true };
      return { k: n <= 14 ? "urgent" : "open", label: "Closes " + md(closes), closes, n };
    }
    if (c.status === "open") return { k: "open", label: "Call listed · confirm with the organizer", n: null, undated: true };
    const short = (t, dflt) => t && t.length <= 30 ? t : dflt;
    if (c.status === "soon") return { k: "soon", label: short(c.text && c.text.split("·")[0].trim(), "Opening soon") };
    if (c.status === "closed") return { k: "closed", label: "Call closed" };
    if (c.status === "none") return { k: "none", label: short(c.text && c.text !== "—" ? c.text : "", "No call") };
    return { k: "tba", label: short(c.text, "Call not posted") };
  }
  // An abstract call as a span: from its opening day (or today, if already open with no published opening) to its due date.
  function callSpan(e) {
    if (e.s.kind === "observance") return null;
    const c = e.call || {}, to = c.closes;
    if (!to || !/^\d{4}-\d{2}-\d{2}$/.test(to)) return null;
    let from = c.opens && c.opens <= to ? c.opens : null;
    if (!from) from = ["open", "urgent"].includes(e.c.k) && TODAY < to ? TODAY : to;
    return { from, to };
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
    // Series-level filing only: CAA meetings are filed under CRNA for the Discipline filter (build.py applies
    // the same fold). This is a relevance mapping for filtering.
    // Organizer wording is never rewritten. A student opportunity keeps the organizer's own roles and words,
    // so AAAA's "CAA student posters" reads as the organizer published it.
    const focusOrder = ["clinical", "academic", "research", "leadership"];
    d.series.forEach(s => {
      s.professions = [...new Set((s.professions || []).map(p => p === "CAA" ? "CRNA" : p))];
      const text = [s.name, s.org_display, s.org, ...(s.specialty || [])].filter(Boolean).join(" ");
      const focus = new Set((s.focus || []).map(f => String(f).toLowerCase()).map(f => f === "executive" ? "leadership" : f));
      if (/research|scientific|science|scholar|evidence/i.test(text)) focus.add("research");
      if (/leader|leadership|executive|dean|management|policy|advocacy/i.test(text)) focus.add("leadership");
      s.studentTag = focus.has("student");   // a meeting organized for students (curator tag); feeds Scope → Students
      s.focus = focusOrder.filter(f => focus.has(f));
    });
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
    EDS.forEach(e => { if (stuOK(e)) e.s.hasStu = true; if (dnpOK(e)) e.s.hasDnp = true; });
    const upcoming = EDS.filter(e => !e.past && !e.expectedRow && e.verify.state !== "rule");
    const mapped = upcoming.filter(e => e.geo && e.geo.country);
    const countries = new Set(mapped.map(e => e.geo.country));
    COUNTRIES = [...countries].sort((a, b) => a.localeCompare(b));
    const continents = new Set(mapped.map(e => e.geo.continent));
    const coverage = $("#coverageCount");
    if (coverage) coverage.textContent = `Of ${upcoming.length} upcoming dated entries, ${mapped.length} have mapped locations in ${countries.size} countries across ${continents.size} continents.`;
    // A catch-all tag is a space-saver on a national meeting that
    // would otherwise list every subspecialty. It is not something a visitor filters by, so it stays
    // a badge and is kept out of the Specialty dropdown.
    const CATCH_ALL_SPEC = new Set(["Multispecialty", "Multidisciplinary", "Multi-specialty"]);
    SPECS = [...new Set(d.series.flatMap(s => s.specialty || []))].filter(x => !CATCH_ALL_SPEC.has(x)).sort();
  }

  /* ---------- matching ---------- */
  function agacnpFit(s) {
    if (s.name === "National APP Week") return true;
    const p = s.professions || [];
    if (!p.some(x => ["NP", "Multidisciplinary"].includes(x)) || (p.includes("CRNA") && !p.includes("NP") && !p.includes("Multidisciplinary"))) return false;
    return (s.specialty || []).some(x => AGACNP_TOPICS.has(x));
  }
  function profOptionMatch(s, prof) {
    const P = s.professions;
    switch (prof) {
      case "STU": return !!s.hasStu || !!s.hasDnp;
      case "DNP": return !!s.hasStu || !!s.hasDnp; // legacy shared links
      case "NP": return P.some(p => ["NP", "Multidisciplinary", "CNS", "CNM"].includes(p));
      case "AGACNP": return agacnpFit(s);
      case "PA": return P.some(p => ["PA", "Multidisciplinary"].includes(p));
      case "CRNA": return P.includes("CRNA");
      case "CNS": return P.includes("CNS");
      case "CNM": return P.includes("CNM");
      case "RNFA": return P.includes("RNFA") || !!s.rnfa_inferred;
    }
    return true;
  }
  function profMatch(s) {
    return !st.prof.length || st.prof.some(prof => profOptionMatch(s, prof));
  }
  function editionProfMatch(e) {
    if (!st.prof.length) return true;
    return st.prof.some(prof => prof === "STU"
      ? (e.expectedRow ? !!e.s.hasStu || !!e.s.hasDnp : stuOK(e) || dnpOK(e))
      : profOptionMatch(e.s, prof));
  }
  // Scope → Students is edition-level when an edition is given: this year's documented student or DNP
  // opportunity, or a meeting organized for students. Without an edition (Directory) any edition counts.
  function scopeOptionMatch(s, v, e) {
    if (v !== "students") return (s.focus || []).includes(v);
    if (s.studentTag) return true;
    if (!e || e.expectedRow) return !!s.hasStu || !!s.hasDnp;
    return stuOK(e) || dnpOK(e);
  }
  function seriesMatch(s, ignoreProf = false, e = null) {
    if (!ignoreProf && !profMatch(s)) return false;
    if (st.scope.length && !st.scope.some(v => scopeOptionMatch(s, v, e))) return false;
    if (st.kind && s.kind !== st.kind) return false;
    if (st.spec && !(s.specialty || []).includes(st.spec)) return false;
    return true;
  }
  // A list card carries the same vocabulary as the filter rows — its Scope tags and its Focus
  // (record type), the latter in that type's colour.
  const SCOPE_LABEL = Object.fromEntries(SCOPE_CHIPS.filter(([v]) => v));
  const scopeBadges = s => scopeTags(s).filter(t => SCOPE_LABEL[t])
    .map(t => badge("scope", t, SCOPE_LABEL[t], `Show every record in the ${SCOPE_LABEL[t]} scope`)).join("");
  function focusBadges(e) {
    const out = [];
    out.push(isCelebration(e)
      ? badge("focus", "celebrations", "Celebration", "Show celebration weeks and days", "focus obs")
      : badge("focus", "conferences", "Conference", "Show conferences, symposiums, summits and courses", "focus meet"));
    if (isOpenNow(e)) out.push(badge("focus", "open", "Open abstracts", "Show every abstract call open now", "focus open"));
    else if (hasUpcomingDeadline(e)) out.push(badge("focus", "due", "Abstracts due", "Show every upcoming abstract deadline", "focus due"));
    return out.join("");
  }
  const scopeTags = s => [...(s.focus || []), ...(s.studentTag || s.hasStu || s.hasDnp ? ["students"] : [])];
  /* ---------- Focus: one record type at a time ---------- */
  const isCelebration = e => e.s.kind === "observance";
  // An upcoming abstract deadline: a dated call that is open, closing soon or opening later.
  const hasUpcomingDeadline = e => !isCelebration(e) && !e.expectedRow && ["open", "urgent", "soon"].includes(e.c.k) && !!(e.call && e.call.closes) && e.call.closes >= TODAY;
  // An abstract call open today, with or without a published due date.
  const isOpenNow = e => !isCelebration(e) && !e.expectedRow && ["open", "urgent"].includes(e.c.k);
  // Whether the current Focus shows a record's own dates (a meeting or celebration), as opposed to only its abstract call.
  const recordFocus = e => !st.focus || (st.focus === "conferences" && !isCelebration(e)) || (st.focus === "celebrations" && isCelebration(e));
  function focusMatch(e) {
    switch (st.focus) {
      case "conferences": return !isCelebration(e);
      case "celebrations": return isCelebration(e);
      case "due": return hasUpcomingDeadline(e);
      case "open": return isOpenNow(e);
    }
    return true;
  }
  function formatClass(e) {
    const g = e.geo || {};
    const format = (e.format || "").toLowerCase();
    const remote = /virtual|online|webinar|remote|live\s*stream/.test(format);
    const onsite = /in[ -]?person|on[ -]?site/.test(format);
    if (/hybrid/.test(format) || (remote && onsite) || (g.online && onsite)) return "hybrid";
    if (g.online || remote) return "online";
    return "live";
  }
  function placeMatch(e) {
    const g = e.geo || {};
    if (st.where && st.where !== formatClass(e)) return false;
    if (st.area) {
      const [k, v] = [st.area.slice(0, 1), st.area.slice(2)];
      if (k === "r" && !(g.cc === "US" && g.region === v)) return false;
      if (k === "c" && g.continent !== v) return false;
      if (k === "n" && g.country !== v) return false;
    }
    if (st.near) {
      // A pin placed only at a state's or country's center is not a venue.
      // It is left out of distance results rather than given a mile count it cannot support.
      if (g.lat == null || g.precision === "state" || g.precision === "country") return false;
      if (miles(st.near.lat, st.near.lon, g.lat, g.lon) > st.radius) return false;
    }
    return true;
  }
  // An exception is any record whose current source check did not confirm it: not found, conflicting,
  // or unreadable without curator evidence on file.
  function isException(e) {
    const v = e.verify || { state: "unchecked" };
    if (["expected", "rule", "archived", "announced"].includes(v.state)) return false;
    // A verified record is verified: the nightly check found the start date, its year and a name word on
    // the organizer page. A stored quote that no longer matches the page is not flagged on its own: a reader
    // would have no reference point and nothing to act on.
    if (v.state === "verified") return false;
    return true;
  }
  function verMatch(e) { return !st.review || isException(e); }
  /* ---------- search synonyms ----------
     The corpus says "Cardiothoracic Surgery"; a clinician types "cardiac". Each query word also matches
     its clinical equivalents. Every expansion below points at wording that actually appears in this
     corpus — the map widens the question, it never invents a record. British and US spellings are
     paired in both directions. */
  const SYN = [
    ["cardiac|cardio|cardiology|cardiovascular|cardiothoracic|heart|ct surgery", ["cardio", "cardiac", "heart", "thoracic", "ecmo", "perfusion", "resuscitation"]],
    ["psych|psychiatry|psychiatric|mental health|behavioral|behavioural", ["psychiatr", "mental health", "behavioral", "psych"]],
    ["icu|intensive care|critical|crit care", ["critical care", "resuscitation", "ecmo", "acute care"]],
    ["er|ed|emergency|trauma", ["emergency", "trauma", "resuscitation"]],
    ["gi|gastro|gastroenterology|endoscopy|liver|hepatology", ["gastro", "endoscopy", "hepatology"]],
    ["renal|kidney|nephrology|dialysis", ["nephrology", "renal", "kidney"]],
    ["neuro|neurology|neuroscience|neurosurgery|stroke", ["neuro"]],
    ["ortho|orthopedic|orthopedics|orthopaedic|orthopaedics|musculoskeletal|msk", ["orthopaed", "orthoped", "musculoskeletal"]],
    ["ob|obgyn|ob-gyn|obstetric|obstetrics|gynecology|gynaecology|midwife|midwifery|maternal", ["women's health", "midwif", "obstetric", "neonatal"]],
    ["peds|pediatric|pediatrics|paediatric|paediatrics|child|neonatal|nicu", ["pediatric", "paediatric", "neonatal"]],
    ["onc|oncology|cancer|hematology|haematology|hem", ["oncology", "hematology", "haematology"]],
    ["lung|pulmonary|pulmonology|respiratory|thoracic", ["pulmonary", "thoracic", "respiratory"]],
    ["anesthesia|anaesthesia|anesthetist|anaesthetist|crna|nurse anesthesia", ["anesthes", "anaesthes", "crna", "perfusion"]],
    ["derm|dermatology|skin", ["dermatology"]],
    ["endocrine|endocrinology|diabetes|diabetic", ["endocrin", "diabetes"]],
    ["id|infectious|infection|antimicrobial", ["infectious", "infection"]],
    ["palliative|hospice|end of life", ["palliative", "hospice"]],
    ["wound|ostomy|continence|skin integrity", ["wound", "ostomy", "continence"]],
    ["geriatric|geriatrics|aging|ageing|older adult|gerontology", ["geriatric", "geronto", "aging"]],
    ["surgery|surgical|perioperative|periop|or nurse", ["surgery", "surgical", "perioperative", "rnfa"]],
    ["research|scholarship|evidence|ebp|scholarly", ["research", "scholarship", "evidence", "scholar"]],
    ["leadership|executive|management|administrator|director", ["leadership", "executive", "administrat"]],
    ["education|faculty|teaching|academic|curriculum", ["education", "academic", "faculty", "nursing scholarship"]],
    ["dnp|capstone|doctoral project|scholarly project", ["dnp", "doctoral", "capstone", "project"]],
    ["toxicology|overdose|poison", ["toxicology", "poison"]],
    ["transplant|vad|lvad", ["transplant", "ishlt"]],
    ["sleep", ["sleep"]],
    ["pain", ["pain"]],
    ["informatics|digital health|technology|ai", ["informatics", "digital health"]],
    ["primary care|family|ambulatory|outpatient", ["primary care", "family", "ambulatory"]],
    ["hospitalist|hospital medicine|inpatient", ["hospital medicine", "hospitalist"]],
    ["policy|advocacy|legislative|regulation", ["advocacy", "policy", "health policy"]]
  ].map(([pat, alts]) => [new RegExp("^(" + pat + ")$", "i"), alts]);
  // A query word matches when the record contains the word itself OR any of its clinical equivalents.
  // A short token is matched on a word boundary, never as a substring: "er" must not match
  // "conference" and "ob" must not match "October". Longer words keep plain substring behaviour,
  // which is what makes partial typing work.
  const boundary = (hay, w) => new RegExp("(^|[^a-z0-9])" + w.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + "([^a-z0-9]|$)", "i").test(hay);
  function wordHit(hay, w) {
    if (w.length <= 3 ? boundary(hay, w) : hay.includes(w)) return true;
    for (const [re, alts] of SYN) if (re.test(w)) { if (alts.some(a => hay.includes(a))) return true; }
    return false;
  }

  function edMatch(e) {
    if (!seriesMatch(e.s, true, e) || !editionProfMatch(e) || !placeMatch(e) || !verMatch(e)) return false;
    if (st.q && !st.q.toLowerCase().split(/\s+/).filter(Boolean).every(w => wordHit(e.hay, w))) return false;
    return true;
  }
  function orbitCallVisible(e) {
    return ["open", "urgent", "soon"].includes(e.c.k);
  }
  function orbitRecordMatch(e) {
    if (!edMatch(e) || (e.expectedRow && !st.expected)) return false;
    if (st.within && e.start > addDays(TODAY, st.within)) return false;
    return e.expectedRow ? st.expected : !e.past;
  }
  function orbitAnnualRecordMatch(e) {
    if (!edMatch(e) || (e.expectedRow && !st.expected)) return false;
    if (st.within && (e.past || e.start > addDays(TODAY, st.within))) return false;
    return e.expectedRow ? st.expected : true;
  }
  // Orbit categories: meetings (Focus → Conferences), abstracts due, open abstracts, celebrations. Focus shows one.
  const ORBIT_CAT_ORDER = ["meet", "due", "open", "obs"];
  const ORBIT_CAT_FOR = { conferences: "meet", due: "due", open: "open", celebrations: "obs" };
  const orbitCats = () => st.focus ? [ORBIT_CAT_FOR[st.focus]] : ORBIT_CAT_ORDER;
  const orbitCatRows = (m, c) => c === "meet" ? m.meetings : c === "obs" ? m.celebrations : c === "due" ? m.due : m.open;
  const byStart = (a, b) => a.start.localeCompare(b.start) || a.s.name.localeCompare(b.s.name);
  const byDue = (a, b) => a.call.closes.localeCompare(b.call.closes) || a.s.name.localeCompare(b.s.name);
  const byOpenDue = (a, b) => (a.call.closes || "9999").localeCompare(b.call.closes || "9999") || a.s.name.localeCompare(b.s.name);
  // One month of the ring, by category. Month scope shows upcoming calls only; the annual (center-label) scope shows every call in the window.
  function orbitMonthData(records, year, month, annual) {
    const key = `${year}-${String(month).padStart(2, "0")}`;
    const start = key + "-01", end = iso(new Date(year, month, 0));
    const dated = records.filter(e => e.start <= end && (e.end || e.start) >= start).sort(byStart);
    const due = records.filter(e => (annual || orbitCallVisible(e)) && e.call && e.call.closes && e.call.closes >= start && e.call.closes <= end).sort(byDue);
    const open = records.filter(e => {
      const c = e.call || {}, opens = c.opens || (c.status === "open" ? TODAY : null), closes = c.closes;
      if ((!annual && !orbitCallVisible(e)) || !opens) return false;
      if (!closes) return ["open", "urgent"].includes(e.c.k) && key === TODAY.slice(0, 7);
      // Under Focus All a call closing this month is listed once, under Abstracts Due. With Focus Open Abstracts
      // that column is the only one shown, so the call stays in it through its closing month.
      return opens <= end && closes >= start && (st.focus === "open" || !(closes >= start && closes <= end));
    }).sort(byOpenDue);
    return { key, meetings: dated.filter(e => !isCelebration(e)), celebrations: dated.filter(isCelebration), due, open };
  }
  function orbitMonthHas(records, year, month) {
    const m = orbitMonthData(records, year, month, false);
    return orbitCats().some(c => orbitCatRows(m, c).length > 0);
  }
  // The Orbit ring is a rolling window: twelve consecutive months starting at st.orbitFrom (the current month by default).
  // Every month carries its year (Sep ’26 … Aug ’27).
  function orbitWindow() {
    const [fy, fm] = st.orbitFrom.split("-").map(Number);
    return Array.from({ length: 12 }, (_, i) => {
      const d = new Date(fy, fm - 1 + i, 1), year = d.getFullYear(), month = d.getMonth() + 1;
      return { year, month, key: `${year}-${String(month).padStart(2, "0")}`, name: MONTH[month - 1] + " " + year, short: MON[month - 1] + " ’" + String(year).slice(2) };
    });
  }
  function orbitLabel() {
    const w = orbitWindow(), a = w[0], b = w[11];
    return a.year === b.year ? String(a.year) : `${a.year}–${String(b.year).slice(2)}`;
  }
  function orbitClamp() {
    const w = orbitWindow();
    if (!w.some(x => x.key === st.cal)) st.cal = w.some(x => x.key === TODAY.slice(0, 7)) ? TODAY.slice(0, 7) : w[0].key;
  }
  function revealFirstOrbitMatch() {
    if (st.display !== "orbit" || st.orbitScope === "year") return;
    const w = orbitWindow(), cur = w.find(x => x.key === st.cal) || w[0];
    const records = EDS.filter(orbitRecordMatch);
    if (orbitMonthHas(records, cur.year, cur.month)) return;
    const first = w.find(x => orbitMonthHas(records, x.year, x.month));
    if (first) st.cal = first.key;
  }

  /* ---------- pieces ---------- */
  const colorOf = s => s.kind === "observance" ? "var(--t-obs)" : "var(--t-meet)";   // colour = record type; disciplines are badges
  /* ---------- badges ----------
     Every badge on a record is a filter you can reach. A badge is a button only when the filter row
     above the list can actually represent it; a value with no control stays a plain tag rather than a
     click that quietly does nothing. Family → control: disc → Discipline chip, scope → Scope chip,
     focus → Focus chip, spec → the Specialty dropdown (107 values, 63 of them used once — far too many
     for a chip row, which is why it is a dropdown and stays one). */
  const PROF_CHIP_VALUES = new Set(PROF_CHIPS.map(([v]) => v).filter(Boolean));
  function badge(kind, value, label, title, cls) {
    const clickable = kind === "spec" ? SPECS.includes(value)
      : kind === "disc" ? PROF_CHIP_VALUES.has(value)
      : kind === "scope" ? !!SCOPE_LABEL[value]
      : kind === "focus";
    const tip = title || (clickable ? `Show every record tagged ${label}` : label);
    if (!clickable) return `<span class="tag ${cls || kind}" title="${esc(tip)}">${esc(label)}</span>`;
    return `<button type="button" class="tag ${cls || kind} tapfilter" data-badge="${esc(kind)}" data-val="${esc(value)}" title="${esc(tip)}">${esc(label)}</button>`;
  }
  const profTags = s => s.professions.map(p => badge("disc", p === "DNP" ? "STU" : p, PLABEL[p] || p, null, "p neutral")).join("")
    + (s.rnfa_inferred ? badge("disc", "RNFA", "NP-RNFA", "Surgical or perioperative meeting relevant to NP first assistants; curator tag", "p neutral") : "");
  const specTags = (s, limit) => (limit ? (s.specialty || []).slice(0, limit) : (s.specialty || []))
    .map(x => badge("spec", x, x, null, "spec")).join("");
  function vBadge(e, exceptionsOnly = false) {
    const v = e.verify || { state: "unchecked" };
    // exceptionsOnly = false: list cards. exceptionsOnly = true: record dialog and Directory (exceptions and projections only).
    // Check times stay in the page header.
    if (v.state === "expected") return `<span class="source-note muted" title="Projected from this meeting's usual month. No date has been published.">Expected month</span>`;
    const [baseLabel, icon] = VSTATE[v.state] || VSTATE.unchecked;
    // Fidelity is presumed: a record that passed its check carries no badge at all. A label appears only
    // when the checks found something to say: a projection, a save-the-date, a rule-computed date, or an exception.
    if (v.state === "verified") return "";
    if (exceptionsOnly && (v.state === "rule" || v.state === "archived")) return "";
    if (v.state === "announced" && exceptionsOnly) return `<span class="vf verified" title="The organizer has published a save-the-date for these days; the detailed programme is still to come.">${ICON.check}Save the date</span>`;
    const label = v.state === "verified" && v.method === "manual" ? "Source reviewed" : baseLabel;
    const when = "";   // the page header carries the check time; repeating it on every record only adds noise
    const tip = v.state === "verified" && v.method === "manual" ? "Confirmed by a manual review of the organizer's own source, not by the nightly text match. Open the record for the quoted wording and the source link, and confirm details with the organizer before booking." :
      v.state === "verified" ? "Start date, year and a distinctive meeting-name word were found on the organizer page. Confirm the end date there before booking." :
      v.state === "not_found" ? "The nightly check could not find these dates on the organizer page. Confirm before relying on them." :
      v.state === "conflict" ? (v.why || "The organizer publishes conflicting dates; confirm the final date before relying on it.") :
      v.state === "expected" ? "Projected from this meeting's usual month. No date has been published." :
      v.state === "announced" ? "The organizer has published a save-the-date for these days. Treat the range as theirs and the programme as still to come." :
      v.state === "archived" ? "The meeting has ended. The date is kept as the organizer's page read when it was recorded, and is not re-checked, because organizers replace the page with the next edition." :
      v.state === "rule" ? "Computed from the organizer's published rule for this observance." :
      "The organizer page could not be read automatically" + (v.why ? " (" + v.why + ")" : "") + ". Shown as compiled on " + (e.compiled || "") + ".";
    if (exceptionsOnly) {
      const plain = v.state === "not_found" ? "Date needs review" :
        v.state === "conflict" ? "Source reviewed" : v.state === "expected" ? "Expected month" : "Source not re-checked";
      // An organizer date ambiguity belongs inside the record, where someone weighing the meeting
      // will read it, not as a warning on every card that passes by.
      const tone = v.state === "not_found" ? "warn" : "muted";
      return `<span class="source-note ${tone}" title="${esc(tip)}">${esc(plain)}</span>`;
    }
    return `<span class="vf ${esc(v.state)}" title="${esc(tip)}">${ICON[icon]}${esc(label + when)}</span>`;
  }
  function callPill(e) {
    if (e.s.kind === "observance" || e.expectedRow || e.past) return "";
    return `<span class="pill ${e.c.k}" title="${esc((e.call && e.call.text) || e.c.label)}">${esc(e.c.label)}</span>`;
  }
  // dateMode "due" or "open" (Focus → Abstracts Due / Open Abstracts): the date block shows the abstract due date
  // and the meeting's own dates move into the meta line.
  function evRow(e, studentMode = false, dateMode = "") {
    const s = e.s, d = D(e.start), b = D(e.end);
    const same = b.getMonth() === d.getMonth() && b.getFullYear() === d.getFullYear();
    const dueOn = dateMode && e.call && e.call.closes ? D(e.call.closes) : null;
    const day = dateMode ? (dueOn ? String(dueOn.getDate()) : "Open") : e.month_only ? MON[d.getMonth()] : e.start === e.end ? String(d.getDate()) : same ? d.getDate() + "–" + b.getDate() : d.getDate() + "→";
    const sub = dateMode ? (dueOn ? "Due " + MON[dueOn.getMonth()] + " " + dueOn.getFullYear() : "No due date posted") : e.month_only ? d.getFullYear() + " · expected" : (same || e.start === e.end ? MON[d.getMonth()] : MON[d.getMonth()] + "–" + MON[b.getMonth()] + " " + b.getDate()) + " " + d.getFullYear();
    // the Focus badge already says Celebration / Conference; kindTag only refines the meeting form
    const kindTag = s.kind === "observance" || s.kind === "conference" ? "" : `<span class="tag">${esc(s.kind[0].toUpperCase() + s.kind.slice(1))}</span>`;
    const dist = st.near && e.geo && e.geo.lat != null ? `<span>${Math.round(miles(st.near.lat, st.near.lon, e.geo.lat, e.geo.lon))} mi away</span>` : "";
    const appWeekNow = s.name === "National APP Week" && e.start <= TODAY && e.end >= TODAY;
    // Red team F17: the card is an <article>; its title is the button that opens the record. A card that was itself
    // a button held the badge buttons inside it, which is invalid and confuses screen readers. A click anywhere on
    // the card still opens the record (data-e on the article).
    const label = s.name + ", " + (dateMode ? (dueOn ? "abstracts due " + longDate(e.call.closes) + ", meeting " : "abstract call open, meeting ") : "") + range(e);
    return `<article class="ev${e.expectedRow ? " expected" : ""}${e.past ? " past" : ""}${appWeekNow ? " app-week-now" : ""}${dateMode ? " by-due" : ""}" data-e="${e.id}">
      <div class="when" style="--c:${dateMode ? "var(--t-call)" : colorOf(s)}"><span class="d">${esc(day)}</span><span class="m">${esc(sub)}</span></div>
      <div class="body">${appWeekNow ? `<div class="live-label">OUR WEEK · HAPPENING NOW THROUGH ${esc(md(e.end))}</div>` : ""}<button type="button" class="ev-open" data-e="${e.id}" aria-label="${esc(label)}"><span class="title">${esc(s.name)}</span><span class="org">${esc(s.org_display || s.org)}</span></button>
        <div class="meta">${dateMode ? `<span class="meeting-dates">Meeting ${esc(range(e))}</span>` : ""}${e.location ? `<span class="loc">${esc(e.location)}</span>` : ""}${dist}${e.format && e.format !== "in person" ? `<span>${esc(e.format[0].toUpperCase() + e.format.slice(1))}</span>` : ""}${e.theme ? `<span><i>${esc(e.theme)}</i></span>` : ""}</div>
        <div class="badges">${profTags(s)}${scopeBadges(s)}${focusBadges(e)}${specTags(s, 2)}${kindTag}</div>${studentMode && e.student ? `<p class="student-line"><b>${esc(e.student.kind)}</b> · ${esc(e.student.detail)}</p>` : ""}</div>
      <div class="side">${studentMode && !dateMode ? (e.student && e.student.deadline && e.student.deadline >= TODAY ? `<span class="student-due">Submit by ${esc(md(e.student.deadline))}</span>` : "") : callPill(e)}${vBadge(e)}</div></article>`;
  }
  const empty = msg => `<div class="empty">${esc(msg)} <button class="linkbtn" data-act="clear">Clear all filters</button></div>`;

  /* ---------- views ---------- */
  function vList() {
    // Focus → Abstracts Due / Open Abstracts lists abstract calls by due month; every other Focus lists records by start month.
    const dateMode = st.focus === "due" || st.focus === "open" ? st.focus : "";
    const keyOf = dateMode ? (e => e.call && e.call.closes ? e.call.closes.slice(0, 7) : "undated") : eMonth;
    let L = dateMode === "due" ? EDS.filter(e => edMatch(e) && hasUpcomingDeadline(e))
      : dateMode === "open" ? EDS.filter(e => edMatch(e) && isOpenNow(e))
      : EDS.filter(e => !e.past && edMatch(e) && (st.expected || !e.expectedRow) && focusMatch(e));
    if (st.within) L = L.filter(e => e.start <= addDays(TODAY, st.within));
    L.sort(dateMode === "due" ? byDue : dateMode === "open" ? byOpenDue : byStart);
    const none = { due: "No upcoming abstract deadlines match these filters.", open: "No open abstract calls match these filters.", celebrations: "No upcoming celebrations match these filters." }[st.focus] || "No upcoming meetings match these filters.";
    if (!L.length && !listContextMonth) return empty(none);

    // A month carried from Calendar or Orbit must remain reachable even when it
    // falls beyond the normal 120-row List page, or has no matching records.
    if (listContextMonth) {
      let through = L.findIndex(e => keyOf(e) >= listContextMonth);
      if (through < 0) through = L.length;
      else {
        while (through < L.length && keyOf(L[through]) === listContextMonth) through++;
        if (!through) through = 1;
      }
      st.more = Math.max(st.more, Math.ceil(Math.max(through, 1) / 120));
    }
    const cap = 120 * st.more, shown = L.slice(0, cap), groups = new Map();
    shown.forEach(e => { const k = keyOf(e); if (!groups.has(k)) groups.set(k, []); groups.get(k).push(e); });
    if (listContextMonth && !groups.has(listContextMonth)) groups.set(listContextMonth, []);
    const studentMode = st.prof.includes("STU") || st.scope.includes("students");
    const emptyMonth = dateMode === "due" ? "No abstract deadlines fall in this month with the current filters."
      : dateMode === "open" ? "No open abstract call is due in this month with the current filters."
      : `No upcoming ${st.focus === "celebrations" ? "celebrations" : "meetings"} start in this month with the current filters.`;

    let h = `<div class="list-section-tools" role="group" aria-label="List section controls"><span>${dateMode ? "Due-month sections" : "Month sections"}</span><button class="btn" data-act="list-expand-all" aria-controls="list-sections">Expand all <b aria-hidden="true">↓</b></button><button class="btn" data-act="list-collapse-all" aria-controls="list-sections">Collapse all <b aria-hidden="true">↑</b></button></div><div class="list-months" id="list-sections">`;
    for (const [k, arr] of [...groups].sort(([a], [b]) => a.localeCompare(b))) {
      const d = k === "undated" ? null : D(k + "-01"), name = d ? `${MONTH[d.getMonth()]} ${d.getFullYear()}` : "Open, no due date posted";
      if (pendingListMonth === k) listDisclosure.set(k, true);
      const open = listDisclosure.has(k) ? listDisclosure.get(k) : listDefaultOpen;
      const noRows = !arr.length
        ? `<p class="list-month-empty">${emptyMonth}${k < TODAY.slice(0, 7) ? " List shows upcoming records only." : ""}</p>`
        : "";
      h += `<details class="month${k === listContextMonth ? " context-month" : ""}" id="list-month-${esc(k)}" data-list-month="${esc(k)}"${open ? " open" : ""}><summary><span class="month-title" role="heading" aria-level="2">${esc(name)}</span><span class="month-count">${arr.length} record${arr.length === 1 ? "" : "s"}</span><span class="list-toggle" aria-hidden="true"><span class="list-toggle-open">Collapse <b>↑</b></span><span class="list-toggle-closed">Expand <b>↓</b></span></span></summary>${noRows || `<div class="list">${arr.map(e => evRow(e, studentMode && !!e.student, dateMode)).join("")}</div>`}</details>`;
    }
    h += `</div>`;
    if (L.length > cap) h += `<button class="btn more" data-act="more">Show ${Math.min(120, L.length - cap)} more of ${L.length - cap} remaining</button>`;
    return h;
  }
  const eMonth = e => e.start.slice(0, 7);
  function positionPendingListMonth() {
    const month = pendingListMonth;
    pendingListMonth = "";
    if (!month || st.display !== "list") return;
    const target = document.getElementById("list-month-" + month);
    if (!target) return;
    listDisclosure.set(month, true);
    target.open = true;
    const bar = $(".bar"), sticky = bar && getComputedStyle(bar).position === "sticky";
    target.style.scrollMarginTop = `${sticky ? Math.ceil(bar.getBoundingClientRect().height) + 12 : 12}px`;
    target.scrollIntoView({ block: "start", behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
  }
  function vCalendar() {
    const [y, m] = st.cal.split("-").map(Number);
    const first = new Date(y, m - 1, 1), start = new Date(first); start.setDate(1 - first.getDay());
    const M = EDS.filter(e => edMatch(e) && !e.expectedRow), items = [];
    const mode = "upcoming";
    M.forEach(e => {
      const meeting = mode === "upcoming" || mode === "directory" || (mode === "past" && e.past);
      if (recordFocus(e) && meeting && !(mode === "upcoming" && e.past)) items.push({ e, from: e.start, to: e.end || e.start });
      const cs = callSpan(e);
      if (!cs || !(mode === "upcoming" || mode === "deadlines")) return;
      // Focus → Abstracts Due marks the due day only; Open Abstracts shows calls with a known open window.
      if (!st.focus) items.push({ e, call: true, from: cs.from, to: cs.to });
      else if (st.focus === "due") items.push({ e, call: true, from: cs.to, to: cs.to });
      else if (st.focus === "open" && cs.from < cs.to) items.push({ e, call: true, from: cs.from, to: cs.to });
    });
    // Meetings view: meetings first, then celebrations, then open abstract calls. Deadlines view: calls first.
    // National APP Week always first; then celebrations, meetings, open abstract calls (deadlines view: calls before meetings).
    const rank = x => !x.call && x.e.s.name === "National APP Week" ? -1 : mode === "deadlines" ? (x.call ? 0 : x.e.s.kind === "observance" ? 1 : 2) : (x.call ? 2 : x.e.s.kind === "observance" ? 0 : 1);
    const expected = st.expected && mode !== "past" ? EDS.filter(e => e.expectedRow && edMatch(e) && recordFocus(e) && e.start.slice(0, 7) === st.cal) : [];
    // Red team F11: a call listed as open with no published due date has no day to sit on in the grid, so in the
    // current month it is listed above the grid instead of being left out.
    const undated = st.cal === TODAY.slice(0, 7) && (!st.focus || st.focus === "open")
      ? M.filter(e => !e.past && e.c.k === "open" && e.c.undated).sort((a, b) => a.s.name.localeCompare(b.s.name)) : [];
    if (PHONE_CAL.matches) return calHead(y, m, expected, undated) + calAgenda(items, y, m, rank);
    const SHOW = 6;
    let weeks = "";
    for (let w = 0; w < 6; w++) {
      const ws = new Date(start); ws.setDate(start.getDate() + w * 7);
      if (w >= 5 && ws.getMonth() !== m - 1) break;
      const wkS = iso(ws), wkE = addDays(wkS, 6);
      const dueThisWeek = x => x.call && x.to >= wkS && x.to <= wkE;
      const priority = x => dueThisWeek(x) ? -2 : rank(x);
      const inWk = items.filter(x => x.from <= wkE && x.to >= wkS)
        .map(x => ({ ...x, a: x.from < wkS ? wkS : x.from, b: x.to > wkE ? wkE : x.to }))
        .sort((p, q) => priority(p) - priority(q) || p.a.localeCompare(q.a) || q.b.localeCompare(p.b) || p.e.s.name.localeCompare(q.e.s.name));
      const emptyWeek = inWk.length === 0;
      const lanes = [];   // last occupied day per lane
      inWk.forEach(x => { let l = lanes.findIndex(end => end < x.a); if (l < 0) { l = lanes.length; lanes.push(x.b); } else lanes[l] = x.b; x.lane = l; });
      const dueLanes = inWk.filter(dueThisWeek).reduce((n, x) => Math.max(n, x.lane + 1), 0);
      const visibleLanes = Math.max(SHOW, dueLanes);
      const nL = lanes.length, hidden = inWk.filter(x => x.lane >= visibleLanes).length;
      let h = "";
      for (let i = 0; i < 7; i++) {
        const d = new Date(ws); d.setDate(ws.getDate() + i); const k = iso(d);
        h += `<div class="cell${d.getMonth() !== m - 1 ? " out" : ""}${k === TODAY ? " today" : ""}" style="grid-column:${i + 1};grid-row:1 / -1"><button class="num" data-dayopen="${k}" aria-label="All records for ${esc(longDate(k))}">${d.getDate()}</button></div>`;
      }
      inWk.forEach(x => {
        const { e, call } = x, c0 = daysBetween(wkS, x.a) + 1, c1 = daysBetween(wkS, x.b) + 2;
        const contL = x.from < wkS, contR = x.to > wkE, span = c1 - c0;
        const due = call && !contR;
        const label = (contL ? "… " : "") + (call ? (due ? "Abstracts due: " : "Abstracts open: ") : "") + esc(e.s.name) + (call ? (span > 1 || !due ? ` <small>due ${esc(md(x.to))}</small>` : "") : span > 1 ? ` <small>${esc(range(e))}</small>` : "");
        h += `<button class="ce${call ? " call" : e.s.kind === "observance" ? " obs" : " meet"}${due ? " due" : ""}${!call && e.s.name === "National APP Week" ? " appweek" : ""}${contL ? " contl" : ""}${contR ? " contr" : ""}${e.past && !call ? " was" : ""}${x.lane >= visibleLanes ? " extra" : ""}" style="--c:${call ? "var(--t-call)" : colorOf(e.s)};grid-column:${c0} / ${c1};grid-row:${x.lane + (x.lane >= visibleLanes ? 3 : 2)}" data-e="${e.id}" title="${esc((call ? "Abstract call" + (x.from < x.to ? " open " + md(x.from) + " –" : "") + " due " + md(x.to) + ": " : "") + e.s.name + " — " + range(e))}">${label}</button>`;
      });
      if (emptyWeek) h += `<div class="week-empty" style="grid-column:1 / -1;grid-row:2">No matching events this week.</div>`;
      if (hidden) h += `<button class="overflow" style="grid-column:1 / -1;grid-row:${visibleLanes + 2}" data-day="${wkS}" data-extra="${hidden}" aria-expanded="false"><span class="overflow-main">+${hidden} more this week</span><span class="overflow-cue">Expand <b aria-hidden="true">↓</b></span></button>`;
      const rc = emptyWeek ? "26px auto" : `26px${Math.min(nL, visibleLanes) ? ` repeat(${Math.min(nL, visibleLanes)}, auto)` : ""}${hidden ? " auto" : ""}`, rx = emptyWeek ? rc : `26px repeat(${nL + 1}, auto)`;
      weeks += `<div class="wk${emptyWeek ? " emptyweek" : ""}" style="grid-template-rows:${rc}" data-rc="${rc}" data-rx="${rx}">${h}</div>`;
    }
    const cells = `<div class="dowrow">${DOW.map(d => `<div class="dow">${d}</div>`).join("")}</div>${weeks}`;
    // Red team F17: the month grid is a labelled group of buttons, not an ARIA grid (it has no grid rows or cells).
    return calHead(y, m, expected, undated) + `<div class="calwrap"><div class="cal calspan" role="group" aria-label="${MONTH[m - 1]} ${y}">${cells}</div></div>`;
  }
  function calHead(y, m, expected, undated = []) {
    const Y0 = +TODAY.slice(0, 4), years = []; for (let yy = Y0 - 3; yy <= DATA.horizon; yy++) years.push(yy);
    return `<div class="calhead">
        <div class="calnav">
          <button class="btn" data-act="prevY" aria-label="Previous year">«</button><button class="btn" data-act="prev" aria-label="Previous month">‹</button>
          <h2>${MONTH[m - 1]} ${y}</h2>
          <button class="btn" data-act="next" aria-label="Next month">›</button><button class="btn" data-act="nextY" aria-label="Next year">»</button>
        </div>
        <div class="calmeta"><div class="caljump">
          <label class="sr" for="calM">Month</label><select id="calM" class="sel">${MONTH.map((n, i) => `<option value="${i + 1}" ${i + 1 === m ? "selected" : ""}>${n}</option>`).join("")}</select>
          <label class="sr" for="calY">Year</label><select id="calY" class="sel">${years.map(yy => `<option ${yy === y ? "selected" : ""}>${yy}</option>`).join("")}</select>
          <button class="btn" data-act="today">Today</button>
        </div></div>
      </div>
      ${expected.length ? `<div class="expectedrow"><b>Expected this month, no date posted yet:</b> ${expected.map(e => `<button class="chip" data-e="${e.id}">${esc(e.s.name)}</button>`).join("")}</div>` : ""}
      ${undated.length ? `<div class="expectedrow undatedrow"><b>Abstract calls open now, no due date posted:</b> ${undated.map(e => `<button class="chip" data-e="${e.id}">${esc(e.s.name)}</button>`).join("")}</div>` : ""}`;
  }
  /* ---------- phone Calendar: a day-by-day agenda of the same records ----------
     A seven-column month grid does not fit a phone held upright, so below 700 px the Calendar lists
     the month by day: each record once, under the day it starts; an abstract call under the day it
     opens and the day it is due; anything already running on the 1st under "Continuing". Desktop and
     tablets keep the grid; the same items, colours and record dialogs are used. */
  function calAgenda(items, y, m, rank) {
    const mS = `${y}-${String(m).padStart(2, "0")}-01`, mE = iso(new Date(y, m, 0));
    const current = mS.slice(0, 7) === TODAY.slice(0, 7);
    const byDay = new Map(), carried = [], ongoing = [];
    const put = (day, r) => { if (!byDay.has(day)) byDay.set(day, []); byDay.get(day).push(r); };
    items.forEach(x => {
      if (x.to < mS || x.from > mE) return;
      if (x.call) {
        if (x.to <= mE) put(x.to, { x, due: true });
        if (x.from < x.to && x.from >= mS) put(x.from, { x, due: false });
        else if (x.from < mS && x.to > mE) carried.push({ x, due: false });
      } else if (x.from >= mS) {
        // A record that started earlier this month and is still running stays in view under "Under way
        // today"; filed under its start day, it would fold away with the earlier days.
        if (current && x.from < TODAY && x.to >= TODAY) ongoing.push({ x });
        else put(x.from, { x });
      }
      else carried.push({ x });
    });
    const order = r => r.due ? -2 : rank(r.x);
    const sortRows = L => L.sort((p, q) => order(p) - order(q) || p.x.e.s.name.localeCompare(q.x.e.s.name));
    const item = r => {
      const { e, call } = r.x;
      const cls = call ? "call" + (r.due ? " due" : "") : e.s.kind === "observance" ? "obs" : "meet";
      const title = call ? (r.due ? "Abstracts due: " : "Abstracts open: ") + e.s.name : e.s.name;
      const sub = call ? (r.due ? `Meeting ${range(e)}` : `Due ${md(r.x.to)} · meeting ${range(e)}`)
        : [range(e), e.location].filter(Boolean).join(" · ");
      return `<button class="ag-item ${cls}${!call && e.s.name === "National APP Week" ? " appweek" : ""}" data-e="${e.id}"><span class="ag-t">${esc(title)}</span><span class="ag-s">${esc(sub)}</span></button>`;
    };
    const days = [...byDay.keys()].sort();
    if (!days.length && !carried.length && !ongoing.length) return `<div class="agenda" aria-label="${MONTH[m - 1]} ${y}"><p class="ag-empty">No matching records in ${MONTH[m - 1]} ${y}.</p></div>`;
    const dayBlock = k => {
      const d = D(k);
      return `<section class="ag-day${k === TODAY ? " today" : ""}"><h3 class="ag-head"><button class="ag-date" data-dayopen="${k}" aria-label="All records for ${esc(longDate(k))}">${esc(DOW[d.getDay()])} ${d.getDate()} ${esc(MON[d.getMonth()])}${k === TODAY ? " · Today" : ""}</button></h3>${sortRows(byDay.get(k)).map(item).join("")}</section>`;
    };
    let h = carried.length ? `<section class="ag-day ag-carry"><h3 class="ag-head">Continuing into ${MONTH[m - 1]}</h3>${sortRows(carried).map(item).join("")}</section>` : "";
    // In the current month the days already past fold away, so the agenda opens at today;
    // records still under way are listed first, above today.
    const earlier = current ? days.filter(k => k < TODAY) : [], rest = current ? days.filter(k => k >= TODAY) : days;
    if (earlier.length) {
      const n = earlier.reduce((t, k) => t + byDay.get(k).length, 0);
      h += `<details class="ag-earlier"><summary>Earlier in ${MONTH[m - 1]} · ${n} record${n === 1 ? "" : "s"}</summary>${earlier.map(dayBlock).join("")}</details>`;
    }
    if (ongoing.length) h += `<section class="ag-day ag-now"><h3 class="ag-head">Under way today</h3>${sortRows(ongoing).map(item).join("")}</section>`;
    h += rest.map(dayBlock).join("");
    return `<div class="agenda" aria-label="${MONTH[m - 1]} ${y}">${h}</div>`;
  }
  const orbitShowAll = new Set();   // "YYYY-MM|group" keys the visitor expanded with "Show all"
  function vOrbit() {
    orbitClamp();
    const win = orbitWindow(), year = orbitLabel();
    const annualFocus = st.orbitScope === "year";
    const records = EDS.filter(annualFocus ? orbitAnnualRecordMatch : orbitRecordMatch);
    const cats = orbitCats();
    const monthly = win.map(w => ({ ...orbitMonthData(records, w.year, w.month, annualFocus), name: w.name, month: w.month, short: w.short }));
    const max = Math.max(1, ...monthly.flatMap(x => cats.map(c => orbitCatRows(x, c).length)));
    const h = n => Math.round(8 + (n / max) * 40);
    const unique = rows => [...new Map(rows.map(e => [e.id, e])).values()];
    const annual = {
      name: "All twelve months",
      meetings: unique(monthly.flatMap(x => x.meetings)).sort(byStart),
      celebrations: unique(monthly.flatMap(x => x.celebrations)).sort(byStart),
      due: unique(monthly.flatMap(x => x.due)).sort(byDue),
      open: unique(monthly.flatMap(x => x.open)).sort(byOpenDue)
    };
    const selectedMonth = monthly.find(x => x.key === st.cal) || monthly[0];
    const selected = annualFocus ? annual : selectedMonth;
    const item = (e, meta, tone) => `<button class="orbit-item ${tone}" data-e="${esc(e.id)}"><span class="orbit-item-date">${esc(meta)}</span><strong>${esc(e.s.name)}</strong><span>${esc(e.s.org_display || e.s.org)}</span></button>`;
    // With a Focus chosen only its group shows, and it opens; with All every group starts collapsed.
    // A month shows its first 12 records per group, and a "Show all" button reveals the rest in place:
    // Orbit is the landing view, and a busy month holds dozens of meetings.
    const group = (title, tone, rows, meta) => {
      const allKey = `${selectedMonth.key}|${tone}`, expanded = !annualFocus && orbitShowAll.has(allKey);
      const shown = annualFocus || expanded ? rows : rows.slice(0, 12);
      return `<details class="orbit-group ${tone}"${st.focus || expanded ? " open" : ""}><summary><span>${esc(title)}</span><b>${rows.length}</b></summary><div>${rows.length ? shown.map(e => item(e, meta(e), tone)).join("") : `<p class="orbit-empty">No ${esc(title.toLowerCase())} in ${annualFocus ? "these twelve months" : "this month"}.</p>`}${!annualFocus && !expanded && rows.length > 12 ? `<button type="button" class="orbit-more" data-act="orbit-all" data-key="${esc(allKey)}">Show all ${rows.length} (${rows.length - 12} more)</button>` : ""}</div></details>`;
    };
    const NOUN = { meet: ["meeting", "meetings"], due: ["abstract deadline", "abstract deadlines"], open: ["open abstract call", "open abstract calls"], obs: ["celebration", "celebrations"] };
    const countLine = x => cats.map(c => { const n = orbitCatRows(x, c).length; return `${n} ${NOUN[c][n === 1 ? 0 : 1]}`; }).join(", ");
    const months = monthly.map((x, i) => `<button class="orbit-month${!annualFocus && x.key === selectedMonth.key ? " selected" : ""}" style="--i:${i}" data-orbit-month="${x.key}" aria-pressed="${!annualFocus && x.key === selectedMonth.key}" title="${esc(`${x.name}: ${countLine(x)}`)}"><span class="orbit-month-name">${esc(MON[x.month - 1])}<span class="orbit-month-year"> ’${esc(String(x.key.slice(2, 4)))}</span></span><span class="orbit-columns" aria-hidden="true">${cats.map(c => `<i class="${c}" style="--h:${h(orbitCatRows(x, c).length)}px"></i>`).join("")}</span><span class="orbit-counts" aria-hidden="true">${cats.map(c => `<i>${orbitCatRows(x, c).length}</i>`).join("")}</span><span class="sr">${esc(countLine(x))}</span></button>`).join("");
    const location = [];
    if (st.where) location.push(st.where[0].toUpperCase() + st.where.slice(1));
    if (st.area) location.push(st.area.slice(2));
    if (st.near) location.push(`${st.radius} mi from ${st.near.label}`);
    if (!location.length) location.push("Global");
    const discipline = st.prof.length ? st.prof.map(prof => PLABEL[prof] || prof).join(" + ") : "All APPs";
    const scopeLabel = st.scope.length ? st.scope.map(x => (SCOPE_CHIPS.find(([v]) => v === x) || [x, x])[1]).join(" + ") : "All scopes";
    const focusLabel = st.focus ? FOCUS_LABEL[st.focus] : "All focus";
    const context = [location.join(" · "), discipline, scopeLabel, focusLabel, st.q ? `Search: ${st.q}` : ""].filter(Boolean);
    const LEGEND = { meet: "Meetings", due: "Abstracts due", open: "Open abstracts", obs: "Celebrations" };
    const RAIL = [
      ["due", () => group("Abstracts due", "due", selected.due, e => e.call && e.call.closes ? longDate(e.call.closes) : "Date not posted")],
      ["meet", () => group("Meetings & Conferences", "meet", selected.meetings, e => range(e))],
      ["open", () => group("Open abstracts", "open", selected.open, e => e.call && e.call.closes ? `Due ${md(e.call.closes)}` : "Open")],
      ["obs", () => group("Celebrations", "obs", selected.celebrations, e => range(e))]
    ].filter(([c]) => cats.includes(c)).map(([, render]) => render()).join("\n        ");
    return `<div class="orbit-shell">
      <section class="orbit-board" aria-label="${esc(win[0].name)} to ${esc(win[11].name)} record density">
        <header class="orbit-heading"><div><p class="eyebrow">Global Orbit</p><h2>Twelve months at a glance</h2></div><p>Choose a month, or the centre label for all twelve. The arrows move the window a year.</p></header>
        <div class="orbit-stage">
          <div class="orbit-core"><button data-act="prevY" aria-label="Twelve months earlier">‹</button><button class="orbit-year" data-orbit-year aria-pressed="${annualFocus}" aria-label="Show all records from ${esc(win[0].name)} to ${esc(win[11].name)}"><strong class="${year.length > 4 ? "span" : ""}">${year}</strong><small class="orbit-context">${context.map(x => `<i>${esc(x)}</i>`).join("")}</small></button><button data-act="nextY" aria-label="Twelve months later">›</button></div>
          ${months}
        </div>
        <div class="orbit-legend" aria-label="Orbit legend">${cats.map(c => `<span><i class="${c}"></i>${LEGEND[c]}</span>`).join("")}</div>
      </section>
      <aside class="orbit-rail">
        <header aria-live="polite" aria-atomic="true"><p class="eyebrow">${annualFocus ? esc(MONTH[win[0].month - 1] + " " + win[0].year) + " – " + esc(MONTH[win[11].month - 1] + " " + win[11].year) : esc(selected.name)}</p><h2>Records in focus</h2><span class="sr">${esc(countLine(selected))}</span></header>
        ${RAIL}
      </aside>
    </div>`;
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
    const inThirty = addDays(TODAY, 30);
    const due = L.filter(e => ["open", "urgent", "soon"].includes(e.c.k) && e.c.closes && e.c.closes <= inThirty)
      .sort((a, b) => a.c.closes.localeCompare(b.c.closes));
    const opening = L.filter(e => e.c.k === "soon" && e.c.opens && e.c.opens <= inThirty && !(e.c.closes && e.c.closes <= inThirty))
      .sort((a, b) => a.c.opens.localeCompare(b.c.opens));
    const open = L.filter(e => ["open", "urgent"].includes(e.c.k) && !(e.c.closes && e.c.closes <= inThirty))
      .sort((a, b) => (a.c.closes || "9999").localeCompare(b.c.closes || "9999"));
    const row = (e, big, small, u) => `<div class="dlrow" data-e="${e.id}" tabindex="0" role="button">
        <div class="count${u ? " u" : ""}">${esc(big)}<small>${esc(small)}</small></div>
        <div class="body"><div class="title">${esc(e.s.name)}</div><div class="org">${esc(e.s.org_display || e.s.org)} · meeting ${esc(range(e))}</div><div class="meta">${esc((e.call && e.call.text) || "")}</div></div>
        <div class="side">${vBadge(e)}</div></div>`;
    let h = `<section class="sec deadline-section due-soon"><h2>Due within 30 days · ${due.length}</h2><div class="list">`;
    h += due.length ? due.map(e => e.c.today ? row(e, "Today", "organizer's cut-off time applies", true)
      : row(e, daysBetween(TODAY, e.c.closes), daysBetween(TODAY, e.c.closes) === 1 ? "day left" : "days left", true)).join("") : `<div class="empty">No deadlines fall within the next 30 days.</div>`;
    h += `</div></section><section class="sec deadline-section opening-soon"><h2>Opening within 30 days · ${opening.length}</h2><div class="list">`;
    h += opening.length ? opening.map(e => row(e, md(e.c.opens), "opens")).join("") : `<div class="empty">No calls are scheduled to open within the next 30 days.</div>`;
    h += `</div></section><section class="sec deadline-section open-now"><h2>Open now · ${open.length}</h2><div class="list">`;
    h += open.length ? open.map(e => e.c.closes ? row(e, md(e.c.closes), "due", false) : row(e, "Listed", "no closing date posted")).join("") : `<div class="empty">No additional open calls match these filters.</div>`;
    return h + `</div></section><p class="fine">Each call appears once: imminent due dates first, then calls opening soon, then other calls already open. A deadline closing today shows the day only; the organizer's cut-off hour and time zone still apply.</p>`;
  }
  // The edition a Directory card offers: the next dated one, or the latest when none is ahead.
  function offeredEdition(sid) {
    const L = EDS.filter(e => e.series === sid && !e.expectedRow).sort((a, b) => a.start.localeCompare(b.start));
    return L.find(e => !e.past && verMatch(e)) || L.filter(e => e.past).pop() || null;
  }
  function directorySeries() {
    // Focus narrows the Directory to series with a matching edition: a meeting or celebration series, an upcoming deadline, or a call open now.
    const editionFilters = st.where || st.area || st.near || st.review || st.focus || st.scope.includes("students");
    // The same word-by-word matching and clinical synonyms as List, applied to the series' own fields.
    // List also searches edition fields (city, theme, sessions); Directory does not.
    const words = (st.q || "").toLowerCase().split(/\s+/).filter(Boolean);
    const seriesHay = s => [s.name, s.org_display || s.org, s.org, (s.specialty || []).join(" "), (s.professions || []).join(" ")].join(" ").toLowerCase();
    // Red team F13: a place filter (format, region, distance) is judged on the edition the card offers, the next
    // dated one or, when none is ahead, the latest. An old edition in Prague must not list a series now bound for Sydney.
    const placeFilters = st.where || st.area || st.near;
    return DATA.series.filter(s => seriesMatch(s) &&
      (!words.length || words.every(w => wordHit(seriesHay(s), w))) &&
      (!editionFilters || EDS.some(e => e.series === s.id && edMatch(e) && focusMatch(e) && (st.expected || !e.expectedRow))) &&
      (!placeFilters || (o => !!o && placeMatch(o))(offeredEdition(s.id))))
      // A series with no edition at all has nothing to show; it is not listed.
      .filter(s => EDS.some(e => e.series === s.id));
  }
  function vDirectory() {
    const S = directorySeries();
    if (!S.length) return empty("No meetings match these filters.");
    const eds = new Map();
    EDS.forEach(e => { if (!eds.has(e.series)) eds.set(e.series, []); eds.get(e.series).push(e); });
    const letters = [...new Set(S.map(s => s.name[0].toUpperCase()))];
    // A level-2 heading (screen readers only) keeps the outline H1 → H2 → H3 when a record opens from here.
    let h = `<h2 class="sr">Every meeting series, A to Z</h2><nav class="alpha" aria-label="Jump to letter">${letters.map(l => `<a href="#" data-letter="${esc(l)}">${esc(l)}</a>`).join("")}</nav><div class="dir">`, cur = "";
    S.forEach(s => {
      const L = (eds.get(s.id) || []).sort((a, b) => a.start.localeCompare(b.start));
      const next = L.find(e => !e.past && !e.expectedRow && verMatch(e));
      const hidden = !next && L.some(e => !e.past && !e.expectedRow);
      const anchor = s.name[0].toUpperCase() !== cur ? (cur = s.name[0].toUpperCase(), ` id="letter-${esc(cur)}"`) : "";
      // The card is an <article>, not a <button>: its badges are buttons of their own, and a button inside
      // a button is invalid HTML. The series opens from the title button (keyboard) or a click anywhere on
      // the card (data-s on the article).
      h += `<article class="srs"${anchor} data-s="${esc(s.id)}"><button type="button" class="srs-open" data-s="${esc(s.id)}"><span class="title">${esc(s.name)}</span><span class="org">${esc(s.org_display || s.org)}</span></button>
        <span class="badges">${profTags(s)}${scopeBadges(s)}${specTags(s, 2)}</span>
        <span class="meta">${next ? "Next recorded: " + esc(range(next)) : hidden ? "Next date awaiting a source check" : esc(s.status_note || "Next date not posted")}${s.archive_url ? " · past-meetings archive" : ""}${next ? " " + vBadge(next, true) : ""}</span>
        <span class="hist">${L.filter(e => !e.expectedRow).map(e => `<span class="${e.past ? "" : "fut"}" title="${esc(range(e))}">${e.start.slice(0, 4)}</span>`).join("")}</span></article>`;
    });
    return h + "</div>";
  }

  function spotlight() {
    const el = $("#spotlight");
    el.hidden = true; return;   // no observance banner in the header
    const current = EDS.filter(e => e.s.kind === "observance" && !e.expectedRow && e.start <= TODAY && e.end >= TODAY && ["verified", "rule"].includes(e.verify.state))
      .sort((a, b) => (a.s.name === "National APP Week" ? -1 : 0) - (b.s.name === "National APP Week" ? -1 : 0))[0];
    if (!current) { el.hidden = true; return; }
    el.hidden = false;
    el.innerHTML = `<div class="live-ribbon"><span class="live-flag">${current.s.name === "National APP Week" ? `OUR WEEK · DAY ${daysBetween(current.start, TODAY) + 1} OF ${daysBetween(current.start, current.end) + 1}` : "HAPPENING NOW"}</span><strong>${esc(current.s.name)}</strong><span class="live-dates">${esc(range(current))} · through ${esc(MON[D(current.end).getMonth()] + " " + D(current.end).getDate())}</span><button class="live-source" data-e="${esc(current.id)}">View official source and details ↗</button></div>`;
  }

  /* ---------- fidelity index ----------
     What it counts: of every dated record the site shows, the share that
       (1) carries the organizer's own wording, or is computed from a published rule,
       (2) holds a good verification state,
       (3) has a source link, and, if the meeting has not happened yet,
       (4) a source link that still resolves, and
       (5) a confirmation no older than 90 days.
     That share is multiplied by the share projected correct from the independent audits' pooled
     error rate (below), so the index reflects the errors audits keep finding.
     It falls when an organizer removes a page an upcoming record depends on, when a check fails
     with no organizer wording on file, when confirmations go stale, or when an audit finds errors. */
  const FID_OK = new Set(["verified", "rule", "announced", "archived"]);
  function fidelityIndex() {
    const dated = EDS.filter(e => !e.expectedRow && !e.month_only);
    if (!dated.length) return null;
    const ok = dated.filter(e => {
      const v = e.verify || {};
      if (!(e.evidence || v.state === "rule")) return false;
      if (!FID_OK.has(v.state)) return false;
      if (!e.source_url) return false;
      if (!e.past) {
        if (e.link_dead) return false;
        if (v.state !== "rule") {
          // Stamps come as dates ("YYYY-MM-DD") or instants ("YYYY-MM-DDThh:mm:ssZ"). D() takes a date only,
          // so the age is taken from the calendar date. An unreadable stamp fails explicitly: NaN > 90 is false.
          const seen = String(v.last_verified || v.checked || "").slice(0, 10);
          const age = /^\d{4}-\d{2}-\d{2}$/.test(seen) ? daysBetween(seen, TODAY) : NaN;
          if (!Number.isFinite(age) || age > 90) return false;
        }
      }
      return true;
    }).length;
    // Independent audits of the upcoming records (sources/audits.json, carried as DATA.audits) count the records
    // wrong in an action-critical field even though they carried organizer evidence. Their pooled rate projects how
    // often a record with evidence is still wrong, including errors no audit has found yet. The index is the share
    // with evidence times the share projected correct; the range uses the 95% Wilson interval of the audit rate.
    // `wrong` is a count; a stale cached file may still carry a list of records, counted by its length.
    const A = (DATA && DATA.audits) || [];
    const audited = A.reduce((t, a) => t + (+a.audited || 0), 0);
    const wrong = A.reduce((t, a) => t + (Array.isArray(a.wrong) ? a.wrong.length : (Number(a.wrong) || 0)), 0);
    const rate = audited ? wrong / audited : 0;
    const [rlo, rhi] = wilsonInterval(wrong, audited);
    const coverage = ok / dated.length;
    return { pct: 100 * coverage * (1 - rate), ok, total: dated.length, coverage: 100 * coverage,
             wrong, audited, audits: A.length, correct: 100 * (1 - rate),
             low: 100 * coverage * (1 - rhi), high: 100 * coverage * (1 - rlo) };
  }
  // 95% Wilson score interval for a proportion x/n, as [low, high]; [0, 0] when nothing was audited.
  function wilsonInterval(x, n, z = 1.959964) {
    if (!n) return [0, 0];
    const p = x / n, d = 1 + z * z / n, c = p + z * z / (2 * n), r = z * Math.sqrt(p * (1 - p) / n + z * z / (4 * n * n));
    return [Math.max(0, (c - r) / d), Math.min(1, (c + r) / d)];
  }

  /* ---------- reliability index ----------
     What it counts: of every upcoming dated record, the share that the latest automated check
       re-confirmed from the organizer's own material (start date, its year and a meeting-name word found
       on the organizer's page, rendered when the page needs JavaScript, or in the organizer's own image
       the record links; carried per edition by build.py as `machine`), plus dates computed from a published rule.
     What it leaves out: records resting on a manual review of the organizer's source or on a
       save-the-date. They count once the automated check can re-read them.
     It falls when organizer sites block automated readers, when pages move, and to the rule-only
     share when no check has completed in 36 hours. Fidelity asks "does every record carry the
     organizer's evidence?"; reliability asks "can the machine reproduce it tonight?" */
  function reliabilityIndex(checkedAt) {
    const up = EDS.filter(e => !e.expectedRow && !e.month_only && !e.past);
    if (!up.length) return null;
    const fresh = !!checkedAt && (Date.now() - Date.parse(checkedAt)) / 36e5 <= 36;
    const rule = up.filter(e => (e.verify || {}).state === "rule").length;
    const machine = fresh ? up.filter(e => e.machine && (e.verify || {}).state !== "rule").length : 0;
    return { pct: (100 * (machine + rule)) / up.length, machine, rule, ok: machine + rule, total: up.length, fresh };
  }

  /* ---------- chip availability: a filter is offered only when it can return a record ---------- */
  // A chip that matches nothing is hidden rather than offered as a dead end.
  // "All" is always kept, and a chip the visitor has already selected is kept so a shared link keeps its control.
  function availableChips() {
    const series = DATA.series || [];
    const scope = new Set(), prof = new Set(), focus = new Set();
    for (const sr of series) {
      for (const t of scopeTags(sr)) scope.add(t);
      for (const [v] of PROF_CHIPS) if (v && profOptionMatch(sr, v)) prof.add(v);
    }
    for (const e of EDS) {
      if (e.expectedRow) continue;
      if (hasUpcomingDeadline(e)) focus.add("due");
      if (isOpenNow(e)) focus.add("open");
      if (!e.past) { (isCelebration(e) ? focus.add("celebrations") : focus.add("conferences")); }
    }
    return { scope, prof, focus };
  }
  let CHIPS_OK = { scope: new Set(), prof: new Set(), focus: new Set() };
  const chipOffered = (kind, v, selected) => !v || selected || CHIPS_OK[kind].has(v);

  /* ---------- controls ---------- */
  const chipRow = (key, list) => list.map(([v, l]) => `<button class="chip${v ? "" : " all"}" data-f="${key}" data-v="${esc(v)}" aria-pressed="${st[key] === v}"${key === "prof" && PROF_TIPS[v] ? ` title="${PROF_TIPS[v]}"` : ""}>${esc(l)}</button>`).join("");
  const profRow = () => PROF_CHIPS.filter(([v]) => chipOffered("prof", v, st.prof.includes(v))).map(([v, l]) => {
    const selected = v ? st.prof.includes(v) : !st.prof.length;
    const dot = v ? `<span class="dot" style="--c:var(${PROF_COLOR[v]})" aria-hidden="true"></span>` : "";
    return `<button class="chip prof-chip${v ? "" : " all"}" data-prof="${esc(v)}" aria-pressed="${selected}"${PROF_TIPS[v] ? ` title="${PROF_TIPS[v]}"` : ""}>${dot}${esc(l)}</button>`;
  }).join("");
  const scopeRow = () => SCOPE_CHIPS.filter(([v]) => chipOffered("scope", v, st.scope.includes(v))).map(([v, l]) => `<button class="chip${v ? "" : " all"}" data-scope="${esc(v)}" aria-pressed="${v ? st.scope.includes(v) : !st.scope.length}"${SCOPE_TIPS[v] ? ` title="${esc(SCOPE_TIPS[v])}"` : ""}>${esc(l)}</button>`).join("");
  const focusRow = () => FOCUS_CHIPS.filter(([v]) => chipOffered("focus", v, st.focus === v)).map(([v, l]) => `<button class="chip${v ? "" : " all"}" data-focus="${esc(v)}" aria-pressed="${st.focus === v}"${FOCUS_TIPS[v] ? ` title="${esc(FOCUS_TIPS[v])}"` : ""}>${esc(l)}</button>`).join("");
  function controls() {
    CHIPS_OK = availableChips();
    $("#quickprof").innerHTML = `<span class="flabel">Discipline</span>${profRow()}`;
    const quickScope = $("#quickscope");   // guarded: a cached older page may lack the Scope row
    if (quickScope) quickScope.innerHTML = `<span class="flabel">Scope</span>${scopeRow()}`;
    $("#quickfocus").innerHTML = `<span class="flabel">Focus</span>${focusRow()}`;
    $("#viewtools").innerHTML = `<div class="seg" role="group" aria-label="Display">
        <button data-display="list" aria-controls="view" aria-pressed="${st.display === "list"}">${ICON.list}List</button>
        <button data-display="calendar" aria-controls="view" aria-pressed="${st.display === "calendar"}">${ICON.cal}Calendar</button>
        <button data-display="orbit" aria-controls="view" aria-pressed="${st.display === "orbit"}">${ICON.orbit}Orbit</button>
        <button data-display="directory" aria-controls="view" aria-pressed="${st.display === "directory"}">${ICON.directory}Directory</button></div>`;
    $("#geoquick").innerHTML = `<span class="flabel">Location</span>
      <button class="chip all" data-act="where-all" aria-pressed="${!st.where}">All</button>
      <button class="chip" data-act="where-live" aria-pressed="${st.where === "live"}">Live</button>
      <button class="chip" data-act="where-online" aria-pressed="${st.where === "online"}">Online</button>
      <button class="chip" data-act="where-hybrid" aria-pressed="${st.where === "hybrid"}">Hybrid</button>
      <label class="geo-label" for="area">Global Region</label>
      <select id="area" class="sel geo-sel"><option value="">All regions</option>
        <optgroup label="Continent">${CONTINENTS.map(c => `<option value="c:${c}" ${st.area === "c:" + c ? "selected" : ""}>${c}</option>`).join("")}</optgroup>
        <optgroup label="Country">${COUNTRIES.map(c => `<option value="n:${esc(c)}" ${st.area === "n:" + c ? "selected" : ""}>${esc(c)}</option>`).join("")}</optgroup>
        <optgroup label="United States">${US_REGIONS.map(r => `<option value="r:${r}" ${st.area === "r:" + r ? "selected" : ""}>US ${r}</option>`).join("")}</optgroup></select>
      <span class="geo-divider" aria-hidden="true"></span>
      <label class="geo-label" for="nearq">Near City</label><input id="nearq" class="geo-input" list="citylist" placeholder="City or ZIP" value="${esc(st.nearQ)}" autocomplete="off" inputmode="search"><datalist id="citylist"></datalist>
      <label class="geo-label" for="radius">within</label><select id="radius" class="sel geo-sel">${[25, 50, 100, 250, 500, 1000, 2000].map(r => `<option value="${r}" ${st.radius === r ? "selected" : ""}>${r} miles</option>`).join("")}</select>
      ${st.nearQ && !st.near ? `<span class="nearmsg warn">No place found for “${esc(st.nearQ)}”. Try a ZIP code or “City, ST”.</span>` : st.near ? `<span class="nearmsg">${esc(st.near.label)}${st.near.others ? ` · ${st.near.others} other place${st.near.others === 1 ? "" : "s"} share this name; add the state or country to choose` : ""}</span>` : ""}`;
    $("#filters").innerHTML = `
      <div class="fgroup"><span class="flabel">Type</span>${chipRow("kind", KIND_CHIPS)}</div>
      <div class="fgroup"><label class="flabel" for="spec">Specialty</label><select id="spec" class="sel"><option value="">All specialties</option>${SPECS.map(s => `<option ${s === st.spec ? "selected" : ""}>${esc(s)}</option>`).join("")}</select>
        <label class="toggle"><input type="checkbox" id="exp" ${st.expected ? "checked" : ""}> Show expected dates through ${DATA.horizon}</label>
        <label class="toggle" title="Show only records whose latest automated source check did not confirm them"><input type="checkbox" id="review" ${st.review ? "checked" : ""}> Needs review only</label></div>`;
    $("#filters").classList.toggle("open", filtersOpen);
    $("#geoquick").classList.toggle("open", filtersOpen);
    $("#fbtn").setAttribute("aria-expanded", String(filtersOpen));
    $("#q").value = st.q;
  }
  const activeCount = () => [st.kind, st.where, st.area, st.near, st.spec, st.expected, st.review, st.q, st.within, st.focus].filter(Boolean).length + st.prof.length + st.scope.length;

  /* ---------- render ---------- */
  function render(keepFocus) {
    const active = document.activeElement;
    const f = keepFocus && active && active.id;
    const replaced = active && active.closest && active.closest("#quickprof,#quickscope,#quickfocus,#geoquick,#filters,#viewtools");
    const restore = replaced ? { id: active.id, display: active.dataset.display, filter: active.dataset.f, value: active.dataset.v, prof: active.dataset.prof, scope: active.dataset.scope, focus: active.dataset.focus } : null;
    spotlight(); controls();
    const v = st.display === "directory" ? vDirectory : st.display === "calendar" ? vCalendar : st.display === "orbit" ? vOrbit : vList;
    $("#view").innerHTML = v();
    // Red team F05: a place the list does not know must not silently drop the distance filter.
    if (st.nearQ && !st.near) $("#view").insertAdjacentHTML("afterbegin", `<p class="nearmiss" role="status">No place found for “${esc(st.nearQ)}”, so these results are not limited by distance. Try a ZIP code or “City, ST”.</p>`);
    let summary;
    if (st.display === "orbit") {
      const w = orbitWindow(), annual = st.orbitScope === "year";
      const recs = EDS.filter(annual ? orbitAnnualRecordMatch : orbitRecordMatch), ids = new Set();
      w.forEach(x => { const m = orbitMonthData(recs, x.year, x.month, annual); orbitCats().forEach(c => orbitCatRows(m, c).forEach(e => ids.add(e.id))); });
      const n = ids.size;
      summary = `${n} record${n === 1 ? "" : "s"} in the Orbit, ${MONTH[w[0].month - 1]} ${w[0].year} to ${MONTH[w[11].month - 1]} ${w[11].year}`;
    } else if (st.display === "directory") {
      const n = directorySeries().length;
      summary = `${n} of ${DATA.series.length} meeting series`;
    } else {
      const n = EDS.filter(e => !e.expectedRow && edMatch(e) && focusMatch(e) && (st.focus === "due" || st.focus === "open" || !e.past) && (!st.within || e.start <= addDays(TODAY, st.within))).length;
      summary = st.focus === "due" ? `${n} upcoming abstract deadline${n === 1 ? "" : "s"}` : st.focus === "open" ? `${n} open abstract call${n === 1 ? "" : "s"}` : `${n} upcoming record${n === 1 ? "" : "s"}`;
    }
    const applied = [];
    if (st.prof.length) applied.push("Disciplines: " + st.prof.map(prof => prof === "AGACNP" ? "AGACNP (curated topic fit)" : PLABEL[prof] || prof).join(" + "));
    if (st.scope.length) applied.push("Scope: " + st.scope.map(x => (SCOPE_CHIPS.find(([v]) => v === x) || [x, x])[1]).join(" + "));
    if (st.focus) applied.push("Focus: " + FOCUS_LABEL[st.focus]);
    if (st.area) applied.push("Global Region: " + st.area.slice(2));
    if (st.where) applied.push("Format: " + st.where[0].toUpperCase() + st.where.slice(1));
    if (st.near) applied.push(`Within ${st.radius} miles of ${st.near.label}`);
    else if (st.nearQ) applied.push(`Near: no place found for ${st.nearQ}; distance not applied`);
    if (st.spec) applied.push("Specialty: " + st.spec);
    if (st.q) applied.push("Search: " + st.q);
    if (st.review) applied.push("Needs review only");
    const stamp = DATA && DATA.built ? stampET(DATA.built).replace(/^Data snapshot /, "") : "";
    $("#summary").innerHTML = `<b>${esc(summary)}</b>` + (applied.length ? `<span class="applied">${esc(applied.join(" · "))}</span>` : "");
    $("#fbtn").textContent = "Filters" + (activeCount() ? " (" + activeCount() + ")" : "");
    writeHash();
    if (f && document.getElementById(f)) { const el = document.getElementById(f); el.focus(); if (el.setSelectionRange && el.value) el.setSelectionRange(el.value.length, el.value.length); }
    else if (restore) {
      const el = (restore.id && document.getElementById(restore.id)) ||
        [...document.querySelectorAll("#quickprof button,#quickscope button,#quickfocus button,#geoquick button,#filters button,#viewtools button")].find(x =>
          (restore.display && x.dataset.display === restore.display) ||
          (restore.prof != null && x.dataset.prof === restore.prof) ||
          (restore.scope != null && x.dataset.scope === restore.scope) ||
          (restore.focus != null && x.dataset.focus === restore.focus) ||
          (restore.filter && x.dataset.f === restore.filter && x.dataset.v === restore.value));
      if (el) el.focus({ preventScroll: true });
    }
    if (st.display === "list" && pendingListMonth) requestAnimationFrame(positionPendingListMonth);
  }

  /* ---------- near: ZIP or city ---------- */
  async function zipLookup(z) {
    const k = z.slice(0, 3);
    if (window.RUNWAY_ZIP) return window.RUNWAY_ZIP[z] || null;
    try { const r = await fetch("geo/zip/" + k + ".json"); if (!r.ok) return null; const j = await r.json(); return j[z] || null; } catch (e) { return null; }
  }
  // Cities carry their state or province (red team F05), so "Springfield, IL", "Springfield Illinois" and
  // "Portland, ME" resolve to the right place. Two-letter US state, Canadian province and Australian state codes are
  // understood, as are common country short forms. Without a qualifier the most populous city of that name is used,
  // and the label says which one it was.
  const US_ST = { AL: "Alabama", AK: "Alaska", AZ: "Arizona", AR: "Arkansas", CA: "California", CO: "Colorado", CT: "Connecticut", DE: "Delaware", DC: "District of Columbia", FL: "Florida", GA: "Georgia", HI: "Hawaii", ID: "Idaho", IL: "Illinois", IN: "Indiana", IA: "Iowa", KS: "Kansas", KY: "Kentucky", LA: "Louisiana", ME: "Maine", MD: "Maryland", MA: "Massachusetts", MI: "Michigan", MN: "Minnesota", MS: "Mississippi", MO: "Missouri", MT: "Montana", NE: "Nebraska", NV: "Nevada", NH: "New Hampshire", NJ: "New Jersey", NM: "New Mexico", NY: "New York", NC: "North Carolina", ND: "North Dakota", OH: "Ohio", OK: "Oklahoma", OR: "Oregon", PA: "Pennsylvania", RI: "Rhode Island", SC: "South Carolina", SD: "South Dakota", TN: "Tennessee", TX: "Texas", UT: "Utah", VT: "Vermont", VA: "Virginia", WA: "Washington", WV: "West Virginia", WI: "Wisconsin", WY: "Wyoming", PR: "Puerto Rico" };
  const CA_PR = { AB: "Alberta", BC: "British Columbia", MB: "Manitoba", NB: "New Brunswick", NL: "Newfoundland and Labrador", NS: "Nova Scotia", NT: "Northwest Territories", NU: "Nunavut", ON: "Ontario", PE: "Prince Edward Island", QC: "Quebec", SK: "Saskatchewan", YT: "Yukon" };
  const AU_ST = { ACT: "Australian Capital Territory", NSW: "New South Wales", NT: "Northern Territory", QLD: "Queensland", SA: "South Australia", TAS: "Tasmania", VIC: "Victoria", WA: "Western Australia" };
  const COUNTRY_ALIAS = { us: "United States", usa: "United States", "u.s.": "United States", "u.s.a.": "United States", america: "United States", "united states of america": "United States",
    uk: "United Kingdom", "u.k.": "United Kingdom", britain: "United Kingdom", "great britain": "United Kingdom", england: "United Kingdom", scotland: "United Kingdom", wales: "United Kingdom",
    uae: "United Arab Emirates", korea: "South Korea", "republic of korea": "South Korea", holland: "Netherlands", "the netherlands": "Netherlands" };
  const fold = x => String(x || "").normalize("NFKD").replace(/[\u0300-\u036f]/g, "").toLowerCase().replace(/\s+/g, " ").trim();
  const cityLabel = c => [c[0], c[4], c[1]].filter(Boolean).join(", ");
  async function cities() {
    if (CITIES) return CITIES;
    let base = window.RUNWAY_CITIES;
    if (!base) { try { const r = await fetch("geo/cities.json"); base = await r.json(); } catch (e) { base = []; } }
    const seen = new Set(base.map(c => fold(c[0] + "|" + (c[4] || "") + "|" + c[1])));
    const seenNC = new Set(base.map(c => fold(c[0] + "|" + c[1])));
    // Venue towns are added so a visitor can search near a meeting's own town. A US venue carries its state code.
    const venueCities = EDS.filter(e => e.geo && e.geo.place && e.geo.country && e.geo.lat != null && e.geo.precision !== "state" && e.geo.precision !== "country")
      .map(e => [e.geo.place, e.geo.country, e.geo.lat, e.geo.lon, e.geo.cc === "US" ? US_ST[e.geo.state] || "" : ""]);
    for (const c of venueCities) {
      const key = fold(c[0] + "|" + c[4] + "|" + c[1]);
      if (seen.has(key) || (!c[4] && seenNC.has(fold(c[0] + "|" + c[1])))) continue;
      base.push(c); seen.add(key); seenNC.add(fold(c[0] + "|" + c[1]));
    }
    CITIES = base;
    return CITIES;
  }
  // Does one qualifier (a state, province, country or their short form) describe city c?
  function qualifies(q, c) {
    const f = fold(q), up = String(q).trim().toUpperCase().replace(/\./g, "");
    const region = fold(c[4]), country = fold(c[1]);
    if (f === region || f === country) return true;
    if (COUNTRY_ALIAS[f] && fold(COUNTRY_ALIAS[f]) === country) return true;
    if (c[1] === "United States" && US_ST[up] && fold(US_ST[up]) === region) return true;
    if (c[1] === "Canada" && CA_PR[up] && fold(CA_PR[up]) === region) return true;
    if (c[1] === "Australia" && AU_ST[up] && fold(AU_ST[up]) === region) return true;
    return false;
  }
  // Split "Springfield, IL", "Springfield IL" or "Paris, France" into a city name and its qualifiers.
  function parsePlace(q) {
    const parts = q.split(",").map(x => x.trim()).filter(Boolean);
    if (parts.length > 1) return { name: parts[0], quals: parts.slice(1) };
    const words = q.trim().split(/\s+/);
    for (let k = Math.min(3, words.length - 1); k >= 1; k--) {
      const tail = words.slice(-k).join(" "), up = tail.toUpperCase().replace(/\./g, "");
      if (US_ST[up] || CA_PR[up] || AU_ST[up] || COUNTRY_ALIAS[fold(tail)] || Object.values(US_ST).some(v => fold(v) === fold(tail))
          || Object.values(CA_PR).some(v => fold(v) === fold(tail)) || Object.values(AU_ST).some(v => fold(v) === fold(tail)))
        return { name: words.slice(0, -k).join(" "), quals: [tail] };
    }
    return { name: q.trim(), quals: [] };
  }
  async function resolveNear() {
    const q = st.nearQ.trim();
    st.near = null;
    if (!q) return;
    if (/^\d{5}$/.test(q)) { const ll = await zipLookup(q); if (ll) st.near = { lat: ll[0], lon: ll[1], label: "ZIP " + q }; return; }
    const C = await cities(), { name, quals } = parsePlace(q), fn = fold(name);
    const fits = c => quals.every(x => qualifies(x, c));
    let hits = C.filter(c => fold(c[0]) === fn && fits(c));
    if (!hits.length && !quals.length) hits = C.filter(c => fold(c[0]).startsWith(fn));
    if (!hits.length) return;
    const hit = hits[0];   // the list runs from the most populous city down
    const others = quals.length ? 0 : C.filter(c => fold(c[0]) === fold(hit[0]) && c !== hit).length;
    st.near = { lat: hit[2], lon: hit[3], label: cityLabel(hit), others };
  }
  async function fillCityList(q) {
    if (!q || /^\d/.test(q)) { $("#citylist").innerHTML = ""; return; }
    const C = await cities(), { name, quals } = parsePlace(q), fn = fold(name);
    $("#citylist").innerHTML = C.filter(c => fold(c[0]).startsWith(fn) && quals.every(x => qualifies(x, c) || fold(c[4]).startsWith(fold(x)) || fold(c[1]).startsWith(fold(x))))
      .slice(0, 12).map(c => `<option value="${esc(cityLabel(c))}">`).join("");
  }

  /* ---------- detail dialog ---------- */
  const byId = id => EDS.find(e => e.id === id);
  const host = u => { try { return new URL(u).hostname.replace(/^www\./, ""); } catch (e) { return u; } };
  function openDay(k) {
    const mode = "upcoming", rows = [];
    EDS.filter(e => edMatch(e) && !e.expectedRow).forEach(e => {
      const meeting = mode === "upcoming" || mode === "directory" || (mode === "past" && e.past);
      if (recordFocus(e) && meeting && !(mode === "upcoming" && e.past) && e.start <= k && e.end >= k) rows.push({ e, what: e.start === k ? "Starts" : e.end === k ? "Final day" : "In progress" });
      const cs = (mode === "upcoming" || mode === "deadlines") ? callSpan(e) : null;
      const callShown = cs && (!st.focus || (st.focus === "due" && cs.to === k) || (st.focus === "open" && cs.from < cs.to));
      if (callShown && cs.from <= k && cs.to >= k) rows.push({ e, what: cs.to === k ? "Abstracts due today" : cs.from === k && cs.from < cs.to ? "Abstract call opens · due " + md(cs.to) : "Abstract call open · due " + md(cs.to), dl: cs.to === k, call: true });
    });
    rows.sort((a, b) => (b.dl ? 1 : 0) - (a.dl ? 1 : 0) || a.e.s.name.localeCompare(b.e.s.name));
    $("#dlg").dataset.cur = "";
    $("#dlg").innerHTML = `<div class="dlg dayview"><button class="x" data-act="close" aria-label="Close">×</button>
      <header><p class="eyebrow">${rows.length} record${rows.length === 1 ? "" : "s"}</p><h3>${esc(DOWL[D(k).getDay()] + ", " + longDate(k))}</h3></header>
      ${rows.length ? `<ul class="daylist">${rows.map(({ e, what, dl, call }) => `<li><button data-e="${esc(e.id)}" style="--c:${call ? "var(--t-call)" : colorOf(e.s)}"><span class="dwhat${dl ? " dl" : ""}">${esc(what)}</span><b>${esc(e.s.name)}</b><span class="dmeta">${esc(e.s.org_display || e.s.org)} · ${esc(range(e))}${e.location ? " · " + esc(e.location) : ""}</span></button></li>`).join("")}</ul>` : `<p class="fine">Nothing on this day with the current filters.</p>`}
    </div>`;
    if (!$("#dlg").open) $("#dlg").showModal();
  }
  function openDetail(e) {
    const s = e.s, v = e.verify || {};
    $("#dlg").dataset.cur = e.id;
    const L = EDS.filter(x => x.series === s.id).sort((a, b) => a.start.localeCompare(b.start));
    const Y0 = +TODAY.slice(0, 4), older = L.filter(x => +x.start.slice(0, 4) < Y0 - 3 && !x.expectedRow).reverse();
    const fix = REPO ? `${REPO}/issues/new?template=fix.yml&title=${encodeURIComponent("Fix: " + s.name + " " + e.start.slice(0, 4))}` : "";
    const li = x => `<li class="${x.id === e.id ? "cur" : ""}"><span class="y">${esc(range(x))}</span><span>${esc(x.location || (x.expectedRow ? ((x.end || x.start) < TODAY ? "No data available" : "Expected; not yet announced") : ""))}${x.detail_url ? ` · <a href="${esc(x.detail_url)}" target="_blank" rel="noopener noreferrer">Program & materials</a>` : ""}</span>${vBadge(x, true)}</li>`;
    $("#dlg").innerHTML = `<div class="dlg"><button class="x" data-act="close" aria-label="Close">×</button>
      <header><p class="eyebrow">${esc(s.org_display || s.org)}</p><h3>${esc(s.name)}</h3><div class="badges">${profTags(s)}${scopeBadges(s)}${specTags(s)}</div></header>
      <dl class="kv">
        <dt>When</dt><dd><b>${esc(range(e))}</b> ${vBadge(e, true)}</dd>
        ${e.location ? `<dt>Where</dt><dd>${esc(e.location)}${e.format && e.format !== "in person" ? " · " + esc(e.format) : ""}</dd>` : ""}
        ${e.theme ? `<dt>Theme</dt><dd><i>${esc(e.theme)}</i></dd>` : ""}
        ${s.kind !== "observance" && !e.expectedRow && !e.past ? `<dt>Call for abstracts</dt><dd>${callPill(e)} ${esc((e.call && e.call.text) || "")}${e.call && e.call.url ? ` · <a href="${esc(e.call.url)}" target="_blank" rel="noopener noreferrer">Submission page</a>` : ""}</dd>` : ""}
        ${e.note ? `<dt>Note</dt><dd>${esc(e.note)}</dd>` : ""}
        ${e.student ? `<dt>Student & DNP opportunity</dt><dd><b>${esc(e.student.kind)}</b> · ${esc(e.student.detail)} <a href="${esc(e.student.url)}" target="_blank" rel="noopener noreferrer">Organizer's student details</a></dd>` : ""}
        ${s.recurrence ? `<dt>Recurs</dt><dd>${esc(s.recurrence)}</dd>` : ""}
        <dt>Scope</dt><dd>${scopeTags(s).map(a => esc(a[0].toUpperCase() + a.slice(1))).join(", ")} <span class="fine">(curated and derived tags)</span></dd>
        ${s.np_pa_basis ? `<dt>Why it's here</dt><dd>${esc(s.np_pa_basis)}</dd>` : ""}
        <dt>${esc(e.start.slice(0, 4))} source</dt><dd>${e.source_url ? `<a href="${esc(e.source_url)}" target="_blank" rel="noopener noreferrer">${esc(host(e.source_url))} · ${esc(e.start.slice(0, 4))} organizer record</a>` : "—"} ${e.link_dead ? ` · <span class="fine">the organizer has since removed this page (${esc(e.link_dead)}); the date above is what it said when recorded</span> · <a href="${esc("https://web.archive.org/web/*/" + e.source_url)}" target="_blank" rel="noopener noreferrer">look for an archived copy</a>` : ""}${e.evidence_image ? ` · <a href="${esc(e.evidence_image)}" target="_blank" rel="noopener noreferrer">dates published in this image</a>` : ""}${e.source_language ? ` · <span class="fine">Original organizer source in ${esc(e.source_language)}; English navigation labels are curator translations where used.</span>` : ""}</dd>
      </dl>
      ${e.evidence
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
  // A year row is judged by the last day of its expected window, not by its year: nothing in the past is
  // "not yet announced"; if the window has closed with no organizer date, the line is "No data available".
  const lastDayOf = (y, mo) => new Date(Date.UTC(y, mo, 0)).toISOString().slice(0, 10);
  function yearRows(s, L) {
    const Y0 = +TODAY.slice(0, 4), rows = [];
    const datedAll = L.filter(x => !x.expectedRow).slice().sort(byStart);
    const usualMonth = datedAll.length ? +datedAll[datedAll.length - 1].start.slice(5, 7) : null;
    for (let y = Y0 - 3; y <= Y0 + 3; y++) {
      const inY = L.filter(x => +x.start.slice(0, 4) === y);
      const dated = inY.filter(x => !x.expectedRow), exp = inY.filter(x => x.expectedRow);
      const tag = y < Y0 ? "past" : y === Y0 ? "now" : "next";
      const windowEnd = exp.length ? (exp[0].end || exp[0].start) : usualMonth ? lastDayOf(y, usualMonth) : y + "-12-31";
      const gone = windowEnd < TODAY;
      if (dated.length) dated.forEach(x => rows.push(`<li class="${tag}${x.id === $("#dlg").dataset.cur ? " cur" : ""}"><span class="y">${esc(range(x))}</span><span>${esc(x.location || "")}${x.detail_url ? ` \u00b7 <a href="${esc(x.detail_url)}" target="_blank" rel="noopener noreferrer">${y} program</a>` : ""}${x.source_url && x.source_url !== s.org_url ? ` \u00b7 <a href="${esc(x.source_url)}" target="_blank" rel="noopener noreferrer">${y} organizer record</a>${x.link_dead ? ` <span class="fine">(page since removed)</span>` : ""}` : ""}</span>${vBadge(x, true)}</li>`));
      else if (exp.length && !gone) rows.push(`<li class="${tag} gap"><span class="y">${esc(range(exp[0]))}</span><span>Expected; not yet announced</span>${vBadge(exp[0], true)}</li>`);
      else if (gone) rows.push(`<li class="${tag} gap"><span class="y">${y}</span><span class="nodata">No data available</span><span></span></li>`);
      else rows.push(`<li class="${tag} gap"><span class="y">${y}</span><span class="nodata">Not yet announced</span><span></span></li>`);
    }
    return rows.join("");
  }
  function icsFor(e) {
    const s = e.s, stamp = new Date().toISOString().replace(/[-:]/g, "").slice(0, 15) + "Z";
    const x = t => String(t || "").replace(/\\/g, "\\\\").replace(/[;,]/g, m => "\\" + m).replace(/\n/g, "\\n");
    const L = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//APP Conference Runway//EN", "CALSCALE:GREGORIAN", "BEGIN:VEVENT", `UID:${e.uid || e.id}@app-conference-runway`, `DTSTAMP:${stamp}`,
      `DTSTART;VALUE=DATE:${e.start.replace(/-/g, "")}`, `DTEND;VALUE=DATE:${addDays(e.end, 1).replace(/-/g, "")}`, `SUMMARY:${x(s.name)} (${x(s.org)})`, `LOCATION:${x(e.location)}`,
      `URL:${e.source_url || ""}`, `DESCRIPTION:${x("Confirm details on the organizer page. Listed on APP Conference Runway.")}`, "END:VEVENT"];
    if (e.c.closes && e.c.closes >= TODAY) L.push("BEGIN:VEVENT", `UID:${e.uid || e.id}-call@app-conference-runway`, `DTSTAMP:${stamp}`, `DTSTART;VALUE=DATE:${e.c.closes.replace(/-/g, "")}`,
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
      const t = ev.target.closest("[data-badge],[data-display],[data-prof],[data-f],[data-scope],[data-focus],[data-act],[data-e],[data-s],[data-letter],[data-day],[data-dayopen],[data-orbit-month],[data-orbit-year]");
      if (!t) return;
      // A badge on a record is a way into the list. Clicking one clears the other
      // families, applies just that filter, closes the record and shows the result as a list.
      if (t.dataset.badge) {
        ev.preventDefault(); ev.stopPropagation();
        const kind = t.dataset.badge, val = t.dataset.val;
        st.prof = []; st.scope = []; st.focus = ""; st.spec = ""; st.review = false; st.q = "";
        if (kind === "disc") st.prof = [val];
        else if (kind === "scope") st.scope = [val];
        else if (kind === "focus") st.focus = val;
        else if (kind === "spec") st.spec = val;
        st.display = "list"; st.more = 1;
        const dlg = $("#dlg"); if (dlg && dlg.open) dlg.close();
        render(); writeHash();
        const view = $("#view"); if (view) { view.focus(); view.scrollIntoView({ block: "start", behavior: "smooth" }); }
        return;
      }
      if (t.dataset.display) {
        const from = st.display, next = t.dataset.display;
        if (next === "list" && (from === "calendar" || (from === "orbit" && st.orbitScope === "month"))) {
          listContextMonth = pendingListMonth = st.cal;
          listDisclosure.set(st.cal, true);
        } else if (next === "list" && from === "orbit" && st.orbitScope === "year") {
          listContextMonth = pendingListMonth = "";
        }
        st.display = next;
        render();
        return;
      }
      if (t.dataset.orbitYear != null) { st.orbitScope = "year"; render(); const yearButton = $("[data-orbit-year]"); if (yearButton) yearButton.focus({ preventScroll: true }); return; }
      if (t.dataset.orbitMonth) { const key = String(t.dataset.orbitMonth); st.orbitScope = "month"; st.cal = key; render(); const monthButton = $(`[data-orbit-month="${key}"]`); if (monthButton) monthButton.focus({ preventScroll: true }); return; }
      if (t.dataset.prof != null) {
        const prof = t.dataset.prof;
        if (!prof) st.prof = [];
        else st.prof = st.prof.includes(prof) ? st.prof.filter(x => x !== prof) : [...st.prof, prof];
        st.more = 1; revealFirstOrbitMatch(); render(); return;
      }
      if (t.dataset.f) { st[t.dataset.f] = st[t.dataset.f] === t.dataset.v && t.dataset.v ? "" : t.dataset.v; st.more = 1; render(); return; }
      if (t.dataset.scope != null) {
        const v = t.dataset.scope;
        if (!v) st.scope = [];
        else st.scope = st.scope.includes(v) ? st.scope.filter(x => x !== v) : [...st.scope, v];
        st.more = 1; revealFirstOrbitMatch(); render(); return;
      }
      if (t.dataset.focus != null) {
        // Focus shows one record type at a time; choosing the active type again returns to All.
        const v = t.dataset.focus;
        st.focus = v && st.focus !== v ? v : "";
        st.more = 1; revealFirstOrbitMatch(); render(); return;
      }
      const act = t.dataset.act;
      if (act === "clear") { const keep = { display: st.display, orbitScope: st.orbitScope, orbitFrom: st.orbitFrom, cal: st.cal }; Object.assign(st, DEF(), keep); render(); return; }
      if (act === "share") {
        const note = `APP Conference Runway: conferences, abstract deadlines, student and DNP project opportunities, and celebration weeks for advanced practice providers, checked nightly against the organizers' own pages.\n${location.origin + location.pathname}\n(Search indexing is discouraged; pass it directly to colleagues.)`;
        copy(note, "Note and link copied — paste it into an email or message.");
        return;
      }
      if (act === "where-all") { st.where = ""; revealFirstOrbitMatch(); render(); return; }
      if (["where-live", "where-online", "where-hybrid"].includes(act)) { const next = act.slice(6); st.where = st.where === next ? "" : next; revealFirstOrbitMatch(); render(); return; }
      if (act === "list-expand-all") {
        listDefaultOpen = true;
        listDisclosure.clear();
        document.querySelectorAll("#view details.month[data-list-month]").forEach(el => { el.open = true; });
        return;
      }
      if (act === "list-collapse-all") {
        listDefaultOpen = false;
        listDisclosure.clear();
        document.querySelectorAll("#view details.month[data-list-month]").forEach(el => { el.open = false; });
        return;
      }
      if (act === "more") { st.more++; render(); return; }
      if (act === "orbit-all") {
        const key = t.dataset.key || "", tone = key.split("|")[1];
        orbitShowAll.add(key); render();
        const next = tone && document.querySelectorAll(`.orbit-group.${tone} .orbit-item`)[12];
        if (next) next.focus({ preventScroll: true });   // keyboard users land on the first record just revealed
        return;
      }
      if (act === "prev" || act === "next") { const [y, m] = st.cal.split("-").map(Number); st.cal = iso(new Date(y, m - 1 + (act === "next" ? 1 : -1), 1)).slice(0, 7); render(); return; }
      if (act === "prevY" || act === "nextY") { const [y, m] = st.cal.split("-").map(Number); st.cal = (y + (act === "nextY" ? 1 : -1)) + "-" + String(m).padStart(2, "0"); if (st.display === "orbit") { const [fy, fm] = st.orbitFrom.split("-").map(Number); st.orbitFrom = (fy + (act === "nextY" ? 1 : -1)) + "-" + String(fm).padStart(2, "0"); } render(); return; }
      if (act === "today") { st.cal = TODAY.slice(0, 7); render(); return; }
      if (act === "close") { $("#dlg").close(); return; }
      if (act === "ics") { icsFor(byId($("#dlg").dataset.e)); return; }
      if (act === "copy") { copy(location.href, "Link copied"); return; }
      if (act === "copyview") { copy(location.href, "Link to this view copied"); return; }
      if (act === "layout") {   // phones only: switch between the mobile and desktop layouts (assets/layout.js)
        // Applied in place, not by reloading: a reload keeps the old zoom, so the desktop layout would open
        // magnified. The choice is remembered in this browser when storage is available.
        const root = document.documentElement, toDesktop = !root.classList.contains("force-desktop");
        const vp = document.querySelector('meta[name="viewport"]');
        const fit = Math.min(1, Math.round((window.innerWidth / 1280) * 1000) / 1000);
        if (vp) vp.setAttribute("content", toDesktop ? `width=1280, initial-scale=${fit}, minimum-scale=${fit}` : "width=device-width,initial-scale=1,viewport-fit=cover");
        root.classList.toggle("force-desktop", toDesktop);
        try { if (toDesktop) localStorage.setItem("runway-layout", "desktop"); else localStorage.removeItem("runway-layout"); } catch (e) { /* this visit only */ }
        t.textContent = toDesktop ? "Switch to the mobile layout" : "Desktop layout";
        render(); window.scrollTo(0, 0);
        return;
      }
      if (act === "filters") { filtersOpen = !filtersOpen; $("#filters").classList.toggle("open", filtersOpen); $("#geoquick").classList.toggle("open", filtersOpen); t.setAttribute("aria-expanded", String(filtersOpen)); return; }
      if (t.dataset.letter) { ev.preventDefault(); const el = document.getElementById("letter-" + t.dataset.letter); if (el) window.scrollTo({ top: el.getBoundingClientRect().top + scrollY - 170 }); return; }
      if (t.dataset.dayopen) { openDay(t.dataset.dayopen); return; }
      if (t.dataset.day) {
        const cell = t.closest(".wk") || t.closest(".cell"), expanded = cell.classList.toggle("expanded");
        if (cell.dataset.rx) cell.style.gridTemplateRows = expanded ? cell.dataset.rx : cell.dataset.rc;
        t.setAttribute("aria-expanded", String(expanded));
        t.innerHTML = expanded
          ? `<span class="overflow-main">Show fewer</span><span class="overflow-cue">Collapse <b aria-hidden="true">↑</b></span>`
          : `<span class="overflow-main">+${t.dataset.extra} more this week</span><span class="overflow-cue">Expand <b aria-hidden="true">↓</b></span>`;
        return;
      }
      if (t.dataset.s) { const L = EDS.filter(e => e.series === t.dataset.s).sort((a, b) => a.start.localeCompare(b.start)); const pick = L.find(e => !e.past && !e.expectedRow) || [...L].reverse().find(e => !e.expectedRow) || L[0]; if (pick) openDetail(pick); return; }
      if (t.dataset.e) { const e = byId(t.dataset.e); if (e) openDetail(e); }
    });
    document.addEventListener("toggle", ev => {
      const el = ev.target;
      if (!el.matches || !el.matches("#view details.month[data-list-month]")) return;
      listDisclosure.set(el.dataset.listMonth, el.open);
    }, true);
    document.addEventListener("keydown", ev => { if ((ev.key === "Enter" || ev.key === " ") && ev.target.matches("[role=button][data-e]")) { ev.preventDefault(); ev.target.click(); } });
    document.addEventListener("change", async ev => {
      const id = ev.target.id;
      if (id === "spec") st.spec = ev.target.value;
      if (id === "exp") st.expected = ev.target.checked;
      if (id === "review") st.review = ev.target.checked;
      if (id === "area") { st.area = ev.target.value; revealFirstOrbitMatch(); }
      if (id === "radius") st.radius = +ev.target.value;
      if (id === "calY" || id === "calM") { st.cal = $("#calY").value + "-" + String($("#calM").value).padStart(2, "0"); render(); return; }
      if (id === "nearq") { st.nearQ = ev.target.value.trim(); st.where = ""; await resolveNear(); }
      if (["spec", "exp", "review", "area", "radius", "nearq"].includes(id)) { st.more = 1; render(); }
    });
    document.addEventListener("input", ev => { if (ev.target.id === "nearq") fillCityList(ev.target.value); });
    document.addEventListener("keydown", async ev => { if (ev.target.id === "nearq" && ev.key === "Enter") { ev.preventDefault(); ev.target.blur(); } });
    let tmr; $("#q").addEventListener("input", ev => { clearTimeout(tmr); tmr = setTimeout(() => { st.q = ev.target.value.trim(); st.more = 1; render(true); }, 180); });
    $("#dlg").addEventListener("close", () => writeHash());
    // Keep keyboard focus inside the open record dialog (Tab wraps between its first and last controls).
    $("#dlg").addEventListener("keydown", ev => {
      if (ev.key !== "Tab") return;
      const f = [...$("#dlg").querySelectorAll('a[href],button,input,select,textarea,[tabindex]:not([tabindex="-1"])')].filter(el => el.offsetParent !== null);
      if (!f.length) return;
      const first = f[0], last = f[f.length - 1];
      if (ev.shiftKey && (document.activeElement === first || document.activeElement === $("#dlg"))) { ev.preventDefault(); last.focus(); }
      else if (!ev.shiftKey && document.activeElement === last) { ev.preventDefault(); first.focus(); }
    });
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
    const srcStamp = d.sources_checked ? stampET(d.sources_checked).replace(/^Data snapshot /, "") : stampET(d.built).replace(/^Data snapshot /, "");
    const f = fidelityIndex();
    // The dot reports the run, not the mood: red when the last check did not land, amber when
    // fidelity has slipped below 95%, green otherwise.
    const checkedAt = d.sources_checked || null;
    const staleHours = checkedAt ? (Date.now() - Date.parse(checkedAt)) / 36e5 : Infinity;
    const failed = !checkedAt || staleHours > 36;
    const tone = failed ? "bad" : (f && f.pct < 95 ? "warn" : "ok");
    const dotTip = failed
      ? "The most recent scheduled source check did not complete. The dates below are as of the time shown."
      : tone === "warn"
        ? "The last source check completed, and the fidelity index is below 95%."
        : "The last source check completed, and the fidelity index is at or above 95%.";
    const pc = x => x.toFixed(2) + "%";
    const fidTip = f
      ? `${f.ok} of ${f.total} dated records carry the organizer's own wording (or a published rule), hold a good verification state, and — for meetings still ahead — a working source link confirmed within 90 days (${pc(f.coverage)}).` +
        (f.audited ? ` Independent audits found ${f.wrong} of ${f.audited} audited upcoming records wrong in a date, format, place, abstract call or eligibility, so a record is projected correct ${pc(f.correct)} of the time, errors not yet found included. Fidelity = ${pc(f.coverage)} × ${pc(f.correct)}; 95% range ${f.low.toFixed(1)}–${f.high.toFixed(1)}%.` : "")
      : "";
    const r = reliabilityIndex(checkedAt);
    const relTip = r
      ? (r.fresh
        ? `${r.ok} of ${r.total} upcoming dated records: ${r.machine} re-confirmed from the organizer's own page or image by the latest automated check, and ${r.rule} computed from a published rule. The other ${r.total - r.ok} rest on a manual review of the organizer's source or a save-the-date, and count once the check can re-read them.`
        : `No automated check has completed in the last 36 hours, so only the ${r.rule} dates computed from a published rule count (${r.ok} of ${r.total}).`)
      : "";
    // Red team F16: a definition held only in a hover title cannot be reached by touch or keyboard. Each index is a
    // button (styled as the text it replaces) that opens its definition beneath the header; hover still shows it.
    const idx = [
      f ? `<button type="button" class="idx" aria-expanded="false" aria-controls="idx-note" title="${esc(fidTip)}" data-note="${esc(fidTip)}">Fidelity Index: ${f.pct.toFixed(2)}%</button>` : "",
      r ? `<button type="button" class="idx" aria-expanded="false" aria-controls="idx-note" title="${esc(relTip)}" data-note="${esc(relTip)}">Reliability Index: ${r.pct.toFixed(2)}%</button>` : ""
    ].filter(Boolean);
    $("#updated").innerHTML =
      `<span class="stamp-line"><i class="stat ${tone}" title="${esc(dotTip)}" aria-hidden="true"></i>Updated ${esc(srcStamp)}</span>` +
      (idx.length ? `<span class="fidline">${idx.join('<span class="idx-sep" aria-hidden="true"> · </span>')}</span><span class="idx-note" id="idx-note" role="note" hidden></span>` : "");
    $("#updated").setAttribute("datetime", d.sources_checked || d.built);
    const lt = $(".layout-toggle");
    if (lt) lt.textContent = document.documentElement.classList.contains("force-desktop") ? "Switch to the mobile layout" : "Desktop layout";
    await resolveNear();
    bind(); wireSkip(); render(); wireIndexNotes(); watchDay();
    if (PHONE_CAL.addEventListener) PHONE_CAL.addEventListener("change", () => { if (st.display === "calendar") render(); });
    if (want && byId(want)) openDetail(byId(want));
  }
  // The index definitions open on click, tap or Enter; a second press, a click elsewhere or Escape closes them.
  function wireIndexNotes() {
    const note = $("#idx-note"), btns = [...document.querySelectorAll("#updated button.idx")];
    if (!note || !btns.length) return;
    const close = () => { note.hidden = true; btns.forEach(b => b.setAttribute("aria-expanded", "false")); };
    btns.forEach(b => b.addEventListener("click", ev => {
      ev.stopPropagation();
      const wasOpen = b.getAttribute("aria-expanded") === "true";
      close();
      if (wasOpen) return;
      // The definitions live in the handoff on this site (§3.4), readable with no GitHub account (2026-09-26).
      const how = ` <a href="ai-handoff.html#34-nightly-verification-and-admission-pipeline" target="_blank" rel="noopener">How both indices are defined</a>`;
      note.innerHTML = esc(b.dataset.note) + how;
      note.hidden = false;
      b.setAttribute("aria-expanded", "true");
    }));
    document.addEventListener("click", ev => { if (!note.hidden && !ev.target.closest("#idx-note")) close(); });
    document.addEventListener("keydown", ev => {
      if (ev.key !== "Escape" || note.hidden) return;
      const open = btns.find(b => b.getAttribute("aria-expanded") === "true");
      close(); if (open) open.focus();
    });
  }
  // Red team F23: "open", "closes today" and "past" are worked out for the day the page loaded. A tab left open
  // past midnight would keep yesterday's statuses, so when the calendar day changes the page reloads itself,
  // with the view (kept in the address) unchanged: at once if it is on screen, or when the visitor returns to it.
  function watchDay() {
    const check = () => { if (iso(new Date()) !== TODAY && document.visibilityState === "visible") location.reload(); };
    document.addEventListener("visibilitychange", check);
    window.addEventListener("pageshow", check);
    const now = new Date(), next = new Date(now.getFullYear(), now.getMonth(), now.getDate() + 1, 0, 0, 30);
    setTimeout(function tick() { check(); setTimeout(tick, 36e5); }, Math.max(1000, next - now));
  }
  boot();
})();
