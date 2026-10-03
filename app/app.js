/* PopUpPick front end. Reads the engine's output files and calculates nothing itself:
   fit, units, reviews, £ and checks all come from outputs/ (written by model/run.py). */
"use strict";

const TYPES = [
  { key: "community", label: "Community", color: "#40C0C0" },
  { key: "concerts", label: "Concerts", color: "#C060B0" },
  { key: "conferences", label: "Conferences", color: "#4B4BF0" },
  { key: "expos", label: "Expos", color: "#8FD3EC" },
  { key: "festivals", label: "Festivals", color: "#F06040" },
  { key: "performing_arts", label: "Performing arts", color: "#FFB088" },
  { key: "sports", label: "Sports", color: "#4FA8CF" },
];
const TYPE = Object.fromEntries(TYPES.map(t => [t.key, t]));
const ARCH = {
  wellness_seeker: "Wellness seeker", trend_enthusiast: "Trend enthusiast", thoughtful_buyer: "Thoughtful buyer",
  smart_saver: "Smart saver", quality_seeker: "Quality seeker", on_the_go_shopper: "On-the-go shopper",
  impulse_buyer: "Impulse buyer", experience_explorer: "Experience explorer", everyday_planner: "Everyday planner",
  conscious_consumer: "Conscious consumer",
};
const SHORT_LABEL = {
  wellness_seeker: "Wellness", trend_enthusiast: "Trend", thoughtful_buyer: "Thoughtful", smart_saver: "Saver",
  quality_seeker: "Quality", on_the_go_shopper: "On-the-go", impulse_buyer: "Impulse", experience_explorer: "Explorer",
  everyday_planner: "Planner", conscious_consumer: "Conscious",
};
const SHORT = a => SHORT_LABEL[a];
const FIT = m => (m >= 0.85 ? "#22A651" : m >= 0.7 ? "#EAC24A" : "#C9C7C0");
const REDUCED = matchMedia("(prefers-reduced-motion: reduce)").matches;
const $ = s => document.querySelector(s);
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const gbp = x => (x < 0 ? "−£" : "£") + Math.abs(Math.round(x)).toLocaleString("en-GB");
const pct = x => `${Math.round(x * 100)}%`;
const signedPct = x => `${x >= 0 ? "+" : "−"}${Math.abs(x * 100).toFixed(1)}%`;
const day = d => new Date(d + "T12:00").toLocaleDateString("en-GB", { weekday: "short", day: "numeric", month: "short" });
const time = s => s.slice(11, 16);
const popupCode = e => `PUP-${e.date.replace(/-/g, "")}-${e.id.slice(0, 4).toUpperCase()}`;

const S = {
  events: [], byId: {}, audience: {}, impact: null, month: null, scores: {}, brands: {}, ready: false,
  filtered: [], sort: "net", selected: null, cursor: -1, size: "medium", plan: [], tab: "map",
  winnerHL: null, openTile: null, pair: null,
  f: { types: new Set(), arche: "", from: "", to: "", setting: "", maxCost: Infinity, search: "", radius: null },
};

/* ------------------------------------------------------------------ data */
function parseCSV(text) {
  const rows = []; let row = [], field = "", q = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (q) {
      if (c === '"' && text[i + 1] === '"') { field += '"'; i++; }
      else if (c === '"') q = false; else field += c;
    } else if (c === '"') q = true;
    else if (c === ",") { row.push(field); field = ""; }
    else if (c === "\n" || c === "\r") {
      if (c === "\r" && text[i + 1] === "\n") i++;
      row.push(field); field = ""; if (row.length > 1 || row[0] !== "") rows.push(row); row = [];
    } else field += c;
  }
  if (field || row.length) { row.push(field); rows.push(row); }
  const [head, ...body] = rows;
  return body.map(r => Object.fromEntries(head.map((h, i) => [h, r[i]])));
}

async function loadData() {
  const get = (u, kind) => fetch(u).then(r => { if (!r.ok) throw new Error(u); return kind === "json" ? r.json() : r.text(); });
  const [lineups, audience, impact, month, scores, brands] = await Promise.all([
    get("/outputs/lineups.json", "json"), get("/outputs/event_audience.json", "json"),
    get("/outputs/impact.json", "json"), get("/outputs/month_plan.json", "json"),
    get("/outputs/scores.csv"), get("/data/processed/brand_features.csv"),
  ]);
  S.audience = audience; S.impact = impact; S.month = month;
  for (const b of parseCSV(brands)) S.brands[b.brand_id] = { name: b.brand_name, stock: +b.units_available_per_month };
  for (const r of parseCSV(scores)) S.scores[`${r.event_id}|${r.brand_id}`] = r;
  S.events = Object.entries(lineups).map(([id, e]) => ({ id, ...e }));
  S.events.forEach(e => (S.byId[e.id] = e));
}

/* ------------------------------------------------------------------ opening sequence */
const splash = { node: $("#splash"), popped: false, pending: false, timers: [] };

function startSplash() {
  const n = splash.node;
  splash.popped = false; splash.pending = false;
  n.className = ""; n.querySelector(".splash-loading").hidden = true;
  const drops = n.querySelector(".droplets"); drops.innerHTML = "";
  const colours = ["#C2FF00", "#4DC9E2", "#ffffff"];
  const count = 10 + Math.floor(Math.random() * 5);
  for (let i = 0; i < count; i++) {
    const a = (i / count) * Math.PI * 2 + Math.random() * 0.4, r = 150 + Math.random() * 120, s = 6 + Math.random() * 10;
    const d = document.createElement("i");
    d.style.cssText = `--x:${Math.cos(a) * r}px;--y:${Math.sin(a) * r}px;--c:${colours[i % 3]};width:${s}px;height:${s}px`;
    drops.appendChild(d);
  }
  splash.timers.forEach(clearTimeout);
  splash.timers = [
    setTimeout(() => tryPop(), REDUCED ? 800 : 2000),
    setTimeout(() => { if (!S.ready) n.querySelector(".splash-loading").hidden = false; }, 5000),
  ];
  n.querySelector(".splash-hit").focus({ preventScroll: true });
}

