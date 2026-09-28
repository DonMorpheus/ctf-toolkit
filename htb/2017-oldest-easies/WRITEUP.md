# Oldest HTB easies — 2026-09-28

**Author:** DonMorpheus (lab) + Ania  
**Scope:** HTB VPN, retired machines, personal Kali  
**Rule:** no flags, no unique lab passwords, no `.ovpn`

One-day pass from the **oldest listings on the site**. Surface is 2017-era: banners equal entry, default creds, leftover webshells, unpatched kernels. Same enum muscle as a modern box; doors are not behind four AD hops.

---

## Precious (Easy, Linux)

pdfkit **0.8.6** (app converts a URL to PDF). That is **OS command injection** in the gem (`CVE-2022-25765`), not SSTI. Target cannot fetch the public internet; host the payload URL on `tun0`.

- After `www-data`: Ruby `.bundle/config` holds another user's password (reuse).
- `sudo ruby update_dependencies.rb` does `YAML.load` on **`/tmp/dependencies.yml`** (filename must be exact). gadget → `id` as root, then drop back to the user. Persistence: `chmod +s /bin/bash` in the gadget, then `bash -p`.
- TTY: `python3 -c 'import pty; pty.spawn("/bin/bash")'` then on Kali `stty raw -echo; fg` and `TERM=xterm`.

## Legacy (Easy, Windows XP)

SMB1 on **XP**. Fingerprint chooses **MS08-067**, not EternalBlue/MS17-010. MSF `ms08_067_netapi`. Old OS, one service, done.

## Devel (Easy, Windows 7 / IIS 7.5)

Anonymous **FTP write** into the IIS webroot. `msfvenom` ASPX → `put` → browse. IIS APPPOOL has `SeImpersonate` / `SeAssignPrimaryToken`; intended LPE is **KiTrap0D** (`ms10_015_kitrap0d`) or Potato-class, not a hanging `getsystem`.

Havoc Demon (2026 implant) on this 2017 Win7 died before SYN. Leave modern C2 for Win10 lab.

## Beep (Medium, Linux, Elastix)

Long nmap (mail, MySQL, Webmin, Asterisk). Do not searchsploit every port. **443** title `Elastix - Login`. Modern OpenSSL/Firefox refuse TLS 1.0 (`security.tls.version.min = 1` or `curl --tlsv1.0 --tls-max 1.0`).

Unauth LFI: EDB **37637**, `/vtigercrm/graph.php?current_language=.../etc/amportal.conf%00` (PHP 5.1 null byte). Config passwords reused as **SSH root**. New OpenSSH vs OpenSSH **4.3**: `no matching key exchange` looks like “needs a key” — it is DH-SHA1 / `ssh-rsa`. Wrapper `-o KexAlgorithms=diffie-hellman-group14-sha1 -o HostKeyAlgorithms=ssh-rsa`.

LFI reads as the Apache user. Root is **password reuse**, a second bug.

## Arctic (Easy, Windows / ColdFusion 8)

Default nmap **misses 8500**. `-p-`. Service `JRun`, `Index of /`, HTTP **slow** (20–30 s). `/CFIDE/administrator` = CF8. Unauth FCKeditor upload **CVE-2009-2265** (EDB 50057). Python 3 `multiprocessing` **spawn** does not inherit `rhost` from `if __name__ == '__main__'` — pass `args=` into `Process`.

User `tolis`. Upgrade to Meterpreter; `local_exploit_suggester` works here (no Defender). Ignore UAC bypass (not admin) and 2020 CVEs. Match **SeImpersonate** → `ms16_075_reflection_juicy` and/or `ms10_092_schelevator` after migrate to x64 `jrunsvc.exe` (WOW64). Paths under `C:\Users\`.

## Grandpa (Easy, Windows 2003 IIS 6)

CVE-**2017-7269** WebDAV `ScStoragePathFromUrl`. MSF `iis_webdav_scstoragepathfromurl`. Session often **broken stdapi** (`getuid` Access denied). `getsystem` is wasted. **Migrate** to `davcdata.exe` (NETWORK SERVICE) first. Suggester: **`ms14_070_tcpip_ioctl`**. Flags live under `C:\Documents and Settings\` not `C:\Users`.

## Granny (Easy, Windows 2003 IIS 6)

Twin banner, **different door**. Nmap `http-webdav-scan`: `PUT` / `MOVE` in Public Options. Intended MSF `iis_webdav_upload_asp` (Devel's trick over HTTP). Same migrate → NETWORK SERVICE → suggester (writeup used `ms15_051_client_copy_image`). Do not copy Grandpa's overflow by habit.

## Bank (Easy, Linux)

Apache default page on the IP. **vhost** `bank.htb` (HTB naming + `Host:`). DNS 53 / AXFR / PTR gave nothing. Compare `curl` IP vs `http://bank.htb/` (302 `login.php`).

