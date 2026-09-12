# Garfield — HackTheBox

Windows / Active Directory. Attack path: **low-priv LDAP write → logon script → ADM reset (ADSI) → Ligolo to RODC → RBCD → RODC krbtgt → Golden Ticket on the writable DC**.

| | |
|--|--|
| **OS** | Windows Server 2019 (DC01 + RODC01) |
| **Domain** | `garfield.htb` |
| **Entry** | Domain user (SMB/LDAP; no WinRM) |
| **User** | `scriptPath` + SYSVOL `scripts\` as Liz |
| **Root / DA** | RBCD on `RODC01$` → `krbtgt_<RODC>` → RODC Golden Ticket → DC01 |

Full write-up: [`WRITEUP.md`](WRITEUP.md)

No flags, hashes, VPN configs, or live tickets in this tree.

---

## Lab setup

```bash
echo '<TARGET_IP>  garfield.htb DC01.garfield.htb' | sudo tee -a /etc/hosts
# Prefer FQDN. Short name DC01 collides with other labs and breaks Kerberos.
```

DC01 (HTB IP): 53, 88, 135, 139, 389, 445, 464, 636, 3268/3269, 3389, 5985, 9389.  
RODC01 is on an **internal Hyper-V switch** (`192.168.100.0/24`) — pivot from DC01.

---

## Attack chain (overview)

```text
j.arbuckle (LDAP write on Liz)
        │ scriptPath + SYSVOL scripts\
        ▼
l.wilson  (logon script / revshell)
        │ LDAP ADSI SetPassword (not WinNT)
        ▼
l.wilson_adm  WinRM on DC01
        │ Ligolo → 192.168.100.2 (RODC01)
        │ MAQ + RBCD on RODC01$
        ▼
Administrator @ CIFS/RODC01  (S4U)
        │ LSA inject krbtgt_<RODC>
        │ RODC Administrators → PRP
        ▼
RODC Golden Ticket (kvno = id << 16) → DC01 DA
```
