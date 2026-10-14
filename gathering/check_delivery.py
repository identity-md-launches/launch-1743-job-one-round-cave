#!/usr/bin/env python3
"""Offline structural checks for Water's first gathering; no dependencies."""
import hashlib
import json
import struct
import zlib
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BARE = "https://api.imd.fun/artifacts/ce5dbc18003365f5a1bf9014a2a357c2cb5c5dc2335dd0eb9b661ae703d36308"


class Gallery(HTMLParser):
    def __init__(self):
        super().__init__()
        self.images = []
        self.records = []
        self.sections = []
        self.dependencies = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "img":
            self.images.append(attrs["src"])
        if tag == "a" and attrs.get("class") == "record":
            self.records.append(attrs["href"])
        if tag == "section":
            self.sections.append(attrs["id"])
        if tag == "script" or (tag == "link" and attrs.get("rel") == "stylesheet"):
            self.dependencies.append(attrs)


def png_info(path):
    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    offset = 8
    header = None
    compressed = []
    ended = False
    while offset < len(data):
        size = int.from_bytes(data[offset:offset+4], "big")
        kind = data[offset+4:offset+8]
        body = data[offset+8:offset+8+size]
        crc = int.from_bytes(data[offset+8+size:offset+12+size], "big")
        assert len(body) == size and zlib.crc32(kind + body) == crc
        if kind == b"IHDR":
            header = struct.unpack(">IIBBBBB", body)
        if kind == b"IDAT":
            compressed.append(body)
        offset += 12 + size
        if kind == b"IEND":
            ended = True
            break
    assert ended and offset == len(data)
    width, height, bits, color, compression, filter_method, interlace = header
    assert bits == 8 and color == 2 and interlace == 0
    assert compression == filter_method == 0
    decoded = zlib.decompress(b"".join(compressed))
    assert len(decoded) == height * (1 + width * 3)
    assert all(decoded[y * (1 + width * 3)] in range(5) for y in range(height))
    return {"format": "PNG", "width": width, "height": height, "mode": "RGB"}


def jpeg_info(path):
    data = path.read_bytes()
    assert data[:2] == b"\xff\xd8" and data[-2:] == b"\xff\xd9"
    offset = 2
    while offset < len(data):
        assert data[offset] == 255
        while data[offset] == 255:
            offset += 1
        marker = data[offset]
        offset += 1
        size = int.from_bytes(data[offset:offset+2], "big")
        if marker in (0xc0, 0xc1, 0xc2):
            bits, height, width, components = struct.unpack(">BHHB", data[offset+2:offset+8])
            assert bits == 8 and components == 3
            return {"format": "JPEG", "width": width, "height": height}
        offset += size
    raise AssertionError("JPEG has no supported frame")


def main():
    wall = ROOT / "artifacts/gathering/wall.png"
    preview = ROOT / "dist/gathering/01.jpg"
    png, jpeg = png_info(wall), jpeg_info(preview)
    assert (png["width"], png["height"]) == (1254, 1254)
    assert (jpeg["width"], jpeg["height"]) == (512, 512)
    r = json.loads((ROOT / "dist/gathering/01.json").read_text())
    assert set(r) == {"name", "image", "attributes"}
    assert r["image"] == "https://api.imd.fun/artifacts/" + hashlib.sha256(wall.read_bytes()).hexdigest()
    attrs = r["attributes"]
    assert [a["trait_type"] for a in attrs] == ["Cave", "Wall", "Number", "Left behind", "Meaning", "One thing"]
    assert all(set(a) == {"trait_type", "value"} for a in attrs)
    assert [attrs[i]["value"] for i in (0, 1, 2, 5)] == ["Water", "Gathering", 1, "Gathering"]
    assert type(attrs[2]["value"]) is int
    assert all(a["value"] for a in attrs)
    pending = {"name": "Not painted yet", "image": BARE,
               "attributes": [{"trait_type": "Cave", "value": "Water"}]}
    folders = [f"line-{n}" for n in range(1, 5)] + ["gathering"]
    for folder in folders:
        directory = ROOT / "dist" / folder
        assert len(list(directory.glob("[0-9][0-9].json"))) == 21
        for number in range(2, 22):
            assert json.loads((directory / f"{number:02}.json").read_text()) == pending
            assert not (directory / f"{number:02}.jpg").exists()
    goals = json.loads((ROOT / "dist/goals.json").read_text())
    assert goals == [{"line": n, "goal": (ROOT / f"line-{n}/GOAL.md").read_text().strip()}
                     for n in range(1, 5)]
    gallery = Gallery()
    gallery.feed((ROOT / "dist/index.html").read_text())
    assert gallery.sections == folders and not gallery.dependencies
    assert len(gallery.images) == len(gallery.records) == 105
    expected = [f"{folder}/{number:02}.json" for folder in folders
                for number in [1] + list(range(21, 1, -1))]
    assert gallery.records == expected
    for href in gallery.records:
        assert (ROOT / "dist" / href).is_file()
    oversized = [str(p.relative_to(ROOT)) for folder in ("gathering", "shared", "dist")
                 for p in (ROOT / folder).rglob("*") if p.is_file() and p.stat().st_size > 100_000]
    assert not oversized, oversized
    assert not list((ROOT / "dist").rglob("__pycache__"))
    print(json.dumps({"valid": True, "wall": png, "preview": jpeg,
                      "paintedRecords": 5, "placeholderRecords": 100,
                      "galleryRecords": len(gallery.records),
                      "unmetVisualRequirements": [],
                      "visualReview": "Recorded separately in REPORT.md; this checker validates structure, not appearance."}, indent=2))


if __name__ == "__main__":
    main()
