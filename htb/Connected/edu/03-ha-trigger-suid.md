# 03 — ha_trigger, brakujący moduł freepbx_ha, SUID bash

## Cel lekcji

Zrozumieć **root na tym boxie**: nie incron spool, tylko **zaufana ścieżka PHP** uruchamiana jako root.

## Reguła incron

```
/usr/local/asterisk/ha_trigger  IN_CLOSE_WRITE  /usr/sbin/sysadmin_ha
```

- Plik `ha_trigger` jest **world-writable** — asterisk może `touch`.
- Przy zamknięciu zapisu → root odpala **`/usr/sbin/sysadmin_ha`** (PHP CLI).

## Co robi sysadmin_ha

Hardcoded include:

1. `.../freepbx_ha/license.php` (opcjonalnie)
2. `.../freepbx_ha/functions.inc/incron.php` → klasa `incron` → **`rootTrigger()`**

Na oryginalnym hoście katalog **`freepbx_ha` nie istniał** — `file_exists` blokował exploit, dopóki nie **stworzyliśmy** modułu w writable `admin/modules/`.

## Payload

W `rootTrigger()` jako root:

```php
chmod('/bin/bash', 04755);
```

Potem `touch /usr/local/asterisk/ha_trigger` → incrond → PHP jako root → SUID.

## Użycie SUID

```bash
/bin/bash -p -c 'id; cat /root/root.txt'
```

`-p` — privileged mode, zachowuje effective UID root.

## Lekcja bezpieczeństwa

- **Writable web root + fixed include path + root cron** = katastrofa.
- Brak modułu w repozytorium **nie** oznacza braku kodu w skryptach HA.

## Ćwiczenia

1. Odtwórz: `scripts/ha_trigger_suid.py` — dodaj komentarze do każdego kroku samodzielnie.
2. `find / -perm -4000 2>/dev/null` na własnej Kali — które SUID znasz (sudo, passwd, …)?
3. **Pytanie:** dlaczego nadpisanie istniejącego `incron.php` mogło nie być potrzebne?

## Skrypt

`~/Desktop/htb/Connected/scripts/ha_trigger_suid.py`