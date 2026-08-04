# Silentium — HackTheBox

Linux Easy. Attack path: **vhost staging → Flowise auth-bypass + RCE → host creds → Gogs CVE → root**.

| | |
|--|--|
| **OS** | Ubuntu 24.04 |
| **Entry** | `silentium.htb` / `staging.silentium.htb` |
| **Foothold** | Flowise 3.0.5 (account takeover + CustomMCP RCE in Docker) |
| **User** | SMTP/env password reuse → SSH `ben` |
| **Root** | Gogs **0.13.3** — CVE-2025-8110 (symlink + PutContents) as root process |

Full write-up: [`WRITEUP.md`](WRITEUP.md)  
Scripts: [`scripts/`](scripts/)

No flags / VPN configs / live API tokens in this tree.

---

## Lab setup

```bash
# HTB VPN (machines)
echo '<TARGET_IP> silentium.htb staging.silentium.htb staging-v2-code.dev.silentium.htb' | sudo tee -a /etc/hosts
```

External ports: **22**, **80**. Internally after foothold: Flowise `:3000`, Gogs `:3001`, MailHog `:8025`/`:1025` (localhost).

---

## Attack chain (overview)

```text
┌──────────────────────┐
│ silentium.htb :80    │  marketing site (team names)
└──────────┬───────────┘
           │ vhost
           ▼
┌──────────────────────┐   forgot-password → tempToken
│ staging.silentium.htb│ ──────────────────────────────► reset + login
│ Flowise 3.0.5        │
└──────────┬───────────┘
           │ CustomMCP node-load (API key)
           │ root *inside Docker*
           ▼
┌──────────────────────┐   env: SMTP_PASSWORD = SSH
│ container secrets    │ ──────────────────────────────► SSH ben@host
└──────────┬───────────┘
           │ user.txt
           ▼
┌──────────────────────┐   register/login, CVE-2025-8110
│ staging-v2-code…     │ ──────────────────────────────► write authorized_keys
│ Gogs 0.13.3 (root)   │
└──────────┬───────────┘
           ▼
        root@host
```

---

## Scripts

| Script | Purpose |
|--------|---------|
| [`scripts/flowise_account_takeover.py`](scripts/flowise_account_takeover.py) | Enum email + forgot/reset → session cookies / API key |
| [`scripts/flowise_custommcp_rce.py`](scripts/flowise_custommcp_rce.py) | CustomMCP RCE helper (command via OOB or short exec) |
| [`scripts/gogs_cve_2025_8110_root.py`](scripts/gogs_cve_2025_8110_root.py) | Create token flow / symlink PutContents → plant SSH key |

Replace placeholders (`TARGET`, credentials you find, `LHOST`). Educational / HTB lab only.
