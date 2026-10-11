# Stream (HTB, Linux / Release Arena)

AIDX ingest on FastAPI, Spring terminal-edge gateway, ClickHouse behind nginx. Dual-use XML: **in-band XXE** for user, **malformed body → DLQ** for root.

- **[WRITEUP.md](WRITEUP.md)** — chain (no flags, no live passwords)
- **[scripts/](scripts/)** — heap extract, ingest, XXE+CH, su brute, `/proc` sniffer, FILE append

| | |
|--|--|
| **OS** | Ubuntu, OpenSSH 9.6p1 |
| **Hosts** | `htb-airport.htb`, `api.htb-airport.htb`, `db.htb-airport.htb` |
| **Entry** | unauthenticated Spring `/actuator/heapdump` + `:8081/feeds/aidx` |
| **User** | heap → ClickHouse `svc_events` → XXE `file://` in `airline` → Kafka SASL = SSH `svc-infra` → `su` |
| **Root** | systemd DLQ timer as root + argv sniff of `clickhouse-client --password` + `GRANT FILE` on the formatter |

No flags, VPN configs, or live passwords in this tree.

## Scripts

| File | Where | What |
|------|-------|------|
| `scripts/heap_extract.py` | Kali | neighbourhood around Hikari setters in the heapdump |
| `scripts/aidx_ingest.py` | Kali | POST AIDX (plain / XXE / malformed→DLQ) |
| `scripts/ch_http.py` | Kali | ClickHouse HTTP Basic |
| `scripts/xxe_read.py` | Kali | ingest XXE + SELECT `flightleg_json.airline` |
| `scripts/su_brute.py` | target | local `su` against a wordlist (fail2ban on :22) |
| `scripts/proc_sniff.py` | target | busy-loop `/proc/<pid>/cmdline` |
| `scripts/ch_file_append.py` | Kali | `INSERT INTO FUNCTION file(...)` append |
| `scripts/replay.sh` | Kali | thin wrapper over the above |

```bash
echo '<TARGET_IP> htb-airport.htb api.htb-airport.htb db.htb-airport.htb' | sudo tee -a /etc/hosts
export TARGET=<TARGET_IP>
./scripts/replay.sh heap
export CH_PASS=...          # setPassword next to setUsername svc_events
./scripts/replay.sh xxe /opt/kafka_2.13-4.3.1/config/server.properties
```
