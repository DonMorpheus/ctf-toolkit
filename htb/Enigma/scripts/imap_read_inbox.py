#!/usr/bin/env python3
"""Read all messages from INBOX via IMAP SSL."""
import imaplib
import email
import sys


def main():
    if len(sys.argv) < 4:
        print(f"Usage: {sys.argv[0]} <host> <user> <password>", file=sys.stderr)
        sys.exit(1)
    host, user, password = sys.argv[1], sys.argv[2], sys.argv[3]
    m = imaplib.IMAP4_SSL(host, 993)
    m.login(user, password)
    m.select("INBOX")
    typ, data = m.search(None, "ALL")
    for num in data[0].split():
        typ, msg = m.fetch(num, "(RFC822)")
        em = email.message_from_bytes(msg[0][1])
        print("=" * 60)
        print("Subject:", em["Subject"])
        print("From:", em["From"])
        if em.is_multipart():
            for part in em.walk():
                if part.get_content_type() in ("text/plain", "text/html"):
                    payload = part.get_payload(decode=True)
                    if payload:
                        print(payload.decode(errors="replace")[:8000])
        else:
            payload = em.get_payload(decode=True)
            if payload:
                print(payload.decode(errors="replace")[:8000])
    m.logout()


if __name__ == "__main__":
    main()