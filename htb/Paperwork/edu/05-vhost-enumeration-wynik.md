# Subdomeny / vhost — wynik na Paperwork

## Metoda
```bash
# Host header fuzz (IP w URL!)
ffuf -u http://10.129.41.146/ -H 'Host: FUZZ.paperwork.htb' -w subdomains-wordlist.txt -mc 200,301,403

# Ręcznie: porównaj rozmiar body (nginx default 301 ≈ 178 B)
curl -sI -H 'Host: admin.paperwork.htb' http://10.129.41.146/
```

## Co wyszło na tym boxie (2026-07-12)
- **~2500** nazw z SecLists: **zero** hostów z inną treścią niż redirect.
- Typowy fałszywy wzorzec: `301` → `Location: http://paperwork.htb/`.
- Jedyny sensowny FQDN w labie: **`paperwork.htb`** (apex).

## nginx default vhost
Gdy tylko jeden `server_name`, reszta Hostów ląduje w **catch-all** → redirect na apex. **Brak ukrytej subdomeny ≠ brak exploitu** — backend może być na **innym porcie** (tu **1515/LPD**) lub pod **jedną ścieżką** (`/download/archive`).

## Panel logowania?
- Brak `/login`, `/admin`, formularzy na apex.
- Tekst na stronie: *management console … **offline*** — fabularnie **nie ma** panelu WWW w tym etapie.
- Pod `/download/` widać **Flask** (404 Werkzeug), ale znaleziona trasa to **`/download/archive`** (ZIP), nie login.

Logi: `loot/vhost-manual.txt`, `loot/login-path-probe.txt`, `loot/gobuster-root-small.txt`.