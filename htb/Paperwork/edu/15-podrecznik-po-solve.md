# Paperwork — podręcznik po solve (pełny łańcuch)

Ten plik jest **po zdobyciu flag** — łączy wątki z `01`–`14` w jedną historię do nauki.

## Mapa ataku (mentalny model)

```text
[Kali]
   │  :80 / :1515 (VPN)
   ▼
[nginx :80] ──proxy──► [CorpoSite Flask :1337]  ← intranet, ZIP z LPD (stary kod)
   │
   └──► LPD :1515 ──► user lp ──► RCE (job_name + shell=True)

[lp @ box]
   └── nc/curl localhost nie wystarczy do user flag
       └── trzeba UID archivist (9100 PJL lub SSH)

[archivist @ box]
   ├── :9100 jetdirect (PJL, log → commands.log)
   ├── mgmt.sock (grupa archivist)
   └── su root (hasło z admin_pins po lockdown)
           └── root.txt
```

## Etap A — Recon (co warto zapamiętać)

1. **Nginx 1.28** na `:80` — nie szukaj PHP; aplikacja to **Flask za proxy** (`Server: Werkzeug` po wejściu na vhost).
2. **`/download/archive`** — ZIP; porównaj rozmiar `server.py` w ZIP (~2820 B) z plikiem na serwerze (~2940 B) → ZIP **≠** produkcja (patrz `11-easy-bez-modulu.md`).
3. **`:1515`** — banner LPD; to **własny Python**, nie moduł Metasploit `lpd`.

**Ćwiczenie (Kali):** pobierz ZIP i diff z lokalną kopią w `loot/archive-src/server.py`:
```bash
curl -sS -o /tmp/pw.zip --resolve paperwork.htb:80:TARGET_IP http://paperwork.htb/download/archive
unzip -p /tmp/pw.zip server.py | wc -c
```

## Etap B — Foothold LPD

Produkcyjny `server.py` (na boxie) po akceptacji kolejki:

- subcommand `2` → czyta plik kontrolny RFC-1179-style;
- wyciąga linię `J<nazwa>` jako **job_name**;
- `subprocess.Popen(f"echo 'Archive: {job_name}' >> /tmp/archive.log", shell=True)`.

Injekcja: zamknij cudzysłów w `job_name` i doklej polecenie.

**Wzorzec z `scripts/lpd_exploit.py`:**
```text
job_name = x'; <TWOJE_Polecenie>; #
```

**Ćwiczenie:** przeczytaj RFC 1179 sekcję o „control file” (linie H, P, J) — `man lpd` / dokumentacja CUPS pomoże z kontekstem historycznym.

## Etap C — Pivot lp → archivist

### C1. Dlaczego nie `lp` do user flag?

- `user.txt` jest w `/home/archivist` (700 dla obcych).
- `_laurel` to konto audytu, nie login.
- `mgmt.sock` wymaga grupy **archivist**.

### C2. Jetdirect `:9100` (tylko localhost)

- Proces: **UID archivist**, root filesystemu PJL = `/home/archivist/printer/`.
- Komendy logowane do **`logs/commands.log`** — to „czarne skrzynka” dla `paperwork-daemon`.

### C3. Pułapka nazw PJL (must-know)

W **tym** kodzie (nie wszędzie w życiu — tu custom):

| Komenda PJL | Znaczenie w `jetdirect.py` |
|-------------|----------------------------|
| `FSUPLOAD` | **Odczyt** pliku (serwer wysyła body) |
| `FSDOWNLOAD` | **Zapis** (klient wysyła body po linii NAME+SIZE) |
| `FSQUERY` / `FSDIRLIST` | listdir |
| `FSEXEC` | stub → `OK`, **brak exec** |

**Zapis klucza SSH** — jedna linia nagłówka, potem raw body:
```text
@PJL FSDOWNLOAD NAME="../.ssh/authorized_keys" SIZE=<N>\r\n
<bytes klucza>
```

Ścieżki: `Filesystem._translate()` + `../` → escape z katalogu drukarki do `~archivist/.ssh/`. Szczegóły: `12-pjl-path-escape.md`.

**Ćwiczenie:** na własnym VM napisz 20-liniowy socket client PJL (Python) — wyślij `FSQUERY NAME="."` i parsuj odpowiedź.

## Etap D — Root (archivist)

### D1. `paperwork-daemon` (user root)

- Trzyma fd do **`/etc/paperwork/admin_pins.conf`** (hasło w formacie `ADMIN_PASSWORD=...`).
- Skanuje `commands.log` pod kątem substringów: `FSQUERY`, `FSUPLOAD`, `FSDOWNLOAD`.
- **Bez triggera:** klient dostaje `SYSTEM_CLEAN` + `SIGNATURE` (SHA-256).
- **Po triggerze:** `ALERT...` + **SCM_RIGHTS** (fd logu + fd configu).

### D2. Co robisz w shellu

1. Jedno PJL z triggerem (np. `FSQUERY`).
2. `connect("/run/paperwork/mgmt.sock")` + `recvmsg()` — odbierz ancillary data.
3. `os.read(fd)` na przekazanych deskryptorach — znajdź `ADMIN_PASSWORD`.
4. `su root` — hasło z pliku działa w **PAM** (to nie „logowanie do Flask”).

### D3. Czego **nie** trzeba było robić

- Fuzz setek ścieżek na `:1337` (brak panelu admina do privesc).
- CVE na nginx / OpenSSH.
- Odczyt `/root/root.txt` przez PJL `../../../root/...` (crash / poza sandboxem).

Więcej technicznie o fd passing: **`16-unix-socket-scm-rights.md`**.

## Checklist pod przyszły podobny box

- [ ] Custom usługa na nietypowym porcie → **pobierz kod** (ZIP, git, backup, `/proc`).
- [ ] `shell=True` / `eval` / format string w logach → **injection**.
- [ ] Usługa lokalna tylko na `127.0.0.1` → **foothold**, potem **SSH/rev z boxa**.
- [ ] Socket `root:grupa` → **czy Twój user jest w grupie** po pivotcie?
- [ ] Logi + daemon reagujący na słowa kluczowe → **trigger + side channel** (tu: SCM_RIGHTS).
- [ ] Sekret w pliku 600 → nie LFI; szukaj **przekazania fd** lub **innego czytelnika**.

## Słowniczek

| Termin | Na Paperwork |
|--------|----------------|
| **Legacy gateway** | LPD `:1515` (tekst z intranetu) |
| **Identifier** | Lore / biznesowy tekst; prawdziwy „identyfikator” roota to zawartość `admin_pins.conf` |
| **Lockdown** | Trigger w logu → daemon zamyka incydent i wysyła dowody przez socket |
| **SIGNATURE** | `sha256("SYSTEM_CLEAN:" + admin_secret)` — weryfikacja stanu, nie sesja WWW |

## Pliki w workspace do powtórki

| Plik | Rola |
|------|------|
| `scripts/lpd_exploit.py` | foothold |
| `scripts/write_ssh_correct.py` | FSDOWNLOAD + klucz |
| `scripts/mgmt_leak_admin.py` | leak po triggerze |
| `loot/privesc-enum-archivist.txt` | enum z SSH |
| `loot/copy-paste.txt` | flagi (nie wklejaj na Discordzie publicznie) |