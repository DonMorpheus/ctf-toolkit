# ACCESS — danglingtree

## Co działa

| Metoda | Tak/Nie | Jak |
|--------|---------|-----|
| SSH | Nie | — |
| WinRM (5985) | Nie (z zewnątrz) | filtered |
| WAC HTTPS :6600 | **Tak** | `anderson.w` / `R3dT3am@Acc3ss#01` → `scripts/wac_ps.py` |
| RDP :3389 | Tak (dla grup) | noah / DevOps_PKI (jake) — `scripts/rdp-noah.sh` |
| SMB | Tak | domain users; C$ z hashem admina |
| Shell jako noah | **Tak** | `scripts/noah_exec.py` (LogonUser pod WAC) |
| DA / SYSTEM | **Tak** | ESC1 cert → Administrator NT hash |

## Credy (przetestowane)

| Sekret | Do czego | Nie mylić z |
|--------|----------|-------------|
| anderson.w / R3dT3am@Acc3ss#01 | WAC, SMB, LDAP | — |
| noah.b / RiverDragon#Storm25 | user flag, DPAPI source | — |
| svc_mail AD / OceanWave#9Sky! | AD svc_mail | hasło SM po force-reset |
| alex.o / SunsetMountainPeak@2025 | FCP na jake | Target PC01 w Cred |
| jake.h / Zz9!Qk7#Mm2$Xx4@Ww5%Ll2026Dan | ADCS ESC1/ESC4/ESC7 | stare HelpdeskCert#… |
| Administrator NT …:8cacb3a97e… | root.txt, C$ | — |

## Replay foothold

```bash
python3 scripts/wac_ps.py -c 'whoami; hostname'
python3 scripts/noah_exec.py 'type $env:USERPROFILE\Desktop\user.txt'
./scripts/sync_time_to_dc.sh
python3 scripts/esc1_get_admin.py
python3 scripts/get_flags.py
```
