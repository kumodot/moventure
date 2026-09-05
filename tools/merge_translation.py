#!/usr/bin/env python3
"""
Merge a translation overlay into a story, turning plain strings into {"en": ..., "pt": ...}.

Overlay format (tools/translations/<book>.<lang>.json):
    { "meta": {"title": "...", "blurb": "..."},
      "nodes": { "<node id>": {"title": "...", "text": "...", "labels": ["...", ...]} } }

Usage:
    python tools/merge_translation.py stories/hollow_lighthouse.json tools/translations/hollow_lighthouse.pt.json pt
"""

import json
import sys
from pathlib import Path


def localize(current, lang, value, base_lang="en"):
    """Return a {lang: text} object holding the existing value(s) plus the new one."""
    if isinstance(current, dict):
        out = dict(current)
    else:
        out = {base_lang: current} if current else {}
    if value:
        out[lang] = value
    return out


def merge(story_path, overlay_path, lang):
    story = json.loads(Path(story_path).read_text(encoding="utf-8"))
    ov = json.loads(Path(overlay_path).read_text(encoding="utf-8"))
    m = story["meta"]
    for k in ("title", "blurb"):
        if k in ov.get("meta", {}):
            m[k] = localize(m.get(k, ""), lang, ov["meta"][k])
    missing = []
    for nid, node in story["nodes"].items():
        o = ov.get("nodes", {}).get(nid)
        if not o:
            missing.append(nid)
            continue
        if "title" in o:
            node["title"] = localize(node.get("title", ""), lang, o["title"])
        if "text" in o:
            node["text"] = localize(node.get("text", ""), lang, o["text"])
        labels = o.get("labels", [])
        for i, c in enumerate(node.get("choices", [])):
            if i < len(labels):
                c["label"] = localize(c.get("label", ""), lang, labels[i])
            else:
                missing.append(f"{nid}: label {i}")
    langs = m.get("langs", ["en"])
    if lang not in langs:
        langs.append(lang)
    m["langs"] = langs
    Path(story_path).write_text(json.dumps(story, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"merged {lang} into {story_path}" + (f"  MISSING: {missing}" if missing else ""))


if __name__ == "__main__":
    merge(*sys.argv[1:4])
