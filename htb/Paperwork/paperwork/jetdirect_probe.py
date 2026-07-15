#!/usr/bin/env python3
"""Probe HP-style jetdirect on 127.0.0.1:9100 (run ON target as lp)."""
import socket
import sys

HOST = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 9100

PAYLOADS = [
    b"FSQUERY\n",
    b"FSQUERY /\n",
    b"FSLIST\n",
    b"FSUPLOAD test.txt\n",
    b"FSDOWNLOAD test.txt\n",
    b"HELP\n",
    b"@PJL INFO ID\n",
    b"\x1b%-12345X@PJL INFO STATUS\n",
]

def one(payload: bytes) -> None:
    s = socket.socket()
    s.settimeout(3)
    s.connect((HOST, PORT))
    s.sendall(payload)
    try:
        data = s.recv(8192)
    except socket.timeout:
        data = b""
    s.close()
    print(f">>> {payload!r}")
    print(data[:2000] if data else "(no response)")

if __name__ == "__main__":
    for p in PAYLOADS:
        one(p)