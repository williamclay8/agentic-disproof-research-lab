"""Static web server for the local Trading Lab product lane."""

from __future__ import annotations

import os
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


WEB_ROOT = Path(__file__).resolve().parent
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 5199


def serve(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> None:
    handler = partial(SimpleHTTPRequestHandler, directory=str(WEB_ROOT))
    server = ThreadingHTTPServer((host, port), handler)
    print(f"Trading Lab web: http://{host}:{port}")
    server.serve_forever()


def main() -> int:
    host = os.environ.get("TRADING_LAB_WEB_HOST", DEFAULT_HOST)
    port = int(os.environ.get("TRADING_LAB_WEB_PORT", str(DEFAULT_PORT)))
    serve(host, port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
