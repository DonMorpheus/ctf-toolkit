# Abducted — Linux Medium (Samba)

Własny zapis łańcucha (lab HTB). **Bez flag.** Hasła z boxa trzymaj lokalnie, nie w git.

```
guest printer (CVE-2026-4480)
  → nobody (print service)
  → rclone.conf (world-readable) → rclone reveal
  → SSH scott (password reuse)
  → transfer share: force user=marcus + wide links
  → SSH marcus (operators)
  → writable smbd.service.d + polkit reload/restart smbd
  → ExecStartPre setuid bash → root
```

## 1. Recon

Tylko SSH + Samba (139/445). Brak WWW.

```bash
nmap -sSVC --open -Pn -p 22,139,445 <RHOST>
smbclient -L //<RHOST> -N
```

Share’y: `HP-Reception` (Printer, guest), `projects`, `transfer`, `IPC$`.

Banner SSH: OpenSSH 9.6p1 Ubuntu — host z epoki sprzed zbiorczego patcha Samba (m.in. printing RCE). Wersji Samba z negocjacji SMB2 nie wyciągniesz; `rpcclient srvinfo` kłamie (`os version 6.1`). Wektor po **powierzchni**: gościnna drukarka, nie po bannerze.

## 2. Foothold — CVE-2026-4480

`print command` (sysv) podstawia `%J` (nazwa joba) i `%s` (spool) do `system()`. Jedyna sanitizacja przed fixem: `'` → `_`. `| ; & < >` przechodzą.

Klienci RAP (`smbclient` print) ucinają metaznaki. Trzeba **spoolss**: `OpenPrinter` → `StartDocPrinter` (`document_name` = `|sh`) → `WritePrinter` (ciało = skrypt) → `EndDocPrinter`.

Job musi być niepusty. Print command jest synchroniczny — payload odpinamy (`setsid … &`).

PoC: [`scripts/cve_2026_4480_spoolss.py`](scripts/cve_2026_4480_spoolss.py) (`python3-samba`).

Shell: `nobody`.

## 3. User — rclone

`/opt/offsite-backup/rclone.conf` jest world-readable. Pole `pass` to **obscure** rclone (odwracalne), nie szyfrowanie:

```bash
rclone reveal '<obscured>'
```

To hasło jest reused na konto `scott` (SSH). User flag w `~scott/user.txt`.

## 4. scott → marcus — wide links

`[transfer]`: `valid users = scott`, `force user = marcus`, `wide links = yes`, globalnie `unix extensions = no` + `allow insecure wide links = yes`.

`scott` może zrobić symlink `/srv/transfer/mh → /home/marcus`, potem przez SMB (operacje jako marcus) wrzucić `authorized_keys`.

[`scripts/marcus_wide_links.sh`](scripts/marcus_wide_links.sh)

`marcus` jest w grupie `operators`.

## 5. marcus → root — polkit + systemd drop-in

`/etc/systemd/system/smbd.service.d` jest `drwxrws---` group `operators`. Drop-in `*.conf` merguje się w `smbd.service` (root).

`pkcheck` na ślepo nie pokaże `manage-units` (warunek `unit=smbd.service`). `org.freedesktop.systemd1.reload-daemon` jest ALLOWED. `systemctl restart smbd` idzie bez hasła.

`ExecStartPre=/bin/cp /bin/bash /tmp/.rb` + `chmod 4755`, potem `/tmp/.rb -p`.

## Notatki

- OOB: ping na `tun0` przed reverse shellem.
- Nie commituj `user.txt` / `root.txt` / kluczy.
