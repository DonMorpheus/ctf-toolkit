# RFC 1179 (LPD) — podstawy pod Paperwork

## Skąd wiedzieć
- Strona: `Compliance Level: RFC 1179`, kolejka `archive_intake`.
- **nmap:** `1515/tcp open` — banner: `Archive_Printer is ready and printing.`
- ZIP `paperwork-archive-v1.02`: serwer `LpdServer` na porcie **1515**.

## Co to jest LPD
**Line Printer Daemon** — stary protokół zlecania wydruku po TCP (historycznie port **515**; w labie często inny, tu **1515**).

Komendy (pierwszy bajt):
- `0x02` — zlecenie joba druku (receive print job)
- `0x03` / `0x04` — status / kolejka (implementacja zwraca gotowość)

## Dlaczego to nie „web server”
**nginx** obsługuje HTTP; **LPD** to osobna usługa. Atak na Easy często = przeczytaj kod z ZIP + połącz się na **1515** (np. `nc`, skrypt Python).

## Ćwiczenie (bezpieczne, tylko lab HTB)
```bash
nc -nv TARGET 1515
# lub: nmap -sV -p 1515 --script banner TARGET
```

## Czytaj dalej (bez exploit chain)
- RFC 1179 — format jobów, linie kontrolne (`J` = nazwa joba w wielu implementacjach).
- Porównaj z `loot/archive-src/server.py` lokalnie (nie wklejaj flag do czatu).

Następny temat w edu: analiza walidacji kolejki i `subprocess` w kodzie → `04-source-leak-zip.md` + notatki własne.