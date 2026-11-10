// Frontend tylko wyświetla i wysyła akcje do Pythona (window.pywebview.api).

const SCREENS = {
  table:      { title: "Stół", template: "tpl-table" },
  counting:   { title: "Liczenie",   feature: "BJ-05", text: "Ćwiczenie Hi-Lo: apka pokaże karty i zapyta o running i true count." },
  stats:      { title: "Statystyki", feature: "BJ-07", text: "Zagraj pierwsze 20 rozdań, żeby zobaczyć statystyki." },
  simulation: { title: "Symulacja",  feature: "BJ-08", text: "10 000 rozdań: Twój styl vs gra idealna vs z liczeniem." },
  cheatsheet: { title: "Ściąga",     feature: "BJ-04", text: "Tabela strategii podstawowej z podświetloną bieżącą sytuacją." },
  settings:   { title: "Ustawienia", feature: "BJ-02", text: "Zasady stołu: liczba talii, S17/H17, podwojenie po splicie, poddanie." },
};

const content = document.getElementById("content");
const navItems = [...document.querySelectorAll(".nav-item")];

function show(screen) {
  const def = SCREENS[screen] ?? SCREENS.table;
  navItems.forEach((b) => b.dataset.screen === screen ? b.setAttribute("aria-current", "page") : b.removeAttribute("aria-current"));
  content.replaceChildren();
  content.style.animation = "none"; void content.offsetWidth; content.style.animation = "";
  if (def.template) {
    content.append(document.getElementById(def.template).content.cloneNode(true));
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
