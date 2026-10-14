#!/usr/bin/env python3
"""Read-only Ethereum transaction settlement evidence. Standard library only."""
import argparse
import json
import re
import sys
import urllib.error
import urllib.request

RPC_URL = "https://ethereum-rpc.publicnode.com"
ZTO = "0xd782bdea4ef02a0bd391eb9089470c8080f0a68e"
TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"


class EvidenceError(ValueError):
    pass


def hash32(value):
    if not isinstance(value, str) or not re.fullmatch(r"0x[0-9a-fA-F]{64}", value):
        raise EvidenceError("expected a 32-byte hash")
    return value.lower()


def quantity(value):
    if not isinstance(value, str) or not re.fullmatch(r"0x(?:0|[1-9a-fA-F][0-9a-fA-F]*)", value):
        raise EvidenceError("invalid RPC hexadecimal quantity")
    return int(value, 16)


class RPC:
    def __init__(self, url):
        if not url.startswith(("https://", "http://")):
            raise EvidenceError("RPC URL must use HTTP or HTTPS")
        self.url = url
        self.sequence = 0

    def call(self, method, params):
        # Only these read methods are available, even to callers importing this module.
        if method not in {"eth_chainId", "eth_getBlockByNumber", "eth_getTransactionReceipt", "eth_getLogs"}:
            raise EvidenceError("method is not an allowed read")
        self.sequence += 1
        request = urllib.request.Request(
            self.url,
            data=json.dumps({"jsonrpc": "2.0", "id": self.sequence, "method": method, "params": params}).encode(),
            headers={"Content-Type": "application/json", "User-Agent": "Pepeolithic-Line3-Settlement/1.0"},
        )
        with urllib.request.urlopen(request, timeout=20) as response:
            raw = response.read(4_000_001)
        if len(raw) > 4_000_000:
            raise EvidenceError("RPC response exceeds size limit")
        result = json.loads(raw)
        if not isinstance(result, dict) or result.get("id") != self.sequence or result.get("jsonrpc") != "2.0":
            raise EvidenceError("invalid RPC response envelope")
        if "error" in result:
            raise EvidenceError("RPC error: " + json.dumps(result["error"]))
        if "result" not in result:
            raise EvidenceError("RPC response has no result")
        return result["result"]


def block(rpc, tag):
    value = rpc.call("eth_getBlockByNumber", [tag, False])
    if not isinstance(value, dict):
        raise EvidenceError("block unavailable for " + tag)
    number = quantity(value.get("number"))
    if tag.startswith("0x") and number != quantity(tag):
        raise EvidenceError("RPC returned the wrong block number")
    return {"number": number, "hash": hash32(value.get("hash"))}


def latest_zto_transfer(rpc, lookback=2048):
    if not isinstance(lookback, int) or not 1 <= lookback <= 16384:
        raise EvidenceError("lookback must be 1..16384")
    if quantity(rpc.call("eth_chainId", [])) != 1:
        raise EvidenceError("ZTO discovery requires Ethereum mainnet")
    head = block(rpc, "latest")["number"]
    floor = max(0, head - lookback + 1)
    end = head
    while end >= floor:
        start = max(floor, end - 511)
        logs = rpc.call("eth_getLogs", [{"address": ZTO, "topics": [TRANSFER], "fromBlock": hex(start), "toBlock": hex(end)}])
        if not isinstance(logs, list):
            raise EvidenceError("invalid logs response")
        candidates = []
        for log in logs:
            if not isinstance(log, dict):
                raise EvidenceError("invalid log")
            if log.get("removed"):
                continue
            number = quantity(log.get("blockNumber"))
            address, topics = log.get("address"), log.get("topics")
            if not isinstance(address, str) or not isinstance(topics, list) or not topics or not isinstance(topics[0], str):
                raise EvidenceError("malformed transfer log filter fields")
            if not start <= number <= end or address.lower() != ZTO or topics[0].lower() != TRANSFER:
                raise EvidenceError("RPC returned a log outside the requested filter")
            candidates.append((number, quantity(log.get("logIndex")), hash32(log.get("transactionHash"))))
        if candidates:
            return max(candidates)[2]
        end = start - 1
    raise EvidenceError("no ZTO transfer in the bounded window; supply a transaction hash or increase --lookback")


