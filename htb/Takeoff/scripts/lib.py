"""Shared HTTP helpers for Takeoff scripts. No secrets in this file."""
from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

import urllib.error
import urllib.parse
import urllib.request
import http.cookiejar

DEFAULT_UA = "takeoff-lab/1.0"


def base_url() -> str:
    t = os.environ.get("TARGET", "").strip()
    if not t:
        raise SystemExit("export TARGET=<ip or takeoff.htb>")
    if t.startswith("http"):
        return t.rstrip("/")
    return f"http://{t}"


def cookie_jar_path() -> Path:
    return Path(os.environ.get("COOKIE_JAR", "cookies.txt"))


def opener(jar: http.cookiejar.MozillaCookieJar | None = None):
    if jar is None:
        p = cookie_jar_path()
        jar = http.cookiejar.MozillaCookieJar(str(p))
        if p.exists() and p.stat().st_size > 0:
            try:
                jar.load(ignore_discard=True, ignore_expires=True)
            except http.cookiejar.LoadError:
                pass
    o = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    o.jar = jar  # type: ignore[attr-defined]
    return o


def save_jar(o) -> None:
    p = cookie_jar_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    if not p.exists():
        p.write_text("# Netscape HTTP Cookie File\n")
    o.jar.save(filename=str(p), ignore_discard=True, ignore_expires=True)


def req(o, method: str, url: str, data: dict | None = None, headers: dict | None = None,
        timeout: int = 20):
    body = None
    hdrs = {"User-Agent": DEFAULT_UA, **(headers or {})}
    if data is not None:
        body = urllib.parse.urlencode(data, doseq=True).encode()
        hdrs.setdefault("Content-Type", "application/x-www-form-urlencoded")
    r = urllib.request.Request(url, data=body, headers=hdrs, method=method)
    try:
        with o.open(r, timeout=timeout) as resp:
            h = dict(resp.headers)
            h["Effective-Url"] = resp.geturl()
            return resp.status, h, resp.read()
    except urllib.error.HTTPError as e:
        h = dict(e.headers)
        return e.code, h, e.read()


def notes_from_pdf(pdf: bytes) -> str:
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        f.write(pdf)
        path = f.name
    try:
        text = subprocess.check_output(
            ["pdftotext", "-raw", path, "-"], text=True, errors="replace"
        )
    finally:
        os.unlink(path)
    m = re.search(r"Notes\n(.*?)(?:Scan QR|\Z)", text, re.S)
    return (m.group(1) if m else text).strip()
