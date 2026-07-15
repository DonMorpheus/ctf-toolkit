# Lektura ogólna (bez spoilerów boxa)

## Łańcuchy „enterprise-lite”

- **NFS / SMB** jako „shared drive” z dokumentami HR — częsty foothold gdy eksport jest szeroki.
- **Mail jako bus credów** — jedna skrzynka → druga → panel aplikacji wewnętrznej.
- **Aplikacja PHP z backup/restore** — zaufany ZIP = zapis plików w docroot (klasa podobna do plugin/update w innych CMS).

## Mail

- Dovecot + Postfix na jednym hoście; enumeracja przez IMAP często szybsza niż scraping Roundcube.
- Hasła startowe współdzielone między użytkownikami — zawsze spray ograniczoną listą (nie cały rockyou na SSH).

## Panel admina na vhoście

- Osobny `server_name` bez linku z landing page — wymusza vhost bruteforce z filtrem odpowiedzi lub logiczne nazwy (`mail001`, `support_001`).

## Localhost services

- `127.0.0.1:high_port` + panel typu **OliveTin / Portainer / Redis** — pivot przez SSH `-L` lub RCE na hoście.
- Usługa jako **root** + akcje z szablonami shell = szukać argumentów ze słabą walidacją, nie tylko RCE w aplikacji WWW.

## Protobuf / nowe API

- SPA z 200 na `/` i 404 na REST — sprawdź `405` na POST, `strings` binarki (`StartAction`, `action_id`), body **application/proto**.

## Dokumentacja

- [OliveTin docs](https://docs.olivetin.app/) — akcje, argumenty, ACL.
- OpenSTAManager — backup w repo źródłowym (`Backup.php`, moduł aggiornamenti).