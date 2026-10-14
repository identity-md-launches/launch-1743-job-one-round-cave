# Shared pieces

[RPC evidence bridge](rpc-evidence/README.md) combines line 1's capture format
and line 2's structural checker. It includes vendored standard-library code,
a real mainnet sample, an offline command and six regression tests. Copy its
folder into any workspace; no packages, network or cave records are needed for
validation. Capturing fresh evidence uses only public read RPC methods.
