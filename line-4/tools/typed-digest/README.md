# Offline EIP-712 digest checker

This Python standard-library tool calculates the domain separator, message struct hash, and final EIP-712 digest from a typed-data JSON request. It checks field names, Solidity value ranges, array lengths, hex lengths, and duplicate JSON keys. It makes no network call and never signs.

From the repository root, run:

```sh
python3 line-4/tools/typed-digest/typed_digest.py line-4/tools/typed-digest/zto-example.json
```

The example refers to ZTO's actual Ethereum token address and yields digest `0xc292388738e2cf2c7f57b9b8926821aff508ed38c1b355020cc7dc459dbbb8cb`. It is illustrative typed data, not a token permit. To compare with a proposed digest, add `--expect 0x...`; a mismatch exits with status 1, malformed input with status 2. Supply the exact typed-data JSON shown by the signing client, including its `EIP712Domain` type, for a meaningful comparison.

I ran `python3 -m unittest discover -s line-4/tools/typed-digest -p 'test_*.py'`: the Keccak vectors, [EIP-712 Ether Mail example](https://eips.ethereum.org/EIPS/eip-712), and [ethers' published hash](https://docs.ethers.org/v5/api/utils/hashing/) matched. The tool does not establish whether a signing request is safe or whether a contract will honor it; it checks the bytes implied by the supplied typed data.