function tryPop() {
  if (splash.popped) return;
  if (!S.ready) { splash.pending = true; return; }            // never pop onto an empty map
  splash.popped = true;
  const n = splash.node;
  document.body.classList.add("revealing");
  if (REDUCED) n.classList.add("gone");
  else { n.classList.add("popping"); setTimeout(() => n.classList.add("gone"), 250); }
  setTimeout(() => {
    n.remove();                                                 // removed from the page afterwards
    document.body.classList.remove("revealing");
    S.map.invalidateSize();
    $("#eventList").focus();
  }, REDUCED ? 650 : 900);
  dropPins();
}

function wireSplash() {
  const n = splash.node;
  n.querySelector(".splash-hit").addEventListener("click", tryPop);
  n.querySelector(".splash-skip").addEventListener("click", tryPop);
  n.addEventListener("keydown", e => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); tryPop(); } });
  $("#replay").addEventListener("click", () => { document.body.appendChild(splash.node); startSplash(); });
}

/* ------------------------------------------------------------------ map */
function initMap() {
  const map = L.map("map", { zoomControl: true, worldCopyJump: false });
  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19, attribution: "© OpenStreetMap contributors",
  }).addTo(map);
  S.cluster = L.markerClusterGroup({ showCoverageOnHover: false, maxClusterRadius: 38, spiderfyOnMaxZoom: true });
  map.addLayer(S.cluster);
  const reset = L.control({ position: "topleft" });
  reset.onAdd = () => {
    const b = L.DomUtil.create("button", "leaflet-bar");
    b.textContent = "⤢"; b.title = "Reset view"; b.style.cssText = "width:34px;height:34px;background:#fff;font-size:16px";
    L.DomEvent.on(b, "click", e => { L.DomEvent.stop(e); fitAll(); });
    return b;
  };
  reset.addTo(map);
  map.on("zoomend", () => $("#map").classList.toggle("zoomed", map.getZoom() >= 11));
  map.on("moveend zoomend", () => setTimeout(markSelectedPin, 50));      // clusters redraw pins after moves
  S.cluster.on("animationend spiderfied", markSelectedPin);
  S.map = map;
  S.markers = {};
  S.events.forEach((e, i) => {
    const aud = S.audience[e.id];
    const size = Math.round(26 + Math.min(e.expected_attendance, 200) / 200 * 22);
    const score = Math.round(e.match * 100);
    const top = aud.top_archetypes[0];
    const html = `<div class="pin" style="--s:${size}px;--fit:${FIT(e.match)};--d:${i * 45}ms" data-id="${e.id}">${score}`
      + `<span class="pin-label">${SHORT(top)} ${pct(aud.crowd[top])}</span></div>`;
    const m = L.marker([e.latitude, e.longitude], {
      icon: L.divIcon({ className: "pin-wrap", html, iconSize: [size, size], iconAnchor: [size / 2, size / 2] }),
      keyboard: true, title: e.title, riseOnHover: true,
    });
    const tops = aud.top_archetypes.map(a => `${ARCH[a]} ${pct(aud.crowd[a])}`).join("<br>");
    m.bindTooltip(`<b>${esc(e.title)}</b><br>${day(e.date)} · match ${score}<br><span style="opacity:.7">${tops}</span>`,
      { className: "tip", direction: "top", offset: [0, -size / 2] });
    m.on("mouseover", () => rowFor(e.id)?.classList.add("hl"));
    m.on("mouseout", () => rowFor(e.id)?.classList.remove("hl"));
    m.on("click", () => select(e.id, { fly: true }));
    S.markers[e.id] = m;
  });
}

function fitAll() {
  const pts = (S.filtered.length ? S.filtered : S.events).map(e => [e.latitude, e.longitude]);
  if (pts.length) S.map.fitBounds(pts, { padding: [40, 40], maxZoom: 12, animate: !REDUCED });
}

function renderMarkers() {
  S.cluster.clearLayers();
  S.cluster.addLayers(S.filtered.map(e => S.markers[e.id]));
  markSelectedPin();
}

function dropPins() {               // pins drop in one after another once the site is revealed
  document.querySelectorAll(".pin").forEach(p => { p.style.animation = "none"; void p.offsetWidth; p.style.animation = ""; });
}

function pinEl(id) { return document.querySelector(`.pin[data-id="${CSS.escape(id)}"]`); }
function markSelectedPin() {
  document.querySelectorAll(".pin.sel").forEach(p => p.classList.remove("sel"));
  if (S.selected) pinEl(S.selected)?.classList.add("sel");
}

function toggleRadius() {
  const btn = $("#fRadius");
  if (S.f.radius) {
    S.map.removeLayer(S.f.radius.circle); S.map.removeLayer(S.f.radius.handle);
    S.f.radius = null; btn.setAttribute("aria-pressed", "false"); $("#radiusCtl").hidden = true;
  } else {
    const centre = S.map.getCenter(), km = +$("#radiusKm").value;
    const circle = L.circle(centre, { radius: km * 1000, color: "#6A6AE2", weight: 2, fillOpacity: 0.06 }).addTo(S.map);
    const handle = L.marker(centre, {
      draggable: true, keyboard: true, title: "Radius centre",
      icon: L.divIcon({ className: "pin-wrap", html: '<div style="width:16px;height:16px;border-radius:50%;background:#6A6AE2;border:3px solid #fff;box-shadow:0 2px 6px rgba(0,0,0,.4)"></div>', iconSize: [16, 16], iconAnchor: [8, 8] }),
    }).addTo(S.map);
    handle.on("drag", () => circle.setLatLng(handle.getLatLng()));
    handle.on("dragend", applyFilters);
    S.f.radius = { circle, handle };
    btn.setAttribute("aria-pressed", "true"); $("#radiusCtl").hidden = false;
  }
  applyFilters();
}

