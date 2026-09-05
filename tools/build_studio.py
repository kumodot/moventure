#!/usr/bin/env python3
"""
Build Moventure Studio: studio/studio_template.html + the engine sections (OLED,
text layout, Engine) copied verbatim from the newest simulator, so the Studio
preview is pixel-identical to the device simulator.

Usage:
    python tools/build_studio.py            -> studio/moventure_studio_vX.Y.Z.html
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STUDIO_VERSION = "0.4.0"

sims = sorted((ROOT / "simulator").glob("moventure_sim_v*.html"), key=lambda p: [int(x) for x in re.findall(r"\d+", p.stem)])
sim = sims[-1].read_text(encoding="utf-8")
start = sim.index("/* =========================================================================\n   SECTION 1")
end = sim.index("/* =========================================================================\n   SECTION 4")
engine = sim[start:end]
engine = re.sub(r"const APP_VERSION = '[^']+';[^\n]*\n", "", engine)   # Studio defines its own APP_VERSION

tpl = (ROOT / "studio" / "studio_template.html").read_text(encoding="utf-8")
out_html = tpl.replace("/* __ENGINE__ */", engine).replace("__STUDIO_VERSION__", STUDIO_VERSION).replace("__PLAYER_URL__", "../simulator/" + sims[-1].name)
out = ROOT / "studio" / f"moventure_studio_v{STUDIO_VERSION}.html"
for old in (ROOT / "studio").glob("moventure_studio_v*.html"):
    if old != out:
        old.unlink()
out.write_text(out_html, encoding="utf-8")
print(f"wrote {out.relative_to(ROOT)} ({out.stat().st_size // 1024} KB) with engine from {sims[-1].name}")
