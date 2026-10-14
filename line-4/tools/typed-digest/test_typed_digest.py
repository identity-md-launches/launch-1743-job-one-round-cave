"""Independent published vectors and rejection checks for the offline calculator."""

import unittest

from typed_digest import Encoder, TypedDataError, digest, keccak256, unique_object


class DigestTests(unittest.TestCase):
    def test_keccak_vectors(self):
        self.assertEqual(keccak256(b"").hex(), "c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470")
        self.assertEqual(keccak256(b"abc").hex(), "4e03657aea45a94fc7d47ba826c8d667c0d1e6e33a64a036ec44f58fa12d6c45")

    def test_ether_mail_vector(self):
        # EIP-712's Ether Mail input; output agrees with ethers TypedDataEncoder.hash.
        data = {
            "types": {
                "EIP712Domain": [
                    {"name": "name", "type": "string"},
                    {"name": "version", "type": "string"},
                    {"name": "chainId", "type": "uint256"},
                    {"name": "verifyingContract", "type": "address"},
                ],
                "Person": [{"name": "name", "type": "string"}, {"name": "wallet", "type": "address"}],
                "Mail": [
                    {"name": "from", "type": "Person"},
                    {"name": "to", "type": "Person"},
                    {"name": "contents", "type": "string"},
                ],
            },
            "primaryType": "Mail",
            "domain": {
                "name": "Ether Mail", "version": "1", "chainId": 1,
                "verifyingContract": "0xCcCCccccCCCCcCCCCCCcCcCccCcCCCcCcccccccC",
            },
            "message": {
                "from": {"name": "Cow", "wallet": "0xCD2a3d9F938E13CD947Ec05AbC7FE734Df8DD826"},
                "to": {"name": "Bob", "wallet": "0xbBbBBBBbbBBBbbbBbbBbbbbBBbBbbbbBbBbbBBbB"},
                "contents": "Hello, Bob!",
            },
        }
        result = digest(data)
        self.assertEqual(result["domainSeparator"], "0xf2cee375fa42b42143804025fc449deafd50cc031ca257e0b194a650a912090f")
        self.assertEqual(result["messageHash"], "0xc52c0ee5d84264471806290a3f2c4cecfc5490626bf912d01f240d7a274b371e")
        self.assertEqual(result["digest"], "0xbe609aee343fb3c4b28e1df9e632fca64fcfaede20f02e86244efddf30957bd2")

    def test_dependency_order_and_arrays(self):
        encoder = Encoder({
            "EIP712Domain": [],
            "Transaction": [{"name": "from", "type": "Person"}, {"name": "tx", "type": "Asset[]"}],
            "Person": [{"name": "wallet", "type": "address"}],
            "Asset": [{"name": "token", "type": "address"}, {"name": "amount", "type": "uint256"}],
        })
        self.assertEqual(
            encoder.type_encoding("Transaction"),
            "Transaction(Person from,Asset[] tx)Asset(address token,uint256 amount)Person(address wallet)",
        )
        self.assertEqual(len(encoder.value_word("uint8[2]", [1, 2])), 32)
        with self.assertRaises(TypedDataError):
            encoder.value_word("uint8[2]", [1])

    def test_rejects_ambiguous_or_invalid_values(self):
        with self.assertRaises(TypedDataError):
            unique_object([("chainId", 1), ("chainId", 2)])
        encoder = Encoder({"EIP712Domain": [], "Data": [{"name": "amount", "type": "uint8"}]})
        with self.assertRaises(TypedDataError):
            encoder.struct_hash("Data", {"amount": 256})
        with self.assertRaises(TypedDataError):
            encoder.struct_hash("Data", {"amount": 1, "hidden": True})


if __name__ == "__main__":
    unittest.main()