/* ------------------------------------------------------------------ filters and list */
function buildFilters() {
  const tb = $("#typeButtons");
  tb.innerHTML = TYPES.map(t => {
    const n = S.events.filter(e => e.event_type === t.key).length;
    return `<button class="type-btn" data-type="${t.key}" aria-pressed="false" style="--c:${t.color}"><i></i>${t.label} <span class="n">${n}</span></button>`;
  }).join("");
  tb.addEventListener("click", ev => {
    const b = ev.target.closest(".type-btn"); if (!b) return;
    const k = b.dataset.type;
    S.f.types.has(k) ? S.f.types.delete(k) : S.f.types.add(k);
    b.setAttribute("aria-pressed", S.f.types.has(k));
    applyFilters();
  });
  $("#fArchetype").insertAdjacentHTML("beforeend", Object.entries(ARCH).map(([k, v]) => `<option value="${k}">${v}s</option>`).join(""));
  const dates = S.events.map(e => e.date).sort();
  for (const id of ["#fFrom", "#fTo"]) { $(id).min = dates[0]; $(id).max = dates[dates.length - 1]; }
  const maxCost = Math.ceil(Math.max(...S.events.map(e => e.value.event_cost)) / 10) * 10;
  Object.assign($("#fCost"), { max: maxCost, value: maxCost });
  $("#fCostOut").textContent = gbp(maxCost);
  const on = (id, ev, fn) => $(id).addEventListener(ev, fn);
  on("#fArchetype", "change", e => { S.f.arche = e.target.value; applyFilters(); });
  on("#fFrom", "change", e => { S.f.from = e.target.value; applyFilters(); });
  on("#fTo", "change", e => { S.f.to = e.target.value; applyFilters(); });
  on("#fSetting", "change", e => { S.f.setting = e.target.value; applyFilters(); });
  on("#fCost", "input", e => { S.f.maxCost = +e.target.value; $("#fCostOut").textContent = gbp(+e.target.value); applyFilters(); });
  on("#search", "input", e => { S.f.search = e.target.value.trim().toLowerCase(); applyFilters(); });
  on("#sortBy", "change", e => { S.sort = e.target.value; renderList(); });
  on("#fRadius", "click", toggleRadius);
  on("#radiusKm", "input", e => {
    $("#radiusOut").textContent = `${e.target.value} km`;
    if (S.f.radius) { S.f.radius.circle.setRadius(e.target.value * 1000); applyFilters(); }
  });
  on("#fClear", "click", () => {
    S.f.types.clear(); document.querySelectorAll(".type-btn").forEach(b => b.setAttribute("aria-pressed", "false"));
    Object.assign(S.f, { arche: "", from: "", to: "", setting: "", maxCost: Infinity, search: "" });
    for (const id of ["#fArchetype", "#fFrom", "#fTo", "#fSetting", "#search"]) $(id).value = "";
    $("#fCost").value = $("#fCost").max; $("#fCostOut").textContent = gbp(+$("#fCost").max);
    if (S.f.radius) toggleRadius(); else applyFilters();
  });
}

function matches(e) {
  const f = S.f, aud = S.audience[e.id];
  if (f.types.size && !f.types.has(e.event_type)) return false;
  if (f.arche && aud.top_archetypes[0] !== f.arche) return false;
  if (f.from && e.date < f.from) return false;
  if (f.to && e.date > f.to) return false;
  if (f.setting !== "" && String(e.indoor) !== f.setting) return false;
  if (e.value.event_cost > f.maxCost) return false;
  if (f.search) {
    const hay = [e.title, e.description, e.category, ...e.brand_names, ...Object.values(e.products)].join(" ").toLowerCase();
    if (!hay.includes(f.search)) return false;
  }
  if (f.radius && S.map.distance([e.latitude, e.longitude], f.radius.circle.getLatLng()) > f.radius.circle.getRadius()) return false;
  return true;
}

function applyFilters() {
  S.filtered = S.events.filter(matches);
  $("#liveCount").textContent = `${S.filtered.length} of ${S.events.length} events`;
  renderList(); renderMarkers(); renderTimeline(); renderTray();
}

function sorted(list) {
  const by = {
    net: (a, b) => b.value.net_value - a.value.net_value, match: (a, b) => b.match - a.match,
    date: (a, b) => a.start.localeCompare(b.start), distance: (a, b) => a.km_from_london - b.km_from_london,
    cost: (a, b) => a.value.event_cost - b.value.event_cost,
  }[S.sort];
  return [...list].sort(by);
}

function rowFor(id) { return document.querySelector(`.row[data-id="${CSS.escape(id)}"]`); }

function renderList() {
  const ol = $("#eventList");
  const list = sorted(S.filtered);
  S.listOrder = list.map(e => e.id);
  if (!list.length) {
    ol.innerHTML = `<li class="empty-list"><img src="/design/rgc-brand-reference/assets/chain.webp" alt=""><p>No events match these filters.</p><p class="muted">Try clearing a filter.</p></li>`;
    return;
  }
  ol.innerHTML = list.map((e, i) => {
    const aud = S.audience[e.id], [a1, a2] = aud.top_archetypes;
    const inPlan = S.plan.includes(e.id);
    return `<li class="row${e.id === S.selected ? " active" : ""}" data-id="${e.id}" role="option" aria-selected="${e.id === S.selected}" style="--c:${TYPE[e.event_type].color};--fit:${FIT(e.match)};animation-delay:${Math.min(i, 12) * 25}ms">
      <span class="dot" title="${TYPE[e.event_type].label}"></span>
      <h3>${esc(e.title)}</h3>
      <span class="score" title="Archetype match">${Math.round(e.match * 100)}</span>
      <span class="meta">${day(e.date)} · ${time(e.start)} · ${e.expected_attendance} people · ${Math.round(e.km_from_london)} km${inPlan ? " · in plan ✓" : ""}</span>
      <span class="chips"><span class="chip top">${ARCH[a1]} ${pct(aud.crowd[a1])}</span><span class="chip small">${ARCH[a2]} ${pct(aud.crowd[a2])}</span></span>
      <span class="why">${gbp(e.value.net_value)} net · ${Math.round(e.exp_reviews)} reviews · ${e.lineup_size} products</span>
    </li>`;
  }).join("");
}

