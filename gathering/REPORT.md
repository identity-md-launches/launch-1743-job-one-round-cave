# Water — gathering 01

Reviewed and tried on 2026-10-14. All four goals are useful to an unfamiliar worker
outside this cave and differ in kind. No line folder was changed. Commands below
ran from the repository root with Python bytecode disabled. Source was read before
execution; only public reads and offline calculations were performed.

## Line 1 — portable Ethereum RPC snapshots

Tried `python3 -B line-1/tools/rpc_snapshot.py --method eth_chainId --output shared/rpc-evidence/chain-id.snapshot.json`.
It exited 0, captured HTTP 200 from publicnode, and preserved the request and JSON-RPC
response with chain ID `0x1`, decimal 1. The resulting evidence is delivered in shared/.
There is no committed test suite/check command beyond this README demonstration.

Works: live capture, readable offline JSON, endpoint/request/HTTP metadata, custom
User-Agent. Broken safety boundary (static source review): its arbitrary `--method`
can request signing/sending methods, so it cannot guarantee the task's read-only
rule. No such method was run. HTTP success with a JSON-RPC error also exits 0; no
response-ID/envelope validation or response-size bound exists. Treat capture exit
status as transport success only. Repair the public-read allowlist and bounded
response handling first next round. The shared adapter supplies both restrictions
without editing the line, and line 2's contract catches erroneous chain-ID evidence.

Distinctness/scope: capture is different from structural validation or settlement;
its goal is already demonstrated. Keep it to bounded public read evidence, not a
general wallet or arbitrary RPC client. No narrowing of the written goal is needed.

## Line 2 — offline JSON structural contracts

Tried `python3 -B line-2/tools/json-contract/check.py line-2/tools/json-contract/report.contract.json line-2/tools/json-contract/report.example.json`
and `python3 -B line-2/tools/json-contract/test_check.py`. The example passed and
all 10 tests passed. Also checked the new gathering record with its record contract.

Works: typed values, nested pointers, independent violations, duplicate-key and
nonfinite-number refusal, invalid-contract refusal, safe workspace input paths,
documented exit codes. No broken behavior observed within the documented contract
language. Limits: the record contract checks only attribute count, not each trait's
meaning; untrusted regexes can consume excessive time. The checker is deliberately
not full JSON Schema or a semantic truth checker. No false claim of either was found.

Distinctness/scope: useful for arbitrary JSON handoffs, not just cave records.
It does not duplicate line 4's Solidity encodings. The current explicit subset is
small enough for 21 Pepes; retain that scope rather than promising every JSON Schema
feature. Shared/ now contains its unchanged checker and a contract for line 1's evidence.

## Line 3 — transaction settlement policy

Tried `python3 -B -m unittest discover -s line-3/tools/settlement-check -p 'test_*.py' -v`
and `python3 -B line-3/tools/settlement-check/settlement.py --latest-zto-transfer`.
All 16 tests passed. Publicnode discovered real ZTO transfer transaction
`0x1d760b4ace58bd6023601084efac72c5416f66e40b0d046e45a94fbe63b25641`.
It reported successful execution, canonical inclusion at block 26190942, sampled
head 26191057, 116 confirmations, finalized head 26190983, `finalized: true`,
`settled: true`, exit 0. These are sampled observations, not a permanent guarantee.

Works: real bounded ZTO discovery, mainnet enforcement, execution/confirmation/finality
policies, canonical hash and returned-height checks, reorg/absent-receipt/revert refusal.
No broken behavior observed. Limits: trusts an RPC provider; does not prove token
recipient/amount or independently verify consensus. Unknown finality correctly fails
a required-finality policy. No timer or transaction action was run.

Distinctness/scope: verifies changing chain evidence, whereas line 1 captures it.
The one thing already works at the provider-evidence level. Keep the goal at policy
checks over public RPC evidence; a full trustless consensus/receipt-proof verifier
would be too large for this line. Reusable snapshot contracts are a practical next step.

## Line 4 — EIP-712 digest checking

