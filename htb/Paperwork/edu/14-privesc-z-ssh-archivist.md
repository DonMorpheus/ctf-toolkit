# Privesc z SSH `archivist` (Paperwork)

## Sesja
- Z Kali: `ssh` / `sshpass` jako **archivist** (agent też robi **BatchMode** — to ten sam poziom co Twoja sesja interaktywna).
- Pełny log enum: `loot/privesc-enum-archivist.txt`.

## Klasyczny enum — wynik (skrót)

| Wektor | Wynik |
|--------|--------|
| `sudo -l` | **brak** `sudo` w PATH |
| SUID | tylko standard (m.in. `/usr/bin/su`) |
| capabilities | `mtr-packet cap_net_raw` |
| cron writable | nie |
| `/etc` writable | nie |
| docker/lxd | nie |
| `linpeas` | niepotrzebny — wektor boxowy |

## Wektor HTB (właściwy)

1. **Grupa:** socket `/run/paperwork/mgmt.sock` → `root:archivist` — tylko **archivist**.
2. **Trigger:** wpis w `/home/archivist/printer/logs/commands.log` z `FSQUERY` / `FSUPLOAD` / `FSDOWNLOAD` (np. jedno `@PJL FSQUERY` na `127.0.0.1:9100`).
3. **Lockdown:** `paperwork-daemon` (root) → `recvmsg` + **SCM_RIGHTS** → fd logu + fd **`/etc/paperwork/admin_pins.conf`**.
4. **Odczyt:** `ADMIN_PASSWORD=...` (skrypt `scripts/mgmt_leak_admin.py`).
5. **Root:** to hasło działa w **`su root`** (PAM) — **nie** wymaga CVE ani CorpoSite `:1337`.

```bash
# na boxie jako archivist
python3 -c 'import socket;s=socket.socket();s.connect(("127.0.0.1",9100));s.sendall(b"@PJL FSQUERY NAME=\".\"\r\n");s.recv(1024)'
python3 ~/mgmt_leak_admin.py   # lub one-liner z edu/09
su -
# hasło = ADMIN_PASSWORD
cat /root/root.txt
```

## Pułapki
- Czyste połączenie z `mgmt.sock` (pusty log) daje tylko `SIGNATURE:` — **nie** plaintext hasła.
- Pin z pliku ≠ zawsze hasło SSH `archivist` na świeżym resecie; **root** `su` z pinem zwykle tak.