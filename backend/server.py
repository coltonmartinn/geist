import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from backend.app import GeistApp
from backend.config import Config


WEB_ROOT = Path(__file__).resolve().parent.parent / "web"


class GeistHandler(BaseHTTPRequestHandler):
    app: GeistApp

    def do_GET(self):
        path = urlparse(self.path).path
        if path.startswith("/api/") or path == "/health":
            status, body = self.app.handle_get(path)
            self._json(status, body)
            return
        self._static(path)

    def do_POST(self):
        status, body = self.app.handle_post(urlparse(self.path).path, self._read_json())
        self._json(status, body)

    def do_PATCH(self):
        status, body = self.app.handle_patch(urlparse(self.path).path, self._read_json())
        self._json(status, body)

    def do_DELETE(self):
        status, body = self.app.handle_delete(urlparse(self.path).path)
        self._json(status, body)

    def log_message(self, fmt, *args):
        print(f"{self.address_string()} - {fmt % args}")

    def _read_json(self) -> dict:
        length = int(self.headers.get("content-length", "0"))
        if length == 0:
            return {}
        try:
            return json.loads(self.rfile.read(length).decode("utf-8"))
        except json.JSONDecodeError:
            return {}

    def _json(self, status: int, body: dict):
        payload = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(payload)))
        self.send_header("cache-control", "no-store")
        self.end_headers()
        self.wfile.write(payload)

    def _static(self, path: str):
        relative = "index.html" if path in ("", "/") else path.lstrip("/")
        file_path = (WEB_ROOT / relative).resolve()
        if WEB_ROOT not in file_path.parents and file_path != WEB_ROOT:
            self.send_error(403)
            return
        if not file_path.exists() or not file_path.is_file():
            self.send_error(404)
            return
        payload = file_path.read_bytes()
        content_type = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("content-type", content_type)
        self.send_header("content-length", str(len(payload)))
        self.send_header("cache-control", "no-store")
        self.end_headers()
        self.wfile.write(payload)


def main():
    config = Config.from_env()
    GeistHandler.app = GeistApp(config)
    server = ThreadingHTTPServer((config.host, config.port), GeistHandler)
    print(f"Geist listening on http://{config.host}:{config.port}")
    print(f"RuView source: {config.ruview_base_url} ({config.source_mode})")
    server.serve_forever()


if __name__ == "__main__":
    main()
