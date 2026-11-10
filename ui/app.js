// Frontend tylko wyświetla i wysyła akcje do Pythona (window.pywebview.api).
import { call } from "./api.js";
import { tableScreen } from "./table.js";

const SCREENS = {
  table:      { title: "Stół", render: (root) => { keyHandler = tableScreen(root, describeRules, currentRules, show); } },
  counting:   { title: "Liczenie", render: renderCounting },
  stats:      { title: "Statystyki", feature: "BJ-07", text: "Zagraj pierwsze 20 rozdań, żeby zobaczyć statystyki." },
  simulation: { title: "Symulacja",  feature: "BJ-08", text: "10 000 rozdań: Twój styl vs gra idealna vs z liczeniem." },
  cheatsheet: { title: "Ściąga",     feature: "BJ-04", text: "Tabela strategii podstawowej z podświetloną bieżącą sytuacją." },
  settings:   { title: "Ustawienia", render: renderSettings },
};

const content = document.getElementById("content");
const navItems = [...document.querySelectorAll(".nav-item")];

let keyHandler = null;

function show(screen) {
  keyHandler = null;
  const def = SCREENS[screen] ?? SCREENS.table;
  navItems.forEach((b) => b.dataset.screen === screen ? b.setAttribute("aria-current", "page") : b.removeAttribute("aria-current"));
  content.replaceChildren();
  content.style.animation = "none"; void content.offsetWidth; content.style.animation = "";
  if (def.render) {
    def.render(content);
  } else {
    content.innerHTML = `
      <header class="screen-head"><div><h1>${def.title}</h1></div></header>
      <section class="placeholder glass"><div>
        <span class="badge">${def.feature} · wkrótce</span>
        <p class="muted">${def.text}</p>
      </div></section>`;
  }
  document.title = `${def.title} · Trener Blackjacka`;
}

navItems.forEach((b) => b.addEventListener("click", () => show(b.dataset.screen)));
document.addEventListener("keydown", (e) => {
  if (e.target.closest("input, textarea, select")) return;
  if (keyHandler && keyHandler(e)) { e.preventDefault(); return; }
  if (e.key.toLowerCase() === "c" && !e.ctrlKey && !e.metaKey) show("cheatsheet");
});

function setStatus(state, text) {
  const dot = document.getElementById("status-dot");
  dot.className = `status-dot ${state}`;
  document.getElementById("status-text").textContent = text;
}

// ---------- Ustawienia: zasady stołu ----------
const RULE_FIELDS = [
  { key: "decks", label: "Liczba talii", options: [[1, "1"], [2, "2"], [4, "4"], [6, "6"], [8, "8"]] },
  { key: "hole_card", label: "Karta zakryta krupiera", options: [["enhc", "Brak (Europa)"], ["peek", "Jest, sprawdza BJ"]],
    hint: "W Europie krupier dobiera drugą kartę dopiero po Twoich ruchach." },
  { key: "enhc_obo", label: "Gdy krupier ma blackjacka", options: [[false, "Tracisz wszystko"], [true, "Tylko stawkę początkową"]],
    hint: "Dotyczy dopłat do podwojenia i rozdzielenia.", showIf: (r) => r.hole_card === "enhc" },
  { key: "h17", label: "Krupier na miękkich 17", options: [[false, "Stoi (S17)"], [true, "Dobiera (H17)"]] },
  { key: "das", label: "Podwojenie po rozdzieleniu", options: [[true, "Tak"], [false, "Nie"]] },
  { key: "surrender", label: "Poddanie", options: [[false, "Nie"], [true, "Tak"]] },
  { key: "blackjack_payout", label: "Wypłata za blackjacka", options: [[1.5, "3:2"], [1.2, "6:5"], [1, "1:1"]] },
];

const describeRules = (r) => [
  `${r.decks} ${r.decks === 1 ? "talia" : r.decks < 5 ? "talie" : "talii"}`,
  r.h17 ? "krupier dobiera na miękkich 17" : "krupier stoi na miękkich 17",
  r.hole_card === "enhc" ? "bez zakrytej karty" : "z zakrytą kartą",
  `blackjack ${{ 1.5: "3:2", 1.2: "6:5", 1: "1:1" }[r.blackjack_payout]}`,
].join(" · ");

