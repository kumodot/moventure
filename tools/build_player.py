#!/usr/bin/env python3
"""
Build the single-file player: the newest simulator HTML with stories.js inlined,
opened straight in player mode. One file, no dependencies, send it to anyone
(Steam Deck browser, phone, friends). Same engine, same books.

Usage:
    python tools/build_player.py            -> simulator/moventure_player_vX.Y.Z.html
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SIM = ROOT / "simulator"

sims = sorted(SIM.glob("moventure_sim_v*.html"), key=lambda p: [int(x) for x in re.findall(r"\d+", p.stem)])
if not sims:
    raise SystemExit("no simulator/moventure_sim_v*.html found")
src = sims[-1]
html = src.read_text(encoding="utf-8")
version = re.search(r"APP_VERSION = '([^']+)'", html).group(1)
stories = (SIM / "stories.js").read_text(encoding="utf-8")

# inline the bundle and force player mode at startup
html = html.replace('<script src="stories.js"></script>', "<script>\n" + stories + "</script>")
html = html.replace("if (new URLSearchParams(location.search).has('player')) setPlayer(true);",
                    "setPlayer(true);   // player build: always starts in player mode")
html = html.replace("<title>Moventure Simulator</title>", "<title>Moventure Player</title>")
html = html.replace("document.title = 'Moventure Simulator v' + APP_VERSION;", "document.title = 'Moventure Player v' + APP_VERSION;")

out = SIM / f"moventure_player_v{version}.html"
for old in SIM.glob("moventure_player_v*.html"):
    if old != out:
        old.unlink()
out.write_text(html, encoding="utf-8")
print(f"wrote {out.relative_to(ROOT)} ({out.stat().st_size // 1024} KB) from {src.name}")
