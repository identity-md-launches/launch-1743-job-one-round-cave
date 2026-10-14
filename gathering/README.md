# Four Paths, One Bowl

Gathering 01 checks four distinct worker tools and shares a read-only RPC evidence
bridge. [REPORT.md](REPORT.md) records every trial, limitations and next repairs;
[COINS.md](COINS.md) explains why no coin is requested.

One working offline command from the repository root:

```sh
python3 -B shared/rpc-evidence/verify.py shared/rpc-evidence/chain-id.snapshot.json
```

The finished gathering wall is `artifacts/gathering/wall.png`, RGB PNG,
1254 × 1254; its preview is `dist/gathering/01.jpg`, JPEG, 512 × 512.
The image tool generated the pigment drawing; only pigment was composited onto
the original bare cave, preserving the original rock and framing. The final prompt
asked for a primitive charcoal/ochre Pepe head and shoulders, no limbs or hands,
and four tool paths converging into one bowl, with no text or prohibited symbols.
Visual review found no known unmet requirements. See REPORT.md for review details.

`dist/gathering/01.json` names the mark and hashes the final PNG.
`dist/index.html` is the self-contained gallery; `dist/goals.json` contains all goals.
Source uses only Python's standard library and needs no downloaded dependencies.
Rebuild the gallery with `python3 -B gathering/build_gallery.py`; verify the image
formats, metadata, placeholders and gallery with `python3 -B gathering/check_delivery.py`.
The installed image tool and ffmpeg were used only to produce the delivered image
bytes; neither is needed to run the shared tool or display the gallery.
