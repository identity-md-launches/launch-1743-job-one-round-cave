#!/usr/bin/env python3
"""Capture one Ethereum JSON-RPC response as a portable offline snapshot."""

import json
import urllib.error
import urllib.request
from urllib.parse import urlsplit


DEFAULT_RPC = "https://ethereum-rpc.publicnode.com"


def rpc_call(url, method, params, timeout):
    allowed = {"eth_chainId", "eth_blockNumber", "eth_getBlockByNumber",
               "eth_getTransactionReceipt", "eth_getLogs", "eth_getBalance", "eth_call"}
    if method not in allowed:
        raise ValueError("method is not an allowed public read")
    parts = urlsplit(url)
    if parts.scheme != "https" or not parts.hostname or parts.username or parts.password:
        raise ValueError("RPC URL must be public HTTPS without credentials")
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
    # Disable proxy discovery so the adapter needs no environment settings.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(request, timeout=timeout) as response:
        raw = response.read(1_000_001)
        if len(raw) > 1_000_000:
            raise ValueError("RPC response exceeds 1 MB")
        return response.status, response.headers.get("Content-Type", ""), json.loads(raw)
