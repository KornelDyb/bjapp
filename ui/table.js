// Ekran Stół: stawka, rozdanie, decyzje z korektą na żywo.
import { call } from "./api.js";

const CHIPS = [1, 5, 10, 25, 50, 100];
const ACTIONS = [["H", "Dobierz"], ["S", "Stój"], ["D", "Podwój"], ["P", "Rozdziel"], ["R", "Poddaj"]];
const RESULT = { win: "Wygrana", lose: "Przegrana", push: "Remis", blackjack: "Blackjack!", bust: "Przebicie", surrender: "Poddanie" };
const RED = new Set(["♥", "♦"]);
const DEAL_MS = 250, STAGGER = 140;

const fmtUnits = (v) => `${v > 0 ? "+" : v < 0 ? "−" : ""}${Math.abs(v).toLocaleString("pl-PL", { maximumFractionDigits: 1 })}`;
const rankLabel = (r) => (r === "T" ? "10" : r);

const S = { bet: 10, state: null, stats: null, feedback: null, details: false, busy: false, prev: { dealer: 0, hands: [], hidden: false } };

export function tableScreen(root, describeRules, rules) {
  root.innerHTML = `
    <header class="screen-head">
      <div><h1>Stół</h1><p class="muted" id="table-rules">${rules ? describeRules(rules) : ""}</p></div>
      <div class="chips">
        <div class="chip glass"><span class="muted">Trafność</span><strong class="num" id="st-acc">—</strong></div>
        <div class="chip glass"><span class="muted">Rozdania</span><strong class="num" id="st-hands">0</strong></div>
        <div class="chip glass"><span class="muted">Wynik</span><strong class="num" id="st-net">0</strong></div>
      </div>
    </header>
    <section class="felt glass" id="felt">
      <div class="zone dealer-zone"><span class="label muted">Krupier <b class="num total" id="dealer-total"></b></span><div class="card-row" id="dealer-cards"></div></div>
      <div class="center" id="center"></div>
      <div class="zone"><div class="hands" id="hands"></div><span class="label muted">Ty</span></div>
    </section>
    <section class="feedback glass" id="feedback" hidden></section>
    <footer class="actions" id="controls"></footer>`;
  S.prev = { dealer: 0, hands: [], hidden: false };
  draw(false);
  return onKey;
}

function onKey(e) {
  if (e.ctrlKey || e.metaKey || e.altKey) return false;
  const k = e.key.toUpperCase();
  if (e.key === " ") {
    if (S.state?.phase !== "player") { deal(); return true; }
    return true;
  }
  if (S.state?.phase === "player" && S.state.legal.includes(k)) { act(k); return true; }
  return false;
}

async function deal() {
  if (S.busy) return;
  S.busy = true;
  try {
    const r = await call("table_new_round", S.bet);
    S.state = r.state; S.stats = r.stats; S.feedback = null;
    S.prev = { dealer: 0, hands: [], hidden: false };
    draw(true);
  } catch { /* toast już pokazany */ } finally { S.busy = false; }
}

async function act(a) {
  if (S.busy) return;
  S.busy = true;
  try {
    const r = await call("table_act", a);
    S.state = r.state; S.stats = r.stats; S.feedback = r.feedback;
    flash(r.feedback.correct);
    draw(true);
  } catch { } finally { S.busy = false; }
}

function flash(ok) {
  const felt = document.getElementById("felt");
  felt.classList.remove("flash-ok", "flash-bad");
  void felt.offsetWidth;
  felt.classList.add(ok ? "flash-ok" : "flash-bad");
}

