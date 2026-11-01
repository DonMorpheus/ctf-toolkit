#!/usr/bin/env python3
"""Register, add a 4242 test card, book cheapest Coach HTB→GLW, print PNR."""
from __future__ import annotations

import os
import re
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import base_url, opener, req, save_jar  # noqa: E402


def main() -> None:
    email = os.environ.get("EMAIL", "lab@example.invalid")
    password = os.environ.get("PASSWORD", "ChangeMe1!")
    name = os.environ.get("NAME", "Lab User")
    base = base_url()
    o = opener()

    print(f"[*] sign-up {email}")
    req(o, "POST", f"{base}/sign-up", {
        "name": name, "email": email, "password": password, "terms": "on",
    })
    st, hdr, _ = req(o, "POST", f"{base}/sign-in", {"email": email, "password": password})
    save_jar(o)
    loc = hdr.get("Location") or hdr.get("location") or ""
    print(f"    login {st} -> {loc or '(cookie jar saved)'}")

    print("[*] payment-cards 4242…4242")
    req(o, "POST", f"{base}/payment-cards", {
        "pan": "4242424242424242",
        "cardholder_name": name,
        "exp_month": "12",
        "exp_year": str(date.today().year + 2),
    })

    day = (date.today() + timedelta(days=1)).isoformat()
    print(f"[*] search HTB -> GLW {day}")
    _, _, body = req(o, "GET", f"{base}/search/results?origin=HTB&destination=GLW&date={day}&pax=1&class=Coach")
    html = body.decode("utf-8", "replace")
    sched = re.findall(r"/schedules/(\d+)", html)
    if not sched:
        raise SystemExit("no schedules — try another date")
    sid = sched[0]
    _, _, shtml = req(o, "GET", f"{base}/schedules/{sid}")
    m = re.search(
        r'data-tier="Coach"[^>]*>\s*<input type="checkbox" name="seat_ids" value="(\d+)"',
        shtml.decode("utf-8", "replace"),
    )
    if not m:
        raise SystemExit("no Coach seat")
    seat = m.group(1)
    print(f"    schedule {sid} seat_id {seat}")

    st, hdr, _ = req(o, "POST", f"{base}/book/start", {"schedule_id": sid, "seat_ids": seat})
    loc = hdr.get("Location") or hdr.get("location") or hdr.get("Effective-Url") or ""
    pnr_m = re.search(r"/book/([A-Z0-9]+)/", loc)
    if not pnr_m:
        raise SystemExit(f"no PNR in {st} {loc}")
    pnr = pnr_m.group(1)
    print(f"[+] PNR {pnr}")

    req(o, "POST", f"{base}/book/{pnr}/passengers", {
        "full_name": name,
        "dob": "1995-01-15",
        "id_type": "passport",
        "id_number": "AB1234567",
    })
    st, hdr, _ = req(o, "POST", f"{base}/book/{pnr}/payment", {"payment_card_id": "1"})
    save_jar(o)
    print(f"    pay {st} {hdr.get('Location') or hdr.get('location')}")
    print(f"[+] booked  PNR={pnr}  cookie jar={os.environ.get('COOKIE_JAR', 'cookies.txt')}")
    print("    next:  python3 02-ssti-read.py /proc/self/environ")


if __name__ == "__main__":
    main()