function wireList() {
  const ol = $("#eventList");
  ol.addEventListener("click", ev => { const r = ev.target.closest(".row"); if (r) select(r.dataset.id, { fly: true }); });
  ol.addEventListener("mouseover", ev => {
    const r = ev.target.closest(".row"); if (!r) return;
    document.querySelectorAll(".pin.pulse").forEach(p => p.classList.remove("pulse"));
    pinEl(r.dataset.id)?.classList.add("pulse");
  });
  ol.addEventListener("mouseleave", () => document.querySelectorAll(".pin.pulse").forEach(p => p.classList.remove("pulse")));
  ol.addEventListener("keydown", ev => {
    const ids = S.listOrder || [];
    if (!ids.length) return;
    if (ev.key === "ArrowDown" || ev.key === "ArrowUp") {
      ev.preventDefault();
      S.cursor = Math.max(0, Math.min(ids.length - 1, S.cursor + (ev.key === "ArrowDown" ? 1 : -1)));
      document.querySelectorAll(".row.hl").forEach(r => r.classList.remove("hl"));
      const r = rowFor(ids[S.cursor]); r.classList.add("hl"); r.scrollIntoView({ block: "nearest" });
    } else if (ev.key === "Enter" && S.cursor >= 0) select(ids[S.cursor], { fly: true });
  });
}

/* ------------------------------------------------------------------ selection and detail panel */
function select(id, opts = {}) {
  S.selected = id; S.winnerHL = null; S.openTile = null;
  const e = S.byId[id];
  document.querySelectorAll(".row.active").forEach(r => { r.classList.remove("active"); r.setAttribute("aria-selected", "false"); });
  const r = rowFor(id);
  if (r) { r.classList.add("active"); r.setAttribute("aria-selected", "true"); r.scrollIntoView({ block: "nearest", behavior: REDUCED ? "auto" : "smooth" }); }
  S.cursor = (S.listOrder || []).indexOf(id);
  renderPanel();
  if (opts.fly && S.tab === "map") {
    const m = S.markers[id];
    S.cluster.zoomToShowLayer(m, () => {
      S.map.flyTo([e.latitude, e.longitude], Math.max(S.map.getZoom(), 13), { duration: REDUCED ? 0 : 0.8 });
      setTimeout(markSelectedPin, REDUCED ? 0 : 850);
    });
  }
  markSelectedPin();
  renderTimeline();
}

function closePanel() {
  S.selected = null;
  $("#panelBody").hidden = true; $("#panelEmpty").hidden = false;
  $("#panel").style.removeProperty("--glow");
  document.querySelectorAll(".row.active").forEach(r => r.classList.remove("active"));
  markSelectedPin(); renderTimeline();
}

function stockShortfalls(planIds) {
  const need = {};
  for (const id of planIds) {
    const e = S.byId[id];
    for (const b of e.brands) need[b] = (need[b] || 0) + e.units_by_size[b][S.size];
  }
  return Object.entries(need).filter(([b, n]) => n > S.brands[b].stock).map(([b, n]) => ({ b, n, have: S.brands[b].stock }));
}

