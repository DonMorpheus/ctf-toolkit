# ctf-toolkit

Lab scripts and small PoCs from **HackTheBox / CTF** practice.  
Maintained by [**Don_Morpheus**](https://github.com/Don_Morpheus).

> Educational use only. Run against systems you are allowed to test (HTB VPN, own VMs).  
> No flags, VPN configs, or live credentials in this repo.

## What's inside

| Path | Description |
|------|-------------|
| [`htb/paperwork/`](htb/paperwork/) | **Paperwork** (Easy) — LPD client, PJL helpers, `mgmt.sock` leak |
| [`profile/`](profile/) | Template for GitHub profile README (`Don_Morpheus/Don_Morpheus`) |

## Quick start

```bash
git clone https://github.com/Don_Morpheus/ctf-toolkit.git
cd ctf-toolkit/htb/paperwork
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
│   └── paperwork/     # one machine per folder as you add more
└── profile/           # optional GitHub landing page
```

More machines → add `htb/<machine-name>/` the same way.

## License

[MIT](LICENSE)