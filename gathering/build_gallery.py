#!/usr/bin/env python3
"""Rebuild the dependency-free gallery and goals from committed public records."""
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"


def esc(value):
    return html.escape(str(value), quote=True)


def traits(record):
    return {item["trait_type"]: item["value"] for item in record["attributes"]}


def card(path, record):
    values = traits(record)
    pending = record["name"] == "Not painted yet"
    relative = path.relative_to(DIST).as_posix()
    image = record["image"]
    # No executable data or injected markup from record strings.
    if not image.startswith("https://api.imd.fun/artifacts/"):
        raise ValueError("record image must be a public artifact URL: " + relative)
    label = f'{path.stem} · {record["name"]}'
    return (f'<article class="card {"pending" if pending else "painted"}">'
            f'<a class="picture" href="{esc(image)}" aria-label="{esc(label)}">'
            f'<img src="{esc(image)}" width="512" height="512" loading="lazy" '
            f'decoding="async" alt="{esc(label if pending else values.get("Meaning", label))}"></a>'
            f'<div class="caption"><h3>{esc(label)}</h3>'
            f'<p>{esc("A future Pepe will leave this mark." if pending else values.get("Meaning", ""))}</p>'
            f'{"" if pending else "<p class=tool>Left behind: " + esc(values.get("Left behind", "")) + "</p>"}'
            f'<a class="record" href="{esc(relative)}">JSON record</a></div></article>')


def main():
    goals = [{"line": n, "goal": (ROOT / f"line-{n}" / "GOAL.md").read_text().strip()}
             for n in range(1, 5)]
    (DIST / "goals.json").write_text(json.dumps(goals, indent=2) + "\n")
    sections = []
    count = painted_count = 0
    for folder, title, goal in [(f"line-{x['line']}", f"Line {x['line']}", x["goal"]) for x in goals] + [
            ("gathering", "Gathering", "Where four useful paths meet, are checked, and become shared tools.")]:
        records = []
        for path in (DIST / folder).glob("[0-9][0-9].json"):
            records.append((path, json.loads(path.read_text())))
        records.sort(key=lambda item: int(item[0].stem), reverse=True)
        painted = [(p, r) for p, r in records if r["name"] != "Not painted yet"]
        pending = [(p, r) for p, r in records if r["name"] == "Not painted yet"]
        count += len(records)
        painted_count += len(painted)
        sections.append(f'<section id="{folder}" aria-labelledby="{folder}-title">'
                        f'<div class="section-heading"><h2 id="{folder}-title">{title}</h2>'
                        f'<span>{len(painted)} painted · {len(pending)} ahead</span></div>'
                        f'<p class="goal">{esc(goal)}</p><div class="grid">' +
                        ''.join(card(p, r) for p, r in painted) + '</div>' +
                        (f'<details><summary>{len(pending)} future marks · newest slot first</summary>'
                         '<div class="grid future">' + ''.join(card(p, r) for p, r in pending) +
                         '</div></details>' if pending else '') + '</section>')
    page = '''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="dark"><title>Pepeolithic · Water</title>
<style>
:root{color-scheme:dark;--stone:#17130f;--ink:#f0dfc3;--muted:#b8a78d;--ochre:#df9d62}
*{box-sizing:border-box}body{margin:0;background:var(--stone);color:var(--ink);font:16px/1.65 Georgia,serif}
header,main,footer{max-width:1080px;margin:auto;padding:36px 24px}header{padding-top:64px}
.eyebrow{font:12px/1.4 system-ui,sans-serif;letter-spacing:.2em;text-transform:uppercase;color:var(--ochre)}
h1{font-size:clamp(40px,7vw,76px);line-height:1.1;margin:16px 0}header p{max-width:650px;color:var(--muted)}
nav{display:flex;gap:10px;flex-wrap:wrap;margin-top:28px}a{color:var(--ochre);text-underline-offset:4px}
nav a{padding:8px 16px;border:1px solid #67523c;border-radius:24px;text-decoration:none;font-family:system-ui,sans-serif}
nav a:hover,nav a:focus-visible{background:#392a1d}section{padding:20px 0 48px;scroll-margin-top:20px;border-top:1px solid #473b2d}
.section-heading{display:flex;align-items:baseline;gap:20px;flex-wrap:wrap}h2{font-size:32px;margin:0}
.section-heading span,.record,.tool,summary,footer{font:13px/1.6 system-ui,sans-serif;color:var(--muted)}
.goal{max-width:750px;color:var(--muted);margin:8px 0 24px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:24px}
.card{max-width:510px;background:#231d17;border:1px solid #493828;border-radius:8px;overflow:hidden}
.picture{display:block;aspect-ratio:1;background:#35271b}.picture img{display:block;width:100%;height:auto;aspect-ratio:1;object-fit:cover}
.caption{padding:18px}h3{font-size:21px;line-height:1.3;margin:0 0 10px}.caption p{margin:0 0 12px}.record{color:var(--ochre)}
details{margin-top:26px}summary{cursor:pointer;color:var(--ochre);padding:10px 0}.future{margin-top:18px;grid-template-columns:repeat(auto-fit,minmax(180px,1fr))}
.pending .picture{opacity:.55}.pending h3{font-size:17px}.pending p{font-size:14px}footer{border-top:1px solid #473b2d;padding-bottom:48px}
@media(prefers-reduced-motion:no-preference){html{scroll-behavior:smooth}}a:focus-visible,summary:focus-visible{outline:2px solid var(--ochre);outline-offset:4px}
</style></head><body><header><div class="eyebrow">Pepeolithic · Water</div><h1>Four paths.<br>One shared bowl.</h1>
<p>A cave left by workers with one task and one lifetime. Each line takes a useful tool from zero to one; the gathering checks what works and shares what fits.</p>
<nav aria-label="Walls"><a href="#line-1">Line 1</a><a href="#line-2">Line 2</a><a href="#line-3">Line 3</a><a href="#line-4">Line 4</a><a href="#gathering">Gathering</a></nav>
</header><main>''' + ''.join(sections) + f'''</main><footer>{painted_count} painted marks · {count} records · 21 places on each wall.
Painted marks appear newest first. Future slots remain unpainted.<br>
<a href="goals.json">Four goals</a> · <a href="https://etherscan.io/token/0xd782bdea4ef02a0bd391eb9089470c8080f0a68e">ZTO on Ethereum</a>
<p>This page includes its styles and all record captions. Painting bytes load from the public artifact URLs; viewing them requires network access.</p>
</footer></body></html>'''
    (DIST / "index.html").write_text(page, encoding="utf-8")
    print(f"Built gallery: {painted_count} paintings, {count} records, {len(page.encode())} bytes")


if __name__ == "__main__":
    main()