function renderPanel() {
  const e = S.byId[S.selected]; if (!e) return;
  const aud = S.audience[e.id], t = TYPE[e.event_type];
  $("#panel").style.setProperty("--glow", t.color);
  $("#panelEmpty").hidden = true;
  const body = $("#panelBody"); body.hidden = false;
  const crowd = Object.entries(aud.crowd).sort((a, b) => b[1] - a[1]);
  const [a1, a2] = aud.top_archetypes;
  const winsOf = pid => Object.entries(e.archetype_winner).filter(([, p]) => p === pid).map(([a]) => a)
    .sort((x, y) => aud.crowd[y] - aud.crowd[x]);
  const inPlan = S.plan.includes(e.id);
  const short = stockShortfalls(inPlan ? S.plan : [...S.plan, e.id]).filter(s => e.brands.includes(s.b));
  const c = e.checks;
  const checks = [
    ["Vegan option", c.vegan], ["Gluten-free option", c.gluten_free], ["Chilled: 2 or fewer", c.chilled_ok],
    [e.adults_restricted ? "No alcohol or CBD here" : "Alcohol & CBD allowed", c.alcohol_ok],
    [short.length ? "Not enough in the warehouse" : "In stock (assumed)", c.in_stock && !short.length],
  ];
  const tv = e.value, hv = e.habit_value;
  const cmp = [
    ["Archetype match", e.match.toFixed(2), e.habit_match.toFixed(2), e.match >= e.habit_match],
    ["Expected reviews", Math.round(e.exp_reviews), Math.round(e.habit_exp_reviews), e.exp_reviews >= e.habit_exp_reviews],
    ["Review income", gbp(tv.review_value), gbp(hv.review_value), tv.review_value >= hv.review_value],
    ["Product given", gbp(tv.product_cost), gbp(hv.product_cost), tv.product_cost <= hv.product_cost],
    ["Event cost", gbp(tv.event_cost), gbp(hv.event_cost), true],
    ["Net value", gbp(tv.net_value), gbp(hv.net_value), tv.net_value >= hv.net_value],
    ["Chance of a loss", pct(tv.p_waste), pct(hv.p_waste), tv.p_waste <= hv.p_waste],
  ];
  const habitNames = e.habit_brands.map(b => S.brands[b]?.name || b).join(", ");
  body.innerHTML = `
    <button class="close" id="closePanel" aria-label="Close details">×</button>
    <span class="badge" style="--c:${t.color}">${t.label}</span>
    <h2>${esc(e.title)}</h2>
    <dl class="facts">
      <dt>Date</dt><dd>${day(e.date)} · ${time(e.start)}–${time(e.end)}</dd>
      <dt>Attendance</dt><dd>${e.expected_attendance} expected</dd>
      <dt>Where</dt><dd>${Math.round(e.km_from_london)} km from London · ${e.indoor ? "indoor" : "outdoor"}</dd>
      <dt>Event cost</dt><dd>${gbp(tv.event_cost)} (pitch, insurance, consumables, transport, staff food)</dd>
      <dt>Pop-up code</dt><dd class="mono">${popupCode(e)}</dd>
    </dl>
    ${e.description ? `<p class="desc">${esc(e.description.replace(/^Sourced from predicthq\.com - /i, ""))}</p>` : ""}

    <h3 class="eyebrow">Who is attending</h3>
    <p class="summary">Mostly ${ARCH[a1].toLowerCase()}s and ${ARCH[a2].toLowerCase()}s.</p>
    <div class="bars">${crowd.map(([a, v], i) => `
      <button class="bar${i === 0 ? " top" : ""}${S.winnerHL === a ? " on" : ""}" data-arch="${a}" title="Highlight the product that wins ${ARCH[a].toLowerCase()}s">
        <span>${ARCH[a]}</span><span class="track"><span class="fill" style="width:${(v / crowd[0][1]) * 100}%"></span></span><span>${pct(v)}</span>
      </button>`).join("")}</div>
    <p class="note">${esc(aud.source_note)}. Click a bar to see which product wins that group.</p>

    <h3 class="eyebrow">Bring</h3>
    <div class="size-toggle" role="group" aria-label="Stall size">
      ${["small", "medium", "large"].map(s => `<button data-size="${s}" aria-pressed="${S.size === s}">${s}</button>`).join("")}
    </div>
    <div class="shelf">${e.brands.map(b => {
      const pid = e.product_ids[b], wins = winsOf(pid);
      return `<button class="tile${S.winnerHL && e.archetype_winner[S.winnerHL] === pid ? " win" : ""}" data-brand="${b}" aria-expanded="${S.openTile === b}">
        <span class="brand">${esc(S.brands[b]?.name || b)}</span>
        <span class="prod">${esc(e.products[b])}</span>
        <span class="units">${e.units_by_size[b][S.size]} <small>units</small></span>
        <span class="rev">~${e.product_reviews[b]} reviews · match ${Math.round(e.product_matches[b] * 100)}</span>
        ${wins.length ? `<span class="wins">${wins.slice(0, 2).map(a => `<span>Wins ${ARCH[a].toLowerCase()}s</span>`).join("")}</span>` : ""}
      </button>`;
    }).join("")}
      ${S.openTile ? tileReasons(e, S.openTile) : ""}
    </div>
    <p class="slot">Best time: ${esc(e.slot)} · ${esc(e.size_line)} · ${S.size} stall</p>

    <h3 class="eyebrow">Lineup checks</h3>
    <div class="checks">${checks.map(([l, ok]) => `<span class="check${ok ? "" : " bad"}">${ok ? "✓" : "✕"} ${l}</span>`).join("")}</div>
    ${short.length ? `<p class="note" style="color:#FFB4AA">${short.map(s => `${esc(S.brands[s.b].name)}: plan needs ${s.n}, warehouse has ${s.have}`).join("; ")}</p>` : ""}

    <h3 class="eyebrow">Why</h3>
    <ul class="why">${e.reasons.map(r => `<li>${esc(r)}</li>`).join("")}</ul>

    <h3 class="eyebrow">Versus the usual lineup</h3>
    <table class="compare"><thead><tr><th></th><th>PopUpPick</th><th>Usual</th></tr></thead><tbody>
      ${cmp.map(([l, a, b, win]) => `<tr><td>${l}</td><td class="${win ? "win" : ""}">${a}</td><td>${b}</td></tr>`).join("")}
    </tbody></table>
    <p class="note">Usual lineup: ${esc(habitNames)}. Expected ${Math.round(e.exp_signups)} new WatchHumans sign-ups and ~${Math.round(tv.est_video_views).toLocaleString("en-GB")} video views.</p>
    <p class="synthetic">Synthetic data, not a measured result.</p>
    ${inPlan ? `<button class="ghost" id="removeFromPlan" style="width:100%;margin-top:18px">In the plan · remove</button>`
             : `<button class="cta" id="addToPlan">Add to plan</button>`}
  `;
  body.querySelector("#closePanel").addEventListener("click", closePanel);
  body.querySelectorAll(".bar").forEach(b => b.addEventListener("click", () => {
    S.winnerHL = S.winnerHL === b.dataset.arch ? null : b.dataset.arch; renderPanel();
  }));
  body.querySelectorAll(".size-toggle button").forEach(b => b.addEventListener("click", () => {
    S.size = b.dataset.size; renderPanel(); renderTray();
  }));
  body.querySelectorAll(".tile").forEach(b => b.addEventListener("click", () => {
    S.openTile = S.openTile === b.dataset.brand ? null : b.dataset.brand; renderPanel();
  }));
  body.querySelector("#addToPlan")?.addEventListener("click", ev => addToPlan(e.id, ev.currentTarget));
  body.querySelector("#removeFromPlan")?.addEventListener("click", () => removeFromPlan(e.id));
}

