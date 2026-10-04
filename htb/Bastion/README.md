# Bastion — HackTheBox

Easy Windows (Server 2016). Attack path: **guest SMB VHD → SAM/L4mpje → C2 as user → mRemoteNG GCM → WinRM/WMI hop to Administrator (no SSH from the operator box)**.

| | |
|--|--|
| **OS** | Windows Server 2016 Standard (10.0.14393) |
| **Host** | `bastion.htb` / WORKGROUP `BASTION` |
| **Entry** | SMB null `Backups` (VHD) |
| **Foothold** | SAM → `L4mpje`; C2 implant as that user (Medium IL) |
| **User** | Desktop as `L4mpje` |
| **Admin** | mRemoteNG AES-GCM (`mR3m`) → CIM `Win32_Process.Create` as Administrator |

Full write-up: [`WRITEUP.md`](WRITEUP.md)  
Script: [`scripts/mremoteng_gcm.py`](scripts/mremoteng_gcm.py)

No flags / VPN configs / live passwords in this tree.

---

## Lab setup

```bash
echo '<TARGET_IP> bastion.htb' | sudo tee -a /etc/hosts
```

External surface (typical): **22** OpenSSH for Windows, **135/139/445** SMB, **5985** WinRM.

---

## Attack chain (operator view)

```text
┌──────────────────────┐  null session, SMB 2.1
│ Share Backups / VHD  │ ──► 7z SAM+SYSTEM (no full 5GB pull)
└──────────┬───────────┘
           │ secretsdump → L4mpje hash → rockyou
           ▼
┌──────────────────────┐  Medium IL, Users only
│ C2 as L4mpje         │ ──► whoami BOF: no Administrators
└──────────┬───────────┘
           │ AppData mRemoteNG confCons.xml AES-GCM
           ▼
┌──────────────────────┐  master mR3m, AAD=salt
│ Administrator pass   │
└──────────┬───────────┘
           │ New-CimSession 127.0.0.1 + Win32_Process.Create
           ▼
┌──────────────────────┐  parent = WMI, not sshd
│ C2 as Administrator  │  Medium/filtered on WinRM logon
└──────────────────────┘
```

`token make` + implant `proc create` is **LOGON_NETCREDENTIALS_ONLY** (local identity stays L4mpje). Do not confuse impersonation with a new High process.
