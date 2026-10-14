"""Deterministic policy and reorg tests. No network or wallet required."""
import hashlib
import unittest

from settlement import EvidenceError, RPC, block, inspect, latest_zto_transfer, quantity, ZTO, TRANSFER


def h(label):
    return "0x" + hashlib.sha256(label.encode()).hexdigest()


TX = h("synthetic transaction for unit tests")


class FakeRPC:
    def __init__(self, height=90, head=100, final=95, status=1, mode=None):
        self.height, self.head, self.final, self.status = height, head, final, status
        self.mode = mode
        self.reads = {}
        self.requests = []

    def call(self, method, params):
        self.requests.append((method, params))
        if method == "eth_chainId":
            return "0x2" if self.mode == "wrong_chain" else "0x1"
        if method == "eth_getTransactionReceipt":
            if self.mode == "missing":
                return None
            return {"transactionHash": h("wrong") if self.mode == "wrong_tx" else TX,
                    "blockNumber": hex(self.height), "blockHash": h(str(self.height)), "status": hex(self.status)}
        if method == "eth_getBlockByNumber":
            tag = params[0]
            if tag == "finalized" and self.mode == "unsupported_finality":
                raise EvidenceError("unsupported tag")
            number = self.head if tag == "latest" else self.final if tag == "finalized" else int(tag, 16)
            self.reads[tag] = self.reads.get(tag, 0) + 1
            digest = h(str(number))
            if self.mode == "orphan" and number == self.height:
                digest = h("other chain")
            if self.mode == "reorg" and tag == hex(self.height) and self.reads[tag] > 1:
                digest = h("changed during collection")
            if self.mode == "head_reorg" and tag == hex(self.head):
                digest = h("head changed during collection")
            if self.mode == "wrong_number" and tag.startswith("0x"):
                number += 1
            return {"number": hex(number), "hash": digest}
        if method == "eth_getLogs":
            if self.mode == "empty_logs":
                return []
            return [{"address": ZTO, "topics": [TRANSFER], "blockNumber": hex(self.head),
                     "logIndex": "0x1", "transactionHash": TX, "removed": self.mode == "removed_log"}]
        raise AssertionError(method)


class SettlementTests(unittest.TestCase):
    def test_finalized_success(self):
        result = inspect(FakeRPC(), TX, minimum=10, require_finalized=True)
        self.assertTrue(result["settled"])
        self.assertEqual(result["confirmations"], 11)
        self.assertTrue(result["finalized"])

    def test_inclusion_counts_as_one(self):
        result = inspect(FakeRPC(height=100), TX, minimum=2)
        self.assertEqual(result["confirmations"], 1)
        self.assertEqual(result["state"], "confirming")

    def test_revert_never_settles(self):
        result = inspect(FakeRPC(status=0), TX, minimum=1)
        self.assertEqual(result["state"], "reverted")
        self.assertFalse(result["settled"])

    def test_unfinalized_policy(self):
        self.assertEqual(inspect(FakeRPC(final=80), TX, 10, True)["state"], "awaiting_finality")
        self.assertTrue(inspect(FakeRPC(final=80), TX, 10, False)["settled"])

    def test_unsupported_finality_is_unknown(self):
        result = inspect(FakeRPC(mode="unsupported_finality"), TX, 10, True)
        self.assertIsNone(result["finalized"])
        self.assertFalse(result["settled"])
        self.assertIn("finalityError", result)

    def test_reorg_and_orphan_fail_closed(self):
        for mode in ("orphan", "reorg", "head_reorg"):
            with self.subTest(mode=mode):
                result = inspect(FakeRPC(mode=mode), TX, 1)
                self.assertEqual(result["state"], "unstable")
                self.assertFalse(result["settled"])

    def test_receipt_ahead_of_sampled_head(self):
        self.assertEqual(inspect(FakeRPC(height=101), TX)["state"], "unstable")

    def test_absent_receipt(self):
        result = inspect(FakeRPC(mode="missing"), TX)
        self.assertEqual(result["state"], "not_included")
        self.assertFalse(result["settled"])

    def test_wrong_transaction_and_chain(self):
        for mode in ("wrong_tx", "wrong_chain"):
            with self.subTest(mode=mode), self.assertRaises(EvidenceError):
                inspect(FakeRPC(mode=mode), TX)

    def test_wrong_returned_block_number(self):
        with self.assertRaises(EvidenceError):
            block(FakeRPC(mode="wrong_number"), hex(90))

    def test_quantity_and_hash_validation(self):
        for value in ("0x00", "0x", "15", -1):
            with self.subTest(value=value), self.assertRaises(EvidenceError):
                quantity(value)
        with self.assertRaises(EvidenceError):
            inspect(FakeRPC(), "not-a-hash")
        with self.assertRaises(EvidenceError):
            inspect(FakeRPC(), TX, 0)

    def test_invalid_receipt_status(self):
        with self.assertRaises(EvidenceError):
            inspect(FakeRPC(status=2), TX)

    def test_discovery_uses_real_zto_filter(self):
        rpc = FakeRPC()
        self.assertEqual(latest_zto_transfer(rpc, 30), TX)
        query = [params[0] for method, params in rpc.requests if method == "eth_getLogs"][0]
        self.assertEqual(query["address"], ZTO)
        self.assertEqual((int(query["fromBlock"], 16), int(query["toBlock"], 16)), (71, 100))

    def test_bounded_empty_discovery(self):
        rpc = FakeRPC(head=2000, mode="empty_logs")
        with self.assertRaises(EvidenceError):
            latest_zto_transfer(rpc, 1025)
        queries = [params[0] for method, params in rpc.requests if method == "eth_getLogs"]
        self.assertEqual(len(queries), 3)
        self.assertEqual(int(queries[-1]["fromBlock"], 16), 976)

    def test_removed_logs_not_discovered(self):
        with self.assertRaises(EvidenceError):
            latest_zto_transfer(FakeRPC(mode="removed_log"), 20)

    def test_no_write_rpc_method_available(self):
        with self.assertRaises(EvidenceError):
            RPC("https://ethereum-rpc.publicnode.com").call("eth_sendRawTransaction", [])


if __name__ == "__main__":
    unittest.main()
