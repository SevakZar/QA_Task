"""Local fake Checkout Payment API. Approach A from the task brief."""

from __future__ import annotations

import argparse
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from mock_server.catalog import resolve

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8080


class PaymentHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):  # noqa: A002
        return

    def do_GET(self):  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path.rstrip("/") != "/payment":
            self._write(404, {"status": 404, "error": "unknown path"})
            return

        cell = parse_qs(parsed.query).get("CellNumber", [None])[0]
        if not cell:
            self._write(400, {"status": 400, "error": "CellNumber is required"})
            return

        http_status, fixture_path = resolve(cell)
        if fixture_path is None:
            self._write(404, {"status": 404, "error": f"unknown CellNumber {cell}"})
            return

        body = json.loads(fixture_path.read_text(encoding="utf-8"))
        self._write(http_status, body)

    def _write(self, status: int, body: dict) -> None:
        payload = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


def make_server(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((host, port), PaymentHandler)


class MockServer:
    def __init__(self, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT):
        self.host = host
        self.port = port
        self._httpd: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"

    def start(self) -> None:
        self._httpd = make_server(self.host, self.port)
        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if self._httpd is not None:
            self._httpd.shutdown()
            self._httpd.server_close()
        if self._thread is not None:
            self._thread.join(timeout=2)


def main() -> None:
    parser = argparse.ArgumentParser(description="Checkout payment mock server")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    args = parser.parse_args()
    httpd = make_server(args.host, args.port)
    print(f"Mock payment API listening on http://{args.host}:{args.port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.shutdown()


if __name__ == "__main__":
    main()
