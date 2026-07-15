# Connected (HTB) — zacznij tutaj

| | |
|--|--|
| **Status** | Ukończone (user + root) |
| **Kontekst HTB** | Maszyna **turniejowa Sezon 11** — praktycznie **brak publicznych writeupów** (stąd hinty z sieci / LinkedIn zamiast klasycznych WP) |
| **IP** | `10.129.245.100` — po resecie sprawdź `target.txt` |
| **Hosts** | `connected.htb`, `pbxconnect` |
| **Flagi** | `loot/copy-paste.txt` |

## Gdzie co jest

| Plik / folder | Po co |
|---------------|--------|
| **[ACCESS.md](ACCESS.md)** | **Jak wejść na maszynę** (SSH, webshell, GUI) — czytaj to zamiast szukać hasła SSH w loot |
| **[notes.md](notes.md)** | Przebieg ataku, wektory, skróty techniczne |
| **[edu/](edu/README.md)** | Tematy do nauki w wolnym czasie + ćwiczenia |
| `nmap/` | Skany |
| `scripts/` | Exploity i enum z Kali |
| `loot/` | Logi surowe, HTML, `loot/INDEX.md` |
| `loot/copy-paste.txt` | Flagi i credy **aplikacyjne** |

## Szybki replay (foothold)

```bash
cd ~/Desktop/htb/Connected/scripts
python3 enum_privesc.py          # nowy URL webshell w output
python3 ha_trigger_suid.py       # root (gdy moduł freepbx_ha + ha_trigger)
```

Root na tym boxie: **`ha_trigger` → `sysadmin_ha` → fałszywy moduł `freepbx_ha` → SUID bash** — opis w `edu/03-ha-trigger-suid.md`.