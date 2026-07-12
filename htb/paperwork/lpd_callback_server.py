#!/usr/bin/env python3
"""POST callback for lpd_post.sh → append loot/lpd-callback.log"""
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

LOG = Path(__file__).resolve().parent.parent / "loot" / "lpd-callback.log"


class Handler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", 0))
        data = self.rfile.read(length)
        tag = self.path.lstrip("/") or "post"
        text = data.decode(errors="replace")
        block = f"\n===\n/{tag}\n{text}\n"
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with LOG.open("a") as f:
            f.write(block)
        print(block, end="")
        self.send_response(200)
        self.end_headers()

    def log_message(self, fmt: str, *args) -> None:
        pass


if __name__ == "__main__":
    HTTPServer(("0.0.0.0", 8900), Handler).serve_forever()