# Nauka — enigma.htb

Materiały po solve; bez spoilerów innych maszyn. Ćwiczenia zakładają Kali + lab HTB.

| # | Plik | Temat |
|---|------|-------|
| 1 | [01-nfs-onboarding-leak.md](01-nfs-onboarding-leak.md) | NFS export, mount, dane w plikach |
| 2 | [02-mail-imap-vhost-chain.md](02-mail-imap-vhost-chain.md) | Roundcube, IMAP, pivot po skrzynkach |
| 3 | [03-openstamanager-backup-restore-rce.md](03-openstamanager-backup-restore-rce.md) | OpenSTA 2.9.x, restore ZIP → RCE |
| 4 | [04-mysql-bcrypt-lateral.md](04-mysql-bcrypt-lateral.md) | config.inc.php, `zz_users`, john |
| 5 | [05-olivetin-privesc.md](05-olivetin-privesc.md) | OliveTin localhost, protobuf API, injekcja |
| 6 | [06-cwiczenia-kali.md](06-cwiczenia-kali.md) | zadania do samodzielnego powtórzenia |
| — | [READING-apt-level.md](READING-apt-level.md) | lektura ogólna (chain, nie ten box) |

Kolejność: 1 → 2 → 3 → (foothold) → 4 → user → 5 → root.