#!/usr/bin/env python3
"""Run ON the box as postgres (DISPLAY=:0). Openbox C-A-t → xterm → type command."""
from __future__ import annotations

import argparse
import os
import time

from Xlib import XK, X, display
from Xlib.ext import xtest

SHIFTED = set('~!@#$%^&*()_+{}|:"<>?')
KEYSYM = {
    " ": "space",
    "-": "minus",
    "/": "slash",
    ".": "period",
    "=": "equal",
    ",": "comma",
    ";": "semicolon",
    "`": "grave",
    "'": "apostrophe",
    "\\": "backslash",
    '"': "quotedbl",
    "&": "ampersand",
    ">": "greater",
    "<": "less",
    ":": "colon",
    "_": "underscore",
    "|": "bar",
    "!": "exclam",
    "(": "parenleft",
    ")": "parenright",
    "{": "braceleft",
    "}": "braceright",
    "$": "dollar",
    "#": "numbersign",
    "*": "asterisk",
    "+": "plus",
    "?": "question",
    "@": "at",
    "~": "asciitilde",
    "^": "asciicircum",
    "%": "percent",
}


def ks(d, name: str) -> int:
    code = d.keysym_to_keycode(XK.string_to_keysym(name))
    if not code:
        raise SystemExit(f"no keycode for {name}")
    return code


def tap(d, name: str, shift: bool = False) -> None:
    code = ks(d, name)
    if shift:
        xtest.fake_input(d, X.KeyPress, ks(d, "Shift_L"))
    xtest.fake_input(d, X.KeyPress, code)
    d.flush()
    time.sleep(0.012)
    xtest.fake_input(d, X.KeyRelease, code)
    if shift:
        xtest.fake_input(d, X.KeyRelease, ks(d, "Shift_L"))
    d.flush()
    time.sleep(0.014)


def type_str(d, s: str) -> None:
    for ch in s:
        if ch.isupper():
            tap(d, ch.lower(), shift=True)
        elif ch in SHIFTED:
            tap(d, KEYSYM[ch], shift=True)
        elif ch in KEYSYM:
            tap(d, KEYSYM[ch])
        elif ch.isalnum():
            tap(d, ch)
        else:
            raise SystemExit(f"unmapped {ch!r}")


def chord_cat(d) -> None:
    for n in ("Control_L", "Alt_L", "t"):
        xtest.fake_input(d, X.KeyPress, ks(d, n))
    d.flush()
    time.sleep(0.05)
    for n in ("t", "Alt_L", "Control_L"):
        xtest.fake_input(d, X.KeyRelease, ks(d, n))
    d.flush()


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--display", default=os.environ.get("DISPLAY", ":0"))
    p.add_argument("--cmd", required=True, help="typed into the new xterm")
    p.add_argument("--wait", type=float, default=1.4, help="seconds after C-A-t")
    args = p.parse_args()
    d = display.Display(args.display)
    chord_cat(d)
    time.sleep(args.wait)
    type_str(d, args.cmd)
    tap(d, "Return")
    print("injected", flush=True)


if __name__ == "__main__":
    main()
