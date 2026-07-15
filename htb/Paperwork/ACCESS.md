# Paperwork — dostęp

| Typ | Status |
|-----|--------|
| SSH | `22` — **`archivist`** hasłem z `ADMIN_PASSWORD` (to nie to samo co pin w pliku na **świeżym** boxie — pin = **root**; hasło usera po resecie często trzeba zsynchronizować lub użyć klucza) lub **klucz** `~/.ssh/id_ed25519` |
| WWW | `80` — nginx → `http://paperwork.htb/` (intranet static) + Flask `/download/archive` |
| Login WWW | **Brak** (konsola PRN-ARCHIVE-01 „offline” w treści strony) |
| LPD | `1515/tcp` — RFC 1179-style (kod: `loot/archive-src/server.py`) |
| Shell | **TAK** — user **`lp`** via LPD (`scripts/lpd_exploit.py` → rev shell) |
| user flag | **`archivist`** → `/home/archivist/user.txt` (nie `lp`, nie `_laurel`) |
| Pivot | **`lp` → jetdirect `127.0.0.1:9100`** — **`FSUPLOAD`+`../` = odczyt** (user.txt ✅); **zapis** klucza → `../.ssh/authorized_keys`; **`ssh archivist`** (brak `id_*` do kradzieży — patrz `loot/PJL-READ-SESSION.md`) |
| Inne opcje | `edu/10-inne-opcje-pivot.md` — co nie działa z `lp`, co po archivist |
| mgmt.sock | tylko grupa **archivist** → leak `admin_pins.conf` (po wejściu jako archivist) |
| root | **`su root`** z hasłem **`ADMIN_PASSWORD`** (to samo co SSH archivist) — CorpoSite nie jest wymagany |

Credy i flagi → `loot/copy-paste.txt`