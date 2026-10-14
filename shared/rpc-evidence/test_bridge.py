"""Offline bridge regressions: contract failures and read-only boundary."""
import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path

from json_contract import load, prepare, validate
from rpc_snapshot import rpc_call

HERE = Path(__file__).resolve().parent


class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.contract = prepare(load(str(HERE / "chain-id.contract.json")))
        self.snapshot = load(str(HERE / "chain-id.snapshot.json"))

    def test_live_capture_matches_mainnet_contract(self):
        self.assertEqual(validate(self.snapshot, self.contract), [])

    def test_rpc_error_is_not_successful_evidence(self):
        self.snapshot["response"] = {"jsonrpc": "2.0", "id": 1,
                                     "error": {"code": -32601, "message": "unsupported"}}
        paths = {e["path"] for e in validate(self.snapshot, self.contract)}
        self.assertEqual(paths, {"/response/result", "/response/error"})

    def test_wrong_chain_envelope_method_and_http(self):
        for section, key, value in (("response", "result", "0x2"),
                                    ("response", "id", 2),
                                    ("request", "method", "eth_sendRawTransaction")):
            changed = copy.deepcopy(self.snapshot)
            changed[section][key] = value
            self.assertTrue(validate(changed, self.contract))
        self.snapshot["http_status"] = 500
        self.assertTrue(validate(self.snapshot, self.contract))

    def test_read_adapter_rejects_sending_before_network(self):
        with self.assertRaises(ValueError):
            rpc_call("https://ethereum-rpc.publicnode.com", "eth_sendRawTransaction", [], 1)

    def test_read_adapter_rejects_credential_url(self):
        with self.assertRaises(ValueError):
            rpc_call("https://user:password@example.invalid", "eth_chainId", [], 1)

    def test_cli_works_without_network(self):
        result = subprocess.run([sys.executable, "-B", str(HERE / "verify.py"),
                                 str(HERE / "chain-id.snapshot.json")],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertTrue(json.loads(result.stdout)["valid"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
