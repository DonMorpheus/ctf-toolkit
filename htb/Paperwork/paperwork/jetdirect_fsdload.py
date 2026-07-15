#!/usr/bin/env python3
"""Pobierz plik z jetdirect (127.0.0.1:9100) przez PJL FSDOWNLOAD — uruchom NA target jako lp."""
import socket
import sys

HOST, PORT = "127.0.0.1", 9100
NAME = sys.argv[1] if len(sys.argv) > 1 else "jetdirect.py"


def pjl_download(name: str) -> bytes:
    s = socket.socket()
    s.settimeout(10)
    s.connect((HOST, PORT))
    cmd = f'@PJL FSDOWNLOAD NAME="{name}"\r\n'.encode()
    s.sendall(cmd)
    chunks = []
    try:
        while True:
            b = s.recv(65536)
            if not b:
                break
            chunks.append(b)
    except socket.timeout:
        pass
    s.close()
    return b"".join(chunks)


if __name__ == "__main__":
    data = pjl_download(NAME)
    sys.stdout.buffer.write(data)