function tileReasons(e, b) {
  const r = S.scores[`${e.id}|${b}`]; if (!r) return "";
  return `<div class="tile-reasons"><b>${esc(S.brands[b]?.name || b)}</b> · expected ${(+r.exp_reviews).toFixed(1)} reviews
    <ul>${[r.reason_1, r.reason_2, r.reason_3].filter(Boolean).map(x => `<li>${esc(x)}</li>`).join("")}</ul></div>`;
}

/* ------------------------------------------------------------------ plan tray */
function capacity() { return +$("#tlCapacity").value; }

function addToPlan(id, fromEl) {
  if (S.plan.includes(id)) return;
  S.plan.push(id);
  if (fromEl && !REDUCED) {
    const a = fromEl.getBoundingClientRect(), t = $("#trayItems").getBoundingClientRect();
    const f = document.createElement("div"); f.className = "fly"; f.textContent = "+ " + S.byId[id].title.slice(0, 28);
    f.style.left = `${a.left}px`; f.style.top = `${a.top}px`; document.body.appendChild(f);
    requestAnimationFrame(() => { f.style.transform = `translate(${t.left - a.left + 20}px, ${t.top - a.top}px) scale(.8)`; f.style.opacity = "0"; });
    setTimeout(() => f.remove(), 750);
  }
  toast(`Added to the plan · pop-up code ${popupCode(S.byId[id])}`);
  refreshAfterPlan();
}
function removeFromPlan(id) { S.plan = S.plan.filter(x => x !== id); refreshAfterPlan(); }
function refreshAfterPlan() { renderTray(); renderList(); renderTimeline(); if (S.selected) renderPanel(); }

function planDates(ids) {
  const c = {}; ids.forEach(id => { const d = S.byId[id].date; c[d] = (c[d] || 0) + 1; });
  return c;
}

function renderTray() {
  const ids = S.plan, cap = capacity();
  const reviews = ids.reduce((s, id) => s + S.byId[id].exp_reviews, 0);
  const hRev = ids.reduce((s, id) => s + S.byId[id].habit_exp_reviews, 0);
  const net = ids.reduce((s, id) => s + S.byId[id].value.net_value, 0);
  const hNet = ids.reduce((s, id) => s + S.byId[id].habit_value.net_value, 0);
  const brands = new Set(ids.flatMap(id => S.byId[id].brands));
  const short = stockShortfalls(ids);
  const dates = planDates(ids), clashes = Object.entries(dates).filter(([, n]) => n > 1).map(([d]) => d);
  const over = ids.length > cap;
  $("#tray").classList.toggle("over", over);
  $("#trayStats").innerHTML = ids.length ? `
    <span class="${over ? "amber" : ""}">Pop-ups <b>${ids.length}</b> of ${cap}${over ? " · over capacity" : ""}</span>
    <span>Reviews <b>${Math.round(reviews)}</b> vs usual ${Math.round(hRev)} (${hRev ? signedPct(reviews / hRev - 1) : "–"})</span>
    <span>Net value <b>${gbp(net)}</b> vs usual ${gbp(hNet)}</span>
    <span>Brands featured <b>${brands.size}</b> of ${Object.keys(S.brands).length} <span class="muted">(clients don't pay for placement)</span></span>
    <span class="${short.length ? "warn" : ""}">${short.length ? `Not enough in the warehouse: ${short.map(s => esc(S.brands[s.b].name)).join(", ")}` : "Stock OK (stock is an assumption)"}</span>
    ${clashes.length ? `<span class="amber">Date clash: ${clashes.map(day).join(", ")}</span>` : ""}`
    : `<span class="muted">Add events to build a plan. RGC usually runs ${cap} a month.</span>`;
  $("#trayItems").innerHTML = ids.map((id, i) => {
    const e = S.byId[id];
    return `<li class="tray-item${dates[e.date] > 1 ? " clash" : ""}" style="--c:${TYPE[e.event_type].color}">
      <span class="dot"></span>
      <span class="nm" data-id="${id}">${esc(e.title)}</span>
      <span class="acts">
        <button data-act="up" data-i="${i}" aria-label="Move earlier" ${i === 0 ? "disabled" : ""}>↑</button>
        <button data-act="down" data-i="${i}" aria-label="Move later" ${i === ids.length - 1 ? "disabled" : ""}>↓</button>
        <button data-act="rm" data-i="${i}" aria-label="Remove from plan">✕</button>
      </span>
      <span class="code">${popupCode(e)} · ${day(e.date)} · ${gbp(e.value.net_value)}</span>
    </li>`;
  }).join("") || "";
}

function wireTray() {
  $("#trayItems").addEventListener("click", ev => {
    const nm = ev.target.closest(".nm"); if (nm) { select(nm.dataset.id, { fly: true }); return; }
    const b = ev.target.closest("button[data-act]"); if (!b) return;
    const i = +b.dataset.i, p = S.plan;
    if (b.dataset.act === "rm") p.splice(i, 1);
    if (b.dataset.act === "up" && i > 0) [p[i - 1], p[i]] = [p[i], p[i - 1]];
    if (b.dataset.act === "down" && i < p.length - 1) [p[i + 1], p[i]] = [p[i], p[i + 1]];
    refreshAfterPlan();
  });
  $("#exportRequests").addEventListener("click", exportRequests);
  $("#tlCapacity").addEventListener("change", () => { renderTray(); renderTimeline(); });
}

async function exportRequests() {
  if (!S.plan.length) { toast("Add events to the plan first"); return; }
  const rows = S.plan.flatMap(id => {
    const e = S.byId[id];
    return e.brands.map(b => ({ brand: S.brands[b]?.name || b, product: e.products[b], units: e.units_by_size[b][S.size],
      event: e.title, date: e.date, popup_code: popupCode(e) }));
  });
  const cols = ["brand", "product", "units", "event", "date", "popup_code"];
  const q = v => `"${String(v).replace(/"/g, '""')}"`;
  const csv = [cols.join(","), ...rows.map(r => cols.map(c => q(r[c])).join(","))].join("\n");
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([csv], { type: "text/csv" })); a.download = "requests.csv"; a.click();
  try {
    const r = await fetch("/api/requests", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(rows) });
    toast(r.ok ? `Request list: ${rows.length} lines, downloaded and saved to outputs/requests.csv` : "Downloaded the request list");
  } catch { toast("Downloaded the request list"); }
}

