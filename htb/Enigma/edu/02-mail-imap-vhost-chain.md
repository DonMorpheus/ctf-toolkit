# Mail — Roundcube, IMAP, łańcuch credów

## Vhost

- Ten sam IP :80, różne `Host:` → różne `root` w nginx.
- Szybki filtr: porównaj **rozmiar** odpowiedzi z bazową stroną `enigma.htb` (~31 KB); fałszywe 302 z tym samym `Size` odrzucaj.

```bash
curl -sI -H 'Host: mail001.enigma.htb' http://<IP>/
```

## Roundcube

- Logowanie: `POST /?_task=login` + `_token` z cookies/HTML.
- Alternatywa: **IMAP** bez UI (szybsze czytanie skrzynek):

```python
import imaplib, email
M = imaplib.IMAP4_SSL('<IP>', 993)
M.login('user', 'pass')
M.select('INBOX')
# fetch RFC822 ...
```

## Pivot

1. Cred z NFS → skrzynka A (Kevin).
2. Spray **tego samego hasła** na inne konta IMAP (sarah często to samo hasło startowe).
3. Mail od IT z **wewnętrznym URL** i kontem aplikacji (OpenSTA) — to nie jest SSH.

## Dovecot / lokalny delivery

- Nagłówki typu `kevin@localhost` = lokalny MTA; nadal czytasz przez IMAP jako ten użytkownik.

## Ćwiczenie

`swaks` wyślij testową wiadomość między użytkownikami na labie Dovecot; potem odczytaj przez `openssl s_client -connect host:993` + ręczne IMAP lub skrypt Python.