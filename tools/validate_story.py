#!/usr/bin/env python3
"""
Moventure story validator.

Checks a story JSON for broken links, dead ends, unreachable nodes and
OLED screen budget violations, then prints stats and (optionally) a Mermaid graph.

Usage:
    python validate_story.py stories/hollow_lighthouse.json
    python validate_story.py stories/hollow_lighthouse.json --mermaid > graph.md
    python validate_story.py stories/*.json --quiet
"""

import argparse
import json
import re
import sys
from collections import deque
from pathlib import Path

# Screen budget for 128x64 with the 5x7 font (see STORY_FORMAT.md)
TEXT_COLS = 21
TEXT_ROWS = 7
MAX_LABEL = 19
MAX_TITLE = 15
CATEGORIES = ["Horror", "Mystery", "Fantasy", "Sci-Fi", "Adventure", "Kids", "SCP"]
CMP_RE = re.compile(r"^(\w+)(>=|<=|==|!=|>|<)(-?\d+)$")


NORMALIZE = {"\u2018": "'", "\u2019": "'", "\u201A": "'", "\u201C": '"', "\u201D": '"', "\u201E": '"',
             "\u2013": "-", "\u2014": "-", "\u2026": "...", "\u00A0": " "}


def normalize(text):
    """Typographic quotes / dashes / ellipsis -> plain, exactly like the simulator."""
    for k, v in NORMALIZE.items():
        text = text.replace(k, v)
    return text


def _font_chars():
    """Every character the device can draw: ASCII 32..126 plus tools/font_ext.txt."""
    chars = set(chr(c) for c in range(32, 127)) | {"\n"}
    ext = Path(__file__).resolve().parent / "font_ext.txt"
    if ext.exists():
        for m in re.finditer(r"^\s*(\d+):", ext.read_text(encoding="utf-8"), re.M):
            chars.add(chr(int(m.group(1))))
    return chars


FONT_CHARS = _font_chars()


LANGS = ["en", "pt", "es"]


def loc(x, lang):
    """A localized string is either a plain string or {"en": ..., "pt": ...}."""
    if isinstance(x, dict):
        return x.get(lang) or ""
    return x or ""


def book_langs(meta):
    t = meta.get("title")
    if isinstance(t, dict):
        return [l for l in LANGS if t.get(l)]
    return [meta.get("lang", "en")]


def unsupported(text):
    return sorted(set(c for c in normalize(text) if c not in FONT_CHARS))


def wrap(text, cols=TEXT_COLS):
    """Same word-wrap the simulator uses, so page counts match."""
    lines = []
    for para in normalize(text).split("\n"):
        line = ""
        for word in para.split(" "):
            if not word:
                continue
            while len(word) > cols:          # hard-break giant words
                if line:
                    lines.append(line)
                    line = ""
                lines.append(word[:cols])
                word = word[cols:]
            if not line:
                line = word
            elif len(line) + 1 + len(word) <= cols:
                line += " " + word
            else:
                lines.append(line)
                line = word
        lines.append(line)
    return lines


def passes(require, flags):
    """Flag checks are exact. Stat comparisons are treated as 'could go either way'
    (the walker does not track stat values), so they never hide an edge here."""
    for r in require or []:
        if CMP_RE.match(r):
            continue
        if r.startswith("!"):
            if r[1:] in flags:
                return False
        elif r not in flags:
            return False
    return True


def edges(node):
    """Every outgoing edge as (target, set, clear, label). Rolls contribute pass and fail."""
    out = []
    for c in node.get("choices", []):
        if c.get("roll"):
            out.append((c["roll"].get("pass"), c.get("set", []), c.get("clear", []), loc(c.get("label", ""), "en") + " PASS"))
            out.append((c["roll"].get("fail"), c.get("set", []), c.get("clear", []), loc(c.get("label", ""), "en") + " FAIL"))
        else:
            out.append((c.get("to"), c.get("set", []), c.get("clear", []), loc(c.get("label", ""), "en")))
    if node.get("goto"):
        out.append((node["goto"], [], [], ""))
    if node.get("roll"):
        out.append((node["roll"].get("pass"), [], [], "fate PASS"))
        out.append((node["roll"].get("fail"), [], [], "fate FAIL"))
    return out


def check_roll(nid, label, roll, nodes, stats, errors):
    if not re.match(r"^\d+d\d+$", roll.get("dice", "1d6")):
        errors.append(f"{nid}: roll '{label}' has bad dice '{roll.get('dice')}' (use NdS, e.g. 1d6)")
    if not isinstance(roll.get("dc"), int):
        errors.append(f"{nid}: roll '{label}' needs an integer dc")
    for k in ("pass", "fail"):
        if roll.get(k) not in nodes:
            errors.append(f"{nid}: roll '{label}' {k} -> unknown node '{roll.get(k)}'")
    if roll.get("stat") and roll["stat"] not in stats:
        errors.append(f"{nid}: roll '{label}' uses stat '{roll['stat']}' not declared in meta.stats")


