#!/usr/bin/env python3
"""Decrypt mRemoteNG 1.76+ AES-GCM passwords (confCons.xml).

Blob = salt(16) || nonce(16) || ciphertext || tag(16)
key  = PBKDF2-HMAC-SHA1(master, salt, iterations=1000, dkLen=32)
AAD  = salt  (MAC fails without this)

Lab / education only. Default master is the historic mRemoteNG value.
"""
from __future__ import annotations

import argparse
import base64
import sys
import xml.etree.ElementTree as ET

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend


def derive(master: str, salt: bytes, iterations: int = 1000) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA1(),
        length=32,
        salt=salt,
        iterations=iterations,
        backend=default_backend(),
    )
    return kdf.derive(master.encode("utf-8"))


def decrypt_blob(b64: str, master: str = "mR3m", iterations: int = 1000) -> str:
    data = base64.b64decode(b64)
    if len(data) < 48:
        raise ValueError("blob too short")
    salt, nonce, rest = data[:16], data[16:32], data[32:]
    key = derive(master, salt, iterations)
    pt = AESGCM(key).decrypt(nonce, rest, salt)
    return pt.decode("utf-8")


def from_xml(path: str, master: str) -> None:
    tree = ET.parse(path)
    root = tree.getroot()
    iters = int(root.attrib.get("KdfIterations", "1000"))
    for node in root.iter():
        if node.tag.endswith("Node") or "Password" in node.attrib:
            name = node.attrib.get("Name", "")
            user = node.attrib.get("Username", "")
            blob = node.attrib.get("Password", "")
            if not blob:
                continue
            try:
                pw = decrypt_blob(blob, master, iters)
            except Exception as e:
                print(f"{name}\t{user}\tFAIL\t{e}")
                continue
            print(f"{name}\t{user}\tOK")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("blob_or_xml", help="Base64 blob or path to confCons.xml")
    p.add_argument("-p", "--master", default="mR3m")
    args = p.parse_args()
    target = args.blob_or_xml
    if target.endswith(".xml"):
        from_xml(target, args.master)
        return 0
    print(decrypt_blob(target, args.master))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as e:
        print(e, file=sys.stderr)
        sys.exit(1)
