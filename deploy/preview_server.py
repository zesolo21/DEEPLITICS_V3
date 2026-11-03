"""Serve the Vercel staging output locally, including its path rewrites."""

from __future__ import annotations

import argparse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"
ROUTES = {
    "/": "/app/index.html",
    "/app": "/app/index.html",
    "/api/v1/public-config": "/api/v1/public-config.json",
    "/api/v1/stories": "/api/v1/stories.json",
}


class PreviewHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(PUBLIC), **kwargs)

    def do_GET(self) -> None:
        path = urlsplit(self.path).path
        self.path = ROUTES.get(path, self.path)
        super().do_GET()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=4173)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), PreviewHandler)
    print(f"Deeplitics staging preview: http://{args.host}:{args.port}/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
