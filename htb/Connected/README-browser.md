# Stealth browser (HTB)

## Setup
```bash
cd ~/Desktop/htb/10.129.45.151
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
# opcjonalnie patchright browsers:
patchright install chromium
```

## Uruchomienie
Upewnij się, że w `/etc/hosts` jest:
`10.129.45.151 connected.htb pbxconnect`

```bash
source .venv/bin/activate
python main.py
```

`USE_PATCHRIGHT=0` — czysty Playwright zamiast Patchright.

## Uwagi (Ania)
- Na Kali bez GUI ustaw `headless=True` lub `DISPLAY` (X11).
- `undetected-chromedriver` = Selenium/Chrome; tu głównie Playwright/Patchright.
- Turnstile/reCAPTCHA v3: wstrzyknięcie tokenu z 2Captcha — osobny hook w `solve_captcha_if_present`.