# Nexus — nexus.htb (HTB EU)

**IP:** `10.129.44.62` (aktualne: `target.txt`)

## VPN
- `machines_eu-1.ovpn` — tun0 10.10.16.106/23

## /etc/hosts
```
10.129.44.62 nexus.htb
```

## Nmap initial
| Port | Service | Notes |
|------|---------|-------|
| 22/tcp | OpenSSH 9.6p1 Ubuntu | |
| 80/tcp | nginx 1.24.0 | redirect → `http://nexus.htb/` |

Skany: `nmap/initial.{nmap,gnmap,xml}`

## Web stack (enumeracja)
- **Reverse proxy / serwer:** nginx **1.24.0** (Ubuntu), tylko **:80** (brak HTTPS na zewnątrz)
- **Aplikacja:** statyczny **HTML** (~49 KB), brak PHP/CGI/API/backendu w nagłówkach
- **WhatWeb:** HTML5, brak frameworków (nie Sonatype Nexus — to „Nexus Energy Authority”)
- **Nikto:** brak krytycznych findingów; brak CSP/HSTS/X-Content-Type-Options
- **Dir fuzz (raft-medium):** brak ukrytych ścieżek (poza główną stroną)
- **Vhost fuzz:** subdomeny → **302** na `http://nexus.htb/` (catch-all)
- **OSINT ze strony:** `careers@nexus.htb`, `j.matthew@nexus.htb` (hiring manager)

## CVE / słabe punkty (nginx 1.24 + SSH)
### nginx 1.24.0 — teoretycznie w zasięgu (searchsploit: brak RCE pod tę wersję)
| CVE | Opis | Realny wektor tutaj? |
|-----|------|----------------------|
| CVE-2024-7347 | ngx_http_mp4_module buffer overread | **Niski** — brak `.mp4` / modułu w użyciu |
| CVE-2025-23419 | reuse sesji SSL przy wielu `server_name` | **Niski** — brak TLS na :80 |
| CVE-2022-41741/42 | mp4 module (stare) | **Niski** — jak wyżej |
| CVE-2019-9511/9513 | HTTP/2 DoS (Rapid Reset / priority) | **Średni** tylko jako DoS, nie RCE |
| Nowsze (2026, 1.29+) | rewrite/proxy/grpc/http3 | **N/A** — wersja 1.24 poza częścią zakresów lub wymaga modułów |

**Wniosek:** nginx jest **stary / EOL-owy** (nuclei: `nginx-eol`), ale na tej maszynie wygląda na **prosty static site** — exploit CVE nginx mało prawdopodobny vs. **SSH + usernames z WWW**.

### OpenSSH 9.6p1 Ubuntu 3ubuntu13.16
- Backport Ubuntu — **brak publicznego RCE** pod ten exact build w searchsploit
- Wektor: **brute/user enum** (`j.matthew`, `careers`, warianty imienia/nazwiska), klucze, leak credów z innego wektora

### Sensowne wektory (priorytet)
1. Usernames / phishing / password spray → **SSH**
2. Dalsza enumeracja (inne hosty, UDP, full TCP, content w HTML/job modal)
3. nginx — tylko jeśli pojawi się **proxy/php/upload/mp4** lub **TLS**

## Subdomeny (ffuf, wordlist 110k, filtr 49296+154)
| Vhost | Status | Uwagi |
|-------|--------|-------|
| **git.nexus.htb** | 200 | **Gitea 1.26.0**, repo `admin/krayin-docker-setup` |
| **billing.nexus.htb** | 302→login | **Krayin CRM** (Laravel), `/admin/login`, cookies XSRF+session |
| mail/smtp/pop3/www | 302 | catch-all → główna strona |

`/etc/hosts`: `git.nexus.htb`, `billing.nexus.htb`

## OWASP / XSS — nexus.htb (główna)
- **Brak** `<form>`, inputów, backendu — statyczny HTML + modal (tylko JS lokalny)
- Query params (`q`, `search`, `name`, …): **brak odbicia** → **XSS/SQLi: nie**
- **TRACE:** 405; **path traversal:** 404/400; **OPTIONS:** 405
- **A05 misconfig:** brak CSP, HSTS, X-Frame-Options, X-Content-Type-Options (nikto)
- **Clickjacking:** brak `X-Frame-Options` / CSP `frame-ancestors` na głównej (teoretycznie ramka UI — niski impact bez sesji)
- **A02:** brak TLS na :80

## OWASP — subdomeny (tu jest surface)
- **git.nexus.htb:** Gitea → auth bypass/CVE, leaked repo, `.env` w docker setup
- **billing.nexus.htb:** Krayin/Laravel → login spray, CSRF token obecny, typowe web app testy (nie reflected XSS na `email` w quick test)

## Repo `krayin-docker-setup` (sklonowane do `loot/krayin-docker-setup/`)
- Pliki: `.env`, `docker-compose.yml`, `documents` (1024 B same zera — placeholder pod volume `storage`)
- **2 commity** — w **pierwszym** `.env` miał `DB_PASSWORD` (potem wyczyszczone w HEAD)
- **Hasło DB z historii gita:** patrz `loot/copy-paste.txt`
- Compose: `webkul/krayin:latest`, MySQL `krayin`, phpMyAdmin :8080 (wewnątrz stacku)
- IMAP prod: `imap.nexus.htb:993` (user/pass w .env wygląda na przykładowe)

## User flag (jones)
- **SSH:** `jones@10.129.44.62` hasło **`N27xh!!2ucY04`** (reuse z Gitea `.env` / Krayin)
- **Flag:** `8b23a023ce38b97fd8bae439ad6e2da8` → `loot/copy-paste.txt`