async function renderSettings(root) {
  root.innerHTML = `<header class="screen-head"><div><h1>Ustawienia</h1>
    <p class="muted">Zasady stołu, przy którym grasz. Strategia przelicza się od razu.</p></div></header>
    <section class="glass settings" id="rules-form"><p class="muted">Ładowanie…</p></section>`;
  let rules, warnings;
  try { ({ rules, warnings } = await call("get_rules")); } catch { return; }
  const form = root.querySelector("#rules-form");

  const draw = () => {
    form.innerHTML = RULE_FIELDS.filter((f) => !f.showIf || f.showIf(rules)).map((f) => `
      <div class="field">
        <div class="field-label">${f.label}${f.hint ? `<span class="muted">${f.hint}</span>` : ""}</div>
        <div class="seg" role="radiogroup" aria-label="${f.label}">
          ${f.options.map(([v, l]) => `<button role="radio" aria-checked="${rules[f.key] === v}"
             data-key="${f.key}" data-val='${JSON.stringify(v)}'>${l}</button>`).join("")}
        </div>
      </div>`).join("") + `
      <div class="field">
        <div class="field-label">Penetracja buta<span class="muted">Ile kart wychodzi przed tasowaniem.</span></div>
        <div class="range"><input type="range" min="50" max="90" step="5" value="${Math.round(rules.penetration * 100)}" id="pen">
        <strong class="num" id="pen-val">${Math.round(rules.penetration * 100)}%</strong></div>
      </div>
      <div class="settings-foot">
        <span class="muted" id="rules-summary">${describeRules(rules)}</span>
        <span class="saved" id="saved" hidden>✓ Zapisano · strategia przeliczona</span>
      </div>
      ${warnings.map((w) => `<p class="warn">⚠ ${w}</p>`).join("")}`;
  };

  const save = async (changes) => {
    try {
      ({ rules, warnings } = await call("set_rules", changes));
      draw();
      const s = form.querySelector("#saved"); s.hidden = false;
      clearTimeout(save.t); save.t = setTimeout(() => { s.hidden = true; }, 2500);
      updateTableSubtitle(rules);
    } catch { draw(); }
  };

  form.addEventListener("click", (e) => {
    const b = e.target.closest("[data-key]");
    if (b) save({ [b.dataset.key]: JSON.parse(b.dataset.val) });
  });
  root.append(await countSettings());
  form.addEventListener("input", (e) => {
    if (e.target.id === "pen") form.querySelector("#pen-val").textContent = `${e.target.value}%`;
  });
  form.addEventListener("change", (e) => {
    if (e.target.id === "pen") save({ penetration: Number(e.target.value) / 100 });
  });
  draw();
}

