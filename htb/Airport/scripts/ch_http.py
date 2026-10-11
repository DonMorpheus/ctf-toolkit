#!/usr/bin/env python3
"""ClickHouse HTTP helper (nginx vhost in front of :8123).

Auth is HTTP Basic. User svc_events is SELECT/INSERT on partner_feed.*;
user default (once you have the password) has FILE on user_files/.

Usage:
  python3 ch_http.py --url http://db.htb-airport.htb/ -u svc_events -p "$CH_PASS" 'SHOW GRANTS'
  python3 ch_http.py -u default -p "$CH_DEFAULT_PASS" \\
      "SELECT flight_number, airline FROM partner_feed.flightleg_json WHERE flight_number='P1'"
"""
from __future__ import annotations

import argparse
import base64
import os
import sys
import urllib.error
import urllib.request


def query(url: str, user: str, password: str, sql: str, timeout: float) -> tuple[int, str]:
    token = base64.b64encode(f"{user}:{password}".encode()).decode()
    req = urllib.request.Request(
        url,
        data=sql.encode(),
        method="POST",
        headers={
            "Authorization": f"Basic {token}",
            "Content-Type": "text/plain; charset=utf-8",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("sql", nargs="?", help="SQL (or stdin / --file)")
    ap.add_argument("--url", default=os.environ.get("CH_URL", "http://db.htb-airport.htb/"))
    ap.add_argument("-u", "--user", default=os.environ.get("CH_USER", "svc_events"))
    ap.add_argument("-p", "--password", default=os.environ.get("CH_PASS", ""))
    ap.add_argument("--file", help="read SQL from file")
    ap.add_argument("--timeout", type=float, default=30)
    args = ap.parse_args()

    if args.file:
        sql = open(args.file, encoding="utf-8").read()
    elif args.sql:
        sql = args.sql
    elif not sys.stdin.isatty():
        sql = sys.stdin.read()
    else:
        ap.error("pass SQL as argument, --file, or stdin")

    if not args.password:
        print("[-] set --password or CH_PASS", file=sys.stderr)
        return 2

    code, body = query(args.url, args.user, args.password, sql, args.timeout)
    sys.stdout.write(body)
    if not body.endswith("\n"):
        sys.stdout.write("\n")
    if code != 200:
        print(f"[-] HTTP {code}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