function cardEl(c, delay, flip) {
  const el = document.createElement("div");
  if (c.hidden) { el.className = "card back"; }
  else {
    const red = RED.has(c.suit);
    el.className = `card face${red ? " red" : ""}`;
    el.innerHTML = `<span class="corner">${rankLabel(c.rank)}<i>${c.suit}</i></span><span class="pip">${c.suit}</span><span class="corner br">${rankLabel(c.rank)}<i>${c.suit}</i></span>`;
    el.setAttribute("aria-label", `${rankLabel(c.rank)} ${c.suit}`);
  }
  if (delay !== null) { el.classList.add(flip ? "flip" : "deal"); el.style.animationDelay = `${delay}ms`; }
  return el;
}

function draw(animate) {
  const st = S.state;
  // statystyki
  const s = S.stats;
  if (s) {
    document.getElementById("st-acc").textContent = s.accuracy === null ? "—" : `${Math.round(s.accuracy * 100)}%`;
    document.getElementById("st-hands").textContent = s.hands;
    const net = document.getElementById("st-net");
    net.textContent = fmtUnits(s.net);
    net.className = `num ${s.net > 0 ? "pos" : s.net < 0 ? "neg" : ""}`;
  }
  let delay = 0;
  const next = () => { const d = animate ? delay : null; delay += STAGGER; return d; };
  // kolejność animacji przy rozdaniu: gracz, krupier, gracz, (krupier)
  const dealerBox = document.getElementById("dealer-cards");
  const handsBox = document.getElementById("hands");
  if (!st) {
    dealerBox.innerHTML = `<div class="card ghost"></div><div class="card ghost"></div>`;
    handsBox.innerHTML = `<div class="hand"><div class="card-row"><div class="card ghost"></div><div class="card ghost"></div></div></div>`;
    document.getElementById("dealer-total").textContent = "";
  } else {
    const fresh = S.prev.dealer === 0;
    const delays = new Map();
    if (fresh && animate) {
      // pierwsze rozdanie: P1, D1, P2, D2
      delays.set("h0-0", 0); delays.set("d-0", STAGGER); delays.set("h0-1", 2 * STAGGER); delays.set("d-1", 3 * STAGGER);
      delay = (st.dealer.cards.length > 1 ? 4 : 3) * STAGGER;
    }
    // ręce gracza
    handsBox.innerHTML = "";
    st.hands.forEach((h, i) => {
      const box = document.createElement("div");
      box.className = `hand${st.active === i && st.hands.length > 1 ? " active" : ""}${h.result ? ` res-${h.result}` : ""}`;
      const row = document.createElement("div");
      row.className = "card-row";
      const prevN = S.prev.hands[i] ?? 0;
      h.cards.forEach((c, j) => {
        let d = null;
        if (animate && j >= prevN) d = delays.has(`h${i}-${j}`) ? delays.get(`h${i}-${j}`) : next();
        row.append(cardEl(c, d, false));
      });
      const meta = document.createElement("div");
      meta.className = "hand-meta";
      meta.innerHTML = `<b class="num">${h.soft && h.total <= 21 ? "miękkie " : ""}${h.total}</b>` +
        `<span class="muted num">stawka ${h.bet}</span>` +
        (h.result ? `<span class="res num">${RESULT[h.result]} ${fmtUnits(h.net)}</span>` : "");
      box.append(row, meta);
      handsBox.append(box);
    });
    // krupier (dobiera po graczu)
    dealerBox.innerHTML = "";
    st.dealer.cards.forEach((c, j) => {
      let d = null, flip = false;
      if (animate) {
        if (j === 1 && S.prev.hidden && !c.hidden) { d = next(); flip = true; }
        else if (j >= S.prev.dealer) d = delays.has(`d-${j}`) ? delays.get(`d-${j}`) : next();
      }
      dealerBox.append(cardEl(c, d, flip));
    });
    const dt = document.getElementById("dealer-total");
    dt.textContent = st.dealer.blackjack ? "Blackjack" : st.dealer.bust ? `${st.dealer.total} · przebicie` : st.dealer.total;
    S.prev = { dealer: st.dealer.cards.length, hands: st.hands.map((h) => h.cards.length), hidden: st.dealer.cards.some((c) => c.hidden) };
  }
  const doneAt = animate ? delay + DEAL_MS : 0;
  drawCenter(doneAt);
  drawFeedback();
  drawControls();
}

