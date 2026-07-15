# HackTheBox — Paperwork (Easy) | Write-up

> **Release Arena EU · Linux · Autor maszyny: LazyTitan33**  
> Krótki, techniczny opis solve’a pod portfolio / LinkedIn — bez gotowych flag i haseł (HTB).

---

## TL;DR

Na **Paperwork** łańcuch wygląda tak: **custom LPD (RFC 1179)** → shell jako usługowy user → **lokalny „drukarkowy” protokół PJL** → pivot na użytkownika aplikacji → **Unix socket + przekazanie deskryptorów plików (SCM_RIGHTS)** → **privilege escalation do root** przez standardowy mechanizm `su`.

To dobry przykład boxa, gdzie **nie ma gotowego modułu Metasploit** — liczy się czytanie kodu, protokołów i uprawnień Linux.

---

## Umiejętności, które ten box ćwiczy

| Obszar | Co robiłem w praktyce |
|--------|------------------------|
| **Recon** | Nmap, identyfikacja nginx + aplikacji za reverse proxy (Werkzeug/Flask) |
| **Web** | Analiza intranetu, wyciek artefaktu (`/download/archive` → ZIP ze źródłem) |
| **Eksploitacja custom** | Klient LPD w Pythonie, injekcja w polu parsowanym przez `shell=True` |
| **Pivot / lateral (local)** | Usługa tylko na `127.0.0.1:9100`, semantyka PJL, path traversal w sandboxie plików |
| **Linux privesc** | Grupy, prawa socketów UNIX, `recvmsg` + SCM_RIGHTS, systemd units |
| **Opsec / metodyka** | Notatki w repo (`notes.md`, `loot/`, `edu/`), unikanie „spamu” na wrażliwe usługi |

---

## 1. Recon i powierzchnia ataku

Po wejściu w sieć HTB (VPN):

- **22/tcp** — OpenSSH  
- **80/tcp** — nginx → vhost `paperwork.htb`  
- **1515/tcp** — usługa przypominająca **LPD (Line Printer Daemon, RFC 1179)**

Strona to korporacyjny **„Intake Portal”** — opisuje kolejkę archiwizacji i **legacy gateway** (LPD). To nie jest typowy WordPress/PHP; stack to **reverse proxy + backend Python**.

Ważny trop: endpoint **`/download/archive`** zwraca archiwum ZIP z plikiem `server.py`. Porównanie rozmiaru i logiki z kodem na serwerze pokazuje, że **ZIP ≠ dokładna kopia produkcji** — na boxie działa **nowsza wersja** obsługi zadań druku (więcej niż „hello world” z leaku).

**Wniosek:** szukam footholdu w **własnym demonie LPD**, nie w CVE nginx.

---

## 2. Foothold — Line Printer Daemon

Analiza `server.py` (z ZIP + później wersja z maszyny) ujawnia wzorzec:

- Akceptacja zlecenia dla skonfigurowanej kolejki (`archive_intake`).
- Odczyt pliku kontrolnego; wyciągnięcie linii **`J<job_name>`**.
- Uruchomienie polecenia w stylu: `echo 'Archive: <job_name>' …` przez **`subprocess` z `shell=True`**.

Klasyczna **command injection** w polu, które developer traktował jako „nazwę zadania”.

Zbudowałem **dedykowany klient LPD** (bajt `\x02` + kolejka, subcommand pliku kontrolnego, rozmiar, treść z linią `J…`) i uzyskałem shell jako użytkownik usługi **`lp`**.

**Lesson learned:** na CTF „Easy” często wystarczy **source code + jeden słaby subprocess**, a nie 0-day.

---

## 3. Pivot — od `lp` do użytkownika aplikacji

User flag nie leży na koncie `lp`. Docelowy użytkownik to **`archivist`** (aplikacja druku / archiwum).

Enumeracja z ograniczonego shella:

| Usługa | Bind | User procesu |
|--------|------|----------------|
| **jetdirect** | `127.0.0.1:9100` | `archivist` |
| **CorpoSite** | `127.0.0.1:1337` | `root` |
| **LPD** | `0.0.0.0:1515` | `lp` |
| **paperwork-daemon** | socket UNIX | `root` |

Jetdirect implementuje **uproszczony PJL** (Printer Job Language) nad TCP:

- W tym kodzie nazwy są **odwrócone** względem intuicji: np. **`FSUPLOAD` = odczyt**, **`FSDOWNLOAD` = zapis** pliku w sandboxie katalogu drukarki.
- Ścieżki typu `../.ssh/authorized_keys` pozwalają wyjść z katalogu usługi ( **`normpath` + join** ).

Po poprawnym zapisie klucza SSH (nagłówek `FSDOWNLOAD` z **`NAME` i `SIZE` w jednej linii**, potem surowe bajty klucza) — logowanie:

```bash
ssh archivist@<TARGET_IP>
```

**Lesson learned:** protokoły „drukarkowe” na CTF to często **file R/W z traversal**, nie magiczny RCE; **`FSEXEC`** bywa stubem zwracającym `OK`.

---

## 4. Privilege escalation — management socket i forensics

Użytkownik `archivist` jest w grze o **root** dzięki:

```text
/run/paperwork/mgmt.sock
  typ: UNIX stream
  prawa: srw-rw---- root:archivist
```

Daemon **`paperwork-daemon`** (root):

1. Monitoruje log komend PJL: `commands.log`.
2. Jeśli w logu pojawią się słowa kluczowe związane z operacjami na plikach (**`FSQUERY` / `FSUPLOAD` / `FSDOWNLOAD`**), uznaje to za incydent bezpieczeństwa.
3. W trybie **lockdown** wysyła klientowi na sockecie komunikat alertu oraz — co kluczowe — przekazuje **deskryptory otwartych plików** metodą **`SCM_RIGHTS`** (`sendmsg` / `recvmsg`).

Klient w grupie `archivist` odbiera te fd i może odczytać m.in. konfigurację z linią **`ADMIN_PASSWORD=…`** (plik normalnie `600 root`).

W trybie „czystym” (bez triggera w logu) daemon odpowiada tylko statusem i **podpisem HMAC-like** (`SIGNATURE` = hash stanu + sekret), **bez** ujawniania plaintext hasła — ładny podział na *weryfikację* vs *ujawnienie przy incydencie*.

**Kroki solve (uproszczone):**

1. Jedna komenda PJL generująca wpis w `commands.log` (np. `FSQUERY`).
2. Połączenie z `mgmt.sock` i `recvmsg()` — odczyt zawartości przekazanego fd.
3. Użycie uzyskanego sekretu jako hasła **`su root`** (PAM) → `root.txt`.

**Lesson learned:** privesc nie zawsze to `sudo -l` / SUID — czasem to **IPC Linux (fd passing)** i zrozumienie, *kiedy* proces root udostępnia dowód.

---

## 5. Co świadomie nie było potrzebne

- Publiczne CVE na nginx / OpenSSH w tym scenariuszu.  
- Godziny fuzzowania panelu admina na `:1337` — intranet i CorpoSite budują **narrację**, nie główny wektor roota.  
- Masowe testy PJL bez przerw (ryzyko **crashu** usługi lokalnej i resetu maszyny).

---

## 6. Metodyka (jak pracuję na boxach)

Struktura katalogu na maszynę:

```text
Paperwork/
  README.md, ACCESS.md, notes.md, target.txt
  nmap/, loot/, scripts/
  edu/          # notatki pod naukę po solve
```

- Flagi i credy → pliki `loot/copy-paste.txt` (nie w publicznym poście).  
- Po solve → materiały **`edu/15–17`** (łańcuch, SCM_RIGHTS, ćwiczenia na Kali).

---

## Podsumowanie jednym zdaniem

**Paperwork** uczy, że „drukarka w sieci” może oznaczać **LPD + PJL + daemon forensics na Unix socket** — i że na Easy wygrywa **czytanie kodu i uprawnień**, nie lista exploitów z Metasploit.

---

## Tagi (LinkedIn)

`#HackTheBox` `#CTF` `#PenetrationTesting` `#Linux` `#Python` `#WebSecurity` `#PrivilegeEscalation` `#RedTeam` `#CyberSecurity` `#LearnByDoing`

---

*Maszyna rozwiązana w ramach HackTheBox. Nie publikuj flag ani haseł — zostaw miejsce innym do nauki.*

**Pełna nauka techniczna (lokalnie, po solve):** `edu/15-podrecznik-po-solve.md`