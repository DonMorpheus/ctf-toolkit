# Easy — czy da się „dodać moduł” do serwisu?

## Krótka odpowiedź: **nie** (w sensie systemd / nginx / plugin Python)

Sprawdzone na boxie jako **`lp`** (log: `loot/lpd-callback.log`, tag `/easy`):

| Serwis | Co jest w unit / katalogu |
|--------|---------------------------|
| **lpdserver** | Tylko `/opt/LPDServer/server.py` — **brak** `plugins/`, `importlib`, drop-inów w `lpdserver.service.d/` |
| **jetdirect** | `/home/archivist/printer/jetdirect.py` — **`lp` nie czyta** katalogu (Permission denied) |
| **CorpoSite** | `/root/staging/CorpoSite/app.py` — root only |
| **nginx** | proxy całego vhosta na `:1337` — **brak** `/modules`, `/plugin` (404) |

**Metasploit `search lpd`** = inne systemy operacyjne, **nie** ten custom Python.

## ZIP ≠ produkcja (ważne na Easy)

`paperwork-archive-v1.02.zip` ma **stary / okrojony** `server.py` (2820 B).

Na maszynie **`server.py` ma ~2940 B** i dodatkowo obsługuje **subcommand 3** (data file) — ale to tylko **odbiór i drain**, **nie** ładowanie modułu ani zapis do drukarki.

Foothold nadal: **injection w `job_name`** (`shell=True`) — to jest cały „moduł” LPD.

## Co na Easy **jest** proste (3 kroki w głowie)

1. **LPD :1515** → shell **`lp`** (już działa).
2. **localhost:9100** → **jedna** komenda PJL zapisuje plik **jako UID archivist** (klucz SSH) — **nie** `FSEXEC`, **nie** rev shell z PJL.
3. **`ssh archivist`** → `user.txt` → potem opcjonalnie **mgmt.sock** (pin z `admin_pins.conf`).

„Prostota” = **jeden poprawny format zapisu** (`jetdirect_upload_ok.py`: `FSUPLOAD` + `SIZE` w **drugiej linii** + body), **bez** spamu testów na 9100 (serwis pada → reset).

## Pułapki które wyglądają na „moduł”

- **`FSEXEC`** → `OK`, ale **nie wykonuje** poleceń.
- **Echo `@PJL FSUPLOAD … SIZE=0`** → odpowiedź protokołu, **nie** znaczy że zapis się udał — zawsze weryfikuj **`ssh archivist`** z Kali.
- **`mgmt.sock`** → tylko grupa **archivist**, nie `lp`.
- **Hasło SSH** archivist → nie jest `archive_intake` / nazwa boxa (szybki test — fail).

## Nie komplikuj

- Nie szukaj CVE na nginx/OpenSSH — patrz `loot/CVE-RESEARCH.md`.
- Nie dodawaj plików do `/opt/LPDServer` — **lp nie ma zapisu** (`root:lp`, `644`).