# Paperwork — edu

Materiały do nauki przy i po boxie. Po solve pełny opis jest w **`15-podrecznik-po-solve.md`**.

## Ścieżka czytania (rekomendowana)

1. Recon: `01` → `06`
2. Foothold: `03`, `04`, `07`
3. Pivot: `08`, `09`, `12`, `11`
4. User / SSH: `09`, `10`
5. Root: `13`, `14`, **`16`**
6. Powtórka + ćwiczenia: **`15`**, **`17`**

## Spis plików

| Plik | Temat |
|------|--------|
| [01-nginx-recon-stack.md](01-nginx-recon-stack.md) | nginx jako reverse proxy — rozpoznanie stacku |
| [02-owasp-passive-active-easy.md](02-owasp-passive-active-easy.md) | Szybki OWASP na cienkiej stronie |
| [03-rfc1179-lpd-basics.md](03-rfc1179-lpd-basics.md) | RFC 1179, kolejka, port 1515 |
| [04-source-leak-zip.md](04-source-leak-zip.md) | Wyciek kodu przez `/download/archive` |
| [05-vhost-enumeration-wynik.md](05-vhost-enumeration-wynik.md) | Subdomeny — brak ukrytego vhostu |
| [06-co-to-za-strona-intranet.md](06-co-to-za-strona-intranet.md) | Intranet, LPD, sens „legacy gateway” |
| [07-lpd-exploit-msf-vs-custom.md](07-lpd-exploit-msf-vs-custom.md) | MSF vs własny klient LPD |
| [08-lp-to-archivist-chain.md](08-lp-to-archivist-chain.md) | lp, daemon, mgmt.sock — łańcuch |
| [09-archivist-jak-wejsc.md](09-archivist-jak-wejsc.md) | Wejście na archivist (PJL / SSH) |
| [10-inne-opcje-pivot.md](10-inne-opcje-pivot.md) | Co nie działa / kolejność kroków |
| [11-easy-bez-modulu.md](11-easy-bez-modulu.md) | Dlaczego nie „dodajesz modułu” |
| [12-pjl-path-escape.md](12-pjl-path-escape.md) | PJL, `../`, zapis klucza |
| [13-root-jako-archivist.md](13-root-jako-archivist.md) | Root po user — `su` + mgmt |
| [14-privesc-z-ssh-archivist.md](14-privesc-z-ssh-archivist.md) | Enum privesc z SSH |
| **[15-podrecznik-po-solve.md](15-podrecznik-po-solve.md)** | **Pełny łańcuch po solve** |
| **[16-unix-socket-scm-rights.md](16-unix-socket-scm-rights.md)** | **SCM_RIGHTS, mgmt.sock** |
| **[17-cwiczenia-kali.md](17-cwiczenia-kali.md)** | **Ćwiczenia offline na Kali** |

Opcjonalnie ogólna lektura APT: `~/Desktop/htb/_template/edu/READING-apt-level.md`.

**Stan boxa:** `../notes.md`, `../loot/`, `../ACCESS.md`.