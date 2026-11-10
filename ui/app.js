// Frontend tylko wyświetla i wysyła akcje do Pythona (window.pywebview.api).

const SCREENS = {
  table:      { title: "Stół", template: "tpl-table" },
  counting:   { title: "Liczenie",   feature: "BJ-05", text: "Ćwiczenie Hi-Lo: apka pokaże karty i zapyta o running i true count." },
  stats:      { title: "Statystyki", feature: "BJ-07", text: "Zagraj pierwsze 20 rozdań, żeby zobaczyć statystyki." },
  simulation: { title: "Symulacja",  feature: "BJ-08", text: "10 000 rozdań: Twój styl vs gra idealna vs z liczeniem." },
  cheatsheet: { title: "Ściąga",     feature: "BJ-04", text: "Tabela strategii podstawowej z podświetloną bieżącą sytuacją." },
  settings:   { title: "Ustawienia", render: renderSettings },
};

const content = document.getElementById("content");
const navItems = [...document.querySelectorAll(".nav-item")];

function show(screen) {
  const def = SCREENS[screen] ?? SCREENS.table;
  navItems.forEach((b) => b.dataset.screen === screen ? b.setAttribute("aria-current", "page") : b.removeAttribute("aria-current"));
  content.replaceChildren();
  content.style.animation = "none"; void content.offsetWidth; content.style.animation = "";
  if (def.render) {
    def.render(content);
  } else if (def.template) {
    content.append(document.getElementById(def.template).content.cloneNode(true));
    if (currentRules) updateTableSubtitle(currentRules);
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
  if (e.key.toLowerCase() === "c" && !e.ctrlKey && !e.metaKey) show("cheatsheet");
});

function setStatus(state, text) {
  const dot = document.getElementById("status-dot");
  dot.className = `status-dot ${state}`;
  document.getElementById("status-text").textContent = text;
}

export function toastError(msg) {
  const t = document.createElement("div");
  t.className = "toast glass";
  t.textContent = msg;
  document.body.append(t);
  setTimeout(() => t.remove(), 5000);
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
  form.addEventListener("input", (e) => {
    if (e.target.id === "pen") form.querySelector("#pen-val").textContent = `${e.target.value}%`;
  });
  form.addEventListener("change", (e) => {
    if (e.target.id === "pen") save({ penetration: Number(e.target.value) / 100 });
  });
  draw();
}

let currentRules = null;
function updateTableSubtitle(rules) {
  currentRules = rules;
  const el = document.querySelector("#table-rules");
  if (el) el.textContent = describeRules(rules);
}

// Wywołanie API z obsługą błędów po ludzku.
export async function call(method, ...args) {
  const api = window.pywebview?.api;
  if (!api) throw new Error("Brak połączenia z Pythonem.");
  const r = await api[method](...args);
  if (!r.ok) { toastError(r.error); throw new Error(r.error); }
  return r;
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