function drawCenter(after) {
  const c = document.getElementById("center");
  const st = S.state;
  c.innerHTML = "";
  if (!st) {
    c.innerHTML = `<p class="lead">Postaw i rozdaj</p><p class="muted">Wybierz stawkę i naciśnij <kbd>Spacja</kbd>.</p>`;
    return;
  }
  if (st.phase !== "done") return;
  const net = st.net;
  const kinds = st.hands.map((h) => h.result);
  const title = kinds.length === 1 ? RESULT[kinds[0]] : net > 0 ? "Wygrana" : net < 0 ? "Przegrana" : "Remis";
  const b = document.createElement("div");
  b.className = `banner ${net > 0 ? "pos" : net < 0 ? "neg" : ""}`;
  b.style.animationDelay = `${after}ms`;
  b.innerHTML = `<strong>${title}</strong><span class="num">${fmtUnits(net)}</span><span class="muted">Spacja — następne rozdanie</span>`;
  c.append(b);
}

function drawFeedback() {
  const box = document.getElementById("feedback");
  const f = S.feedback;
  if (!f) { box.hidden = true; return; }
  box.hidden = false;
  box.className = `feedback glass ${f.correct ? "ok" : "bad"}`;
  const cost = f.correct ? "" : `<span class="cost num">Ten błąd kosztuje średnio ${(f.cost * 100).toLocaleString("pl-PL", { maximumFractionDigits: 1 })}% stawki</span>`;
  const rows = f.evs.map((e) => `<li class="${e.action === f.best ? "best" : ""}${e.action === f.taken ? " taken" : ""}">
      <span>${e.name}${e.action === f.taken ? ' <em class="muted">(Twój ruch)</em>' : ""}</span><b class="num">${e.label}</b></li>`).join("");
  box.innerHTML = `
    <div class="fb-main">
      <span class="fb-icon" aria-hidden="true">${f.correct ? "✓" : "✕"}</span>
      <div class="fb-text"><strong>${f.correct ? "Dobrze" : "Błąd"}</strong><p>${f.sentence}</p>${cost}</div>
      ${f.evs.length ? `<button class="link" id="fb-toggle" aria-expanded="${S.details}">${S.details ? "Ukryj" : "Szczegóły"}</button>` : ""}
    </div>
    ${f.evs.length && S.details ? `<ul class="evs"><li class="muted head"><span>Ruch</span><span>Średni wynik (× stawka)</span></li>${rows}</ul>` : ""}`;
  box.querySelector("#fb-toggle")?.addEventListener("click", () => { S.details = !S.details; drawFeedback(); });
}

function drawControls() {
  const box = document.getElementById("controls");
  const st = S.state;
  if (st?.phase === "player") {
    box.innerHTML = ACTIONS.map(([k, n]) =>
      `<button class="btn" data-act="${k}" ${st.legal.includes(k) ? "" : "disabled"}><kbd>${k}</kbd> ${n}</button>`).join("");
    box.querySelectorAll("[data-act]").forEach((b) => b.addEventListener("click", () => act(b.dataset.act)));
  } else {
    box.innerHTML = `<div class="bet">
        <span class="muted">Stawka</span>
        ${CHIPS.map((c) => `<button class="chip-btn${c === S.bet ? " on" : ""}" data-bet="${c}" aria-pressed="${c === S.bet}">${c}</button>`).join("")}
      </div>
      <button class="btn primary" id="deal"><kbd>Spacja</kbd> Rozdaj</button>`;
    box.querySelectorAll("[data-bet]").forEach((b) => b.addEventListener("click", () => { S.bet = Number(b.dataset.bet); drawControls(); }));
    box.querySelector("#deal").addEventListener("click", deal);
  }
}

// dla testów i podglądu
export const _state = S;
