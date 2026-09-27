# Layover — Linux (airport / dual-homed)

Lab notes from an HTB machine. **No flags.** Keep box passwords local, out of git.

```
xrdp contractor (jumpbox only)
  → monitor-mode capture on passenger Wi-Fi
  → Craft CP (jenny) → SSTI CVE-2026-31857 → www-data
  → CRAFT_SECURITY_KEY decrypts htbairways_settings.mailRelayPassword
  → su - aporter  (Linux password ≠ SMTP space; use underscore)
  → CUPS 2.4.16 GHSA-c54j-2vqw-wpwp → sudoers overwrite → root
```

External ports on the jumpbox are only SSH + xrdp. The portal (`Craft CMS Solo 5.9.8`) is on the passenger Wi-Fi LAN and is **not** reachable from Kali `tun0`. Reverse shells from the portal must land on the jumpbox, not on Kali.

## 1. Jumpbox

Linux kiosk, hostname `airside-ws01`. Dual-homed: passenger Wi-Fi (open SSID) and an LXD segment. `contractor` has sudo and dumpcap. No `user.txt` / `root.txt` here — this host is only a pivot.

xrdp drive share is enough to drop scripts onto the kiosk (`thinclient_drives/share`).

## 2. Wi-Fi → Craft CP

Client isolation on the associated STA interface. Credential sniffing needs a **monitor-mode** NIC on the same channel as the AP, not the associated iface.

POST `/miles/login.php` is a decoy (always Blue Member). Real CP account is **Jenny** from the capture. Miles Gold / lounge is flavour, not the foothold.

Treat unauthenticated `/admin` grinding as a dead end (`generate-transform` patched, GraphQL 500).

## 3. www-data — CVE-2026-31857

Authenticated CP user, POST `/admin/actions/element-search/search`, `AuthorConditionRule.elementId` = Twig. Gadget:

```twig
{{ ['CMD']|filter('system') }}
```

Webroot `/var/www/portal/web`; `@dotenv` is `/var/www/portal/.env`. Copy `.env` into `/web/assets/` (nginx serves `/assets` statically; other webroot paths go to Craft 404).

Portal PHP **cannot** OOB to Kali. Background the reverse (`nohup`) to the jumpbox Wi-Fi address so the worker can return.

## 4. `.env` key → blob → aporter

Module `modules/htbairways` stores SMTP relay settings in `htbairways_settings`. The password column is **not** plaintext:

```php
$securityKey = Craft::$app->getConfig()->getGeneral()->securityKey;
$password = Craft::$app->getSecurity()
    ->decryptByKey(base64_decode($kv['mailRelayPassword']), $securityKey);
```

`securityKey` is `CRAFT_SECURITY_KEY` from `.env`. User field defaults to `aporter`. That Linux account exists on the portal (`/etc/passwd`).

Craft users table is only `admin` + `jenny` (bcrypt). There is no other encrypted OS secret in that settings table.

The decrypted blob has a **space**. `su` / `ssh` with the space fail. Replace the space with an underscore — that is the OS password. `su - aporter` from `www-data` is the intended hop (raw `nc` reverse has no TTY, so a successful `su` looks hung until you type `id`).

`sshd` still offers `password` from localhost; a wrong password is `Permission denied (publickey,password)`. Cloud-init `PasswordAuthentication no` in `sshd_config.d/60-*.conf` vs `yes` in `10-htb.conf` is noisy; the working hop is **`su`**, not a new SSH session from Kali.

`aporter` is **not** in sudoers yet (`may not run sudo on portal`).

## 5. Root — CUPS 2.4.16, GHSA-c54j-2vqw-wpwp

`cupsd` as root, `127.0.0.1:631`, `cups.sock` world-writable. `/run/cups/certs/0` is `root:root 0640` — you cannot `cat` the Local token.

Server: `CUPS/2.4.16`. Advisory: [GHSA-c54j-2vqw-wpwp](https://github.com/OpenPrinting/cups/security/advisories/GHSA-c54j-2vqw-wpwp) (patched 2.4.17).

`CUPS-Create-Local-Printer` is not an admin-limited op. Bait `device-uri` = `ipp://127.0.0.1:<highport>/ipp/print`. Validation thread connects as `@SYSTEM`, libcups sends `Authorization: Local` from `certs/0`. Answer `401` with `WWW-Authenticate: Local trc="y"` first, steal the token on the retry.

Admin `/admin/` + token:

1. Create a **temporary** queue with `file:///etc/sudoers.d/<user>-pwn` (normal `FileDevice` policy rejects this on `CUPS-Add-Modify-Printer` if you supply the URI there).
2. Persist without resending `device-uri`: `ppd-name=raw`, `printer-is-shared=true`.
3. `Print-Job` `application/vnd.cups-raw` (gzip) with a sudoers line. Scheduler opens the URI as root (`O_WRONLY|O_CREAT|O_TRUNC`). Racey — retry.

PoC: [`scripts/ghsa_c54j_cups_local.py`](scripts/ghsa_c54j_cups_local.py)

Then `sudo -n id` / `sudo -n -i`. Basic auth on `/admin/` as `aporter` is **403 Forbidden** (not in `@SYSTEM`); the Local token is the whole point.

## Notes

- OOB: portal → jumpbox Wi-Fi IP, never Kali `tun0`.
- Do not commit `.env`, flags, or the plaintext OS/SMTP strings.
- Ligolo is optional; the portal is already reachable from the jumpbox.
