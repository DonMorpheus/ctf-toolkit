# enigma.htb

| Pole | Wartość |
|------|---------|
| IP | `10.129.239.191` (sprawdź `target.txt` po respawn) |
| Status | **solved** (user + root) |
| VPN | `machines_eu-1.ovpn` → `tun0` |

## /etc/hosts

```
10.129.239.191 enigma.htb mail001.enigma.htb support_001.enigma.htb
```

## Pliki

| Plik | Po co |
|------|--------|
| `ACCESS.md` | replay wejścia / shell |
| `notes.md` | przebieg ataku |
| `loot/copy-paste.txt` | flagi + credy |
| `edu/` | nauka po boxie |