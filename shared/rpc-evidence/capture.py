#!/usr/bin/env python3
"""Read-only, stdout-only adapter for line 1's snapshot collector."""
import argparse
import json
import sys
import time
from urllib.parse import urlsplit

from rpc_snapshot import DEFAULT_RPC, rpc_call

# Intentionally small: no arbitrary RPC method, signing, account access or sends.
READS = {"eth_chainId", "eth_blockNumber", "eth_getBlockByNumber",
         "eth_getTransactionReceipt", "eth_getLogs", "eth_getBalance", "eth_call"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--method", choices=sorted(READS), default="eth_chainId")
    parser.add_argument("--params", default="[]")
    parser.add_argument("--rpc-url", default=DEFAULT_RPC)
    args = parser.parse_args()
    try:
        url = urlsplit(args.rpc_url)
        if url.scheme != "https" or not url.hostname or url.username or url.password:
            raise ValueError("RPC URL must be public HTTPS without credentials")
        params = json.loads(args.params)
        if not isinstance(params, list):
            raise ValueError("params must be an array")
        started = int(time.time())
        status, content_type, response = rpc_call(args.rpc_url, args.method, params, 15)
        print(json.dumps({"captured_at_unix": started, "rpc_url": args.rpc_url,
                          "http_status": status, "content_type": content_type,
                          "request": {"jsonrpc": "2.0", "id": 1,
                                      "method": args.method, "params": params},
                          "response": response}, indent=2))
        return 0
    except (ValueError, OSError) as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
