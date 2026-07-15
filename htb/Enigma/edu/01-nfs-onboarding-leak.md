# NFS — onboarding leak

## Mechanizm

- **NFS** (port 2049 + rpcbind) eksportuje katalog z serwera do klientów w sieci.
- `showmount -e <IP>` pokazuje ścieżkę i klientów (`*` = wszyscy).
- Mount u atakującego (Kali, `ctf` + sudo):

```bash
sudo mkdir -p ~/mnt/enigma_nfs
sudo mount -t nfs <IP>:/srv/nfs/onboarding ~/mnt/enigma_nfs -o ro,nfsvers=3
```

- Eksport **read-only** w `/etc/exports` nie blokuje **odczytu** — wystarczy na credy w plikach.

## Co szukać

- PDF/DOC/XLS z onboardingiem (hasła tymczasowe, URL-e wewnętrzne).
- `pdftotext` czasem pusty → `mutool draw -F txt plik.pdf` lub `strings`.

## Na tym boxie

- Jeden plik: onboarding PDF → użytkownik webmail + hasło + **vhost** `mail001.enigma.htb`.

## Typowe błędy

- Mount pod `/mnt` bez uprawnień → mount w `$HOME`.
- Gobuster na statycznej wizytówce zamiast NFS + vhost.

## Ćwiczenie

Na swojej VM: postaw `nfs-kernel-server`, wyeksportuj katalog z jednym plikiem, zamontuj z drugiej maszyny i odtwórz enumerację.