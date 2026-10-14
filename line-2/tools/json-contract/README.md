# JSON contract checker

Check a worker report, API response, manifest, or other JSON deliverable before handing it to someone else. This Python 3.10+ tool uses only the standard library, works offline, and reports every independent structural violation with a JSON Pointer location. It does not read environment variables, use wallets, contact a service, or write files. Give it only nonsecret inputs within the workspace; hidden paths and paths resolving outside the current workspace are refused.

From the repository root, see it working:

```sh
python3 -B line-2/tools/json-contract/check.py line-2/tools/json-contract/report.contract.json line-2/tools/json-contract/report.example.json
```

It prints `{"valid": true, "errors": []}` (formatted across lines) and exits 0. Replace the last two arguments with your own contract and document. Exit 1 means the document violates the contract; exit 2 means a bad contract, JSON parse error, or file access error. Errors on a nested field look like `{"path":"/checks/0/passed","rule":"type","message":"expected boolean"}`. An empty path means the root document. Pointer keys escape `~` as `~0` and `/` as `~1`.

## Contract language

This is an explicitly limited contract language, **not a full JSON Schema implementation**. Each contract node requires `type`: object, array, string, integer, number, boolean, or null. Integer means an integer JSON literal; `1.0` is a number. Booleans never satisfy number or integer rules.

- Object: `properties` maps names to child contracts; `required` names declared properties; `additionalProperties: false` rejects undeclared names. Other properties are allowed by default. Child contracts apply only to fields present in the document.
- Array: `items` checks every element; `minItems` and `maxItems` bound length.
- String: `minLength` and `maxLength` count Unicode code points; `pattern` uses Python regular-expression search. Anchor a pattern with `^` and `$` when appropriate for your input.
- Integer/number: inclusive `minimum` and `maximum`.
- All types: nonempty `enum` lists allowed values. Numeric equality treats 1 and 1.0 as equal, but distinguishes true and 1 recursively.

Unknown rules and rules incompatible with their type are errors, so a misspelling cannot silently weaken validation. Duplicate JSON keys, nonfinite numbers, inputs larger than 1 MB, malformed regexes, and contradictory bounds are rejected. Contracts and their regular expressions must come from a trusted author; this is not a sandbox for adversarial regexes. It checks structure, not truth, provenance, cryptographic correctness, network state, or cross-field relationships. In particular the supplied `record.contract.json` checks top-level record fields, image URL syntax, and attribute count; it does not verify individual attribute meanings or order.

## What happened when tried

The example worker report passed. The actual existing `dist/line-1/01.json` also passed the deliberately limited record contract. A modified in-memory worker report with a string in `passed`, negative `seconds`, and an extra field produced all three expected pointer locations. Ten regression tests passed, covering boundaries, nested fields, enums, pointer escaping, invalid contracts, path refusal, and CLI exit codes. Additional scratch checks exercised duplicate keys, nonfinite JSON numbers, invalid-document CLI exit 1, and huge integers.

Run the committed offline suite:

```sh
python3 -B line-2/tools/json-contract/test_check.py
```

## Wall and record

The mark is **Shape Keeper**: Pepe checks the shapes before passing them onward. First mark of line 2, number 01, in Water. Used the supplied bare cave because this line had no earlier records. The generated wall is a square 1254 × 1254 PNG; the preview is a 512 × 512 JPEG, beside `dist/line-2/01.json`. SHA-256 in that record identifies the PNG bytes.

Visual review: warm rough rock, cracks, light, water and framing remain recognizable; the small central figure has Pepe's heavy-lidded eyes and wide mouth, with charcoal and ochre pigments. No text, numbers, frame, logos or handprints are visible. Both hands are concealed; there are no visible digits to count. No known unmet visual requirements. Image generation preserves the appearance of the background rather than guaranteeing pixel-identical stone. Preview quality is intentionally compressed below 100 KB. These are local checks, not independent certification.
