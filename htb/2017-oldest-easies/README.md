# 2017 oldest easies — lab session 2026-09-28

Retired HTB machines, oldest-on-site order, one sitting. Full notes: [`WRITEUP.md`](WRITEUP.md).

No flags or live passwords in git.

| Box | OS | Intended vector |
|-----|-----|-----------------|
| [Precious](../Precious/) | Linux | pdfkit URL injection → sudo YAML |
| [Legacy](../Legacy/) | Win XP | MS08-067 |
| [Devel](../Devel/) | Win7 IIS | FTP write → ASPX → KiTrap0D |
| [Beep](../Beep/) | Linux PBX | Elastix LFI → password reuse |
| [Arctic](../Arctic/) | Win 2008 R2 | ColdFusion 8 upload → local kernel/Potato |
| [Grandpa](../Grandpa/) | Win 2003 IIS6 | WebDAV ScStoragePathFromUrl → ms14_070 |
| [Granny](../Granny/) | Win 2003 IIS6 | WebDAV PUT/MOVE → local LPE |
| [Bank](../Bank/) | Linux | vhost + failed-encrypt dump + `.htb` PHP |
| [Blocky](../Blocky/) | Linux | JAR decompile → SSH reuse → sudo |
| [Mirai](../Mirai/) | Linux / Pi | Pi-hole → default SSH → USB carve |
| [Shocker](../Shocker/) | Linux | Shellshock CGI → sudo perl |
| [Bashed](../Bashed/) | Linux | exposed phpbash → sudo user → root cron |
