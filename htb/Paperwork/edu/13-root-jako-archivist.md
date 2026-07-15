# Root — czy da się jako **archivist**?

## Krótka odpowiedź

**Tak** — root na Paperwork jest zaplanowany **po wejściu jako `archivist`** (UID 1000), nie jako `lp` i **nie** przez PJL odczyt `/root/root.txt`.

**User flag** dało się wziąć jako `lp` przez PJL (`FSUPLOAD` + `../user.txt`).  
**Root** wymaga uprawnień grupy **archivist** do `mgmt.sock` i dalszego łańcucha.

## Co **nie** zadziała (potwierdzone)

| Pomysł | Wynik |
|--------|--------|
| PJL `FSUPLOAD` → `../../../root/root.txt` | reset / **Connection refused** na 9100 |
| PJL → `/etc/paperwork/admin_pins.conf` | poza sandboxem / crash |
| `mgmt.sock` jako **`lp`** | **Permission denied** (socket `root:archivist`) |
| CorpoSite `:1337` — `/admin`, `/pin`, `/verify` | **404** (fuzz `cf1337`) |
| SSH `archivist` z Kali (klucz) | nadal **Permission denied** (klucz nie wgrany) |

## Łańcuch root (z `paperwork-daemon`)

1. **Zatruj** `commands.log` komendą z triggerami: `FSQUERY` / `FSUPLOAD` / `FSDOWNLOAD` (jetdirect `:9100`).
2. Jako **`archivist`** połącz się z **`/run/paperwork/mgmt.sock`**.
3. Daemon robi **lockdown** → `recvmsg` + **SCM_RIGHTS** → fd **`admin_pins.conf`** (+ log).
4. Odczyt **`ADMIN_PASSWORD=`** (plik ~38 B w `/etc/paperwork/admin_pins.conf`).
5. **Root:** hasło z kroku 4 = **`su root`** (potwierdzone na `10.129.41.199`) — **nie** trzeba znajdować panelu na `:1337`.
6. **CorpoSite** / **laurel** — lore / forensics; privesc do roota idzie przez **`ADMIN_PASSWORD`** w PAM/`su`.

Skrypt na target **jako archivist**: `scripts/mgmt_chain.sh`  
Skrypt leak: `scripts/mgmt_leak_admin.py`

## Co musisz mieć przed rootem

**Shell jako `archivist`**, np.:

- działający **`ssh archivist@paperwork`** (klucz w `authorized_keys` — zapis PJL nadal problematyczny), **albo**
- `su archivist` hasłem — hasło zwykle dopiero z **kroku 4** (pętla: najpierw mgmt bez hasła SSH).

Praktycznie: **napraw zapis klucza SSH** (jeden test po resecie 9100) **albo** interaktywny sposób wejścia na `archivist`, potem `mgmt_chain.sh`.

## PJL a root

PJL **nie** zastępuje shella `archivist` dla `mgmt.sock`.  
Może pomóc **tylko** w czytaniu plików **pod** `/home/archivist/...` (`../user.txt` ✅), nie `/root`.

## Następne kroki (kolejność)

1. Reset boxa jeśli **9100** pada.
2. Wejście **archivist** (SSH / inny).
3. Trigger PJL + `mgmt_leak_admin.py` → pin do `loot/copy-paste.txt`.
4. **`su root`** hasłem z leaku → `root.txt`.
5. Nauka po solve: **`15-podrecznik-po-solve.md`**, **`16-unix-socket-scm-rights.md`**, ćwiczenia **`17-cwiczenia-kali.md`**.