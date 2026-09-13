# Management — HTB Write-up

**Author:** DonMorpheus (lab) + Ania  
**Machine:** Management (Linux)  
**Hosts:** `management.htb`, `sso.management.htb`  
**Scope:** HTB VPN / personal lab only  

> **No flags or live passwords** in this document.

---

## TL;DR

```
https://sso.management.htb/openam
        │ CVE-2026-33439 (JATO jato.clientSession, pre-auth RCE)
        ▼
openam (uid 996, Tomcat)
        │ GLPI config_db.php → MariaDB 127.0.0.1
        │ glpi_authldaps bind pass (GLPI 11 XChaCha20, AAD=nonce)
        ▼
SSH owen  (password reuse z LDAP bind svc-glpi)
        │ sudo rdiff-backup --server --restrict-path /opt/backup --restrict-mode read-only *
        │ extra argv: --restrict-mode read-write --restrict-path /
        ▼
backup '/::/root' → id_ed25519  →  SSH root
```

| Phase | Vector |
|-------|--------|
| Recon | 22 / 80 / 443 / **4444** (OpenDJ admin SSL) / **50389** (LDAP). HTTP→HTTPS; HTTPS+IP → `management.htb` |
| Foothold | OpenAM ≤16.0.5 **CVE-2026-33439** — pre-auth RCE przez JATO `jato.clientSession`. URL **musi** być vhost SSO (HEAD/exploit nie followuje 301 z IP) |
| User | MariaDB tylko localhost. Konto **aplikacji** `glpi`. Encrypted LDAP bind w `glpi_authldaps` → plaintext reused as Linux `owen` |
| Root | Nie crash Pythona. **sudoers `*` + argparse last-wins** na `--restrict-path` / `--restrict-mode` |

---

## 1. Recon

```bash
echo '<TARGET_IP> management.htb sso.management.htb' | sudo tee -a /etc/hosts
nmap -sT -Pn -p 22,80,443,389,636,4444,50389,8080,8443 <TARGET_IP>
```

- **80** → HTTPS. **HTTPS po IP** → 301 na `https://management.htb` (Host header).
- `management.htb` — statyczna SPA (`assets/app.enc`, AES-GCM; marketing, bez credów owena).
- `sso.management.htb` — OpenAM pod `/openam` (JATO 200: `/ui/Login`, `/ui/PWResetUserValidation`, `/ui/PWResetQuestion`). nginx `proxy_pass` na Tomcat `127.0.0.1:8080`.
- OpenDJ w tym samym procesie Java: LDAP **50389**, administration connector **4444** (SSL, nie HTTP).
- MariaDB **127.0.0.1:3306** — z Kali nie wejdziesz.

---

## 2. Foothold — OpenAM CVE-2026-33439

Pre-auth RCE w JATO: zdeserializowany `jato.clientSession` na endpointach resetu hasła.

Pułapka labowa: klient, który robi **HEAD i nie followuje 301**, umiera na `http://<IP>`. Cel:

```text
POST https://sso.management.htb/openam/ui/PWResetUserValidation
```

Runtime: **Java 21** (domyślny `java` na Kali bywa nowszy — `JAVA_HOME` na 21). Shell jako **`openam`**, `HOME=/opt/openam`, Tomcat `/opt/openam-tomcat`.

LDAP anon: bind OK, search 0 (ACI). Ludzie: praktycznie `uid=demo`. **Brak `uid=owen`.**

---

## 3. User — GLPI DB → reuse hasła

Z shellem `openam`:

- `/opt/glpi/config/config_db.php` — host `127.0.0.1`, user `glpi`, baza `glpidb`.
- `mysql -h 127.0.0.1 -u glpi` działa **niezależnie od UID Linuxa** (openam i owen). `SHOW DATABASES` = `glpidb` + `information_schema`. `SELECT mysql.user` → denied. `root@localhost` = **unix_socket** (`ERROR 1698`) — nie zalogujesz się hasłem z tego konta.
- W `glpi_authldaps` encrypted `rootdn_passwd` (GLPI **11**: XChaCha20-Poly1305 IETF, **AAD = nonce**, klucz z `glpicrypt.key`).
- Decrypt = hasło bindu `cn=svc-glpi,ou=services,dc=management,dc=htb`.
- To samo hasło jest hasłem Linux **`owen`** (SSH). `user.txt` jest `root:owen` `640`.

OpenAM JCEKS (`configstorepwd` / `dsameuserpwd`) = Directory Manager OpenDJ, **nie** hasło owena.

---

## 4. Root — rdiff-backup argparse jailbreak

```text
(root) NOPASSWD: /usr/bin/rdiff-backup --server --restrict-path /opt/backup --restrict-mode read-only *
```

`/usr/bin/rdiff-backup` to **Python 2.2.6** (entrypoint → `rdiffbackup.run`). `--server` = RPC na stdin/stdout. `Security.initialize(restrict_mode, restrict_path)` bierze **wynik parsera**.

`--restrict-path` / `--restrict-mode` to `argparse` **`store`** → **ostatnie wygrywają**.  
Trailing `*` w sudoers **wymaga** extra argv i **przepuszcza je do Pythona**. Sudo nie rozróżnia „to dał sudoers” vs „to dokleił owen”.

```bash
rdiff-backup --remote-schema \
  'sudo -n /usr/bin/rdiff-backup --server --restrict-path /opt/backup --restrict-mode read-only --restrict-mode read-write --restrict-path {h}' \
  backup '/::/root' /tmp/stolen-root
```

`{h}=/` → serwer jako root czyta `/root`, zapis leci lokalnie jako owen. W `/root/.ssh` jest `id_ed25519` (ten sam w `authorized_keys`) → `ssh -i … root@<IP>`.

Repo `/opt/backup` **już istnieje**, ale to mirror strony (`index.html`, `app.enc`), nie `/root`. Nocny `mgmt-backup.timer` idzie gdzie indziej (`/opt/backups`, borg) — 700, bez jailbreaku niewidoczne.

Helper: [`scripts/rdiff_sudo_jailbreak.sh`](scripts/rdiff_sudo_jailbreak.sh)

### To nie jest crash / „niezamknięta komenda”

`--server` bez klienta interpretuje stdin jako protokół binarny → `MemoryError` / „impossibly high data amount” jeśli wrzucisz śmieci. To nie exploit.

`--debug` (rpdb na `127.0.0.1:4444`) jest w **nowym** CLI `rdiff-backup server --debug`. Sudoers ma **stare** `--server` → `unrecognized arguments: --debug`.

`read-only` blokuje m.in. `fs_abilities.single_set_globals` (`list` pada). Extra `--restrict-mode read-write` to zdejmuje.

---

## 5. Top 3 przy takim sudo+Python CLI

1. **Extra argv zjada jail** — dwie te same flagi, last-wins; potem `backup` / read `/root`.
2. **Serwer = FS API jako root** — jak RW: `backup` (czytaj) albo `restore` w drugą stronę (`authorized_keys`, cron).
3. **Interpreter, nie rdiff** — `--debug`/rpdb, `PYTHONPATH` (tu `env_reset` to ubija), CWD w `sys.path`. Tu niepotrzebne.

Kolejność: `sudo -l` ma `*`? → `grep add_argument` pod restrict → druga taka sama flaga → czytaj `/root`.

---

## Notatki

- MySQL user ≠ Linux user. `3306` localhost-only.
- `owen` nie ma w LDAP ani w `glpi_users`.
- Writable poza home: `/tmp`, `/var/crash`, `/var/lib/php/sessions` (1733, bez listowania) — nie wektor.
- Nie commituj `user.txt` / `root.txt` / kluczy / `config_db.php`.
