#!/usr/bin/env python3
"""Stealth WWW probe — wymaga działającego Playwright/Patchright (pip install -r requirements.txt)."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from browser.stealth_browser import StealthBrowser  # noqa: E402

IP = sys.argv[1] if len(sys.argv) > 1 else "10.129.46.7"
OUT = ROOT / "loot" / "stealth-scan-latest.json"
URLS = [
    "http://connected.htb/",
    "http://connected.htb/admin/",
    "https://connected.htb/",
    "http://pbxconnect/",
]

def main() -> None:
    results = []
    b = StealthBrowser()
    try:
        b.launch(headless=True)
        for url in URLS:
            entry = {"url": url, "status": None, "server": None, "title": None, "error": None}
            try:
                resp = b.page.goto(url, wait_until="domcontentloaded", timeout=20000)
                if resp:
                    entry["status"] = resp.status
                    h = resp.headers
                    entry["server"] = h.get("server") or h.get("Server")
                entry["title"] = b.page.title()
            except Exception as e:
                entry["error"] = str(e)[:400]
            results.append(entry)
            print(entry)
    finally:
        b.close()
    OUT.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"saved {OUT}")

if __name__ == "__main__":
    main()