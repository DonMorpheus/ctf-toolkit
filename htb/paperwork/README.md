# HTB — Paperwork (scripts)

| Script | Role |
|--------|------|
| `lpd_exploit.py` | RFC 1179-style client; command injection via `job_name` |
| `write_ssh_correct.py` | PJL `FSDOWNLOAD` — write SSH pubkey to `authorized_keys` |
| `mgmt_leak_admin.py` | After FS* trigger: `mgmt.sock` + SCM_RIGHTS → read config fd |
| `mgmt_chain.sh` | Trigger + leak one-liner on target |
| `pjl_read_compact.py` / `pjl_read_one.py` | PJL read helpers |
| `path_escape_pjl.py` | Path traversal tests under jetdirect root |
| `jetdirect_upload_ok.py` | Working upload format reference |
| `archivist_root_enum.py` | Privesc prep enum from archivist context |
| `lpd_callback_server.py` | Receive exfil on Kali (companion to `lpd_post.sh`) |
| `lpd_post.sh` | Run cmd on target via LPD → POST to `LHOST:8900` |
| `corpo_fuzz1337.sh` | Local Flask path probe (run on target) |

Environment:

- `LHOST` — your HTB VPN IP for callbacks (default in scripts is a placeholder; override with `export`).

Conceptual chain (no spoilers): **LPD → archivist → printer log trigger → management socket → local privesc.**  
Write-up (public): see author’s LinkedIn / local notes — not duplicated here.