# Paperwork (HackTheBox — Easy, Linux)

Release Arena EU · custom **LPD** + **PJL** / printer stack on Ubuntu.

| | |
|--|--|
| **Scripts** | [`paperwork/`](paperwork/) |
| **Focus** | LPD command injection → archivist pivot → `mgmt.sock` / SCM_RIGHTS |

High-level chain (no spoilers): foothold on **1515**, localhost **9100**, then Linux privesc via management daemon — not a public web admin panel.

Script index: [`paperwork/README.md`](paperwork/README.md).