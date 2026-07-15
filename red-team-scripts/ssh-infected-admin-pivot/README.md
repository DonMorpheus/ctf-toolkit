# ssh-infected-admin-pivot

Skrypty do write-upu **Admin SSH to infected machine? His computer gone.**

| Plik | Kiedy |
|------|--------|
| `pivot_agent_to_admin.sh` | Admin użył **`ssh -A`** |
| `pivot_proc_root_key.sh` | Admin **`ssh -i`** bez agenta, klient na tym samym hoście |
| `pivot_infected_admin.sh` | Auto: agent → proc |
| `watch_ssh_client_pivot.sh` | **Persistence:** loop na nowe PID `ssh` klienta |
| `pivot_via_remote_forward.sh` | **Bez `-A`:** tunel `ssh -R` → jego port 22 na localhost |
| `post_pivot_admin_host.sh` | Po wejściu na PC admina — uruchom `remote_on_admin_host.sh`, zapis do loot |
| `post_pivot_via_agent.sh` | Agent pivot + zbieranie na adminie w jednym |

```bash
chmod +x *.sh
export VICTIM_USER=legacy ADMIN_USER=admin
sudo ./pivot_infected_admin.sh 172.17.0.2
sudo ./watch_ssh_client_pivot.sh 172.17.0.2   # w tle / systemd (lab)
```

Zmienne: `SSH_SERVER_PORT`, `ADMIN_SSH_PORT`, `REMOTE_CMD`, `OUT_KEY`, `INTERVAL`, `STATE_FILE`.

Write-up (sekcja persistence): [WRITEUP-admin-ssh-infected-machine.md](../WRITEUP-admin-ssh-infected-machine.md)

Wymuszenie `-A` na serwerze (pułapka): [WRITEUP-ssh-agent-forward-trap.md](../WRITEUP-ssh-agent-forward-trap.md) + [../ssh-agent-forward-trap/](../ssh-agent-forward-trap/)