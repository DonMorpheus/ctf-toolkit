# Management (HTB, Linux)

nginx + **OpenAM** (SSO) + **OpenDJ** + **GLPI** + localhost MariaDB.  
Foothold: pre-auth RCE on OpenAM → app secrets → SSH `owen` (password reuse) → sudo `rdiff-backup --server` argparse jailbreak → root SSH key.

- **[WRITEUP.md](WRITEUP.md)** — łańcuch (bez flag i haseł)
- **[scripts/rdiff_sudo_jailbreak.sh](scripts/rdiff_sudo_jailbreak.sh)** — privesc przez extra argv (`*` w sudoers)

## Scripts

| File | What |
|------|------|
| `scripts/rdiff_sudo_jailbreak.sh` | z SSH `owen`: last-wins `--restrict-path /` + `--restrict-mode read-write`, potem `backup /root` |

```bash
# po SSH jako owen (nie root)
bash scripts/rdiff_sudo_jailbreak.sh
# → /tmp/stolen-root/root.txt + /tmp/stolen-root/.ssh/id_ed25519
```

Foothold OpenAM (CVE-2026-33439) zostawiamy w labie — tu tylko łańcuch i privesc.  
No flags, VPN configs, or live passwords in this tree.
