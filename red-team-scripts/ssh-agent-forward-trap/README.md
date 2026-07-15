# SSH agent-forward trap (`-A` only)

Forces **`ssh -A`** on **port 22**; English deny message if agent not forwarded. Blocks **`-R` / `-L`** on matched account.

| File | Role |
|------|------|
| `require_agent_forward.sh` | `ForceCommand` checker |
| `sshd_match_legacy.snippet` | Production: **`LocalPort 22`** |
| `sshd_match_legacy_lab_2221.snippet` | Isolated lab sshd |
| `install_trap.sh` | Install to `/usr/local/bin/` |

After admin connects with `-A`:

```bash
export SSH_SERVER_PORT=22
sudo ../ssh-infected-admin-pivot/pivot_agent_to_admin.sh <ADMIN_IP>
```

**Write-up:** [WRITEUP-ssh-agent-forward-trap.md](../WRITEUP-ssh-agent-forward-trap.md)  
**Kali lab:** `~/Desktop/htb/ttp-docker-ssh-lab/setup_kali_user.sh` (uses `:2221`)