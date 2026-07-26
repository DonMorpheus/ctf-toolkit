# notes — dzcampaigns (DarkZero Campaigns)

## Status

- **User:** done  
- **System:** done (BO ExtraSID)  
- **Linux root:** done via ksu (no root.txt)  

## Key facts

- External IP (arena): check HTB; internal `172.16.20.{1,2,3}`  
- Dual forest: DARKZERO.EXT ↔ DARKZERO.HTB  
- HTB trustAttributes to EXT: **72**  
- BO membership: InfrastructureAdministrators (empty)  
- ExtraSID **S-1-5-32-551** not filtered the same way as domain SIDs  

## Flags

User / system: **read on box** (`~/user.txt`, DC01 `Desktop\root.txt`). Not published here.

## Attack chain (ordered)

1. Handlebars AST RCE → darkzero  
2. josh Rangers1 → kinit EXT  
3. Gitea negotiate → CI as svc-runner  
4. user flag  
5. OU write → AD root → ksu  
6. celia babygurl13 → dump EXT  
7. golden ExtraSID BO → CIFS DC01 backup intent → system  

## Tools / loot

- `scripts/ast_rce.py`, `forge_bo_extrasid.py`, `smb_bo_get.py`  
- `loot/ntds-ext-full.txt`, `loot/copy-paste.txt`  
- SOCKS chisel `127.0.0.1:1080`  

## Gotchas

- Wrong VPN (machines vs arena)  
- Clock skew breaks Kerberos  
- Gitea password login fails — SPNEGO  
- Impacket getST cross-realm flaky — use MIT kvno on SRV01  
- SRV01 pyOpenSSL/GEN_EMAIL breakage  
