# lp → archivist / _laurel (Paperwork) — stan enum

## `.env`
**Brak** plików `.env` na boxie (`find` pusty). Credy nie w env — patrz **`/etc/paperwork/admin_pins.conf`** (root-only).

## `_laurel` ≠ user do `su`
- Konto systemowe **laurel** (audit log): `/var/log/laurel`, shell `/bin/false`.
- Config: `/etc/laurel/config.toml` — **czytelny dla `lp`**.
- `read-users` w config **zakomentowane** — logi `audit.log` są `600 _laurel`.

## Broken / interesujące permy
| Obiekt | Uwagi |
|--------|--------|
| `/usr/bin/paperwork-daemon` | **world-readable** — cała logika lockdown + leak FD |
| `/run/paperwork/mgmt.sock` | `srw-rw---- root:archivist` — tylko grupa **archivist (1000)** |
| `/opt/LPDServer/server.py` | `645` root:lp — lp czyta kod |
| `/etc/paperwork/admin_pins.conf` | `600 root` — treść przez **SCM_RIGHTS** z daemona |

## Łańcuch (z `paperwork-daemon`)
1. **jetdirect** (`127.0.0.1:9100`, user **archivist**) loguje komendy → `commands.log`.
2. Jeśli w logu: `FSQUERY`, `FSUPLOAD`, `FSDOWNLOAD` → daemon **lockdown**.
3. Lockdown wysyła przez UNIX socket **`SCM_RIGHTS`**: fd logu + fd **`admin_pins.conf`**.
4. Klient musi być w grupie **archivist** (połączenie do `mgmt.sock`).

## Co robić jako `lp` (w Twoim shellu)
```bash
# 1) Zsyntetyzuj „malice” w logu (wymaga protokołu jetdirect — testuj nc):
printf '...\n' | nc 127.0.0.1 9100

# 2) Jako archivist (po wejściu w grupę / user):
python3 -c '...'  # connect mgmt.sock, recvmsg → pread admin_fd

# 3) WWW backend (nie entry, ale enum):
curl -s http://127.0.0.1:1337/
```

## User flag
Prawdopodobnie **`/home/archivist/user.txt`** (nie `lp`, nie `_laurel`).

Pełny log enum: `loot/lpd-callback.log`, skrypt: `scripts/lpd_post.sh`.