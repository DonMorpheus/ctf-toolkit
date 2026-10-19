# Autopilot scripts

Fill `../secrets.env` from `../secrets.example.env`. Then:

```bash
chmod +x *.sh *.py
./replay.sh foothold
./replay.sh lpe
./replay.sh chisel
./replay.sh dcpivot
```

`07-ntlmrelayx.sh` must stay in a TTY (stdin). `--smb-port 9445`, SOCKS `1082`.