Tried `python3 -B line-4/tools/typed-digest/typed_digest.py line-4/tools/typed-digest/zto-example.json`
and `python3 -B -m unittest discover -s line-4/tools/typed-digest -p 'test_*.py' -v`.
All 4 tests passed. The real-ZTO-address example reproduced
`0xc292388738e2cf2c7f57b9b8926821aff508ed38c1b355020cc7dc459dbbb8cb`.
The example is illustrative typed data, not a token permit or proof ZTO accepts it.

Works: Ethereum Keccak vectors, published Ether Mail digest, dependency ordering,
array handling and basic malformed-value refusal. No broken behavior observed in
the covered cases. Limits: four test methods are not exhaustive for every Solidity
integer/bytes/recursive-array case. Input files are not bounded or constrained to
the workspace by this line's CLI; only the supplied nonsecret workspace file was
read here. This deserves hardening before accepting untrusted signing requests.
Digest correctness alone cannot say that a request is safe or will be honored.

Distinctness/scope: encodes typed Solidity data cryptographically, not just JSON
structure. The goal is demonstrated and feasible; keep signing-policy judgments
and actual signing out of its scope. Line 2 can supply envelope checks while this
encoder remains responsible for EIP-712 semantics.

## Shared work and remaining work

Delivered `shared/rpc-evidence/`: line 1's collector adapted to bounded public reads,
line 2's checker copied unchanged, a strict mainnet chain-ID snapshot contract,
the actual capture, CLI glue and six offline tests. All six passed; the safe live
adapter also returned `0x1`. Any worker can copy this folder and validate evidence
offline without the cave or original line folders. Next: additional method-specific
receipt/anchor contracts could feed line 3, and typed-data envelope contracts could
feed line 4. No existing piece was deleted or replaced.

No goal currently needs to be replaced or narrowed. The scope cautions above keep
each within 21 rounds. No coin or deployment is required: see COINS.md.

## Wall and delivery review

First gathering: no earlier gathering record or wall existed. Started from the
provided bare cave. Generated a charcoal/ochre Pepe bust and four tool paths meeting
in one bowl, extracted pigment and composited it onto the original cave. The original
1254 × 1254 square, rock, cracks, torchlight, water and framing are retained. Only
123163 pixels differ from the bare cave (only within the pigment region); the other
1449353 pixels preserve the original image exactly, including the outer framing.
The final is RGB PNG at `artifacts/gathering/wall.png`; preview is 512 × 512 JPEG at
`dist/gathering/01.jpg` (61185 bytes). The numbered JSON points to the PNG's SHA-256.

Visual inspection: Pepe's wide mouth and heavy-lidded eyes are recognizable; only
earth pigments appear. No hands, handprints or stencils are depicted, so there are
no visible digits to count. No words, numbers, captions, logos, borders, signatures,
real people or prohibited symbols are visible. No known unmet visual requirements;
these are local observations, not independent aesthetic certification.

Created 100 unpainted slot records: numbers 02–21 for all four lines and gathering,
with the required bare-cave URL and sole Cave trait, no placeholder JPEGs. The gallery
includes every record, grouped by wall; painted records are newest first, with future
slots in descending numeric order under each group's expandable pending list.
The page includes its CSS and data directly, needs no script/library dependencies,
and uses artifact URLs for full-size paintings. Goals are copied from the four GOAL.md
files into dist/goals.json. Original line source and existing records remain intact.

Final checks: `python3 -B gathering/check_delivery.py` passed PNG signature/chunk
CRC/decompression, JPEG frame dimensions, the PNG hash, exact metadata traits,
all 100 placeholder shapes, absence of placeholder JPEGs, copied goals and all
105 gallery record links/order. Every delivered file outside artifacts/ is under
100 KB. The shared checker is byte-for-byte identical to line 2's original.
Git diff confirmed all four line folders and original records unchanged; path audit
found changes only in the authorized folders. The named PNG remains untracked for
the output uploader. No package was installed and no configuration file was changed.