// ---------- Liczenie: zasady Hi-Lo ----------
async function renderCounting(root) {
  let st = null;
  try { st = (await call("table_status")).stats; } catch { }
  const pct = (v) => (v === null || v === undefined ? "—" : `${Math.round(v * 100)}%`);
  root.innerHTML = `<header class="screen-head"><div><h1>Liczenie</h1>
    <p class="muted">Hi-Lo: licznik jest ukryty, a przy stole co kilka rozdań padnie pytanie o count.</p></div>
    <div class="chips"><div class="chip glass"><span class="muted">Trafność liczenia</span><strong class="num">${pct(st?.count_accuracy)}</strong></div>
    <div class="chip glass"><span class="muted">Pytań w sesji</span><strong class="num">${st?.count_checks ?? 0}</strong></div></div></header>
    <section class="info-grid">
      <div class="glass info"><h2>Wartości kart</h2>
        <div class="hilo"><div><b class="pos">+1</b><span>2 3 4 5 6</span></div><div><b>0</b><span>7 8 9</span></div><div><b class="neg">−1</b><span>10 J Q K A</span></div></div>
        <p class="muted">Running count = suma wartości wszystkich kart, które wyszły od tasowania. Po tasowaniu liczysz od zera.</p></div>
      <div class="glass info"><h2>True count</h2>
        <p class="formula num">true = running ÷ talie w bucie</p>
        <p class="muted">Przykład: running +6, w bucie zostały 3 talie → true +2. Odpowiedź uznaję, gdy różni się o najwyżej 0,5.</p></div>
      <div class="glass info"><h2>Kiedy liczenie ma sens</h2>
        <ul><li>Ręczne tasowanie lub but z kartą odcięcia — <b class="pos">tak</b>.</li>
        <li>Tasownica ciągła (karty wracają po każdym rozdaniu) — <b class="neg">nie</b>, count zawsze ≈ 0.</li>
        <li>Wysoki true count = więcej dziesiątek i asów w bucie = przewaga po Twojej stronie.</li>
        <li>Kasyno może poprosić o opuszczenie stołu, jeśli widać, że liczysz — graj spokojnie.</li></ul></div>
      <div class="glass info"><h2>Ustawienia</h2>
        <p class="muted">Jak często pytać i czy pokazywać licznik zmienisz w Ustawieniach albo przyciskiem „Licznik” na stole.</p>
        <button class="btn" id="to-settings">Przejdź do Ustawień</button></div>
    </section>`;
  root.querySelector("#to-settings").addEventListener("click", () => show("settings"));
}

const COUNT_FIELDS = [
  { key: "count.every", label: "Pytanie o count", def: 3, options: [[1, "Co rozdanie"], [3, "Co 3"], [5, "Co 5"], [0, "Wyłączone"]],
    hint: "Przed stawką, po ilu rozdaniach pytać o running i true count." },
  { key: "count.show", label: "Licznik na stole", def: false, options: [[false, "Ukryty"], [true, "Widoczny"]],
    hint: "Widoczny licznik pomaga na start, ale nie ćwiczy liczenia w głowie." },
];

async function countSettings() {
  const sec = document.createElement("section");
  sec.className = "glass settings";
  const vals = {};
  for (const f of COUNT_FIELDS) {
    try { const v = (await call("get_setting", f.key)).value; vals[f.key] = v ?? f.def; } catch { vals[f.key] = f.def; }
  }
  const draw = (saved) => {
    sec.innerHTML = `<h2 class="sec-title">Liczenie kart</h2>` + COUNT_FIELDS.map((f) => `
      <div class="field"><div class="field-label">${f.label}<span class="muted">${f.hint}</span></div>
        <div class="seg" role="radiogroup" aria-label="${f.label}">${f.options.map(([v, l]) =>
          `<button role="radio" aria-checked="${vals[f.key] === v}" data-ckey="${f.key}" data-val='${JSON.stringify(v)}'>${l}</button>`).join("")}</div></div>`).join("") +
      `<div class="settings-foot"><span></span><span class="saved" ${saved ? "" : "hidden"}>✓ Zapisano</span></div>`;
  };
  sec.addEventListener("click", async (e) => {
    const b = e.target.closest("[data-ckey]");
    if (!b) return;
    const v = JSON.parse(b.dataset.val);
    try { await call("set_setting", b.dataset.ckey, v); vals[b.dataset.ckey] = v; draw(true); } catch { }
  });
  draw(false);
  return sec;
}

let currentRules = null;
function updateTableSubtitle(rules) {
  currentRules = rules;
  const el = document.querySelector("#table-rules");
  if (el) el.textContent = describeRules(rules);
}

async function connect() {
  try {
    const r = await call("ping");
    setStatus("ok", `Połączono · v${r.version}`);
    updateTableSubtitle((await call("get_rules")).rules);
  } catch (e) {
    setStatus("err", "Brak połączenia");
  }
}

show("table");
if (window.pywebview?.api) connect();
else {
  window.addEventListener("pywebviewready", connect);
  // podgląd w zwykłej przeglądarce (bez Pythona)
  setTimeout(() => { if (!window.pywebview?.api) setStatus("", "Podgląd bez Pythona"); }, 1500);
}
