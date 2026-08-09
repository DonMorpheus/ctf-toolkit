> **Repo path:** [`ctf-toolkit/htb/DanglingTree`](https://github.com/DonMorpheus/ctf-toolkit/tree/main/htb/DanglingTree)

# danglingtree.htb (HTB turniej / AD)

| Pole | Wartość |
|------|---------|
| Domain | `danglingtree.htb` |
| DC | `dc.danglingtree.htb` |
| OS | Windows Server 2025 (Build 26100) |
| Status | **user + root** |
| Write-up | [WRITEUP.md](./WRITEUP.md) |

## Path (skrót)

`guest` → `anderson.w` (WAC) → `noah.b` (user) → `alex.o` (DPAPI) → `jake.h` (FCP) → **ESC1** → Administrator

## Szybki start (lab)

```bash
# czas do DC (Kerberos)
./scripts/sync_time_to_dc.sh <IP>

# WAC / noah
python3 scripts/wac_ps.py -c 'whoami'
python3 scripts/noah_exec.py 'whoami'

# DA (przy gotowym jake + ESC1 templates)
python3 scripts/esc1_get_admin.py
python3 scripts/get_flags.py
```

## Pliki

| Plik | Opis |
|------|------|
| `WRITEUP.md` | pełny przebieg |
| `ACCESS.md` | co działa (shell/WAC/SMB) |
| `notes.md` | notatki robocze |
| `scripts/` | replay (WAC, noah, FCP, ESC1, flags) |
| `WRITEUP.md (flags) / local lab `loot/copy-paste.txt`` | flagi + credy |

## Flagi

- user: `ae276f322ed6850b63a1e1c0944df018`
- root: `75ac3d7cd89ad1c1b41ab7a9ebe07c70`