def inspect(rpc, tx_hash, minimum=12, require_finalized=False):
    tx_hash = hash32(tx_hash)
    if not isinstance(minimum, int) or minimum < 1:
        raise EvidenceError("minimum confirmations must be positive")
    chain_id = quantity(rpc.call("eth_chainId", []))
    if chain_id != 1:
        raise EvidenceError("this tool is scoped to Ethereum mainnet (chain ID 1)")
    head = block(rpc, "latest")
    receipt = rpc.call("eth_getTransactionReceipt", [tx_hash])
    report = {"chainId": chain_id, "transactionHash": tx_hash, "head": head,
              "policy": {"minimumConfirmations": minimum, "requireFinalized": require_finalized},
              "settled": False}
    if receipt is None:
        report.update(state="not_included", reason="No receipt: transaction may be pending, unknown, or dropped.")
        return report
    if not isinstance(receipt, dict) or hash32(receipt.get("transactionHash")) != tx_hash:
        raise EvidenceError("receipt transaction hash does not match the request")
    height = quantity(receipt.get("blockNumber"))
    inclusion_hash = hash32(receipt.get("blockHash"))
    status = quantity(receipt.get("status"))
    if status not in (0, 1):
        raise EvidenceError("invalid receipt execution status")
    canonical = block(rpc, hex(height))
    report.update(inclusion={"number": height, "hash": inclusion_hash}, execution="succeeded" if status else "reverted")
    if height > head["number"] or canonical["hash"] != inclusion_hash:
        report.update(state="unstable", reason="Receipt is inconsistent with the sampled canonical head.")
        return report
    # Finalized may be unsupported. Never equate an unsupported tag with finality.
    try:
        finalized = block(rpc, "finalized")
        if finalized["number"] > head["number"]:
            raise EvidenceError("finalized block is ahead of the sampled head")
        if block(rpc, hex(finalized["number"])) != finalized:
            raise EvidenceError("finalized block is not canonical")
        report["finalizedHead"] = finalized
        is_finalized = height <= finalized["number"]
    except (EvidenceError, urllib.error.URLError, TimeoutError) as exc:
        is_finalized = None
        report["finalityError"] = str(exc)
    # Check both anchors again: do not accept a reorg occurring during collection.
    if block(rpc, hex(height)) != canonical or block(rpc, hex(head["number"])) != head:
        report.update(state="unstable", reason="Canonical chain changed during the check.")
        return report
    confirmations = head["number"] - height + 1
    report.update(confirmations=confirmations, finalized=is_finalized)
    if not status:
        report.update(state="reverted", reason="Transaction executed but reverted.")
    elif confirmations < minimum:
        report.update(state="confirming", reason="Confirmation threshold has not been reached.")
    elif require_finalized and is_finalized is not True:
        report.update(state="awaiting_finality", reason="Finality policy has not been proven.")
    else:
        report.update(state="settled", settled=True, reason="Execution and canonical-chain evidence meet the selected policy.")
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--tx", help="Ethereum transaction hash")
    source.add_argument("--latest-zto-transfer", action="store_true", help="discover a recent real ZTO transfer")
    parser.add_argument("--rpc", default=RPC_URL)
    parser.add_argument("--confirmations", type=int, default=12)
    parser.add_argument("--require-finalized", action="store_true")
    parser.add_argument("--lookback", type=int, default=2048, help="ZTO discovery blocks, max 16384")
    args = parser.parse_args(argv)
    if args.confirmations < 1 or not 1 <= args.lookback <= 16384:
        parser.error("confirmations must be positive and lookback must be 1..16384")
    try:
        rpc = RPC(args.rpc)
        tx = latest_zto_transfer(rpc, args.lookback) if args.latest_zto_transfer else args.tx
        report = inspect(rpc, tx, args.confirmations, args.require_finalized)
        if args.latest_zto_transfer:
            report["discovery"] = {"token": ZTO, "lookbackBlocks": args.lookback}
        print(json.dumps(report, indent=2))
        return 0 if report["settled"] else 1
    except (EvidenceError, urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
        print(json.dumps({"settled": False, "state": "error", "reason": str(exc)}, indent=2))
        return 2


if __name__ == "__main__":
    sys.exit(main())
