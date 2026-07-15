# Connected — dostęp do maszyny (ACCESS)

Ten plik odpowiada na: *„jak się zalogować i zobaczyć box jak człowiek?”*

## TL;DR

| Metoda | Działa? | Uwagi |
|--------|---------|--------|
| **SSH jako `asterisk`** | **Nie** (u nas) | Żadne hasło z loot nie przeszło spray — patrz niżej |
| **SSH jako `root`** | Nie | Brak credów |
| **Webshell (RCE)** | **Tak** | Główny sposób pracy na systemie jako `asterisk` |
| **FreePBX Admin GUI** | **Tak** | `admin` / `admin123` (ustawione w DB) |
| **MySQL z Kali** | Nie | tylko localhost na boxie |
| **Reverse shell** | Opcjonalnie | Nie był wymagany do flag |

**Wniosek:** szukanie „hasła SSH asterisk” na tym boxie to ślepy zaułek — credy z FreePBX/MySQL **nie są** hasłami kont Linux.

---

## Dlaczego nie ma SSH dla asterisk?

1. **Spray SSH** — wszystkie zebrane sekrety aplikacyjne → **zero trafień** (`loot/ssh-spray.txt`).
2. **Enum** — `asterisk` ma shell, ale typowo na PBX:
   - logowanie hasłem wyłączone lub hasło nieustawione / losowe,
   - ewentualnie tylko **klucz** (nie znaleziony w loot).
3. **Hook `toggle-sshkeys-rpm`** (sysadmin) — na tym hoście **nie zadziałał** (brak repo/DNS Sangoma) — nie dostaniesz tak łatwo klucza roota przez pakiet.

To nie znaczy, że SSH na porcie 22 jest zamknięte — znaczy, że **nie mamy poprawnego sposobu uwierzytelnienia**.

---

## Jak normalnie „być na boxie”

### 1) Webshell (zalecane do nauki / powtórek)

```bash
cd ~/Desktop/htb/Connected/scripts
python3 enum_privesc.py
```

W outputcie: URL typu `http://connected.htb/<katalog>/<plik>.php?cmd=id`  
Każde uruchomienie = **nowy katalog** (CVE upload). Stary URL po restarcie Apache może paść.

**Ręcznie w przeglądarce / curl:**

```bash
curl -s 'http://connected.htb/XXXX/YYYY.php?cmd=whoami'
# → asterisk
```

### 2) Interaktywniej (opcjonalnie)

Z webshella możesz odpalić reverse shell na Kali — wtedy masz „prawdziwy” terminal. Wymaga `tun0` i otwartego listenera. Na HTB często wystarczy webshell + `cmd=`.

### 3) Panel admina (HTTP)

- URL: `https://connected.htb/admin/` (lub http)
- Login: **`admin` / `admin123`**
- To **nie** daje shella — tylko GUI i zrozumienie modułów.

### 4) MySQL **na samym boxie** (przez webshell)

```bash
mysql -u freepbxuser -p'mZzDpAGKTmPJ' asterisk -e 'SELECT username,password_sha1 FROM ampusers;'
```

Credy: `loot/copy-paste.txt`.

---

## Co jest w copy-paste.txt (i czego to NIE jest)

| Sekret | Służy do |
|--------|----------|
| `freepbxuser` / `mZzDpAGKTmPJ` | MariaDB na localhost |
| `admin` / `admin123` | FreePBX ACP |
| `manager` / `manag3rpa55word` | cxpanel API |
| AMI secrets | Asterisk Manager (5038), nie SSH |
| HTML `admin_key` / `ucp_extra` | tokeny w JS, nie hasło SSH |

---

## Po root (SUID bash)

Gdy `/bin/bash` ma SUID:

```bash
# przez webshell:
cmd=/bin/bash+-p+-c+'id;cat+/root/root.txt'
```

Albo lokalnie na boxie (jeśli masz już shell): `/bin/bash -p`.

---

## Checklist po resecie maszyny

1. VPN EU, ping IP z `target.txt`
2. `/etc/hosts`: `connected.htb pbxconnect` → IP
3. `python3 enum_privesc.py` → nowy webshell
4. Flagi od zera lub `ha_trigger_suid.py` jeśli tylko powtórka privesc