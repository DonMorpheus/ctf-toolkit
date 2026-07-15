# Connected — lektura na poziom APT (umiejętność, nie malware)

Box **nie był łatwy**: PBX, dwa mechanizmy incron, licencja/Sangoma, fałszywy brak modułu HA. **S11 tournament** — bez normalnego writeupu w internecie; nauka z własnego śladu (`notes.md`, `edu/`) ma tu większą wartość niż przy „Retired + 200 WP”. Ten plik zbiera **źródła ogólne** — żebyś rozumiał *klasy* problemów (trust path, root triggers, app creds ≠ OS), nie żeby odtworzyć jedną flagę z writeupu.

**Jak czytać:** 2–3 pozycje tygodniowo, notatki własne w `notes.md`. Po każdym rozdziale: jedno zdanie „co bym sprawdził na następnym Linux/web boxie”.

---

## 1. Linux — privesc i „cichy root”

| Temat | Gdzie | Po co |
|-------|--------|--------|
| SUID/SGID, capabilities | `man 7 credentials`, GTFOBins (koncepty SUID) | `/bin/bash -p`, `incrontab` |
| Cron vs **incron** | `man incrond`, `man 5 incrontab` na Kali | drugi trigger na Connected |
| File permissions + traversal | *The Linux Programming Interface* (rozdz. 15, 18) — fragmenty | writable `admin/modules` |
| systemd timers | `systemctl list-timers`, arch wiki systemd | porównanie z incron |

**Ćwiczenie APT:** na własnej VM — reguła incron + skrypt jako root; potem **tylko** zmiana pliku w katalogu writable przez usera `www-data` i pytanie: *czy root coś includuje stamtąd?*

---

## 2. Aplikacja uruchamiana jako root (trust path)

To sedno **ha_trigger** — nie „magiczny cron”, tylko **root wykonuje kod, który ładuje ścieżki z dysku**.

| Temat | Gdzie | Po co |
|-------|--------|--------|
| OWASP: insecure file permissions / deployment | OWASP WSTG — konfiguracja, uprawnienia plików | moduł `freepbx_ha` stworzony z niczego |
| PHP `include` / `require` i ścieżki | PHP manual: `include`, autoload, `file_exists` | `sysadmin_ha` |
| Supply chain / „missing package” | ogólne case studies (npm, pip) — **analogia myślowa** | moduł nie zainstalowany, ścieżka zostaje |

**Pytanie na poziom APT:** *Jeśli demon root robi `require_once($fixed_path)` — kto powinien kontrolować katalog nadrzędny?*

---

## 3. FreePBX / Asterisk / VoIP (kontekst biznesowy)

| Temat | Gdzie | Po co |
|-------|--------|--------|
| Architektura FreePBX (moduły, ACP, UCP) | docs.sangoma.com / wiki FreePBX — *Module Development* (overview) | AJAX, `ampusers`, moduły |
| Asterisk Manager Interface (AMI) | Asterisk docs: AMI, `manager.conf` | port 5038, sekrety ≠ SSH |
| Sangoma / sysadmin (high level) | opisy modułu Sysadmin (bez walkthroughów HTB) | hooki, licencja, yum |
| ionCube / encoded PHP (świadomość) | dokumentacja ionCube — *co to jest* | `update-ports` nie do reverse w 5 min |

Nie musisz być telefonistą — musisz wiedzieć, że **PBX = wiele demonów + panel + spool**, nie jeden „Apache”.

---

## 4. Web → RCE (foothold tej maszyny)

| Temat | Gdzie | Po co |
|-------|--------|--------|
| SQL injection (second order, stacked) | PortSwigger Web Security Academy — SQLi | `ampusers` |
| Unrestricted / path traversal upload | OWASP: File Upload, WSTG-INPV | `fwbrand` traversal |
| Session i auth panelu admina | PortSwigger — session, access control | fake admin |
| CVE / advisories (fakty) | NVD, GHSA dla **endpoint** / FreePBX 16.x | `loot/cve-57819-notes.md` jako indeks lokalny |

**Ćwiczenie APT:** przejrzyj request upload w Burp i zaznacz: *authentication boundary*, *path normalization*, *post-upload execution*.

---

## 5. Sieć i „prawie działa” (sysadmin, yum, DNS)

| Temat | Gdzie | Po co |
|-------|--------|--------|
| outbound restrictions na CTF | własne notatki + `notes.md` Connected | `katanafpbx`, mirrorlist |
| yum/dnf w obrazach vendorowych | Red Hat docs: yum, repo | `ssh_keys` nie wchodzi |
| DNS na maszynie izolowanej | `resolv.conf`, NetworkManager | aktywacja licencji |

To odróżnia **APT mindset** od „jeszcze jeden exploit”: *dlaczego ścieżka vendorowa jest świadomie zepsuta na labie*.

---

## 6. Książki / długie formy (wybierz jedną ścieżkę)

| Ścieżka | Pozycja | Uwagi |
|---------|---------|--------|
| Linux głęboko | Michael Kerrisk — *TLPI* | procesy, UID, pliki |
| Web ofensywnie | Dafydd Stuttard — *The Web Application Hacker's Handbook* (wybrane rozdz.) | upload, auth, injection |
| Metodologia | MITRE ATT&CK — persistence, privilege escalation (techniki, nie CVE HTB) | mapowanie kroków |
| OSCP-style bez spoilerów | oficjalne materiały PWK / notatki własne | checklisty, nie IP Connected |

---

## 7. Na Kali — praktyka bez HTB

```bash
# incron (lab lokalny)
sudo apt install incron
# /etc/incron.d/test — reguła na /tmp/watch

# SUID świadomie
find / -perm -4000 -type f 2>/dev/null | head
ls -la /bin/bash /usr/bin/sudo

# PHP include trap (własny docker)
# dwa pliki: root-cron.sh + writable podkatalog — symulacja trust path
```

---

## 8. Czego **nie** traktować jako „lektury APT”

- Losowe skróty „Top 10 privesc one-liners” bez kontekstu.
- Writeupy **tej konkretnej maszyny** — Ty chciałeś uczyć się mechanizmu; LinkedIn / garnitur / Google dev mogą podać *hint* (cron/incron), ale **zrozumienie** = własny diagram + `edu/03`.
- Crackowanie haseł SHA1 admina jako „główna technika” — na Connected to był boczny tor.

---

## 9. Checklist „jestem gotowy na podobny box”

- [ ] Narysuję z pamięci: incron spool **vs** pojedynczy plik triggera (`ha_trigger`).
- [ ] Wyjaśnię, czemu `freepbxuser` nie loguje do SSH.
- [ ] Opiszę łańcuch CVE foothold w 4 krokach bez nazw plików z PoC.
- [ ] Wiem, kiedy kernel LPE odpuszczam na rzecz vendor privesc.
- [ ] Po wejściu na shell: `find` writable + `grep -r` root scripts pod `include`/`require`.

---

## Powiązane pliki w tym folderze

1. `01-freepbx-foothold-cve57819.md`  
2. `02-incron-sysadmin-manager.md`  
3. `03-ha-trigger-suid.md` ← ten z LinkedIn/cron vibe  
4. `04-asterisk-ami-mysql.md`  
5. `05-linux-privesc-patterns.md`  

*LinkedIn i garnitur premium nie robią roota — robi zrozumienie, że vendor HA często ma „dziwny” trigger. Reszta to Ty w `edu/` i na labie.*