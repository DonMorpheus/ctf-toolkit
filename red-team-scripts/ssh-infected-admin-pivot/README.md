# ssh-infected-admin-pivot

Skrypty do write-upu **Admin SSH to infected machine? His computer gone.**

| Plik | Kiedy |
|------|--------|
| `pivot_agent_to_admin.sh` | Admin użył **`ssh -A`** |
| `pivot_proc_root_key.sh` | Admin **`ssh -i`** bez agenta, klient na tym samym hoście |
| `pivot_infected_admin.sh` | Auto: agent → proc |

```bash
chmod +x *.sh
export VICTIM_USER=legacy ADMIN_USER=admin
sudo ./pivot_infected_admin.sh 172.17.0.2
```

Zmienne: `SSH_SERVER_PORT`, `ADMIN_SSH_PORT`, `REMOTE_CMD`, `OUT_KEY`.