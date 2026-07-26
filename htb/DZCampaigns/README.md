# HTB DarkZero Campaigns (dzcampaigns) — write-up & scripts

Repozytorium do maszyny **dzcampaigns.htb** / DarkZero Campaigns (Hack The Box, HARD / tournament).

| | |
|--|--|
| Status | **ukończone** (user + system) |
| VPN | Release Arena EU |
| OS | Ubuntu SRV01 + dual forest AD (EXT / HTB) |
| Flagi | `loot/copy-paste.txt` |

## Pliki

- **[WRITEUP.md](WRITEUP.md)** — pełny łańcuch ze szczegółami  
- **[ACCESS.md](ACCESS.md)** — szybki replay  
- **[notes.md](notes.md)** — przebieg / notatki  
- **`scripts/`** — RCE, ExtraSID BO, SMB backup-intent  

## Szybki start (wymaga żywego boxa + VPN)

```bash
# 1) RCE (cookie jar zalogowanego usera w loot/)
python3 scripts/ast_rce.py 'id'

# 2) po DA EXT: forge BO ExtraSID + odczyt root flag na DC01
python3 scripts/forge_bo_extrasid.py --help
python3 scripts/smb_bo_get.py --help
```

## Topology (skrót)

- **SRV01** `172.16.20.3` — web + Gitea runner, domain EXT  
- **DC02** `172.16.20.2` — DARKZERO.EXT + Gitea  
- **DC01** `172.16.20.1` — DARKZERO.HTB (system flag)  

## Uwaga

Flagi i hasła są w WRITEUP / `loot/copy-paste.txt`.  
Repo najlepiej trzymać **private**.

## Licencja

Materiał edukacyjny HTB — zgodnie z regulaminem HTB.
