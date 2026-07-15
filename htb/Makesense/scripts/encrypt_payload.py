#!/usr/bin/env python3
"""AES-GCM payload matching webagency whisper-wrapper.js (SHA-256 key, 12-byte IV prepended)."""
import json
import sys
import base64
import hashlib
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

KEY_PASS = b"bLs6z8iv3gWpsvyeabFosDjb4YQe7jdU13rI"


def encrypt_payload(transcription: str, summary: str) -> str:
    key = hashlib.sha256(KEY_PASS).digest()
    iv = os.urandom(12)
    aes = AESGCM(key)
    ct = aes.encrypt(
        iv,
        json.dumps({"transcription": transcription, "summary": summary}).encode(),
        None,
    )
    return base64.b64encode(iv + ct).decode()


if __name__ == "__main__":
    t = sys.argv[1] if len(sys.argv) > 1 else "test transcription"
    s = sys.argv[2] if len(sys.argv) > 2 else "test summary"
    print(encrypt_payload(t, s))