# Settlement check

Check an Ethereum transaction's execution status, inclusion in the current canonical chain, confirmation count, and optional consensus finality. This is a Python 3 standard-library tool; no installation, wallet, key, environment configuration, signing, or transaction sending is involved. It writes JSON to stdout only.

From the repository root, one command demonstrates it against the real ZTO token:

```sh
python3 -B line-3/tools/settlement-check/settlement.py --latest-zto-transfer
```

The command searches backward through at most 2048 Ethereum blocks, in chunks of 512, using ZTO's real Transfer event filter and the publicnode endpoint. It checks the newest transfer transaction found. Discovery is bounded and can report no transfer; it never invents a hash. `--lookback` permits up to 16384 blocks. HTTP requests have a 20-second timeout and a custom User-Agent.

To check a transaction already known to a worker, including one involving IMD or another contract:

```sh
python3 -B line-3/tools/settlement-check/settlement.py --tx 0x1d760b4ace58bd6023601084efac72c5416f66e40b0d046e45a94fbe63b25641 --require-finalized
```

That is a real transaction discovered during this round, not a placeholder. The tool requires Ethereum mainnet (chain ID 1). `--rpc https://eth.drpc.org` selects the other public endpoint from the brief. The default policy is successful execution and at least 12 confirmations, counting the inclusion block as confirmation one. `--confirmations N` changes the threshold. `--require-finalized` additionally requires the receipt's block to be at or below the canonical finalized head. Unsupported finality is reported as unknown and cannot satisfy a finality policy.

Exit status is 0 when the selected policy is met, 1 for a valid check that does not meet it, and 2 for invalid input or a failed RPC check. States include `settled`, `confirming`, `awaiting_finality`, `reverted`, `not_included`, `unstable`, and `error`. A null receipt cannot distinguish pending, unknown, or dropped transactions. When evidence is inconsistent, the tool fails closed; it does not retry until it gets a preferred answer.

## What happened when tried

On 2026-10-14, publicnode returned the real ZTO transfer transaction shown above. The strict policy first reported `awaiting_finality`: successful execution, 38 confirmations, and an inclusion height ahead of the finalized head. A subsequent check recorded in [live-example.json](live-example.json) met the default 12-confirmation policy with 48 confirmations. It still explicitly recorded `finalized: false`; meeting a confirmation policy is different from proving consensus finality. The sample is historical evidence, not a claim about the chain at the time this README is read.

Offline checks:

```sh
python3 -B -m unittest discover -s line-3/tools/settlement-check -p 'test_*.py' -v
```

All 16 tests passed. They cover successful finality, confirmation boundaries, reverted and absent receipts, unsupported finality, orphaned receipts, reorgs during collection, wrong block numbers, mismatched hashes, invalid quantities and statuses, mainnet enforcement, bounded ZTO discovery, removed logs, and refusal of transaction-sending RPC methods. Synthetic test hashes are explicitly generated as fixtures and never used by the live command.

## Evidence limits

The tool trusts the chosen RPC provider; it is not an independent consensus verifier or a cryptographic receipt-proof verifier. It reads the inclusion and sampled-head anchors again to detect changes during collection, but a reorg can occur after it exits. A confirmation policy can accept a transaction that is not finalized. A provider that consistently lies can defeat these checks.

Successful execution does not prove that a payment reached the expected recipient or that the expected token amount moved. Discovery identifies a ZTO Transfer event, but this first piece checks settlement of the transaction, not the business meaning of its logs. Workers must validate recipient, token, amount, and their own settlement policy separately. No monitoring timer or automatic action is included.
