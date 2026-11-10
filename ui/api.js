// Most do Pythona (window.pywebview.api) + błędy po ludzku.
export function toastError(msg) {
  const t = document.createElement("div");
  t.className = "toast glass";
  t.setAttribute("role", "alert");
  t.textContent = msg;
  document.body.append(t);
  setTimeout(() => t.remove(), 5000);
}

export async function call(method, ...args) {
  const api = window.pywebview?.api;
  if (!api) throw new Error("Brak połączenia z Pythonem.");
  const r = await api[method](...args);
  if (!r.ok) { toastError(r.error); throw new Error(r.error); }
  return r;
}
