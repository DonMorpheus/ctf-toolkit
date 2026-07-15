# 04 — Asterisk, AMI, MySQL — credy aplikacyjne vs Linux

## Cel lekcji

Przestać mieszać **hasła z configów** z **hasłami do SSH**.

## Co słucha na localhost (Connected)

| Port | Usługa | Credy z loot |
|------|--------|----------------|
| 3306 | MariaDB | `freepbxuser` / `mZzDpAGKTmPJ` |
| 5038 | AMI | sekrety `cxmanager*con`, `fe1mYBs7D5P3` |
| 6379 | Redis | (enum, bez klucza do SSH) |
| 22 | SSH | **brak** — spray negatywny |

## AMI (Asterisk Manager Interface)

- API do sterowania połączeniami, nie shell.
- Sekret w `manager.conf` / FreePBX — do auth AMI, nie do `ssh asterisk@`.

## MySQL

- `ampusers` — hasła adminów GUI (SHA1).
- `LOAD_FILE('/root/root.txt')` — na tym hoście **NULL** (uprawnienia, `secure_file_priv`).

## Ćwiczenia

1. Przez webshell: `ss -tlnp | grep -E '3306|5038|22'`.
2. Zaloguj się do MySQL lokalnie na boxie i wypisz 3 tabele z prefiksem `amp`.
3. Przeczytaj `loot/ssh-spray.txt` — lista prób; dodaj własną hipotezę *dlaczego* `mZzDpAGKTmPJ` nie jest hasłem SSH.

## Powiązanie z ACCESS.md

Zawsze sprawdzaj plik **ACCESS.md** w folderze maszyny przed szukaniem „hasła do wszystkiego”.