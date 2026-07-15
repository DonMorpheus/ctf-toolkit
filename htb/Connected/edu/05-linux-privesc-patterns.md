# 05 — Wzorce privesc na przykładzie Connected

## Mapa wektorów (ten box)

| Wektor | Status | Nauka |
|--------|--------|-------|
| Kernel exploit | odrzucony (suggester) | kiedy nie tracić czasu |
| sudo | hasło wymagane | zawsze `sudo -l` |
| SUID /usr/bin/incrontab | jest | ograniczony kontekst |
| incron + sysadmin_manager | częściowy | podpisane hooki |
| ha_trigger + PHP | **root** | trust path |
| Licencja / yum / ssh_keys | zablokowane siecią | realny świat PBX |

## Checklist na każdy Linux box

1. `id`, `sudo -l`, `find / -perm -4000 2>/dev/null`
2. Cron + **incron** + systemd timers
3. Writable przez użytkownika shella: `/etc`, cron.d, unit files, **web modules**
4. Procesy root + nietypowe ścieżki (`/usr/sbin/sysadmin_ha`)
5. Sieć outbound (yum, curl licencji)

## Ćwiczenie syntezy

Napisz **jeden akapit** „jak bym atakował Connected od zera” bez narzędzi — potem porównaj z `notes.md`.

## Kernel

Szczegóły: `loot/kernel-exploit-report.txt` — dobry przykład dokumentacji „dlaczego nie”.