Dirbust **medium** list → `/balance-transfer/` (many `.acc`). Sort by size (`?C=S;O=A`); the **small** file is failed encryption → plaintext creds. Login, Support upload. Filter blocks `.php`; Apache **`AddType` `.htb` as PHP**. Reverse as `www-data`.

SSH with the **web** password fails. SUID find **on the target** (not on Kali — snap/kismet is your box). Non-standard: `/var/htb/bin/emergency` (`-rwsr-xr-x`) → `euid=0`. PHP reverse has no job control; `pty.spawn` + `stty` will not attach.

`/inc/*.php` listing does **not** leak source (Apache executes).

## Blocky (Easy, Linux)

80 redirects to `blocky.htb` (vhost in the Location). WordPress + Minecraft. Gobuster: **`/plugins/` at webroot**, not `wp-content/plugins`. Cute file browser loads jQuery; files come from `scan.php` JSON: `BlockyCore.jar` (custom) vs public `griefprevention`.

JAR = zip. `strings` on the **`.jar`** misses constant-pool (compressed). `unzip` + `javap -c -p` on the `.class` → `sqlUser=root` / `sqlPass=...`. phpMyAdmin works, **intended** is SSH reuse. Username: `curl -sI 'http://blocky.htb/?author=1'` → `/author/notch/`. `notch` in sudoers → `sudo -i`.

## Mirai (Easy, Linux / Raspberry Pi)

SSH, dnsmasq, lighttpd **“Website Blocked”**, Platinum UPnP/DLNA. Gobuster 200-wildcard (every path is the block page) → `--exclude-length`. `/admin` = Pi-hole “Designed For Raspberry Pi”.

Default **Raspbian SSH** (`pi` / published default), not the Pi-hole web password. `pi` is sudo. User flag on **Desktop**. `/root/root.txt` is a hint: USB. `/media/usbstick/damnit.txt` — directory entry gone, sectors remain. `strings /dev/sdb` (or image + strings). testdisk shows 0-byte file.

## Shocker (Easy, Linux)

Apache 80 + SSH **2222** (unused for foothold). Box name hints Shellshock. Medium gobuster times out; `common.txt` + `/cgi-bin/` **403 means found**. `-x sh,cgi` → `user.sh` (uptime CGI).

**Not SSTI.** CVE-2014-6271: Apache CGI copies headers into env; old bash parses `() {` as a function and runs the trailing command **before** `user.sh` logic. `user.sh` is not a backdoor. Search path: `searchsploit apache cgi bash` — you do not need the nickname first.

MSF `apache_mod_cgi_bash_env_exec`: `TARGETURI=/cgi-bin/user.sh`. Default `linux/x86/meterpreter` dies on **x64**. Module rejects `linux/x64/meterpreter`. Use **`cmd/unix/reverse_bash`** or a one-liner `User-Agent` + `nc`. User `shelly`. `sudo -l`: NOPASSWD **`/usr/bin/perl`** → `sudo /usr/bin/perl -e 'exec "/bin/bash"'`.

## Bashed (Easy, Linux)

Only 80. Gobuster `/dev/`. `phpbash.php` is an **intentional leftover webshell** (POST `cmd=`), not a CVE. `www-data`. `sudo -l`: NOPASSWD ALL as **`scriptmanager` only**. `sudo -u scriptmanager bash -i` **exits** in phpbash (no TTY). One-shots: `sudo -u scriptmanager cat /scripts/test.py`.

`test.py` writes `test.txt`; `test.txt` owned by **root**, refreshed ~60s → root cron. Overwrite `test.py` as scriptmanager (`chmod u+s /bin/bash` or write `/root/root.txt` to a world-readable path). Wait one minute. `chmod u s` (space) is a no-op. `sudo -u scriptmanager python3 -c 'open("/root/root.txt")'` still denied — cron is root, sudo is not.

---

## Lessons that repeat

| Habit | Where it bit |
|--------|----------------|
| `-p-` / odd ports | Arctic 8500, Shocker SSH 2222 |
| Product+version → searchsploit, not every port | Beep, Grandpa, Shocker |
| Same banner ≠ same bug | Grandpa overflow vs Granny PUT |
| `Host:` / machine name | Bank, Blocky |
| Default IoT creds | Mirai |
| Password reuse | Precious, Beep, Blocky |
| Broken IIS session → migrate | Grandpa, Granny |
| Payload arch / Python spawn | Arctic 50057, Shocker MSF |
| Find SUID **on the target** | Bank |
| Cron = file you can write, job you do not start | Bashed |

Official HTB PDFs for these machines (Arrexel / ch4p / issue / mrb3n, 2017).
