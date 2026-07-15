# Ćwiczenia na Kali (enigma — powtórka)

## 1. NFS

- [ ] `showmount -e <IP>` i mount do `~/mnt/...`
- [ ] Wyciągnij tekst z PDF bez GUI (mutool/strings)

## 2. HTTP / vhost

- [ ] Jedna komenda pętla: 5 hostów `*.enigma.htb`, wypisz kod + rozmiar
- [ ] Dopisz wpisy do `/etc/hosts`

## 3. Mail

- [ ] Logowanie IMAP SSL (Python lub `openssl`)
- [ ] Spray 3 użytkowników jednym hasłem z leaku

## 4. OpenSTA

- [ ] Login curl + cookie jar
- [ ] Zbuduj `evil.zip`, restore, `id` przez webshell
- [ ] (Opcja) Pobierz backup z UI i `unzip -l` — zrozum strukturę

## 5. Post-www-data

- [ ] Odczyt `config.inc.php`
- [ ] Dump `zz_users`, john bcrypt
- [ ] `su haris` + user flag

## 6. OliveTin

- [ ] Tunel SSH na 1337
- [ ] Uruchom akcję `date` protobufem
- [ ] Injekcja `backup_database` + odczyt logów

## Bonus

- [ ] Nmap tylko NFS: `--script nfs-showmount`
- [ ] Porównaj: restore przez `controller.php` vs `actions.php`