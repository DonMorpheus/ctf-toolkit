# Curling — HackTheBox

Easy Linux (Ubuntu, Joomla Protostar). Attack path: **secret in webroot → Joomla template RCE → C2 as www-data → elevate to floris → cron `curl -K` as root → C2 as root**.

| | |
|--|--|
| **OS** | Ubuntu / Apache 2.4.29, Joomla Protostar |
| **Host** | `curling.htb` |
| **Entry** | `/secret.txt` + CMS user from a post |
| **Foothold** | `/administrator/` → template `index.php` `system($_REQUEST[…])` |
| **User** | `password_backup` nested archive → SSH/C2 as `floris` |
| **Root** | writable `curl -K` input in cron |

Full write-up: [`WRITEUP.md`](WRITEUP.md)

No flags / VPN configs / live passwords in this tree.

---

## Attack chain (operator view)

```text
┌─────────────────────┐
│ Joomla template RCE │ ──► C2 as www-data
└──────────┬──────────┘
           │ elevate -u floris -p  (pty su / sudo -S)
           ▼
┌─────────────────────┐
│ C2 as floris        │ ──► cron curl -K (RW input)
└──────────┬──────────┘
           │ url + output=/etc/crontab → SUID bash / implant
           ▼
┌─────────────────────┐
│ C2 as root          │  new PID, not the same www-data row
└─────────────────────┘
```

`elevate spawn` on this kernel copies the ELF but **does not** turn the existing PID into uid 0. Root is a **new callback**.
