# nginx 1.28.0 — rozpoznanie (Paperwork)

## Co zobaczyliśmy na boxie
- **Port 80:** `Server: nginx/1.28.0 (Ubuntu)` w nagłówku odpowiedzi.
- **nmap `-sV`:** http → nginx; skrypt `http-server-header` potwierdza wersję.
- **Brak 443** w initial — cały front to HTTP (typowe w labie).

## nginx ≠ aplikacja
nginx często **tylko serwuje pliki** lub **proxy_pass** do backendu (Python, Node, itd.).  
Na Paperwork strona główna to **statyczny HTML** (Intake Portal); dynamiczna logika może być na **innym porcie** (tu: **1515/tcp** — LPD).

## Ćwiczenia na Kali
```bash
curl -sI http://TARGET/
sudo nmap -Pn -p 80,443,8080 -sV --script http-server-header,http-title TARGET
whatweb http://TARGET/   # jeśli zainstalowane
```

## Na co patrzeć
| Sygnał | Znaczenie |
|--------|-----------|
| `Content-Type: text/html` + mały zestaw ścieżek | często static lub 1–2 endpointy |
| `Content-Disposition: attachment` | pobieranie pliku (ZIP, binarka) |
| Brak `X-Frame-Options`, CSP, HSTS | słaba twardość nagłówków (OWASP) — nie exploit sam w sobie |

Zapis z boxa: `loot/http-headers.txt`, `loot/security-headers.txt`.