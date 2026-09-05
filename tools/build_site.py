#!/usr/bin/env python3
"""
Build the GitHub Pages site into docs/ (Pages source: main branch, /docs folder).

    docs/
      index.html          library portal (reads catalog.json)
      catalog.json        built from stories/*.json
      stories/*.json      the books (same files as the repo's stories/, minus gen_*)
      player/index.html   the simulator in online mode (fetches the catalog, ?book=, ?add=)
      studio/index.html   Moventure Studio
      .nojekyll

Usage:
    python tools/build_site.py
"""

import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"


def newest(pattern, folder):
    files = sorted(folder.glob(pattern), key=lambda p: [int(x) for x in re.findall(r"\d+", p.stem)])
    if not files:
        raise SystemExit(f"no {pattern} in {folder}")
    return files[-1]


def main():
    subprocess.run([sys.executable, str(ROOT / "tools" / "build_catalog.py")], check=True)
    # Overwrite in place: folders are kept (Google Drive / Explorer can hold a lock on them on
    # Windows, and rmtree would die halfway), stale files are removed one by one.
    for sub in ("stories", "player", "studio"):
        (DOCS / sub).mkdir(parents=True, exist_ok=True)
    for old in DOCS.rglob("*"):
        if old.is_file():
            try:
                old.unlink()
            except PermissionError:
                print(f"warning: could not remove {old.relative_to(ROOT)}, overwriting")
    (DOCS / ".nojekyll").write_text("")

    # catalog + books
    shutil.copy(ROOT / "catalog.json", DOCS / "catalog.json")
    import json
    cat = json.loads((ROOT / "catalog.json").read_text(encoding="utf-8"))
    for b in cat["books"]:
        shutil.copy(ROOT / b["file"], DOCS / b["file"])

    # portal
    shutil.copy(ROOT / "site" / "index_template.html", DOCS / "index.html")

    # player: newest simulator, online mode (no stories.js), base path to the site root
    sim = newest("moventure_sim_v*.html", ROOT / "simulator")
    html = sim.read_text(encoding="utf-8")
    html = html.replace('<script src="stories.js"></script>', "<script>window.MOVENTURE_BASE = '../';</script>")
    html = html.replace("<title>Moventure Simulator</title>", "<title>Moventure Player</title>")
    html = html.replace("document.title = 'Moventure Simulator v' + APP_VERSION;", "document.title = 'Moventure Player v' + APP_VERSION;")
    (DOCS / "player" / "index.html").write_text(html, encoding="utf-8")

    # studio
    studio = newest("moventure_studio_v*.html", ROOT / "studio")
    st = studio.read_text(encoding="utf-8")
    st = re.sub(r"const PLAYER_URL = '[^']*';", "const PLAYER_URL = '../player/';", st)
    (DOCS / "studio" / "index.html").write_text(st, encoding="utf-8")

    n = sum(1 for _ in DOCS.rglob("*") if _.is_file())
    print(f"built docs/ ({n} files) from {sim.name} and {studio.name}")


if __name__ == "__main__":
    main()
