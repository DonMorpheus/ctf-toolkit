# SSH agent-forward trap (`-A` only)

Forces admins to connect with **`ssh -A`** on **port 22**; blocks sessions without forwarded agent. Disables **`-R` / `-L`** for the matched account.

| File | Role |
|------|------|
| `require_agent_forward.sh` | `ForceCommand` — English deny message |
| `sshd_match_legacy.snippet` | `Match User legacy` + **`LocalPort 22`** |
| `install_trap.sh` | Copy script to `/usr/local/bin/` |

**Pivot:** set `SSH_SERVER_PORT=22`, then [pivot_to_admin_pc.sh](../ssh-infected-admin-pivot/pivot_to_admin_pc.sh).

**Write-up:** [WRITEUP-ssh-agent-forward-trap.md](../WRITEUP-ssh-agent-forward-trap.md)

**Kali lab (isolated `:2221`, not system SSH):** `~/Desktop/htb/ttp-docker-ssh-lab/` + `ACCESS-AGENT-TRAP.md`