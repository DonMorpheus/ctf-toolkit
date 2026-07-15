# Red Team Scripts

TTP tooling for **authorized** labs (HTB, own VMs, contracted pentests).  
Part of [DonMorpheus/ctf-toolkit](https://github.com/DonMorpheus/ctf-toolkit) — sibling to [`htb/`](../htb/).

## Attack chain (recommended order)

```
1. ssh-agent-forward-trap/     → force admin: ssh -A only (port 22)
2. Admin connects              → agent on infected host
3. ssh-infected-admin-pivot/   → pivot to admin PC
4. post_pivot_via_agent.sh     → remote_on_admin_host.sh (loot / beacon template)
```

## Scenarios

| Scenario | Write-up | Directory / script |
|----------|----------|-------------------|
| **`-A` trap** (EN deny message) | [WRITEUP-ssh-agent-forward-trap.md](./WRITEUP-ssh-agent-forward-trap.md) | [ssh-agent-forward-trap/](./ssh-agent-forward-trap/) |
| SSH pivot → admin workstation | [WRITEUP-admin-ssh-infected-machine.md](./WRITEUP-admin-ssh-infected-machine.md) | [ssh-infected-admin-pivot/](./ssh-infected-admin-pivot/) |
| **No `-A`:** `ssh -R` tunnel | [WRITEUP-admin-ssh-remote-forward-no-agent.md](./WRITEUP-admin-ssh-remote-forward-no-agent.md) | `pivot_via_remote_forward.sh` |
| **`nc -e`** reverse from admin | [WRITEUP-admin-nc-infected-reverse.md](./WRITEUP-admin-nc-infected-reverse.md) | local: `~/Desktop/htb/ttp-nc-lab` |

## Defaults

| Variable | Production | Kali isolated lab |
|----------|------------|-------------------|
| `SSH_SERVER_PORT` | **22** | **2221** |
| `ADMIN_IP` | from `ss` peer | e.g. Docker `172.17.0.2` |

## Legal

Use only on systems you own or are explicitly allowed to test.