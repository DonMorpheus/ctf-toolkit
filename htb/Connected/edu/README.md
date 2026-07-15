# Connected — nauka w wolnym czasie

Czytaj po kolei lub wybierz temat. Każdy plik ma **teorię**, **powiązanie z boxem** i **ćwiczenia na Kali** (bez psucia produkcji).

## Mapa tematów

| # | Plik | Poziom | O czym |
|---|------|--------|--------|
| 1 | [01-freepbx-foothold-cve57819.md](01-freepbx-foothold-cve57819.md) | średni | SQLi → fake admin → upload → RCE |
| 2 | [02-incron-sysadmin-manager.md](02-incron-sysadmin-manager.md) | głęboki | incrond, spool, podpisane hooki, `sysadmin_manager` |
| 3 | [03-ha-trigger-suid.md](03-ha-trigger-suid.md) | głęboki | `ha_trigger`, brakujący moduł, SUID, model zaufania ścieżek |
| 4 | [04-asterisk-ami-mysql.md](04-asterisk-ami-mysql.md) | średni | AMI :5038, DB, dlaczego to nie SSH |
| 5 | [05-linux-privesc-patterns.md](05-linux-privesc-patterns.md) | przegląd | SUID, cron/incron, capabilities — porównanie wektorów z tego boxa |
| ★ | **[READING-apt-level.md](READING-apt-level.md)** | **lektura** | **Książki, man, OWASP, docs — żeby wejść na poziom APT (umiejętność)** |

## Sugerowana kolejność (weekend)

1. Dzień 1 — przeczytaj **01**, odtwórz foothold (`enum_privesc.py`), zapisz własny schemat w notatniku.
2. Dzień 2 — **02** + przejrzyj `loot/incron-ssh-summary.txt` i `notes.md` (sekcja incron).
3. Dzień 3 — **03** + ręcznie: `mkdir` modułu, `touch ha_trigger`, `ls -la /bin/bash`.
4. Dzień 4 — **04** + **05**, lista „co bym sprawdził na innym PBX”.

## Zasady ćwiczeń

- Lab tylko HTB / własna VM.
- Nie polegaj na starym URL webshell — zawsze generuj nowy.
- Jak coś nie działa: najpierw **ACCESS.md**, potem log w `loot/`.

## Materiały zewnętrzne (oficjalne / techniczne)

- FreePBX / Sangoma — dokumentacja modułów (framework, sysadmin, endpoint).
- `man incrond`, `man 5 incrontab` na Kali.
- CVE / GHSA dla endpoint 16.x (upload, SQLi) — wpisy z `loot/cve-57819-notes.md`.

Po kolejnym boxie agent dopisze folder `edu/` w tym samym stylu.