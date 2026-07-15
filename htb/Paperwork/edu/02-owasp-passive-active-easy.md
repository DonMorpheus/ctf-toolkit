# OWASP — szybki przejazd (Easy / cienka powierzchnia WWW)

## Kontekst Paperwork
- Jedna strona informacyjna + **`/download/archive`** (plik ZIP).
- **Brak formularzy** na stronie głównej → klasyczne **XSS stored/reflected** przez UI mało prawdopodobne bez kolejnego endpointu.

## Co sprawdziliśmy (2026-07-12)

### A03 Injection (SQLi / command)
- **SQLi:** brak parametrów DB w WWW na `/` i `/download/archive` (query string nie zmienia treści HTML poza długością odpowiedzi ZIP).
- **Command injection:** nie przez nginx/HTML — szukać w **backendie** (tu wskazówka: protokół spoolera, kod w ZIP).

### A03 XSS
- Payload: `<script>alert(1)</script>` w `?x=`, `?search=` — **brak odbicia** w body (stały HTML 2844 B).
- `/download/archive?x=...` — nadal plik ZIP, bez HTML → **XSS mało realne** na tym path.

### A05 Security misconfiguration
- Brak typowych nagłówków hardeningu na `/` (np. CSP, HSTS) — zapis w `loot/security-headers.txt`.
- **Information disclosure:** publiczny ZIP z kodem procesora (`server.py`) — kategoria wycieku informacji / supply chain wewnętrzny.

### A01 Broken access control
- `/download/archive` dostępny bez auth — zamierzony „legacy gateway” w fabule boxa.

## Narzędzia (Kali)
```bash
# Reflected XSS (ręcznie)
curl -s "http://TARGET/?q=<script>alert(1)</script>" | grep -F '<script>'

# Dir bust (ukryte ścieżki)
gobuster dir -u http://TARGET/ -w /usr/share/wordlists/dirb/common.txt -s 200,301,302,403

# Skanery (jako user z uprawnieniami do ~/.config)
nikto -h http://TARGET
nuclei -u http://TARGET -tags misconfig,exposure
```

## Wniosek na Easy
Gdy WWW jest **marketingowa**, OWASP w przeglądarce często **odcina się szybko** — następny wektor to **inna usługa TCP** (tu **1515**) lub **kod z wycieku**.

Logi: `loot/xss-reflection-test.txt`, `loot/gobuster-common.txt`.