#!/usr/bin/env python3
"""Capture one Ethereum JSON-RPC response as a portable offline snapshot."""

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


DEFAULT_RPC = "https://ethereum-rpc.publicnode.com"


def rpc_call(url, method, params, timeout):
    request_body = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    encoded = json.dumps(request_body, separators=(",", ":")).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=encoded,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "IdentityMD-Line1-RPC-Snapshot/1.0",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read()
        return response.status, response.headers.get("Content-Type", ""), json.loads(raw)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--method", default="eth_chainId", help="JSON-RPC method")
    parser.add_argument("--params", default="[]", help="JSON array of method parameters")
    parser.add_argument("--rpc-url", default=DEFAULT_RPC)
    parser.add_argument("--output", type=Path, help="write snapshot JSON here")
    parser.add_argument("--timeout", type=float, default=15.0)
    args = parser.parse_args()

    try:
        params = json.loads(args.params)
        if not isinstance(params, list):
            raise ValueError("--params must decode to a JSON array")
        started = time.time()
        status, content_type, response = rpc_call(args.rpc_url, args.method, params, args.timeout)
        snapshot = {
            "captured_at_unix": int(started),
            "rpc_url": args.rpc_url,
            "http_status": status,
            "content_type": content_type,
            "request": {"jsonrpc": "2.0", "id": 1, "method": args.method, "params": params},
            "response": response,
        }
        rendered = json.dumps(snapshot, indent=2, sort_keys=True) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
        else:
            sys.stdout.write(rendered)
    except (ValueError, OSError, urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        print(f"rpc-snapshot: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
