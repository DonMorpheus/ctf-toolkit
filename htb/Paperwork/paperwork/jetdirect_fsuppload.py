#!/usr/bin/env python3
"""
Test PJL FS* na 127.0.0.1:9100 (uruchom NA target jako lp).
Cel: wpis FSQUERY/FSUPLOAD do commands.log + ewentualny zapis pliku jako archivist.
"""
import socket
import sys

HOST, PORT = "127.0.0.1", 9100

def send_raw(data: bytes, label: str) -> None:
    s = socket.socket()
    s.settimeout(5)
    s.connect((HOST, PORT))
    s.sendall(data)
    chunks = []
    try:
        while True:
            b = s.recv(4096)
            if not b:
                break
            chunks.append(b)
    except socket.timeout:
        pass
    s.close()
    print(f"=== {label} ===")
    print(b"".join(chunks)[:1500] or "(empty)")

def main() -> None:
    # 1) Wymuszenie wpisu w logu (triggery paperwork-daemon)
    send_raw(b"FSQUERY /\r\n", "plain FSQUERY")
    send_raw(b"@PJL FSQUERY\r\n", "PJL FSQUERY")
    send_raw(b"@PJL FSDIR LIST\r\n", "PJL FSDIR LIST")

    # 2) Mini upload (nazwa testowa w katalogu printera archivist)
    body = b"test-from-lp\n"
    hdr = f'@PJL FSUPLOAD NAME="lp_probe.txt" SIZE={len(body)}\r\n'.encode()
    send_raw(hdr + body + b"\x0c", "PJL FSUPLOAD small file")

if __name__ == "__main__":
    main()