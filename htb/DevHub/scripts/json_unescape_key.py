#!/usr/bin/env python3
"""Turn OpsMCP JSON dump (escaped \\n) into a valid OpenSSH private key file.

OpenSSH refuses a key that is missing the trailing newline after
-----END OPENSSH PRIVATE KEY-----
`printf "$(sed …)"` strips that newline. This script always writes it.

Usage:
  python3 json_unescape_key.py dump.json root_id_rsa
  # or a one-line file that still contains literal \\n
  python3 json_unescape_key.py /tmp/root_key root_id_rsa
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def extract(raw: str) -> str:
    raw = raw.strip()
    key = None
    if raw.startswith("{"):
        data = json.loads(raw)
        key = data.get("root_private_key") or data.get("key")
        if not key:
            raise SystemExit("JSON has no root_private_key")
    else:
        key = raw.replace("\\n", "\n")
    key = key.replace("\r\n", "\n").strip() + "\n"
    if "BEGIN OPENSSH PRIVATE KEY" not in key:
        raise SystemExit("not an OpenSSH private key")
    return key


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    args = ap.parse_args()
    key = extract(Path(args.src).read_text())
    Path(args.dst).write_text(key)
    Path(args.dst).chmod(0o600)
    print(f"wrote {args.dst} ({len(key)} bytes, trailing_nl={key.endswith(chr(10))})")


if __name__ == "__main__":
    main()
