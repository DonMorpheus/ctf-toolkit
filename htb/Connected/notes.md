# Connected (HTB) — stan sesji (ukończone 2026-07-11)

## Target
| Pole | Wartość |
|------|---------|
| IP | `10.129.245.100` (sprawdź `target.txt` po resecie) |
| Hosts | `connected.htb`, `pbxconnect` |
| VPN | `~/Downloads/machines_eu-1.ovpn` (EU machines) |
| Aplikacja | FreePBX **16.0.40.7**, Sangoma Linux **7.8.2003** |
| Porty | 22, 80, 443 (Apache 2.4.6, PHP 7.4.16) |

## Zrobione
- Initial nmap → `nmap/initial.*`
- Recon WWW (admin, UCP, cxpanel), leaki w HTML
- **User:** RCE **CVE-2025-57819** (PoC / `scripts/get_user_flag.py`, `enum_privesc.py`)
- Shell: użytkownik **`asterisk`** (webshell pod `/var/www/html/<rnd>/`)
- **User flag:** `1703ca3d357807a6d6e329394d1d3d21` → `loot/user-flag.txt`
- Admin GUI: hasło w MySQL ustawione na **`admin` / `admin123`**
- Privesc enum: cron, **incrond**, sysadmin_manager, AMI, DB localhost, Vega :4000

## Root (final)
- **`ha_trigger`** → `/usr/sbin/sysadmin_ha` (root PHP) → moduł **`freepbx_ha`** (utworzony w writable `admin/modules`) → `rootTrigger()` → **SUID `/bin/bash`**
- Skrypt: `scripts/ha_trigger_suid.py`, log: `loot/ha-trigger-suid-run2.log`
- **Root flag:** `0cb4497552faba9ded930de4568630bb` → `loot/root-flag.txt`
- Nauka: `edu/03-ha-trigger-suid.md`

## Nie priorytet
- Stabilny reverse shell (webshell wystarczył)
- SSH jako asterisk — **nie ma** (patrz `ACCESS.md`)

---

## Wejście (RCE)
- Łańcuch: SQLi `endpoint` ajax → tymczasowy admin → upload webshell `upload_cust_fw`
- Skrypt: `scripts/enum_privesc.py` → `get_shell()` (nowy URL przy każdym uruchomieniu)
- CVE: `scripts/CVE-2025-57819_exploit.py`, notatki `loot/cve-57819-notes.md`

---

## Credy / sekrety
Wszystko w **`loot/copy-paste.txt`** (i skrót `~/Desktop/htb/copy-paste.txt`).

| Co | Wartość |
|----|---------|
| MySQL | `freepbxuser` / `mZzDpAGKTmPJ` |
| Admin GUI | `admin` / `admin123` |
| cxpanel API | `manager` / `manag3rpa55word` |
| AMI cxpanel | `cxmanager*con` |
| AMI inny | `fe1mYBs7D5P3` |
| HTML leak admin | `qf0cl1r2o9sd79s2bn7habsu4r` |
| HTML leak UCP | `h0kesimg5368cii56h2i7ll8qn` |

SSH: brak potwierdzonego logowania (spray → `loot/ssh-spray.txt`).

---

## Privesc — incron / sysadmin (główny wektor)

### Działa (root)
- **`FreePBX::Hooks->runModuleSystemHook("framework", "logrotate")`** → plik `/etc/logrotate.d/freepbx-fwJOB` (**root:root**)
- **`framework` `yum-update-system`** → logi root w `/dev/shm/yumwrapper/` (czytelne jako asterisk)
- Mechanizm: zapis pliku w `/var/spool/asterisk/incron/` → **incrond** → **`/usr/bin/sysadmin_manager`** (podpisane hooki)

### Trigger z CLI (na boxie)
```php
include "/etc/freepbx.conf";
$fpbx = FreePBX::create();
$fpbx->Hooks->runModuleSystemHook("sysadmin", "HOOKNAME");
// parametry tablicowe: trzeci argument array(...) → base64 w nazwie pliku
```

### Format incron (Hooks.class.php)
- Ścieżka: `/var/spool/asterisk/incron/{module}.{hook}[.{params}]`
- Puste parametry: np. `sysadmin.dump-iptables` (nie wklejać treści skryptu do pliku — to params)

### Zablokowane / słabe
- **`update-ports`** (ionCube): zwraca `true`, ale **`/usr/sbin/sysadmin_portmgmt` nie istnieje**; Sysadmin „Machine not activated” bez pełnej licencji
- **`toggle-sshkeys-rpm`**: yum nie ma repo (DNS **`mirrorlist.sangoma.net`**); pakiet **`ssh_keys`** nie zainstalowany
- **`dump-iptables`**: hook `true`, brak trwałego `/tmp/iptables-save-output` przez incron (ręczny `sysadmin_manager` jako asterisk tworzył pusty plik)
- Sieć z boxa: **ping 8.8.8.8 100% loss**; aktywacja online (`katanafpbx.schmoozecom.com`) nie działa
- Plik licencji: **`/etc/schmooze/schmooze.zl`** istnieje — pełna aktywacja / `fwconsole sa info` **nie dokończone**
- MySQL **`LOAD_FILE('/root/root.txt')`** → **NULL**
- Legacy spool: `touch .../sysadmin/portmgmt_setup` — bez efektu bez portmgmt

Szczegóły: `loot/incron-ssh-summary.txt`, `loot/privesc-root-push.log`, `loot/escalation-paths.txt`, `loot/incron-root-flag-run.log`

---

## Kernel / LPE (fallback)
- **Boot:** `5.4.239-1.el7.elrepo.x86_64` (2023-03-30)
- **SELinux:** Disabled; `gcc`/`make` obecne
- **linux-exploit-suggester:** tylko trafienia „less probable” (nf_tables, Ubuntu OverlayFS, itd.)
- **`nf_tables`** nie w `lsmod`; **`ip_tables`** tak
- **Żaden kernel exploit nie był uruchomiony** — brak roota z tej ścieżki
- Raport: **`loot/kernel-exploit-report.txt`**, enum: **`loot/kernel-enum.txt`**

---

## Usługi localhost (enum)
- 3306 MariaDB, 6379 Redis, 27017 Mongo, **5038** AMI, **4000** Vega, 25 Postfix
- **sudo** dla asterisk: wymaga hasła; **incrontab** SUID

---

## Skrypty (Kali)
| Skrypt | Cel |
|--------|-----|
| `enum_privesc.py` | RCE + `get_shell()` |
| `get_user_flag.py` | user flag |
| `privesc_root_push.py` | testy incron / sysadmin_manager |
| `confirm_root_incron_mysql_ssh.py` | incron + MySQL + SSH spray |
| `incron_get_root_flag.py` | batch hooków (bez flagi) |
| `set_admin_password.py` | admin w DB |

---

## Loot — indeks
| Plik | Zawartość |
|------|-----------|
| `copy-paste.txt` | flagi + credy |
| `user-flag.txt` | user |
| `privesc-enum.txt` | pełny enum |
| `kernel-exploit-report.txt` | kernel LPE ocena |
| `incron-ssh-summary.txt` | incron stan |
| `root-incron-ssh.txt` | hooki + testy |
| `fast-privesc-test.txt` | szybkie testy |
| `update-ports-strings.txt` | strings update-ports |

---

## Start tutaj po przerwie

1. `README.md` → `ACCESS.md` → `edu/README.md`
2. Replay: `scripts/enum_privesc.py` (nowy webshell)

---

*Bez walkthroughów zewnętrznych. Materiały edukacyjne: `edu/`.*