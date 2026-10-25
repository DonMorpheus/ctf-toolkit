# DutyBound scripts

Fill `../secrets.example.env` → `../secrets.env` locally. `airsnacks.htb` in `/etc/hosts`.

```bash
export TARGET=<ip> LHOST=<tun0>
chmod +x *.sh *.py
./replay.sh hosts
# terminal A:  nc -lvnp 6666
# terminal B:  nc -lvnp 7777
./replay.sh autopwn
```

| File | Where | What |
|------|-------|------|
| `bcbp.py` | Kali | IATA M-format + `airline_use` SQLi helper |
| `01-hosts.sh` | Kali | hosts line |
| `02-postgres-rce.py` | Kali | cart + `COPY TO PROGRAM` |
| `03-xinject.py` | **target** (postgres) | Openbox `C-A-t` → type `--cmd` |
| `04-csv-root.sh` | **target** (kiosk) | writable CSV → `eval` as root |
| `autopwn.py` | Kali | HTTP stager + BCBP RCE + X11 + CSV |
| `replay.sh` | Kali | wrapper |
