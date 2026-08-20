#!/usr/bin/env python3
"""Gogs passwd+salt (SQLite user table) → hashcat 10900 PBKDF2-HMAC-SHA256."""
from __future__ import annotations

import argparse
import base64
import sys


def convert(salt: str, hexhash: str, n: int = 10000) -> str:
    b64salt = base64.b64encode(salt.encode("ascii")).decode("ascii")
    b64hash = base64.b64encode(bytes.fromhex(hexhash)).decode("ascii")
    return f"sha256:{n}:{b64salt}:{b64hash}"


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("salt")
    p.add_argument("hash", help="hex digest from user.passwd")
    p.add_argument("-n", type=int, default=10000, help="PBKDF2 iterations")
    args = p.parse_args()
    print(convert(args.salt, args.hash, args.n))
    return 0


if __name__ == "__main__":
    sys.exit(main())
