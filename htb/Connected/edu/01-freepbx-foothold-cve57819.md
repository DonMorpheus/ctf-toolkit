# 01 — Foothold: FreePBX endpoint → RCE (CVE-2025-57819)

## Cel lekcji

Zrozumieć łańcuch **bez klikania exploitów w ciemno**: gdzie jest zaufanie, gdzie jest SQL, gdzie ląduje plik PHP.

## Model FreePBX (skrót)

- **ACP** — panel `/admin/`, użytkownicy w tabeli `asterisk.ampusers`.
- **Moduły** — katalog `admin/modules/<nazwa>/`, AJAX pod `/admin/ajax.php?module=...`.
- **Endpoint** — zarządzanie firmware telefonów; upload do ścieżek zależnych od `fwbrand`.

## Łańcuch na Connected

1. **SQLi** w parametrze `brand` (endpoint ajax `model`) — możesz modyfikować `ampusers`.
2. **INSERT** tymczasowego admina z znanym hasłem SHA1.
3. **Sesja** w `config.php` — logowanie do ACP.
4. **`upload_cust_fw`** — traversal w `fwbrand` (`../../../var/www/html/<twoj_katalog>`).
5. **Webshell** — wykonanie jako użytkownik procesu Apache → **`asterisk`**.

## Dlaczego to nie daje SSH

RCE = kontekst **www-data/asterisk w Apache**, nie login systemowy. Hasło admina GUI ≠ hasło Unix.

## Ćwiczenia

1. Uruchom `scripts/enum_privesc.py` i narysuj diagram 5 kroków własnymi słowami.
2. W Burp prześledź jeden request `upload_cust_fw` — które pola są multipart?
3. Na Kali: `sqlmap` **nie** uruchamiaj na HTB bez potrzeby — wystarczy zrozumieć manualny INSERT z PoC.
4. **Pytanie kontrolne:** co się stanie po `restart-apache` jeśli webshell leży poza ścieżką modułu?

## Pliki na boxie

- `loot/cve-57819-notes.md`
- `scripts/CVE-2025-57819_exploit.py`, `get_user_flag.py`