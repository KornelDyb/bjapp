"""Podgląd UI w zwykłej przeglądarce z prawdziwym Pythonowym Api (bez okna pywebview).

python tools/dev_server.py [port]  ->  http://localhost:8765
Wstrzykuje window.pywebview.api, który woła Api przez HTTP — ten sam kontrakt co w oknie.
"""
import json
import sys
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.api import Api  # noqa: E402
from app.paths import UI_DIR, db_path  # noqa: E402
from app.storage.db import Database  # noqa: E402

SHIM = b"""<script>
window.pywebview = { api: new Proxy({}, { get: (_, m) => (...args) =>
  fetch('/__api/' + m, { method: 'POST', body: JSON.stringify(args) }).then(r => r.json()) }) };
window.dispatchEvent(new Event('pywebviewready'));
</script>"""


class Handler(SimpleHTTPRequestHandler):
    api: Api

    def do_POST(self):
        method = self.path.removeprefix("/__api/")
        args = json.loads(self.rfile.read(int(self.headers["Content-Length"] or 0)) or b"[]")
        fn = getattr(self.api, method, None)
        result = fn(*args) if fn and not method.startswith("_") else {"ok": False, "error": f"Brak metody {method}"}
        body = json.dumps(result).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            html = (UI_DIR / "index.html").read_bytes().replace(b"</head>", SHIM + b"</head>")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html)
        else:
            super().do_GET()

    def log_message(self, *a):
        pass


def serve(port: int = 8765) -> ThreadingHTTPServer:
    Handler.api = Api(Database(db_path()))
    return ThreadingHTTPServer(("127.0.0.1", port), partial(Handler, directory=str(UI_DIR)))


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    print(f"Podgląd: http://localhost:{port}")
    serve(port).serve_forever()
