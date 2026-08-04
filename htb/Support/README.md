# Support — HackTheBox

Linux Easy (Windows AD / Domain Controller). Attack path: **guest SMB tools → LDAP service password → user password in AD attribute → WinRM → RBCD → Domain Admin**.

| | |
|--|--|
| **OS** | Windows Server 2022 (Domain Controller) |
| **Domain** | `support.htb` / host `DC` |
| **Entry** | Guest SMB share `support-tools` |
| **Foothold** | `UserInfo.exe` encrypted LDAP creds → `support` password in AD `info` |
| **User** | WinRM as `support` |
| **Root / DA** | `SeMachineAccountPrivilege` + **FullControl** on `DC$` → **RBCD** |

Full write-up: [`WRITEUP.md`](WRITEUP.md)  
Scripts: [`scripts/`](scripts/)

No flags / VPN configs / live session tickets in this tree.

---

## Lab setup

```bash
echo '<TARGET_IP> support.htb dc.support.htb' | sudo tee -a /etc/hosts
# optional: use DC as DNS for Kerberos SPNs
```

External surface (typical): **53, 88, 135, 139, 389, 445, 464, 593, 636, 3268, 3269, 5985, 9389** (+ dynamic RPC).

---

## Attack chain (overview)

```text
┌─────────────────────┐  guest (empty)
│ SMB support-tools   │ ──────────────────────► UserInfo.exe.zip
└──────────┬──────────┘
           │ decrypt LDAP bind password (XOR)
           ▼
┌─────────────────────┐  support\ldap
│ LDAP authenticated  │ ──────────────────────► user "support" info=
└──────────┬──────────┘
           │ password reuse
           ▼
┌─────────────────────┐
│ WinRM support       │  user context on DC
└──────────┬──────────┘
           │ SeMachineAccountPrivilege + FullControl on DC$
           ▼
┌─────────────────────┐
│ RBCD (FAKE$ → DC$)  │  S4U → Administrator → secrets / C$
└─────────────────────┘
```

---

## Scripts

| Script | Purpose |
|--------|---------|
| [`scripts/userinfo_decrypt.py`](scripts/userinfo_decrypt.py) | Decode the embedded LDAP password from `UserInfo` style cipher |
| [`scripts/rbcd_to_da.sh`](scripts/rbcd_to_da.sh) | Add computer, set RBCD on `DC$`, request ST, optional secretsdump |

Replace placeholders. Educational / HTB lab only.
