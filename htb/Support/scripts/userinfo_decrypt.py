#!/usr/bin/env python3
"""
Decrypt the static LDAP password cipher from HTB Support's UserInfo.exe.

Algorithm (from decompiled Protected.getPassword):
  plain[i] = b64decode(cipher)[i] XOR key[i % len(key)] XOR 0xDF
  key = b"armando"

Usage:
  python3 userinfo_decrypt.py
  python3 userinfo_decrypt.py --cipher 'BASE64...'
"""
from __future__ import annotations

import argparse
import base64
import sys


DEFAULT_CIPHER = "0Nv32PTwgYjzg9/8j5TbmvPd3e7WhtWWyuPsyO76/Y+U193E"
DEFAULT_KEY = b"armando"


def decrypt(cipher_b64: str, key: bytes = DEFAULT_KEY) -> str:
    data = base64.b64decode(cipher_b64)
    out = bytes((data[i] ^ key[i % len(key)] ^ 0xDF) for i in range(len(data)))
    return out.decode("latin-1")


def main() -> int:
    p = argparse.ArgumentParser(description="UserInfo.exe password decrypt (Support lab)")
    p.add_argument("--cipher", default=DEFAULT_CIPHER, help="Base64 ciphertext")
    p.add_argument("--key", default=DEFAULT_KEY.decode(), help="ASCII XOR key (default armando)")
    args = p.parse_args()
    try:
        plain = decrypt(args.cipher, args.key.encode("ascii"))
    except Exception as e:
        print(f"[-] {e}", file=sys.stderr)
        return 1
    print(plain)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
