# Autopilot (HTB Season 12 / Release Arena)

Linux **grommunio** mail appliance on the edge, Active Directory behind it. User on the mail host, domain root on DC01.

- **[WRITEUP.md](WRITEUP.md)** — chain (no flags, no live passwords)
- **[scripts/](scripts/)** — WebDAV foothold, postfix LPE, reverse SMB proxy, DNS spoof, ntlmrelayx, DA C$

| | |
|--|--|
| **OS** | openSUSE (grommunio) + Windows Server 2025 DC |
| **Hosts** | `grommunio.autopilot.htb` / `mail.autopilot.htb` / `autopilot.htb` |
| **Entry** | 443 only; WebDAV PUT into Nextcloud data (executable PHP) |
| **User** | Admin API `daemon_directory` → fake `postfix-script` as root |
| **Root / DA** | reverse SOCKS/SMB proxy + DnsAdmins A-record spoof + ntlmrelayx **or** reverse TCP SMB bridge + DA `C$` |

No flags, VPN configs, or live passwords in this tree. Copy `secrets.example.env` → `secrets.env`.

## Lab setup

```bash
cp secrets.example.env secrets.env   # fill BOX_IP + recovered secrets
echo '<TARGET_IP> grommunio.autopilot.htb autodiscover.autopilot.htb mail.autopilot.htb files.autopilot.htb autopilot.htb' | sudo tee -a /etc/hosts
# clock: sudo date -u -s "$(curl -skI https://grommunio.autopilot.htb | awk -F': ' 'tolower($1)=="date"{print $2}')"
```

External surface: **443** (nginx). Internal: DC `172.16.20.1` signing **on**, workstation `172.16.20.15` signing **off**.

## Attack chain (overview)

```text
VPN 443
  └─ grommunio Files WebDAV PUT  →  grofiles PHP
        └─ Admin API dbconf  daemon_directory = WEBDIR
              └─ postfix.service restart  →  uid 0
                    ├─ chisel reverse proxy (SOCKS, :445, WS02:445)
                    ├─ firewalld allow 445
                    ├─ DnsAdmins replace ws01 A  →  ntlmrelayx
                    └─ reverse SMB bridge  →  DA  →  DC01 C$
```

## Scripts

| File | What |
|------|------|
| `scripts/01-hosts.sh` | hosts line + TLS Date |
| `scripts/02-foothold.sh` | WebDAV PHP |
| `scripts/03-root-postfix.sh` | `daemon_directory` LPE |
| `scripts/04-chisel.sh` | reverse proxy |
| `scripts/05-fw-445.sh` | firewalld 445/139 |
| `scripts/06-dns-hijack.py` | DnsAdmins `dnsRecord` (LE, TTL BE) |
| `scripts/07-ntlmrelayx.sh` | `--smb-port 9445` → unsigned host |
| `scripts/08-pth-root.sh` | PTH Administrator via SSH `-L` |
| `scripts/09-dcpivot.py` | reverse SMB + DA `C$` |
| `scripts/replay.sh` | step wrapper |

```bash
cd htb/Autopilot/scripts
./replay.sh hosts
./replay.sh foothold
./replay.sh lpe
./replay.sh chisel
./replay.sh dcpivot      # close: DA over reverse SMB
# optional relay path:
./replay.sh fw
./replay.sh dns
./replay.sh relay        # leave running
```

Needs: `chisel`, Impacket `ntlmrelayx.py`, `ldap3`, `requests`, HTB VPN (`tun0`). Educational / HTB lab only.
