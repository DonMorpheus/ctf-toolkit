# SSH agent-forward trap (`-A` only)

Forces admins to connect with **`ssh -A`**; blocks sessions without forwarded agent. Disables **`-R` / `-L`** on the match block.

| File | Role |
|------|------|
| `require_agent_forward.sh` | `ForceCommand` — English deny message |
| `sshd_match_legacy.snippet` | `Match User legacy` + port |
| `install_trap.sh` | Copy script to `/usr/local/bin/` |

**Attack after admin connects:** [../ssh-infected-admin-pivot/pivot_to_admin_pc.sh](../ssh-infected-admin-pivot/pivot_to_admin_pc.sh)

**Write-up:** [WRITEUP-ssh-agent-forward-trap.md](../WRITEUP-ssh-agent-forward-trap.md)

**Local lab:** `~/Desktop/htb/ttp-docker-ssh-lab/` + `ACCESS-AGENT-TRAP.md`