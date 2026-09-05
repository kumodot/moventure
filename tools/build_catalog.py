#!/usr/bin/env python3
"""
Build catalog.json from stories/*.json: the index the online player, the library
portal and (later) the hardware read. Only books that pass the validator are listed.

Usage:
    python tools/build_catalog.py               -> catalog.json (repo root)
"""

import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from validate_story import validate, book_langs, loc, wrap, TEXT_ROWS  # noqa: E402

SKIP_PREFIXES = ("gen_", "teste_")  # generator output and test books are not catalog material


def entry(path, book):
    m = book["meta"]
    langs = book_langs(m)
    nodes = book["nodes"]
    words = sum(len(loc(n.get("text", ""), langs[0]).split()) for n in nodes.values())
    pages = sum(max(1, -(-len(wrap(loc(n.get("text", ""), langs[0]))) // TEXT_ROWS)) for n in nodes.values())
    return {
        "id": path.stem,
        "file": f"stories/{path.name}",
        "title": m.get("title"),
        "blurb": m.get("blurb", ""),
        "author": m.get("author", ""),
        "category": m.get("category", "Misc"),
        "tier": m.get("tier", 1),
        "langs": langs,
        "license": m.get("license", ""),
        "based_on": m.get("based_on", ""),
        "series": m.get("series", ""),
        "nodes": len(nodes),
        "endings": sum(1 for n in nodes.values() if n.get("ending")),
        "words": words,
        "pages": pages,
        "version": m.get("version", 1),
    }


def main():
    books = []
    for p in sorted((ROOT / "stories").glob("*.json")):
        if p.name.startswith(SKIP_PREFIXES):
            continue
        if not validate(str(p), quiet=True):
            print(f"skipping {p.name}: validator errors")
            continue
        books.append(entry(p, json.loads(p.read_text(encoding="utf-8"))))
    order = {"SCP": 5}
    import re

    def series_no(b):                       # "Foundation Files, no. 3." in the blurb -> 3
        m = re.search(r"no\. ?(\d+)", loc(b["blurb"], "en") if isinstance(b["blurb"], dict) else str(b["blurb"]))
        return int(m.group(1)) if m else 999

    books.sort(key=lambda b: (b["id"] != "hollow_lighthouse", order.get(b["category"], 0), series_no(b), b["tier"], b["id"]))
    catalog = {"name": "Moventure Library", "updated": date.today().isoformat(), "count": len(books), "books": books}
    (ROOT / "catalog.json").write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote catalog.json with {len(books)} books: " + ", ".join(b["id"] for b in books))


if __name__ == "__main__":
    main()
