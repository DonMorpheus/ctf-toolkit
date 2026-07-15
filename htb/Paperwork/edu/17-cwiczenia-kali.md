# Ćwiczenia na Kali (po Paperwork)

Zadania **offline / własne VM** — utrwalenie bez ponownego spamowania HTB.

## Poziom 1 — protokoły

1. **LPD mini-lab**  
   Napisz `server.py` z jednym `shell=True` i klienta wysyłającego job `J` — zrozum bajty `\x02`, `\x00`, rozmiar pliku kontrolnego.  
   *Cel:* w 10 minut odtworzyć foothold bez patrzenia w `lpd_exploit.py`.

2. **PJL echo**  
   Serwer TCP na `9100` przyjmujący linię `@PJL ECHO ...` i odsyłający echo.  
   *Cel:* zrozumieć `\r\n` vs `\n` i timeouty `recv`.

3. **Path join**  
   W Pythonie odtwórz `normpath(join(root, user_input))` i przetestuj:
   - `../.ssh/authorized_keys`
   - `....//....//etc/passwd`  
   *Cel:* przewidzieć co przejdzie bez czytania `jetdirect.py`.

## Poziom 2 — Linux IPC

4. **Dwa fd przez socket**  
   Dwa procesy: root (lub user A) otwiera `/etc/hostname` i wysyła fd przez `AF_UNIX`; user B robi `recvmsg` i `read`.  
   *Cel:* zrozumieć SCM_RIGHTS bez HTB.

5. **Uprawnienia socketu**  
   Ustaw `chmod 660` i grupę na pliku `.sock`; sprawdź `connect` jako user w grupie i poza nią.  
   *Cel:* mapowanie na `mgmt.sock`.

## Poziom 3 — enum pod privesc

6. **Skrypt enum „archivist-style”**  
   Z jednego SSH wywołania wypisz:
   - `id`, `ss -tln`, `systemctl list-units --type=service --state=running`
   - find SUID, `getcap -r /usr 2>/dev/null`  
   Zapisz do pliku z datą — jak `loot/privesc-enum-archivist.txt`.

7. **Diff ZIP vs prod**  
   Automatyczny skrypt: pobierz `/download/archive`, rozpakuj, porównaj rozmiar i `md5sum` z `nmap/scripts` lub ręcznym uploadem — heurystyka „fałszywy artefakt”.

## Poziom 4 — myślenie obronne (Blue)

8. **Jak naprawić LPD?**  
   Lista: `shell=False`, lista dozwolonych znaków w `job_name`, osobny user bez login shell, seccomp.

9. **Jak naprawić jetdirect?**  
   Chroot bez `..`, whitelist komend PJL, brak logowania surowych FS* do pliku czytanego przez root daemon — **albo** daemon nie przekazuje fd configu.

10. **Jak naprawić mgmt?**  
    Osobny kanał audytu; tylko metadane w lockdown; rotacja sekretu; brak przekazywania fd do `admin_pins` — użycie HMAC challenge-response (jak `SIGNATURE` w trybie clean).

## Szybka ściąga komend (box archivist)

```bash
# trigger
python3 -c 'import socket;s=socket.socket();s.connect(("127.0.0.1",9100));s.sendall(b"@PJL FSQUERY NAME=\".\"\r\n");s.recv(1024)'

# leak (skrypt w ../scripts/mgmt_leak_admin.py)

# root
su -   # hasło z ADMIN_PASSWORD w leaku
```

Nie traktuj tego jako „jedyny styl życia” — na produkcji szukasz **własnej** kombinacji z enumu.