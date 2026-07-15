#!/usr/bin/env python3
import base64
import socket

name = "jetdirect.py"
s = socket.socket()
s.settimeout(15)
s.connect(("127.0.0.1", 9100))
s.sendall(f'@PJL FSDOWNLOAD NAME="{name}"\r\n'.encode())
buf = b""
try:
    while True:
        b = s.recv(65536)
        if not b:
            break
        buf += b
except socket.timeout:
    pass
s.close()
print("len", len(buf))
print(buf[:200])
if len(buf) > 500:
    print("B64_START")
    print(base64.b64encode(buf).decode())