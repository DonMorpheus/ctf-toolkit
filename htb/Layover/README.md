# Layover (HTB, Linux)

Passenger Wi-Fi kiosk (xrdp) plus an airside Craft CMS portal. Dual-homed jumpbox → Craft SSTI as a CP user → decrypt a settings blob with `CRAFT_SECURITY_KEY` → local `su` → CUPS 2.4.16 file overwrite → root.

- **[WRITEUP.md](WRITEUP.md)** — chain (no flags, no live passwords)
- **[scripts/](scripts/)** — GHSA-c54j-2vqw-wpwp local CUPS PoC

## Scripts

| File | What |
|------|------|
| `scripts/ghsa_c54j_cups_local.py` | unprivileged local user: leak `Authorization: Local`, persist `file:///etc/sudoers.d/…`, print a sudoers line |

```bash
# on the portal host as the unprivileged user (localhost:631, CUPS 2.4.16)
python3 scripts/ghsa_c54j_cups_local.py --user aporter
sudo -n id
```

No flags, VPN configs, or live passwords in this tree.
