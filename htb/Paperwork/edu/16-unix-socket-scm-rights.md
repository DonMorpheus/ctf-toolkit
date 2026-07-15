# Unix domain socket + SCM_RIGHTS (Paperwork / ogólna nauka)

## Po co to na boxie?

`paperwork-daemon` (root) nie może po prostu wysłać hasła w plaintext na `mgmt.sock` przy każdym połączeniu — wtedy każdy w grupie **archivist** miałby je od razu. Zamiast tego:

- **Stan normalny:** tylko hash (`SIGNATURE`) — dowód że daemon zna sekret, bez jego ujawniania.
- **Stan incydentu:** daemon uznaje, że archivist musi **zobaczyć dowody** (log + plik configu) → przekazuje **fd** do już otwartych plików roota.

To klasyczny wzorzec **privilege boundary**: root **udostępnia odczyt** konkretnego fd zamiast chmod na pliku.

## Unix domain socket vs TCP

| | TCP `127.0.0.1:port` | UNIX `path.sock` |
|--|----------------------|------------------|
| Adres | IP + port | ścieżka w FS |
| Widoczność | często firewall | prawa pliku/katalogu |
| Typowe użycie | usługi sieciowe | docker, DB, **lokalny IPC** |

Na Paperwork: `srw-rw---- root archivist /run/paperwork/mgmt.sock` → tylko **root** i **archivist**.

**Ćwiczenie (Kali, lokalnie, bez roota na drugim koncie):**
```bash
# terminal 1 — prosty serwer (Python)
python3 - <<'PY'
import socket, os
path = "/tmp/demo.sock"
if os.path.exists(path): os.unlink(path)
s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.bind(path)
os.chmod(path, 0o660)  # symulacja grupy
s.listen(1)
print("listen", path)
c, _ = s.accept()
c.sendall(b"hello\n")
c.close(); s.close()
PY
# terminal 2
python3 -c 'import socket;s=socket.socket(socket.AF_UNIX);s.connect("/tmp/demo.sock");print(s.recv(16))'
```

## SCM_RIGHTS — przekazywanie fd

W Linux **deskryptor pliku** można wysłać razem z wiadomością na sockecie (`sendmsg` / `recvmsg`), kontrolując to przez **ancillary data** (`SCM_RIGHTS`).

Szkic (jak w `paperwork-daemon`):

```python
# nadawca (root)
log_fd = os.open("/path/to/log", os.O_RDONLY)
admin_fd = os.open("/etc/secret", os.O_RDONLY)
fds = array.array("i", [log_fd, admin_fd])
conn.sendmsg([b"ALERT...\n"], [(socket.SOL_SOCKET, socket.SCM_RIGHTS, fds)])

# odbiorca (archivist)
msg, anc, flags, addr = conn.recvmsg(4096, socket.CMSG_LEN(32))
for cmsg_level, cmsg_type, cmsg_data in anc:
    if cmsg_type == socket.SCM_RIGHTS:
        received = array.array("i", cmsg_data)
        for fd in received:
            print(os.read(fd, 4096))
            os.close(fd)
```

**Ważne:**

- Odbiorca dostaje **nowy numer fd** (kopę procesową), ale wskazuje na **ten sam plik** (inode) co u roota.
- Uprawnienia odczytu są „dziedziczone” z tego, że root otworzył plik — **nie** musisz móc `cat` pliku na dysku jako archivist.
- Po `recvmsg` **zamknij** fd po odczycie (`os.close`).

**Python 3.13:** `socket.CMSG_LEN(32)` — nie `CMSG_LEN * 32` (TypeError).

## Powiązanie z triggerem w `commands.log`

1. `jetdirect` loguje np. `Command: @PJL FSQUERY ...` do `commands.log`.
2. Daemon robi `content.upper()` i szuka substringów — wystarczy **jedna** z listy.
3. Przy lockdown tworzy też `/root/quarantine/evidence.zip` (archivist **nie** czyta — to ślad forensics dla lore).

**Ćwiczenie:** jako archivist na boxie (po solve):
```bash
# pusty log → clean
: > /home/archivist/printer/logs/commands.log
python3 -c 'import socket;s=socket.socket(socket.AF_UNIX);s.connect("/run/paperwork/mgmt.sock");print(s.recv(512).decode())'
# powinno: STATUS: SYSTEM_CLEAN
```

## SIGNATURE vs plaintext

```python
token = hashlib.sha256(f"SYSTEM_CLEAN:{secret}".encode()).hexdigest()
```

- Klient może **zweryfikować**, że daemon zna sekret (jeśli sam zna sekret z innego kanału).
- Klient **nie** odzyskuje sekretu z samego hasha.
- Pełny sekret pojawia się dopiero w ścieżce **lockdown + SCM_RIGHTS**.

To dobry temat pod pytania rekrutacyjne: *„jak udostępnić dowód bez chmod 644 na /etc/secret?”*

## Błędy które warto rozpoznać

| Objaw | Przyczyna |
|-------|-----------|
| `Permission denied` na `mgmt.sock` | nie jesteś w grupie archivist (np. nadal `lp`) |
| Tylko `SYSTEM_CLEAN`, brak `ADMIN_PASSWORD` | log bez triggera — najpierw PJL FS* |
| `ALERT` ale pusty ancillary | błąd w `recvmsg` (buffer CMSG, zamknięty socket) |
| `Connection reset` na 9100 | zbyt wiele testów PJL — reset maszyny HTB |

## Dalsza lektura (ogólna)

- `man 7 unix` — UNIX domain sockets
- `man 3 sendmsg` / `SCM_RIGHTS`
- Linux **file descriptor passing** (classic Stevens / APUE topic)

Powrót do całości: **`15-podrecznik-po-solve.md`**.