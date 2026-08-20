# Ghostlink — HackTheBox

Hard Windows AD. Attack path: **anonymous MQTT → NTLM coerce → HTTP relay → double-encoded path traversal → KeePass → Gogs CVE-2025-8110 → crack Gogs PBKDF2 → ESC11 DA**.

| | |
|--|--|
| **OS** | Windows Server DC (`dc01`) + internal IIS ARR to file-share and Gogs |
| **Domain** | `ghostlink.htb` |
| **Entry** | MQTT `:1883` anonymous healthcheck JSON |
| **Foothold** | Authenticated Gogs RCE as `git` (CVE-2025-8110) |
| **User** | Linux `nvirelli` (password reuse from Gogs SQLite) |
| **DA** | ADCS **ESC11** (ICPR relay) → `DC01$` cert → Administrator |

Full write-up: [`WRITEUP.md`](WRITEUP.md)  
Scripts: [`scripts/`](scripts/)

No flags, VPN configs, or live session secrets in this tree.

---

## Lab setup

```bash
echo '<TARGET_IP> ghostlink.htb dc01.ghostlink.htb gpz-op26-secure.ghostlink.htb gpz-op26-toolkits.ghostlink.htb' | sudo tee -a /etc/hosts
```

Your HTB VPN address (`tun0`) is the listener IP for MQTT coerce, reverse shells, and Chisel.

Typical surface: **53, 80, 88, 135, 139, 389, 445, 464, 593, 636, 1883, 3268, 3269, 5985, 9389**.  
SMB signing is **required** on the DC. Clock skew is often **~8 hours** (Kerberos).

---

## Attack chain (overview)

```text
┌──────────────────────┐  anonymous subscribe/publish
│ MQTT :1883           │ ── healthcheck.url ──► HTTP GET as svc_canary
└──────────┬───────────┘
           │ NTLM relay (not crack) to gpz-op26-secure
           ▼
┌──────────────────────┐  IIS kernel auth → ghostsurf -k + SOCKS
│ Secure file share    │ ── /api/download double-URL-encode ──► NTUSER.DAT
└──────────┬───────────┘
           │ RecentDocs db.zip → KeePass (keyfile, empty master pw)
           ▼
┌──────────────────────┐  Gogs 0.13.3
│ gpz-op26-toolkits    │ ── CVE-2025-8110 symlink .git/config ──► git shell
└──────────┬───────────┘
           │ steal /opt/gogs/data/gogs.db  (other port than revsh)
           ▼
┌──────────────────────┐  hashcat 10900 + rockyou trimmed ^.{20,}$
│ nvirelli             │ ── su -c via stdin pipe (no TTY)
└──────────┬───────────┘
           │ Chisel reverse SOCKS → 172.16.20.10
           ▼
┌──────────────────────┐
│ ESC11 ICPR relay     │  coerce DC$ → CA RPC → DomainController PFX → DA
└──────────────────────┘
```

---

## Scripts

| Script | Purpose |
|--------|---------|
| [`scripts/mqtt_set_healthcheck.sh`](scripts/mqtt_set_healthcheck.sh) | Retained MQTT publish: point `secureshare` healthcheck at your HTTP listener |
| [`scripts/encode_traversal.py`](scripts/encode_traversal.py) | Double URL-encode a Windows path for `/api/download/` |
| [`scripts/gogs_cve_2025_8110_gitconfig.py`](scripts/gogs_cve_2025_8110_gitconfig.py) | CVE-2025-8110: relative `.git/config` symlink + `sshCommand` reverse shell |
| [`scripts/gogs_hash_to_hashcat.py`](scripts/gogs_hash_to_hashcat.py) | Gogs salt+hex → hashcat mode 10900 |
| [`scripts/proxychains-pivot.conf`](scripts/proxychains-pivot.conf) | SOCKS5 `127.0.0.1:1081` for Chisel reverse socks |
| [`scripts/README.md`](scripts/README.md) | Flags, listeners, gotchas |

Replace placeholders (`<TARGET_IP>`, `<TUN0_IP>`, credentials from *your* loot). Educational / HTB lab only.
