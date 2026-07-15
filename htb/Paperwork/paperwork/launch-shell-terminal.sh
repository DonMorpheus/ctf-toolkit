#!/usr/bin/env bash
# Otwórz NOWE okno terminala z interaktywnym listenerem (wymaga GUI / DISPLAY).
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
CMD="bash -lc 'cd ${DIR} && ./open-interactive-shell.sh; exec bash'"

export DISPLAY="${DISPLAY:-:0}"

if command -v qterminal >/dev/null; then
  qterminal -e bash -lc "cd ${DIR} && ./open-interactive-shell.sh; exec bash" &
elif command -v xfce4-terminal >/dev/null; then
  xfce4-terminal --title="HTB Paperwork — shell lp" -e "$CMD" &
elif command -v gnome-terminal >/dev/null; then
  gnome-terminal --title="HTB Paperwork — shell lp" -- bash -lc "cd ${DIR} && ./open-interactive-shell.sh; exec bash" &
elif command -v konsole >/dev/null; then
  konsole -p tabtitle="Paperwork shell" -e bash -lc "cd ${DIR} && ./open-interactive-shell.sh; exec bash" &
elif command -v xterm >/dev/null; then
  xterm -title "Paperwork shell" -e bash -lc "cd ${DIR} && ./open-interactive-shell.sh; exec bash" &
else
  echo "Brak emulatora terminala (xfce4-terminal / gnome-terminal / xterm)."
  echo "Uruchom ręcznie w dowolnym terminalu:"
  echo "  ${DIR}/open-interactive-shell.sh"
  exit 1
fi
echo "[+] Nowe okno terminala powinno się otworzyć."