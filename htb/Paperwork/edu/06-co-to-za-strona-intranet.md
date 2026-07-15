# „Śmieszna” strona — o co chodzi w Paperwork?

## Fabuła UI
To **korporacyjny intranet** „Department of Records & Archives”:
- **Intake Portal** — zgłaszanie dokumentów do archiwum.
- **RFC 1179** — protokół **drukarki / kolejki wydruku** (LPD), nie REST API.
- Kolejka **`archive_intake`** — jobs trafiają jak „wydruk” do archiwizacji.
- **`PRN-ARCHIVE-01`** — fikcyjny spooler; konsola zarządzania **offline** (stąd brak panelu admina w WWW).

## Dwie warstwy techniczne
| Warstwa | Rola |
|---------|------|
| nginx :80 | Statyczna „wizytówka” + proxy do Flask pod `/download/` |
| LPD :1515 | Prawdziwy „procesor” zleceń (kod w ZIP) |

## Dlaczego to wygląda absurdalnie
Box **parodiuje** stare corporate IT: zamiast S3/SharePoint — **drukarka sieciowa** jako pipeline dokumentów. To hint: **wektor nie będzie typowym logowaniem do WordPressa**, tylko **protokół + kod z wycieku**.

## Dla CTF
Nie szukaj na siłę **panelu logowania** — przeczytaj komunikat *offline* dosłownie. Szukaj: **port 1515**, **`server.py`**, kolejka z intranetu.