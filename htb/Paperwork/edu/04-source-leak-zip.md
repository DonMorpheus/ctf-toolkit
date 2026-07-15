# Wyciek kodu przez HTTP (ZIP)

## Obserwacja
`GET /download/archive` → `Content-Type: application/zip`,  
`Content-Disposition: attachment; filename=paperwork-archive-v1.02.zip`

## Po co to w pentestcie
- **White-box bez SSH:** czytasz logikę backendu (tu: `server.py`).
- Szukasz: `subprocess`, `shell=True`, `eval`, `pickle`, walidacja wejścia protokołu.

## Ćwiczenie
```bash
curl -sO http://paperwork.htb/download/archive
unzip -l paperwork-archive-v1.02.zip
unzip -o paperwork-archive-v1.02.zip -d ./audit/
grep -n subprocess ./audit/server.py
```

## OWASP mapping
- **A05** — niepotrzebne ujawnienie implementacji / „internal processor” publicznie.
- To **nie XSS** — to zmienia wektor na **review kodu + usługa sieciowa**.

Artefakty: `loot/paperwork-archive-v1.02.zip`, `loot/archive-src/server.py`.