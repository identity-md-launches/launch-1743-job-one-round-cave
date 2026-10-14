# RPC evidence bridge

Connect line 1's real Ethereum snapshot format to line 2's offline structural
checker. A worker can capture public read evidence, hand over ordinary JSON, and
reject an RPC error, wrong chain, wrong response ID or malformed handoff offline.
Python 3.10+ standard library only; no installation, secrets, wallets or signing.

From the repository root, one offline demonstration:

```sh
python3 -B shared/rpc-evidence/verify.py shared/rpc-evidence/chain-id.snapshot.json
```

It prints `valid: true` and exits 0. The included snapshot was captured from
publicnode during gathering 01 on 2026-10-14; it returned `0x1`. It is historical
provider evidence, not a proof of current state. This contract is deliberately
only for `eth_chainId` snapshots, not arbitrary RPC results. Other results need
their own explicit contracts. Exit 1 means invalid evidence; 2 means input error.

Capture fresh evidence, then validate it (the output must stay in the workspace):

```sh
python3 -B shared/rpc-evidence/capture.py > shared/rpc-evidence/fresh.snapshot.json
python3 -B shared/rpc-evidence/verify.py shared/rpc-evidence/fresh.snapshot.json
```

`capture.py` provides a short read-only method allowlist and HTTPS-only endpoints
without URL credentials. Its default is the brief's publicnode endpoint. It
writes only stdout. Capture preserves RPC error responses so they can be inspected;
capture exit 0 alone does not mean the request succeeded. Validate afterward.
The adapter limits RPC bodies to 1 MB, matching the checker input limit.
Avoid private data in RPC parameters: read calls still disclose parameters to
the chosen public provider.

The checker refuses hidden paths, files over 1 MB, and paths outside the current
workspace. Run from the root of the workspace containing these files. This entire
folder can be copied into another worker's workspace; it has no line-folder
dependency. Imported source never reads configuration or environment variables.

```sh
python3 -B shared/rpc-evidence/test_bridge.py
```

Six offline bridge tests passed. Tests distinguish RPC success from HTTP success,
exercise malformed evidence and refuse send methods before any network request.
Validation checks a structure, not provider honesty, freshness or consensus.

## Provenance

`json_contract.py` is an unchanged copy of line 2's
`tools/json-contract/check.py`. `rpc_snapshot.py` reuses line 1's
`tools/rpc_snapshot.py` collector, with its arbitrary-method CLI removed and a
read allowlist, HTTPS credential rejection and response-size limit added.
Proxy discovery is disabled, so capture does not need environment settings.
The new contract and adapters combine them without editing either line.
Line 3 can reuse this handoff pattern for receipt/anchor contracts; line 4 can
reuse the structural checker for typed-data envelopes, while its own encoder
remains responsible for EIP-712 semantics.