def check_effects(nid, obj, stats, errors, uses):
    for k in obj.get("mod", {}):
        uses["stats"] = True
        if k not in stats:
            errors.append(f"{nid}: mod on '{k}' but it is not in meta.stats")
    for r in obj.get("require", []) or []:
        m = CMP_RE.match(r)
        if m:
            uses["stats"] = True
            if m.group(1) not in stats:
                errors.append(f"{nid}: require '{r}' uses stat '{m.group(1)}' not declared in meta.stats")


def validate(path, mermaid=False, quiet=False):
    with open(path, encoding="utf-8") as f:
        book = json.load(f)

    errors, warnings = [], []
    nodes = book.get("nodes", {})
    meta = book.get("meta", {})
    start = meta.get("start")
    stats = meta.get("stats", {})
    uses = {"roll": False, "stats": bool(stats)}
    if start not in nodes:
        errors.append(f"meta.start '{start}' is not a node")
    if meta.get("category") not in CATEGORIES:
        warnings.append(f"meta.category '{meta.get('category')}' not in {CATEGORIES}")
    if not meta.get("license"):
        warnings.append("meta.license missing (e.g. 'CC BY-NC-ND 4.0', 'CC BY-SA 3.0', 'All rights reserved')")
    if meta.get("category") == "SCP" or meta.get("based_on"):
        if "BY-SA" not in str(meta.get("license", "")):
            warnings.append("derived from a CC BY-SA source: meta.license should be CC BY-SA")
        if not meta.get("based_on"):
            warnings.append("meta.based_on missing (source title, author and URL are required for derived works)")
    tier = meta.get("tier", 1)
    if tier not in (1, 2, 3):
        errors.append(f"meta.tier must be 1, 2 or 3 (got {tier!r})")

    # --- structural checks ---------------------------------------------------
    langs = book_langs(meta)
    for nid, n in nodes.items():
        if "text" not in n:
            errors.append(f"{nid}: missing text")
        for lang in langs:
            title = loc(n.get("title", ""), lang)
            if len(title) > MAX_TITLE:
                warnings.append(f"{nid}: title '{title}' is {len(title)} chars (max {MAX_TITLE})")
            if len(langs) > 1 and "text" in n and not loc(n["text"], lang):
                warnings.append(f"{nid}: text has no '{lang}' translation")
            labels = [loc(c.get("label", ""), lang) for c in n.get("choices", [])]
            for lab in labels:
                if len(lab) > MAX_LABEL:
                    warnings.append(f"{nid}: label '{lab}' is {len(lab)} chars (max {MAX_LABEL})")
                if len(langs) > 1 and not lab:
                    warnings.append(f"{nid}: a choice label has no '{lang}' translation")
            bad_chars = unsupported(loc(n.get("text", ""), lang) + title + "".join(labels))
            if bad_chars:
                warnings.append(f"{nid}: characters with no glyph on the device, shown as '?': {' '.join(bad_chars)}")
        choices = n.get("choices", [])
        for c in choices:
            if c.get("roll"):
                check_roll(nid, loc(c.get("label", ""), "en"), c["roll"], nodes, stats, errors)
                uses["roll"] = True
                if "to" in c:
                    warnings.append(f"{nid}: choice '{c.get('label')}' has both 'to' and 'roll' ('to' is ignored)")
            elif c.get("to") not in nodes:
                errors.append(f"{nid}: choice '{c.get('label')}' -> unknown node '{c.get('to')}'")
            check_effects(nid, c, stats, errors, uses)
        check_effects(nid, n, stats, errors, uses)
        if n.get("goto") and n["goto"] not in nodes:
            errors.append(f"{nid}: goto -> unknown node '{n['goto']}'")
        if n.get("roll"):
            check_roll(nid, "fate", n["roll"], nodes, stats, errors)
            uses["roll"] = True
        if not choices and not n.get("ending") and not n.get("goto") and not n.get("roll"):
            errors.append(f"{nid}: dead end (no choices, no ending, no goto, no roll)")
        if n.get("ending") and (choices or n.get("goto") or n.get("roll")):
            warnings.append(f"{nid}: ending node also has choices/goto/roll (they will be ignored)")

    # --- reachability with flag states (state = node + frozenset of flags) ---
    reachable_nodes = set()
    endings_hit = set()
    dead_states = []
    if start in nodes:
        seen = set()
        q = deque([(start, frozenset())])
        while q:
            nid, flags = q.popleft()
            if (nid, flags) in seen:
                continue
            seen.add((nid, flags))
            reachable_nodes.add(nid)
            n = nodes[nid]
            flags = (flags | set(n.get("set", []))) - set(n.get("clear", []))
            if n.get("ending"):
                endings_hit.add(nid)
                continue
            if n.get("goto") or n.get("roll"):
                for to, st, cl, _ in edges(n):
                    if to in nodes:
                        q.append((to, frozenset((flags | set(st)) - set(cl))))
                continue
            visible = [c for c in n.get("choices", []) if passes(c.get("require"), flags)]
            if not visible:
                dead_states.append((nid, sorted(flags)))
            for c in visible:
                for to, st, cl, _ in edges({"choices": [c]}):
                    if to in nodes:
                        q.append((to, frozenset((flags | set(st)) - set(cl))))

    for nid in nodes:
        if nid not in reachable_nodes:
            warnings.append(f"{nid}: unreachable from start")
    for nid, flags in dead_states:
        errors.append(f"{nid}: no visible choice with flags {flags} (reader gets stuck)")

    # --- tier consistency: T1 = choices only, T2 = + rolls, T3 = + stats ------
    needed = 3 if uses["stats"] else 2 if uses["roll"] else 1
    if needed > tier:
        errors.append(f"book uses {'stats' if needed == 3 else 'dice rolls'} but declares tier {tier} (needs tier {needed})")
    elif needed < tier:
        warnings.append(f"book declares tier {tier} but only uses tier {needed} features")

    # --- stats ---------------------------------------------------------------
    total_pages = 0
    total_words = 0
    for n in nodes.values():
        txt = loc(n.get("text", ""), langs[0])
        lines = wrap(txt)
        total_pages += max(1, -(-len(lines) // TEXT_ROWS))
        total_words += len(txt.split())
    n_edges = sum(len(edges(n)) for n in nodes.values())
    endings = {k: v.get("ending") for k, v in nodes.items() if v.get("ending")}

    if not quiet:
        title = loc(meta.get("title", path), langs[0])
        print(f"== {title} ==")
        print(f"tier {tier}  {meta.get('category', '?')}  langs: {'/'.join(langs)}  nodes: {len(nodes)}  edges: {n_edges}  pages: {total_pages}  words: {total_words}")
        print(f"endings: {len(endings)} ({', '.join(f'{k}:{v}' for k, v in endings.items())})")
        print(f"reachable endings: {len(endings_hit)}/{len(endings)}")
        for w in warnings:
            print("  WARN ", w)
        for e in errors:
            print("  ERROR", e)
        print("OK" if not errors else f"FAILED ({len(errors)} errors)")

    if mermaid:
        print(to_mermaid(book))

    return not errors


def to_mermaid(book):
    nodes = book["nodes"]
    out = ["```mermaid", "flowchart TD"]
    lang = book_langs(book.get("meta", {}))[0]
    for nid, n in nodes.items():
        label = (loc(n.get("title", ""), lang) or nid).replace('"', "'")
        if n.get("ending") == "good":
            out.append(f'    {nid}(["{label}"]):::good')
        elif n.get("ending") == "bad":
            out.append(f'    {nid}(["{label}"]):::bad')
        elif n.get("ending"):
            out.append(f'    {nid}(["{label}"]):::neutral')
        else:
            out.append(f'    {nid}["{label}"]')
    for nid, n in nodes.items():
        if n.get("goto"):
            out.append(f"    {nid} -.-> {n['goto']}")
        if n.get("roll"):
            out.append(f'    {nid} -.->|"fate {n["roll"].get("dice", "1d6")} vs {n["roll"].get("dc")} PASS"| {n["roll"].get("pass")}')
            out.append(f'    {nid} -.->|"fate FAIL"| {n["roll"].get("fail")}')
        for c in n.get("choices", []):
            if c.get("roll"):
                r = c["roll"]
                lab = (loc(c.get("label", ""), lang) + f" ({r.get('dice', '1d6')}" + (f"+{r['stat']}" if r.get("stat") else "") + f" vs {r.get('dc')})").replace('"', "'")
                out.append(f'    {nid} -.->|"{lab} PASS"| {r.get("pass")}')
                out.append(f'    {nid} -.->|"{lab} FAIL"| {r.get("fail")}')
                continue
            lab = loc(c.get("label", ""), lang)
            tags = []
            if c.get("require"):
                tags.append("?" + ",".join(c["require"]))
            if c.get("set"):
                tags.append("+" + ",".join(c["set"]))
            if c.get("clear"):
                tags.append("-" + ",".join(c["clear"]))
            if tags:
                lab += " (" + " ".join(tags) + ")"
            lab = lab.replace('"', "'")
            arrow = "-->" if not c.get("require") else "-.->"
            out.append(f'    {nid} {arrow}|"{lab}"| {c["to"]}')
    out.append("    classDef good fill:#2e7d32,color:#fff")
    out.append("    classDef bad fill:#b71c1c,color:#fff")
    out.append("    classDef neutral fill:#616161,color:#fff")
    out.append("```")
    return "\n".join(out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+")
    ap.add_argument("--mermaid", action="store_true", help="print a Mermaid flowchart of the story graph")
    ap.add_argument("--quiet", action="store_true", help="only print errors")
    args = ap.parse_args()
    ok = True
    for f in args.files:
        ok = validate(f, mermaid=args.mermaid, quiet=args.quiet) and ok
    sys.exit(0 if ok else 1)
