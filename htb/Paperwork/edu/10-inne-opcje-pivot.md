# Paperwork — inne opcje pivotu `lp` → `archivist`

## Co **nie** jest osobnym wejściem na user flagę

| Pomysł | Dlaczego nie |
|--------|----------------|
| **`_laurel` / audit** | Konto systemowe (`/bin/false`), flaga w **`archivist`** |
| **`cat /home/archivist/user.txt` jako `lp`** | Uprawnienia katalogu — musisz **być** archivist |
| **`mgmt.sock` z `lp`** | `srw-rw---- root:archivist` — Permission denied |
| **`/etc/paperwork/admin_pins.conf` bezpośrednio** | `600 root` |
| **`/proc/*/fd` daemona / jetdirect** | `fd` zamknięte dla `lp` |
| **SUID** (`su`, `mount`, …) | Brak binarki „run as archivist” |
| **Panel WWW na :80** | Intranet statyczny, brak logowania na apex |
| **Tylko LPD** | Zawsze user **`lp`**, nie zmienia UID |

---

## Ścieżki **realne** (box Easy)

### A) **Jetdirect `127.0.0.1:9100`** (główna, tu utknęliśmy na formacie)

**Działające PJL (potwierdzone):**
- `@PJL FSMKDIR`, `FSDELETE`, `FSCHMOD` → `OK`
- `@PJL FSQUERY` → listing katalogów
- `@PJL INFO ID` → banner

**Zapis klucza SSH (cel):** jedna z poniższych — **nazwy na tym boxie są mylące**:
- **`FSUPLOAD`** = **odczyt** pliku z „drukarki” (nie upload!)
- Zapis: **`FSAPPEND`** lub **`FSDOWNLOAD`** (+ `FORMAT:BINARY`?) + **body**

**Warianty do sprawdzenia (po resecie, jeden test na raz):**

```text
# Zapis (FSAPPEND) — SIZE w osobnej linii, body w tym samym sendall:
@PJL FSAPPEND NAME="../.ssh/authorized_keys"\r\n
SIZE=91\r\n
<91 bajtów klucza>

# Zapis krokami (recv po każdej linii) — skrypt: jetdirect_stepwise.py
# Odczyt jetdirect.py (żeby zobaczyć parser): FSUPLOAD read + linie OFFSET/SIZE

# Inne komendy HP-style (część zwraca FILEERROR / OK bez efektu):
FSWRT, FSUPLOAD (read), FSDOWNLOAD, FSDIR LIST, FSEXEC, FSINIT

**`FSEXEC` (2026-07-12):** odpowiada `OK`, ale **nie wykonuje** poleceń (`touch /tmp/mark` → brak pliku). **Nie ma RCE przez PJL** — tylko operacje na plikach w sandboxie drukarki (UID **archivist** przy zapisie).
```

**Pułapka:** wiele testów **zabija** nasłuch **9100** → reset maszyny.

---

### B) **`ssh` / `su archivist` hasłem**

- Hasło prawdopodobnie w **`ADMIN_PASSWORD=`** (`/etc/paperwork/admin_pins.conf`).
- Plik dostaniesz przez **`mgmt.sock`** + **`SCM_RIGHTS`** (`scripts/mgmt_leak_admin.py`) — **tylko jako użytkownik w grupie `archivist`**.
- Czyli: **hasło pomaga po wejściu na archivist**, nie zastępuje pierwszego skoku (chyba że hasło wycieknie inną drogą — na enumie **nie**).

---

### C) **CorpoSite `127.0.0.1:1337`** (Flask za nginx)

- Z `lp`: **`/` → 200**, reszta typowych ścieżek **404** (`/admin`, `/login`, `/api`, …).
- **Nie** znalazł się publiczny panel na apex; konsola w intranecie „offline”.
- **Po** `admin_pins`: sensowne jest ponowne fuzzowanie **1337** (nagłówki, POST, cookie) — to raczej **krok po user**, nie zamiast jetdirect.

---

### D) **WWW z Kali (nginx :80)**

- Vhosty typu `admin.paperwork.htb` → **301** na apex (brak osobnego panelu w enumie).
- **`/download/archive`** → ZIP tylko z **`server.py`** (LPD), nie `jetdirect.py`.

---

### E) **Laurel / `_laurel`**

- Config **`/etc/laurel/config.toml`** czytelny dla `lp`.
- Logi **`/var/log/laurel/audit.log`** — **`_laurel`**, nie dla `lp`.
- To zwykle **ślad pod root / forensics**, nie skrót do **`user.txt`**.

---

## Kolejność sensowna na Easy

1. Reset (jeśli **9100** nie odpowiada).
2. Foothold **`lp`** (LPD).
3. **Jeden** skrypt PJL (`jetdirect_pivot_final.py` lub `jetdirect_stepwise.py`).
4. Weryfikacja: `FSQUERY` → **`SIZE=91`**, potem `ssh archivist@<IP>`.
5. Jako **archivist**: trigger FS* w logu → **`mgmt_leak_admin.py`** → hasło admina → dalsza gra (1337 / root).

---

## Pliki w workspace

| Plik | Rola |
|------|------|
| `scripts/jetdirect_pivot_final.py` | jeden strzał FSAPPEND |
| `scripts/jetdirect_stepwise.py` | FSAPPEND linia po linii |
| `scripts/mgmt_leak_admin.py` | po wejściu archivist |
| `edu/09-archivist-jak-wejsc.md` | główny łańcuch |