/* ------------------------------------------------------------------ timeline (month plan) */
function buildTimelineControls() {
  const months = [...new Set(S.events.map(e => e.date.slice(0, 7)))].sort();
  $("#tlMonth").innerHTML = months.map(m => `<option value="${m}">${new Date(m + "-01T12:00").toLocaleDateString("en-GB", { month: "long", year: "numeric" })}</option>`).join("");
  if (months.includes(S.month.month)) $("#tlMonth").value = S.month.month;
  $("#tlMonth").addEventListener("change", renderTimeline);
  $("#useRecommended").addEventListener("click", () => {
    if ($("#tlMonth").value !== S.month.month) { toast("No recommended plan for this month"); return; }
    S.plan = S.month.popups.map(p => p.event_id).filter(id => S.byId[id]);
    $("#tlCapacity").value = String(S.month.capacity);
    toast(`Loaded the recommended plan: ${S.plan.length} pop-ups, ${gbp(S.month.net_value)} net`);
    refreshAfterPlan();
  });
}

function renderTimeline() {
  if (!S.month) return;
  const m = $("#tlMonth").value;
  const evs = S.filtered.filter(e => e.date.startsWith(m)).sort((a, b) => a.start.localeCompare(b.start));
  const dates = planDates(S.plan);
  const weeks = {};
  for (const e of evs) {
    const d = new Date(e.date + "T12:00"), monday = new Date(d); monday.setDate(d.getDate() - ((d.getDay() + 6) % 7));
    const wk = monday.toISOString().slice(0, 10);
    ((weeks[wk] ??= {})[e.date] ??= []).push(e);
  }
  const recNet = S.month.month === m ? S.month.net_value : null;
  const myNet = S.plan.filter(id => S.byId[id].date.startsWith(m)).reduce((s, id) => s + S.byId[id].value.net_value, 0);
  const note = $("#tlNote");
  const clash = Object.values(dates).some(n => n > 1), over = S.plan.length > capacity();
  note.className = "tl-note" + (clash || over ? " warn" : "");
  note.textContent = [
    recNet != null ? `Recommended: ${S.month.popups.length} pop-ups, ${gbp(recNet)} net vs ${gbp(S.month.habit_net_value)} usual · ${S.month.skipped_events} likely losses skipped` : "",
    S.plan.length ? `Your plan this month: ${gbp(myNet)} net` : "",
    clash ? "Two pop-ups on one day" : "", over ? "Over capacity" : "",
  ].filter(Boolean).join(" · ");
  $("#timeline").innerHTML = Object.keys(weeks).length ? Object.entries(weeks).map(([wk, days]) => `
    <div class="tl-week"><h3 class="eyebrow">Week of ${day(wk)}</h3><div class="tl-days">
      ${Object.entries(days).map(([d, list]) => `<div class="tl-day${dates[d] > 1 ? " clash" : ""}"><h4>${day(d)}</h4>
        ${list.map(e => `<button class="tl-event${S.plan.includes(e.id) ? " inplan" : ""}${e.id === S.selected ? " active" : ""}" data-id="${e.id}" style="--c:${TYPE[e.event_type].color}">
          <span class="t">${time(e.start)} · ${TYPE[e.event_type].label} · match ${Math.round(e.match * 100)}</span>${esc(e.title)}
          <span class="t">${gbp(e.value.net_value)} net${S.plan.includes(e.id) ? " · in plan ✓" : ""}</span></button>`).join("")}
      </div>`).join("")}
    </div></div>`).join("")
    : `<div class="empty-list"><img src="/design/rgc-brand-reference/assets/chain.webp" alt=""><p>No events this month with these filters.</p></div>`;
}

function wireTimeline() {
  $("#timeline").addEventListener("click", ev => { const b = ev.target.closest(".tl-event"); if (b) select(b.dataset.id); });
}

/* ------------------------------------------------------------------ tabs */
function setTab(tab) {
  S.tab = tab;
  $("#tabMap").setAttribute("aria-selected", tab === "map"); $("#tabTimeline").setAttribute("aria-selected", tab === "timeline");
  $("#mapView").hidden = tab !== "map"; $("#timelineView").hidden = tab !== "timeline";
  if (tab === "map") setTimeout(() => { S.map.invalidateSize(); markSelectedPin(); }, 0);
  else renderTimeline();
}

/* ------------------------------------------------------------------ impact drawer */
function rangeBar(lo, hi, pt, fmt) {
  const min = Math.min(0, lo) - Math.abs(hi - lo) * 0.25, max = Math.max(hi, pt) + Math.abs(hi - lo) * 0.25;
  const x = v => ((v - min) / (max - min)) * 100;
  return `<div class="range" role="img" aria-label="${fmt(pt)}, 95% interval ${fmt(lo)} to ${fmt(hi)}">
    <span class="axis"></span><span class="zero" style="left:${x(0)}%"></span>
    <span class="ci" style="left:${x(lo)}%;width:${x(hi) - x(lo)}%"></span><span class="pt" style="left:${x(pt)}%"></span></div>
    <p class="note">${fmt(lo)} to ${fmt(hi)} (95% interval) · line = no change</p>`;
}

