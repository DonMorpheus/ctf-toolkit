# DutyBound (HTB, Linux / Release Arena)

AirSnacks self-checkout kiosk. IATA **BCBP** boarding-pass parse → SQLi → PostgreSQL **COPY TO PROGRAM**, then Openbox X11 keystrokes into the kiosk session, then a **systemd.path** eval on a group-writable CSV.

- **[WRITEUP.md](WRITEUP.md)** — chain (no flags, no live passwords)
- **[scripts/](scripts/)** — BCBP builder, COPY RCE, XTEST inject, CSV root, autopwn

| | |
|--|--|
| **OS** | Ubuntu, OpenSSH 8.9p1, nginx 1.18 |
| **Host** | `airsnacks.htb` |
| **Entry** | HTTPS POS; POST `/checkout/boarding-pass/verify` `{raw: BCBP}` |
| **User** | `airline_use` SQLi → `postgres` → X11 `:0` `C-A-t` → `dutyfree-kiosk` |
| **Root** | `pos-ops` write `/opt/vrs/data/duty-rates.csv` → `vrs-duty-apply.path` → `eval` |

No flags, VPN configs, or live passwords in this tree.

## Attack chain (overview)

```text
Kali tun0
  └─ 443 nginx  airsnacks.htb
        └─ BCBP airline_use  SQLi stacked
              └─ COPY TO PROGRAM   uid postgres
                    └─ XTEST  Openbox C-A-t  xterm
                          └─ dutyfree-kiosk (pos-ops)
                                └─ PathModified CSV
                                      └─ apply-duty-rates.sh eval  uid 0
```

## Scripts

| File | Where | What |
|------|-------|------|
| `scripts/bcbp.py` | Kali | one-leg BCBP + `COPY TO PROGRAM` wrapper |
| `scripts/01-hosts.sh` | Kali | hosts line |
| `scripts/02-postgres-rce.py` | Kali | cart + verify |
| `scripts/03-xinject.py` | target | python-xlib `C-A-t` |
| `scripts/04-csv-root.sh` | target | writable rates file |
| `scripts/autopwn.py` | Kali | HTTP stager + full chain |
| `scripts/replay.sh` | Kali | wrapper |

```bash
echo '<TARGET_IP> airsnacks.htb' | sudo tee -a /etc/hosts
export TARGET=<TARGET_IP> LHOST=<tun0>
# terminal A: nc -lvnp 6666
# terminal B: nc -lvnp 7777
./scripts/replay.sh autopwn
```

Needs: `python3` on Kali; on the box, `python3-xlib` is already installed. Educational / HTB lab only.
