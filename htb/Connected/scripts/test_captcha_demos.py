#!/usr/bin/env python3
"""Test StealthBrowser na publicznych stronach demo CAPTCHA (legalne, bez ataku)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from browser.stealth_browser import StealthBrowser

DEMOS = [
    ("Google reCAPTCHA v2 demo", "https://www.google.com/recaptcha/api2/demo"),
    ("reCAPTCHA appspot demo", "https://recaptcha-demo.appspot.com/recaptcha-v2-checkbox.php"),
    ("2Captcha reCAPTCHA v2 demo", "https://2captcha.com/demo/recaptcha-v2"),
    ("Cloudflare Turnstile (managed)", "https://demo.turnstile.workers.dev/"),
]


def main() -> None:
    headless = "--gui" not in sys.argv
    browser = StealthBrowser()
    out_dir = ROOT / "loot" / "captcha-tests"
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        browser.launch(headless=headless)
        for name, url in DEMOS:
            print(f"\n=== {name} ===\n    {url}")
            try:
                browser.page.goto(url, wait_until="domcontentloaded", timeout=45000)
                browser.page.wait_for_timeout(3000)
                recaptcha = browser.page.locator("iframe[src*='recaptcha']").count()
                turnstile = browser.page.locator(
                    "iframe[src*='challenges.cloudflare'], div.cf-turnstile"
                ).count()
                print(f"    iframe recaptcha: {recaptcha}, turnstile widgets: {turnstile}")
                browser.solve_captcha_if_present()
                safe = url.split("//")[1].replace("/", "_")[:60]
                path = out_dir / f"{safe}.html"
                path.write_text(browser.page.content(), encoding="utf-8")
                print(f"    zapisano: {path}")
            except Exception as e:
                print(f"    BŁĄD: {e}")
    finally:
        browser.close()
    print("\n[+] Koniec. Sprawdź loot/captcha-tests/")


if __name__ == "__main__":
    main()