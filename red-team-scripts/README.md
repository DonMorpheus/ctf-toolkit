# Red Team Scripts

Skrypty TTP (lab / authorized red team) — obok `htb/` w [ctf-toolkit](https://github.com/DonMorpheus/ctf-toolkit).

| Scenariusz | Dokument | Skrypty |
|------------|----------|---------|
| **Pułapka `-A` only** (EN message, ForceCommand) → pivot na admin PC | [WRITEUP-ssh-agent-forward-trap.md](./WRITEUP-ssh-agent-forward-trap.md) | `ssh-agent-forward-trap/` |
| Admin SSH na skompromitowany host → pivot na jego maszynę | [WRITEUP-admin-ssh-infected-machine.md](./WRITEUP-admin-ssh-infected-machine.md) | `ssh-infected-admin-pivot/` |
| **Bez `-A`:** SSH `-R` RemoteForward → jego sshd u ciebie | [WRITEUP-admin-ssh-remote-forward-no-agent.md](./WRITEUP-admin-ssh-remote-forward-no-agent.md) | `pivot_via_remote_forward.sh` |
| Admin `nc` na zainfekowany serwer → reverse shell z jego PC | [WRITEUP-admin-nc-infected-reverse.md](./WRITEUP-admin-nc-infected-reverse.md) | lab: `htb/ttp-nc-lab` lokalnie |

**Zasada:** tylko scope, który kontrolujesz (własny lab, HTB, pentest z umową).