function renderImpact() {
  const I = S.impact, M = S.month;
  const maxR = Math.max(...I.per_popup.map(p => Math.max(p.reviews_tool, p.reviews_habit)));
  $("#impactBody").innerHTML = `
    <p class="eyebrow" style="color:var(--rgc-muted-on-dark)">Impact against how RGC plans today</p>
    <div class="big">${gbp(I.monthly_impact_gbp)}<span style="font-size:20px"> / month</span></div>
    <p>${gbp(I.monthly_lineup_gain_gbp)} from better lineups + ${gbp(I.monthly_time_saved_gbp)} of marketing time (${I.monthly_hours_saved} h). About ${gbp(I.yearly_impact_gbp)} a year.</p>
    <p class="synthetic">Synthetic data, not a measured result.</p>
    <h3 class="eyebrow" style="margin-top:22px;color:var(--rgc-muted-on-dark)">Reviews per pop-up: ${signedPct(I.review_uplift)}</h3>
    ${rangeBar(I.review_ci_low, I.review_ci_high, I.review_uplift, signedPct)}
    <h3 class="eyebrow" style="margin-top:18px;color:var(--rgc-muted-on-dark)">Net value per pop-up: ${gbp(I.net_gain_per_popup)} more</h3>
    ${rangeBar(I.net_gain_ci_low, I.net_gain_ci_high, I.net_gain_per_popup, gbp)}
    <div class="kpis">
      <div class="kpi"><div class="v">${gbp(I.net_value_tool)}</div><div class="l">Net per pop-up, PopUpPick</div></div>
      <div class="kpi"><div class="v">${gbp(I.net_value_habit)}</div><div class="l">Net per pop-up, usual lineup</div></div>
      <div class="kpi"><div class="v">${I.reviews_tool.toFixed(1)} vs ${I.reviews_habit.toFixed(1)}</div><div class="l">Reviews per pop-up</div></div>
      <div class="kpi"><div class="v">${pct(I.waste_rate_tool)} vs ${pct(I.waste_rate_habit)}</div><div class="l">Pop-ups that lose money</div></div>
      <div class="kpi"><div class="v">${gbp(M.net_value)} vs ${gbp(M.habit_net_value)}</div><div class="l">${M.month} plan vs usual</div></div>
      <div class="kpi"><div class="v">${I.poisson_test_deviance.toFixed(2)} vs ${I.footfall_baseline_test_deviance.toFixed(2)}</div><div class="l">Sign-up forecast error vs footfall guess</div></div>
    </div>
    <h3 class="eyebrow" style="color:var(--rgc-muted-on-dark)">${I.n_test} held-out pop-ups: reviews, PopUpPick vs usual</h3>
    <div class="pairs">${I.per_popup.map((p, i) => `
      <button class="pair${S.pair === i ? " on" : ""}" data-i="${i}">
        <span class="lbl">${p.popup_id}</span>
        <span class="bars2"><span class="b t" style="width:${p.reviews_tool / maxR * 100}%"></span><span class="b h" style="width:${p.reviews_habit / maxR * 100}%"></span></span>
      </button>`).join("")}</div>
    <p class="note"><span style="color:#C2FF00">■</span> PopUpPick · <span style="opacity:.6">■</span> usual lineup. Click a pop-up for details.</p>
    <div class="pair-detail" id="pairDetail">${S.pair != null ? pairText(I.per_popup[S.pair]) : ""}</div>
    <p class="note">${esc(I.method)}.</p>`;
  $("#impactBody").querySelectorAll(".pair").forEach(b => b.addEventListener("click", () => { S.pair = +b.dataset.i; renderImpact(); }));
}
function pairText(p) {
  return `${p.popup_id} · ${TYPE[p.event_type]?.label || p.event_type} · ${p.footfall} people · PopUpPick brought ${p.tool_lineup.map(b => S.brands[b]?.name || b).join(", ")} · reviews ${p.reviews_tool} vs ${p.reviews_habit} · net ${gbp(p.net_value_tool)} vs ${gbp(p.net_value_habit)}`;
}
function openImpact() { S.lastFocus = document.activeElement; $("#impactDrawer").hidden = false; renderImpact(); $("#closeImpact").focus(); }
function closeImpact() { $("#impactDrawer").hidden = true; S.lastFocus?.focus(); }

function renderStrip() {
  const I = S.impact;
  $("#upliftStrip").innerHTML = `<b>${gbp(I.monthly_impact_gbp)}</b>/month · <b>${signedPct(I.review_uplift)}</b> reviews<br><span class="tag">synthetic data, not a measured result</span>`;
}

let toastTimer;
function toast(msg) { const t = $("#toast"); t.textContent = msg; t.hidden = false; clearTimeout(toastTimer); toastTimer = setTimeout(() => (t.hidden = true), 3200); }

/* ------------------------------------------------------------------ start */
async function main() {
  const nosplash = new URLSearchParams(location.search).has("nosplash");
  wireSplash();
  if (nosplash) splash.node.remove(); else startSplash();
  try { await loadData(); }
  catch (err) {
    splash.node.querySelector(".splash-loading").hidden = false;
    splash.node.querySelector(".splash-loading").textContent = "Couldn't load the outputs: run python app.py";
    console.error(err); return;
  }
  initMap(); buildFilters(); buildTimelineControls();
  wireList(); wireTray(); wireTimeline();
  $("#tabMap").addEventListener("click", () => setTab("map"));
  $("#tabTimeline").addEventListener("click", () => setTab("timeline"));
  $("#openImpact").addEventListener("click", openImpact);
  $("#closeImpact").addEventListener("click", closeImpact);
  $("#impactDrawer").addEventListener("click", e => { if (e.target.id === "impactDrawer") closeImpact(); });
  document.addEventListener("keydown", e => {
    if (e.key !== "Escape") return;
    if (!$("#impactDrawer").hidden) closeImpact(); else if (S.selected) closePanel();
  });
  renderStrip();
  applyFilters();
  fitAll();
  S.ready = true;
  if (nosplash || splash.pending) tryPop();
}
main();
