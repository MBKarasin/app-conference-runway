/* Plan your attendance: door-to-door dates, travel, lodging and the price of attendance for one meeting,
   from the visitor's own ZIP code, city or country.
   - Every price shown comes from the organizer's own page, with its link, the date it was read and its confidence.
     A price the organizer has not published reads "Not posted", never a guess.
   - Travel fares are not estimated (they change by the hour); the panel links out to search them instead.
   - The visitor's place stays in this browser. It reaches another site only if the visitor opens a link out.
   No third-party requests: fee and airport data load from this site. Airports: OurAirports (public domain). */
(function () {
  "use strict";
  const API = () => window.RunwayAPI;
  const esc = s => String(s == null ? "" : s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  let ATT = null, AIRPORTS = null, TYPED = null;   // TYPED: what the visitor last typed, kept across re-renders of the record
  const rad = x => x * Math.PI / 180;
  function km(a, b) {
    const dLat = rad(b.lat - a.lat), dLon = rad(b.lon - a.lon);
    const h = Math.sin(dLat / 2) ** 2 + Math.cos(rad(a.lat)) * Math.cos(rad(b.lat)) * Math.sin(dLon / 2) ** 2;
    return 2 * 6371 * Math.asin(Math.min(1, Math.sqrt(h)));
  }
  async function attendance() {
    if (ATT) return ATT;
    try { const r = await fetch("data/attendance.json", { cache: "no-cache" }); ATT = r.ok ? await r.json() : { records: {} }; }
    catch (e) { ATT = { records: {} }; }
    return ATT;
  }
  async function airports() {
    if (AIRPORTS) return AIRPORTS;
    try { const r = await fetch("geo/airports.json"); AIRPORTS = r.ok ? await r.json() : []; } catch (e) { AIRPORTS = []; }
    return AIRPORTS;
  }
  // Airports with scheduled service within 160 km, large ones preferred unless a medium one is much closer.
  function nearAirports(p, list, max) {
    return list.map(a => ({ a, d: km(p, { lat: a[4], lon: a[5] }) }))
      .filter(x => x.d <= 160)
      .sort((x, y) => (x.d - (x.a[6] === 2 ? 60 : 0)) - (y.d - (y.a[6] === 2 ? 60 : 0)))
      .slice(0, max || 3);
  }
  const store = {
    get() { try { return localStorage.getItem("runway-plan-from") || ""; } catch (e) { return ""; } },
    set(v) { try { localStorage.setItem("runway-plan-from", v); } catch (e) { /* storage blocked: nothing kept */ } }
  };
  const host = u => { try { return new URL(u).hostname.replace(/^www\./, ""); } catch (e) { return u; } };
  const PERIOD_ORDER = ["early", "early bird", "advance", "regular", "standard", "late", "onsite", "on-site", "all"];
  const cap = s => String(s || "").replace(/^\w/, c => c.toUpperCase());
  const dayName = s => ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"][API().D(s).getDay()];
  const nice = s => dayName(s) + " " + API().md(s);

  function mountSkeleton(el, e) {
    const from = TYPED != null ? TYPED : (API().near() || store.get());
    el.innerHTML = `<h4 class="plan-h">Plan your attendance</h4>
      <p class="plan-sub">Door-to-door dates, travel, lodging and the price of attendance, from where you are.</p>
      <form class="plan-from" autocomplete="off">
        <label for="plan-in">Starting from</label>
        <input id="plan-in" type="text" inputmode="text" placeholder="ZIP code, city, or country" value="${esc(from)}" list="citylist">
        <button class="btn primary" type="submit">Plan</button>
      </form>
      <p class="plan-privacy">Your place stays in this browser. It is sent to another site only if you open one of the links out (maps, flights, lodging).</p>
      <div class="plan-out" aria-live="polite"></div>`;
    el.querySelector("form").addEventListener("submit", ev => { ev.preventDefault(); run(el, e); });
    el.querySelector("#plan-in").addEventListener("input", ev => { TYPED = ev.target.value; });
  }

  async function run(el, e) {
    const q = el.querySelector("#plan-in").value.trim();
    const out = el.querySelector(".plan-out");
    out.innerHTML = `<p class="fine">Working…</p>`;
    const [att, place] = await Promise.all([attendance(), q ? API().resolvePlace(q) : Promise.resolve(null)]);
    if (q) store.set(q);
    const rec = (att.records || {})[e.id] || null;
    let html = "";
    if (q && !place) html += `<p class="plan-warn">“${esc(q)}” is not a place this site knows. Try a five-digit ZIP code, a city with its state or country (“Portland, ME”, “London, UK”), or a country.</p>`;
    const trip = place ? await tripPlan(e, place, rec) : null;
    if (trip) html += trip.summary;
    html += `<div class="plan-grid">`;
    html += costBlock(e, rec);
    if (trip) html += trip.blocks;
    else if (!q) html += `<section class="plan-card muted"><h5>Travel and lodging</h5><p>Enter your ZIP code, city or country above to add door-to-door dates, directions or flights, and lodging.</p></section>`;
    html += `</div>`;
    html += await lowerCost(e, rec, place, trip);
    html += `<p class="plan-foot">Prices are the organizer's own, as read on the date shown, and can change; taxes and fees may apply. Confirm on the organizer's page before you register or book.</p>`;
    out.innerHTML = html;
    out.querySelectorAll("[data-open]").forEach(b => b.addEventListener("click", () => API().open(b.dataset.open)));
  }

  /* ---------- the price of attendance ---------- */
  function confTag(it) {
    return it && it.confidence === "Medium" ? ` <span class="conf med" title="${esc(it.why_medium || "Not yet confirmed by code on the organizer's page")}">Medium</span>` : "";
  }
  function srcLine(url, on, extra) {
    return `<span class="plan-src"><a href="${esc(url)}" target="_blank" rel="noopener noreferrer">${esc(host(url))}</a>${on ? " · read " + esc(API().longDate(on)) : ""}${extra || ""}</span>`;
  }
  function costBlock(e, rec) {
    const today = API().TODAY;
    const orgPage = e.source_url;
    if (!rec) {
      return `<section class="plan-card"><h5>Registration</h5><p><b>Not captured yet.</b> This meeting's prices have not been read into the Runway. See the organizer's page: ${orgPage ? srcLine(orgPage, "") : "no link on file"}.</p></section>`;
    }
    if (rec.status === "unreadable") {
      return `<section class="plan-card"><h5>Registration</h5><p><b>Not captured.</b> The organizer's site does not allow automated reading, so prices are not shown here. Registration details: ${srcLine(rec.page_url || orgPage, "")}.</p></section>`;
    }
    const fees = (rec.fees || []).slice();
    let body = "";
    if (rec.status === "closed") body += `<p class="plan-warn">Registration is closed${rec.notes ? " (" + esc(rec.notes) + ")" : ""}.</p>`;
    if (!fees.length) {
      body += `<p><b>Not posted.</b> The organizer has not published prices${rec.status === "not_posted" && rec.notes ? ": " + esc(rec.notes) : ""}. ${srcLine(rec.page_url || orgPage, rec.checked_on)}</p>`;
    } else {
      // Group by scope (full meeting first), then attendee, in the organizer's period order.
      const scopeRank = s => /full|all/i.test(s || "full") ? 0 : /one|day|single/i.test(s) ? 1 : /virtual|online|on-demand|digital/i.test(s) ? 2 : 3;
      const pr = p => { const i = PERIOD_ORDER.indexOf(String(p || "").toLowerCase()); return i < 0 ? 5 : i; };
      fees.sort((a, b) => scopeRank(a.scope) - scopeRank(b.scope) || String(a.attendee).localeCompare(String(b.attendee)) || pr(a.period) - pr(b.period));
      // When every price shares one confidence, it is said once under the table instead of on every row.
      const allMedium = fees.every(f => f.confidence === "Medium");
      const row = f => {
        const ended = f.period_ends && f.period_ends < today;
        const bits = [cap(f.attendee), f.period && f.period !== "all" ? cap(f.period) + (f.period_ends ? (ended ? " (ended " + API().md(f.period_ends) + ")" : " (until " + API().md(f.period_ends) + ")") : "") : "", f.scope && !/^full$/i.test(f.scope) ? cap(f.scope) : ""].filter(Boolean);
        return `<tr class="${ended ? "ended" : ""}"><td>${esc(bits.join(" · "))}</td><td class="amt" title="${esc("Organizer's wording: “" + f.quote + "”")}">${esc(f.amount_text || (f.amount != null ? f.amount : ""))}${rec.currency && !/[$€£¥₹]|[A-Z]{3}/.test(f.amount_text || "") ? " " + esc(rec.currency) : ""}${allMedium ? "" : confTag(f)}</td></tr>`;
      };
      const current = fees.filter(f => !(f.period_ends && f.period_ends < today)), ended = fees.filter(f => f.period_ends && f.period_ends < today);
      const urls = [...new Set(fees.map(f => f.url))];
      body += `${current.length ? `<table class="fees"><caption class="sr">Registration prices</caption><tbody>${current.map(row).join("")}</tbody></table>` : `<p>Every posted rate's period has ended; see the organizer's page for the current price.</p>`}
        ${ended.length ? `<details class="fees-ended"><summary>Rates whose period has ended (${ended.length})</summary><table class="fees"><tbody>${ended.map(row).join("")}</tbody></table></details>` : ""}
        ${allMedium ? `<p class="conf-line"><span class="conf med">Confidence: Medium</span> ${esc(fees[0].why_medium || "not yet confirmed by code on the organizer's page")}.</p>` : ""}
        <p class="plan-srcs">Source${urls.length > 1 ? "s" : ""}: ${urls.map(u => srcLine(u, rec.checked_on)).join(" · ")}${rec.currency ? ` · prices in ${esc(rec.currency)}` : ""}</p>`;
      if (rec.notes) body += `<p class="fine">${esc(rec.notes)}</p>`;
    }
    return `<section class="plan-card"><h5>Registration</h5>${body}</section>`;
  }

  /* ---------- door to door ---------- */
  async function tripPlan(e, place, rec) {
    const A = API();
    const online = /virtual|online/i.test(e.format || "") && !/hybrid/i.test(e.format || "");
    const g = e.geo && e.geo.lat != null ? { lat: e.geo.lat, lon: e.geo.lon } : null;
    const us = place.country === "United States";
    const dist = d => us ? Math.round(d * 0.621371).toLocaleString() + " mi" : Math.round(d).toLocaleString() + " km";
    const from = esc(place.label) + (place.proxy ? ` <span class="fine">(standing in for ${esc(place.proxy)})</span>` : "");
    if (online) {
      return { summary: `<p class="plan-summary"><b>Online meeting.</b> No travel from ${from}. Session times are the organizer's; check them against your time zone.</p>`, blocks: "", mode: "online", d: 0 };
    }
    if (!g || (e.geo && ["state", "country"].includes(e.geo.precision))) {
      return { summary: `<p class="plan-summary">The venue is not mapped precisely enough to plan travel from ${from}${e.location ? " (" + esc(e.location) + ")" : ""}.</p>`, blocks: "", mode: "unknown", d: null };
    }
    const d = km(place, g);
    const start = e.start, end = e.end || e.start;
    const days = A.daysBetween(start, end) + 1;
    let mode, arrive, depart, travelHtml = "";
    const gmap = (o, t, how) => `https://www.google.com/maps/dir/?api=1&origin=${o.lat},${o.lon}&destination=${t.lat},${t.lon}&travelmode=${how}`;
    const osm = (o, t) => `https://www.openstreetmap.org/directions?engine=fossgis_osrm_car&route=${o.lat}%2C${o.lon}%3B${t.lat}%2C${t.lon}`;
    if (d <= 80) {
      mode = "commute"; arrive = start; depart = end;
      const mins = Math.round((d * 1.3) / 50 * 60 / 5) * 5;
      travelHtml = `<p><b>Commute.</b> About ${dist(d)} in a straight line; roughly ${mins < 60 ? mins + " minutes" : (mins / 60).toFixed(1) + " hours"} each way by car at typical speeds (an approximation; check a map).</p>
        <p class="plan-links"><a href="${esc(gmap(place, g, "driving"))}" target="_blank" rel="noopener noreferrer">Driving directions</a> · <a href="${esc(gmap(place, g, "transit"))}" target="_blank" rel="noopener noreferrer">Public transit</a> · <a href="${esc(osm(place, g))}" target="_blank" rel="noopener noreferrer">OpenStreetMap</a></p>`;
    } else if (d <= 400) {
      const hrs = (d * 1.25) / 90;
      mode = "drive"; arrive = hrs > 2.5 ? A.addDays(start, -1) : start; depart = hrs > 4 ? A.addDays(end, 1) : end;
      travelHtml = `<p><b>Drive or rail.</b> About ${dist(d)} in a straight line; roughly ${hrs.toFixed(1)} hours by road (an approximation).</p>
        <p class="plan-links"><a href="${esc(gmap(place, g, "driving"))}" target="_blank" rel="noopener noreferrer">Driving directions</a> · <a href="${esc(gmap(place, g, "transit"))}" target="_blank" rel="noopener noreferrer">Rail and transit</a> · <a href="${esc(osm(place, g))}" target="_blank" rel="noopener noreferrer">OpenStreetMap</a></p>`;
    } else {
      mode = "fly"; arrive = A.addDays(start, -1); depart = d > 1500 || place.country !== (e.geo && e.geo.country) ? A.addDays(end, 1) : end;
      const list = await airports();
      const home = nearAirports(place, list, 3), there = nearAirports(g, list, 3);
      const ap = x => `<b>${esc(x.a[0])}</b> ${esc(x.a[1])} <span class="fine">(${dist(x.d)})</span>`;
      const q = home.length && there.length ? `Flights from ${home[0].a[0]} to ${there[0].a[0]} on ${arrive} returning ${depart}` : "";
      travelHtml = `<p><b>Fly.</b> About ${dist(d)} in a straight line.</p>
        <p>Near you: ${home.length ? home.map(ap).join(" · ") : "no airport with scheduled flights within 160 km"}</p>
        <p>Near the venue: ${there.length ? there.map(ap).join(" · ") : "no airport with scheduled flights within 160 km"}</p>
        ${q ? `<p class="plan-links"><a href="${esc("https://www.google.com/travel/flights?q=" + encodeURIComponent(q))}" target="_blank" rel="noopener noreferrer">Search flights ${esc(home[0].a[0])} → ${esc(there[0].a[0])}</a>${there.length ? ` · <a href="${esc(gmap({ lat: there[0].a[4], lon: there[0].a[5] }, g, "transit"))}" target="_blank" rel="noopener noreferrer">Airport to venue</a>` : ""}</p>` : ""}
        <p class="fine">Fares are not estimated here; they change by the hour.${place.country && e.geo && e.geo.country && place.country !== e.geo.country ? " International trip: check passport and entry requirements for " + esc(e.geo.country) + "." : ""}</p>`;
    }
    if (start < A.TODAY) {   // already under way: no arrival advice in the past
      arrive = A.TODAY < arrive ? arrive : A.TODAY;
      if (depart < arrive) depart = arrive;
    }
    const nights = Math.max(0, A.daysBetween(arrive, depart));
    const underway = start < A.TODAY;
    const plan = underway ? `Under way now, through ${nice(end)}.` + (mode === "commute" ? " A day trip from here." : ` Arriving ${nice(arrive)} leaves ${Math.max(0, A.daysBetween(arrive, end) + 1)} day${A.daysBetween(arrive, end) === 0 ? "" : "s"} of the meeting.`) : mode === "commute"
      ? `Day trip${days > 1 ? "s" : ""}: ${nice(start)}${days > 1 ? " to " + nice(end) : ""}; home each night.`
      : `Arrive ${nice(arrive)}${arrive < start ? " (the day before)" : ""} · attend ${nice(start)}${days > 1 ? " – " + nice(end) : ""} · return ${nice(depart)}${depart > end ? " (the day after)" : ""} · ${nights} night${nights === 1 ? "" : "s"}.`;
    const summary = `<p class="plan-summary"><b>From ${from}</b> to ${esc(e.location || "the venue")}: ${plan}</p>`;
    let lodging;
    if (mode === "commute") lodging = `<p>Not needed for a day trip.</p>`;
    else {
      const hb = rec && rec.hotel_block;
      const lodgingSearch = `https://www.google.com/maps/search/${encodeURIComponent("hotels near " + (e.location || ""))}`;
      if (hb) {
        const rate = String(hb.rate_text || "").match(/(\d[\d,]*(?:\.\d+)?)/);
        const cutPassed = hb.cutoff && hb.cutoff < A.TODAY;
        const est = rate && nights ? Math.round(parseFloat(rate[1].replace(/,/g, "")) * nights) : null;
        lodging = `<p><b>Official hotel block:</b> ${esc(hb.hotel || "listed by the organizer")}${hb.rate_text ? " · " + esc(hb.rate_text) : ""}${confTag(hb)}${hb.cutoff ? ` · ${cutPassed ? "booking cut-off passed " : "book by "}${esc(A.md(hb.cutoff))}` : ""}</p>
          ${est ? `<p>${nights} night${nights === 1 ? "" : "s"} at the block rate: about ${esc((rec.currency && rec.currency !== "USD" ? rec.currency + " " : "$") + est.toLocaleString())} before taxes (an estimate from the posted rate).</p>` : ""}
          <p class="plan-srcs">${srcLine(hb.url, rec.checked_on)} · <a href="${esc(lodgingSearch)}" target="_blank" rel="noopener noreferrer">Other lodging near the venue</a></p>`;
      } else {
        lodging = `<p><b>Official hotel block: not posted</b>${rec ? "" : " (not captured yet)"}. ${nights} night${nights === 1 ? "" : "s"} to cover.</p>
          <p class="plan-links"><a href="${esc(lodgingSearch)}" target="_blank" rel="noopener noreferrer">Lodging near the venue</a>${e.source_url ? " · " + srcLine(e.source_url, "", " (organizer page)") : ""}</p>`;
      }
    }
    const blocks = `<section class="plan-card"><h5>Getting there</h5>${travelHtml}</section><section class="plan-card"><h5>Lodging</h5>${lodging}</section>`;
    return { summary, blocks, mode, d, arrive, depart, nights };
  }

  /* ---------- lower-cost ways to take part (factual, in the organizer's terms) ---------- */
  async function lowerCost(e, rec, place, trip) {
    const A = API(), today = A.TODAY, items = [];
    const fees = (rec && rec.fees) || [];
    const vo = rec && rec.virtual_option;
    if (vo && vo.available) items.push(`Online or on-demand participation is offered.${confTag(vo)} ${srcLine(vo.url, rec.checked_on)}`);
    else if (/hybrid/i.test(e.format || "")) items.push(`The organizer lists this meeting as hybrid; an online option may be available. ${e.source_url ? srcLine(e.source_url, "") : ""}`);
    const lowest = (pred, label) => {
      const xs = fees.filter(pred).filter(f => f.amount != null && !(f.period_ends && f.period_ends < today)).sort((a, b) => a.amount - b.amount);
      if (xs.length) items.push(`${label}: ${esc(xs[0].amount_text || xs[0].amount)} (${esc(cap(xs[0].attendee))}${xs[0].period && xs[0].period !== "all" ? ", " + esc(xs[0].period) : ""}).${confTag(xs[0])}`);
    };
    lowest(f => /student/i.test(f.attendee || ""), "Student rate");
    lowest(f => /one|day|single/i.test(f.scope || "") && !/full/i.test(f.scope || ""), "One-day rate");
    lowest(f => /virtual|online|on-demand|digital/i.test(f.scope || "") || /virtual|online|digital/i.test(f.attendee || ""), "Online rate");
    const early = fees.filter(f => /early|advance/i.test(f.period || "") && f.period_ends && f.period_ends >= today).sort((a, b) => a.period_ends.localeCompare(b.period_ends));
    if (early.length) items.push(`Early rate available until ${esc(A.longDate(early[0].period_ends))}.`);
    for (const s of (rec && rec.support) || []) items.push(`${esc(cap(s.kind))}${s.eligibility ? " — " + esc(s.eligibility) : ""}.${confTag(s)} ${srcLine(s.url, rec.checked_on)}`);
    let near = "";
    if (place && trip && trip.d != null && trip.d > 80) {
      const prof = new Set(e.s.professions || []);
      const horizon = A.addDays(today, 365);
      const cands = A.eds().filter(x => x.id !== e.id && !x.past && !x.expectedRow && !x.month_only && x.s.kind !== "observance" && x.start <= horizon
          && x.geo && x.geo.lat != null && !["state", "country"].includes(x.geo.precision) && (x.s.professions || []).some(p => prof.has(p)))
        .map(x => ({ x, d: km(place, { lat: x.geo.lat, lon: x.geo.lon }) }))
        .filter(o => o.d < Math.min(trip.d * 0.5, 300))
        .sort((a, b) => a.d - b.d).slice(0, 3);
      if (cands.length) {
        const us = place.country === "United States";
        near = `<div class="plan-near"><p class="flabel">Meetings for the same disciplines nearer you (next 12 months)</p><ul>${cands.map(o =>
          `<li><button type="button" class="linkbtn" data-open="${esc(o.x.id)}">${esc(o.x.s.name)}</button> <span class="fine">${esc(A.range(o.x))} · ${esc(o.x.location || "")} · ${us ? Math.round(o.d * 0.621371) + " mi" : Math.round(o.d) + " km"}</span></li>`).join("")}</ul></div>`;
      }
    }
    if (!items.length && !near) return "";
    return `<section class="plan-card wide"><h5>Ways to take part at lower cost</h5>${items.length ? `<ul class="plan-list">${items.map(i => `<li>${i}</li>`).join("")}</ul>` : `<p class="fine">No reduced rates, online option or support has been captured for this meeting yet.</p>`}${near}</section>`;
  }

  window.RunwayPlan = {
    mount(el, e) {
      mountSkeleton(el, e);
      run(el, e);   // registration prices show at once; travel appears when a place is given
    }
  };
})();
