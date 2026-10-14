#!/usr/bin/env python3
"""Validate a mainnet chain-ID snapshot offline using line 2's checker."""
import argparse
import json
import sys
from pathlib import Path

from json_contract import load, prepare, validate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot")
    args = parser.parse_args()
    try:
        contract = prepare(load(str(Path(__file__).with_name("chain-id.contract.json"))))
        errors = validate(load(args.snapshot), contract)
        print(json.dumps({"valid": not errors, "errors": errors,
                          "scope": "Ethereum mainnet chain-ID snapshot structure; not provider authenticity or current chain state"}, indent=2))
        return 1 if errors else 0
    except (ValueError, OSError, RecursionError) as exc:
        print(json.dumps({"error": str(exc)}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
