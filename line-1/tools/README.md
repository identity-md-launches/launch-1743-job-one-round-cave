# RPC snapshot

This tool gives a worker one portable, offline-readable record of a live Ethereum JSON-RPC response. It stores the endpoint, request method and parameters, HTTP metadata, and the exact parsed response; it never uses a wallet, reads secrets, signs, or sends a transaction.

I tried it against Ethereum’s public JSON-RPC endpoint with `eth_chainId`; it returned a successful JSON-RPC response and wrote a snapshot. Network access is required for capture, but the resulting file can be inspected offline.

Run it:

```sh
python3 line-1/tools/rpc_snapshot.py --method eth_chainId --output /tmp/ethereum-chain-id.json
```

The output is ordinary JSON and can be opened later without the network.
