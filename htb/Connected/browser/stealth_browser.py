"""Playwright / Patchright browser z podstawowym stealth pod panele WWW (HTB)."""
from __future__ import annotations

import os
import random
import time
from typing import Optional

# Patchright = fork Playwright pod mniejszą detekcję; fallback na playwright
try:
    if os.environ.get("USE_PATCHRIGHT", "1") == "1":
        from patchright.sync_api import sync_playwright
    else:
        from playwright.sync_api import sync_playwright
except ImportError:
    from playwright.sync_api import sync_playwright

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
]


class StealthBrowser:
    def __init__(self) -> None:
        self._pw = None
        self.browser = None
        self.context = None
        self.page = None

    def launch(
        self,
        headless: bool = False,
        proxy: Optional[dict] = None,
        extra_hosts: Optional[dict] = None,
    ):
        """
        headless=False — widać okno (debug logowania FreePBX/UCP).
        extra_hosts: np. {"connected.htb": "10.129.45.151"}
        """
        self._pw = sync_playwright().start()
        launch_args = [
            "--no-sandbox",
            "--disable-blink-features=AutomationControlled",
            "--disable-extensions",
        ]
        self.browser = self._pw.chromium.launch(headless=headless, args=launch_args)

        ctx_opts = {
            "viewport": {"width": 1920, "height": 1080},
            "user_agent": random.choice(USER_AGENTS),
            "locale": "pl-PL",
            "ignore_https_errors": True,
        }
        if proxy:
            ctx_opts["proxy"] = proxy
        self.context = self.browser.new_context(**ctx_opts)
        if extra_hosts:
            # Playwright 1.38+: route przez hosts w /etc/hosts na Kali; tu dokumentacja
            pass
        self.page = self.context.new_page()
        self._stealth_inject()
        return self.page

    def _stealth_inject(self) -> None:
        self.page.add_init_script(
            """
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3]});
            """
        )

    def human_move(self, selector: str) -> None:
        loc = self.page.locator(selector).first
        box = loc.bounding_box()
        if not box:
            return
        x = box["x"] + random.uniform(5, min(30, box["width"] - 5))
        y = box["y"] + random.uniform(5, min(30, box["height"] - 5))
        self.page.mouse.move(x, y, steps=random.randint(8, 15))
        time.sleep(random.uniform(0.3, 0.8))
        self.page.mouse.click(x, y)

    def solve_captcha_if_present(self) -> None:
        if self.page.locator("iframe[src*='recaptcha']").count() > 0:
            print("[stealth] reCAPTCHA — próba checkbox...")
            try:
                frame = self.page.frame_locator("iframe[src*='recaptcha']").first
                frame.locator(".recaptcha-checkbox-border").click(timeout=5000)
                time.sleep(8)
            except Exception:
                pass
        if self.page.locator("iframe[src*='challenges.cloudflare']").count() > 0:
            print("[stealth] Cloudflare Turnstile — czekam / ewentualnie 2Captcha token")

    def go_to_and_scrape(self, url: str, wait_until: str = "domcontentloaded") -> str:
        self.page.goto(url, wait_until=wait_until)
        time.sleep(random.uniform(2, 4))
        self.solve_captcha_if_present()
        return self.page.content()

    def close(self) -> None:
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self._pw:
            self._pw.stop()