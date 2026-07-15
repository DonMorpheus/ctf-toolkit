#!/usr/bin/env python3
import base64
import socket

s = socket.socket()
s.settimeout(20)
s.connect(("127.0.0.1", 9100))
s.sendall(b'@PJL FSDOWNLOAD NAME="jetdirect.py" SIZE=5119\r\n')
s.shutdown(socket.SHUT_WR)
buf = b""
try:
    while True:
        c = s.recv(65536)
        if not c:
            break
        buf += c
except socket.timeout:
    pass
s.close()
print("len", len(buf))
if buf:
    print(buf[:400].decode(errors="replace"))
    if len(buf) > 1000:
        open("/tmp/jetdirect.b64", "wb").write(base64.b64encode(buf))
        print("saved_b64")