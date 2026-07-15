# SSH trap: only `ssh -A` — then his workstation is gone

## Idea

On a **compromised server** you control `sshd` so that user `legacy` (port `2221` in lab):

- **Rejects** logins **without** forwarded agent (`SSH_AUTH_SOCK` missing).
- Prints an **English** policy message telling admin to use **`ssh -A`**.
- Sets **`AllowTcpForwarding no`** — no **`-R` / `-L`** bypass without `-A` pivot path.

Admin complies → **agent always on your host** → run `pivot_to_admin_pc.sh`.

## Deny message (client sees)

```text
ACCESS DENIED: ForwardAgent required (ssh -A). All other methods are disabled.
Example: ssh -A -i <key> legacy@host -p 2221
```

## Install (repo)

```bash
sudo ./ssh-agent-forward-trap/install_trap.sh
# merge ssh-agent-forward-trap/sshd_match_legacy.snippet → sshd_config → restart sshd
```

Kali lab (all-in-one):

```bash
echo 'wasd' | su -c 'bash ~/Desktop/htb/ttp-docker-ssh-lab/setup_kali_user.sh'
```

## Test

```bash
ssh -a -i key -p 2221 legacy@host    # ACCESS DENIED
ssh -A -i key -p 2221 legacy@host    # session OK (with local ssh-agent + key)
```

Admin Docker: `entry_agent_trap.sh` — `ssh-agent`, `ssh-add`, `ssh -A`.

## MITRE

| ID | Note |
|----|------|
| T1552.006 | Agent forwarding abuse after forced `-A` |
| T1021.004 | SSH to admin workstation |
| T1078 | Valid accounts |

## Defense

- Never require `ForwardAgent` on untrusted jumps.
- `AllowAgentForwarding no` on servers admins should not use for signing.
- Detect long-lived sessions + agent sockets under `/home/*/.ssh/agent/`.

## Related

- [WRITEUP-admin-ssh-infected-machine.md](./WRITEUP-admin-ssh-infected-machine.md)
- [ssh-infected-admin-pivot/](./ssh-infected-admin-pivot/)