# FireFlow — fireflow.htb (HTB EU)

**IP:** `10.129.244.214` (aktualne: `target.txt`)

## /etc/hosts
```
10.129.244.214 fireflow.htb
```

## Nmap initial (`nmap/initial.*`)
| Port | State | Service | Version |
|------|-------|---------|---------|
| 22/tcp | open | ssh | OpenSSH 9.6p1 Ubuntu 3ubuntu13.16 |
| 443/tcp | open | ssl/http | **nginx** (TLS cert CN/SAN: **fireflow.htb**, `*.fireflow.htb`) |
| 9100, 30000, 30718, 30951, 31038, 31337 | filtered | — | — |

- HTTPS redirect: `https://fireflow.htb/`
- Org na cert: Task Force Nightfall

## Subdomeny (vhost)
- Cert SAN: `fireflow.htb`, `*.fireflow.htb`
- **Rzeczywiste vhosty (gobuster 5k + ręcznie):**
  - `fireflow.htb` → landing (12913 B)
  - `flow.fireflow.htb` → Langflow (1142 B SPA shell)
- Reszta `*.fireflow.htb` → **301** na `https://fireflow.htb/` (catch-all)

## Ukryte / istotne ścieżki
- `fireflow.htb`: brak hitów gobuster (raft-small) poza główną stroną; kotwice `#status`, `#context`
- `flow.fireflow.htb`: `/docs` (Swagger UI), `/health`, `/openapi.json`, `/api/v1/*`, `/playground/<uuid>`, `/logs` → **403**

## RCE — `build_public_tmp` (bez auth)
- Cookie: `client_id=<dowolny>`
- `POST /api/v1/build_public_tmp/<flow_id>/flow` z body `inputs` + **`data`** (nadpisuje graf z public_flow)
- Wstrzyknięcie w `TextOperations` → `template.code.value` → `process_text()` → `subprocess`
- Skrypt: `scripts/build_public_rce.py`
- Wynik: **`www-data`** na hoście (`/var/lib/langflow`)

## Enum www-data → credy
- **`/etc/langflow/.env`**: `LANGFLOW_SUPERUSER` / `LANGFLOW_SUPERUSER_PASSWORD`, `LANGFLOW_SECRET_KEY`
- **SSH `nightfall@`** — hasło jak superuser Langflow (sprawdzone)
- **K3s** aktywny: `6443`, `10250`, kubelet porty; Langflow `127.0.0.1:7860` → nginx `flow.*`
- **`/opt/lab/firewall.sh`** — root-only (`-rwx------`)
- Pełny zrzut: `loot/www-data-enum.txt`