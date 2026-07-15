# 02 — incrond i sysadmin_manager (ścieżka „prawie root”)

## Cel lekcji

Rozróżnić **dwa mechanizmy** na Connected:

- spool **`/var/spool/asterisk/incron/`** → `/usr/bin/sysadmin_manager`
- plik **`/usr/local/asterisk/ha_trigger`** → `/usr/sbin/sysadmin_ha` (osobny temat w 03)

## incrond w 5 zdaniach

- Demon **`incrond`** reaguje na zdarzenia inotify (np. zamknięcie zapisu pliku).
- Reguły w **`/etc/incron.d/`** (root).
- FreePBX wrzuca „żądanie” jako **nazwę pliku** w spoolu; manager czyta format `moduł.hook.parametry`.

## sysadmin_manager

- Uruchamiany jako **root** (przy poprawnym triggerze).
- Wykonuje **podpisane** hooki z modułu **sysadmin** — nie dowolny bash z nazwy pliku.
- Stąd frustracja z `.CONTENTS` i wklejaniem skryptu do nazwy — to **params**, nie payload.

## Co na Connected działało (dowody)

- Hooki **framework** (np. logrotate) — pliki root w `/etc/logrotate.d/`.
- **`runModuleSystemHook`** z PHP CLI — wygodny trigger przy już działającym FreePBX.

## Co nie dało root flag

- **yum / ssh_keys** — brak DNS/repo.
- **update-ports** — ionCube, brak `sysadmin_portmgmt`, licencja.
- **dump-iptables** — mylący artefakt, nie czytelnik root.txt.

## Ćwiczenia

1. Na Kali: `apt install incron` w VM labowej, prosta reguła na `/tmp/test` (nie na HTB jeśli reset).
2. Przeczytaj `loot/incron-ssh-summary.txt` i dopisz własną tabelę: hook → efekt → blokada.
3. **Pytanie:** czym różni się trigger w spoolu od `touch ha_trigger`?

## Głębiej

- Kod: `Hooks.class.php` w module framework — generowanie nazw plików incron.
- Porównaj z cron: kiedy incron jest lepszy dla aplikacji PBX?