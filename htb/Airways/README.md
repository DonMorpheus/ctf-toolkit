# Airways (HTB, Windows AD / Release Arena)

AIRWAYS domain. Unauth GeoNetwork 4.4.11 XSLT RCE, then ESC13 on `GroupPolicy_Audit` → PKINIT extra SID → `gPLink` write on `OU=IT` → OUned user GPO. The GPO has to process **on DC01** (Isabel RDP), not on the workstation.

- **[WRITEUP.md](WRITEUP.md)** — chain (no flags, no live passwords)
- **[scripts/](scripts/)** — formatter zip, ESC13 enroll, gPLink, OUned example, RDP helper

| | |
|--|--|
| **OS** | Debian GeoNetwork + Windows Server 2022 DC + Win10 workstation |
| **Host** | `geo.airways.htb` / `airways.htb` |
| **Entry** | 80 nginx → GeoNetwork `/geonetwork` |
| **User** | `AIRWAYS\Isabel.O` local admin on `WKSTN01` |
| **Root** | User GPO Immediate Task as SYSTEM **on DC01** after Isabel RDP |

No flags, VPN configs, or live passwords in this tree. Copy `secrets.example.env` → `secrets.env`.

## Attack chain (overview)

```text
Kali tun0
  └─ 80  geo.airways.htb  GeoNetwork 4.4.11
        └─ unauth formatter ZIP  view.xsl  Runtime.exec
              └─ SOCKS into 192.168.100.0/24
                    ├─ GN01   .2   Linux app
                    ├─ WKSTN01 .3  Win10  (OU=Servers)
                    └─ DC01   .1  Server 2022  (OU=Domain Controllers)
                          Isabel.O in OU=IT, RDP Users on the DC
                          ESC13 GroupPolicy_Audit (ECDSA P-256)
                          PKINIT PAC extra SID GPO-Auditors
                          gPLink WRITE on OU=IT → OUned fake LDAP
                          RDP Isabel → DC01  ⇒  SYSTEM Immediate Task on the DC
```

## Scripts

| File | Where | What |
|------|-------|------|
| `scripts/01-geonetwork-rce.py` | Kali | unauth formatter upload + trigger |
| `scripts/formatter/` | Kali | `view.xsl` + `config.properties` |
| `scripts/02-enroll-esc13.ps1` | **WKSTN01** as Isabel | CertEnroll `GroupPolicy_Audit` → PFX |
| `scripts/03-gplink.sh` | Kali | PKINIT TGT + `bloodyad -k` set `gPLink` |
| `scripts/ouned.example.ini` | Kali | Synacktiv OUned `command-type=user`, domain SMB |
| `scripts/04-rdp-dc.sh` | Kali | Isabel RDP to DC01 through SOCKS |
| `scripts/pkinit-ecdsa.patch` | Kali | ECDSA SHA-256 CMS for PKINITtools |
| `scripts/replay.sh` | Kali | hosts + formatter wrapper |

```bash
cp secrets.example.env secrets.env   # TARGET, LHOST, FORMATTER_CMD, …
echo '<TARGET_IP> geo.airways.htb airways.htb' | sudo tee -a /etc/hosts
export TARGET=<ip> LHOST=<tun0>
./scripts/replay.sh rce
```

Needs: `python3`, SOCKS (`chisel`/`proxychains4`), `bloodyad`, patched PKINITtools, OUned. Educational / HTB lab only.
