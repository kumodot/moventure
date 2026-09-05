# Moventure Story Format (v2)

A Moventure "book" is one JSON file. Underneath the prose it is a directed graph:
every **node** is a page (or a short run of pages) and every **choice** is an edge.
Flags, dice rolls and stats turn edges on and off, which is what makes the same graph
tell different stories depending on what the reader did (and rolled) earlier.

## Tiers and categories

Every book declares what it needs from the reader, so the shelf can say it up front:

| tier | name | uses | feel |
|---|---|---|---|
| 1 | Choices | `choices`, flags | classic "turn to page 42" gamebook |
| 2 | Choices + dice | + `roll` | Lone Wolf style, luck matters |
| 3 | Choices + dice + stats | + `meta.stats`, `mod`, stat comparisons in `require` | pocket RPG, Fighting Fantasy style |

The validator refuses a book that uses features above its declared tier, and warns when a
book declares a higher tier than it uses.

`meta.category` is one of: `Horror`, `Mystery`, `Fantasy`, `Sci-Fi`, `Adventure`, `Kids`, `SCP`.
Books adapted from the SCP Foundation wiki (CC BY-SA 3.0) go in `SCP`, must credit the entry in
`meta.based_on` and must carry `"license": "CC BY-SA 3.0"`.
The library groups books by category (Left / Right on the device changes the shelf).

## Languages

Any reader-facing string (`meta.title`, `meta.blurb`, node `title` and `text`, choice `label`)
is either a plain string or an object with one entry per language:

```json
"text": { "en": "The door is ajar.", "pt": "A porta está entreaberta." }
```

`meta.langs` lists the languages the book carries (`["en", "pt"]`; `es` also supported). The
device keeps two settings apart: the interface language (menu) and the book language, which
the reader picks per book among the languages the author provided (cover: Left / Right; menu:
Book). A book defaults to the interface language when it has it, else to its first language. One file, one graph, all languages: the structure cannot drift between
translations. The validator checks every language (label length, missing translations,
characters with no glyph). `tools/merge_translation.py` merges a translation overlay into a
book; Moventure Studio edits both languages side by side.

## Structure

```
book
 ├─ meta
 │    ├─ title, author, version, blurb (blurb shows on the cover screen, <= 4 lines)
 │    ├─ tier        1 | 2 | 3
 │    ├─ category    see list above
 │    ├─ start       id of the first node
 │    ├─ license     e.g. "CC BY-NC-ND 4.0", "CC BY-SA 3.0", "CC0", "All rights reserved"
 │    ├─ based_on    for derived works: source title, author, URL and its license (required)
 │    ├─ series      optional series name shown nowhere yet (catalog use)
 │    └─ stats       tier 3 only: starting values, e.g. { "luck": 2, "aim": 2, "grit": 5 }
 ├─ flags            optional list of known flag names (documentation for editors)
 └─ nodes            { id: node, ... }
      ├─ title       caption on the status bar (<= 15 chars; longer titles marquee). Localizable.
      ├─ text        page text. "\n" starts a new paragraph. Auto word-wrapped and paginated. Localizable.
      ├─ set / clear flags applied on entering the node
      ├─ mod         stats applied on entering the node, e.g. { "grit": -1 }
      ├─ choices[]   edges out of this node
      │    ├─ label     <= 19 chars (longer labels marquee when selected). Localizable.
      │    ├─ to        target node id (omit when using roll)
      │    ├─ require   list of conditions, all must hold (see below)
      │    ├─ set / clear / mod   applied when the choice is taken
      │    └─ roll      dice check instead of a fixed target (see below)
      ├─ goto        auto-jump after the text, no choice shown
      ├─ roll        node-level "fate" roll after the text, no choice shown
      └─ ending      "good" | "bad" | "neutral" -> terminal page
```

### Conditions (`require`)

```
"has_key"      flag must be set
"!has_key"     flag must NOT be set
"grit>0"       stat comparison: >  >=  <  <=  ==  !=   (tier 3)
```

A choice whose `require` fails is simply not shown. Two choices with the same label and
complementary requirements is the normal way to write "same action, different outcome".

### Dice (`roll`)

```json
{ "label": "Strike the match",
  "roll": { "dice": "1d6", "stat": "luck", "dc": 4,
            "pass": "match_lit", "fail": "match_wet", "hidden": false } }
```

Roll `dice` (`NdS`), add the value of `stat` if given, compare with `dc`: total >= dc is a
pass. The device shows the roll on the DICE screen (a tumbling cube, then the pip face and
`5+2=7 vs 4 PASS`). `hidden: true` skips the screen and the reader only sees the consequence
in the prose. A node can carry a `roll` of its own (fate, no choice).

### Stats (`meta.stats`, `mod`)

Small integers, clamped to 0..99 by the engine. `mod` adds (negative subtracts). The
STATS screen (menu) shows each stat with a bar where 10 is full. A combat loop is just:

```json
"fight": { "text": "...", "choices": [
  { "label": "Attack", "roll": { "dice": "1d6", "stat": "aim", "dc": 6, "pass": "win", "fail": "miss" } } ] },
"miss":  { "text": "It hits back.", "mod": { "grit": -1 }, "choices": [
  { "label": "Get up",    "to": "fight", "require": ["grit>0"] },
  { "label": "Stay down", "to": "dead",  "require": ["grit<=0"] } ] }
```

## Rules the engine follows

1. The reader starts at `meta.start` with no flags and `meta.stats` as starting values.
2. On entering a node: apply `set` / `clear` / `mod`, show the text paginated
   (21 columns, 7 rows under the status bar).
3. On the last page, A does the first that applies: `ending` -> ending screen;
   `goto` -> jump; `roll` -> fate roll; otherwise open the choice menu with every
   choice whose `require` passes. No visible choice = dead end (validator error).
4. Taking a choice applies its `set` / `clear` / `mod`, then `roll` (if any) or `to`.
5. Rolls are decided the moment the choice is taken; the animation is only visual.

## Screen budget (why the length limits exist)

| Thing | Limit | Why |
|---|---|---|
| text column | 21 chars | 21 x 6 px = 126 px, 1 px margin each side |
| text rows per page | 7 | 8 px status bar + 1 px gap + 7 x 8 px rows |
| choice label | 19 chars | cursor ">" + space + label |
| library row | 16 chars | leaves room for the tier tag "T2" |
| node title | 15 chars | leaves room for the "2/3" page counter |
| visible choices | 6 | the menu scrolls beyond that |
| stats shown | 5 | one row each |

## Graph view

The same file is the map. `tools/validate_story.py --mermaid` prints it as a Mermaid
flowchart, and the simulator draws it live: current node highlighted, path taken in
yellow, `require` edges dashed, roll edges green (pass) / red (fail).

## Writing books with an LLM

Paste this file plus one example book into the prompt, name a theme, tier and category,
and ask for "N nodes, M flags, K endings, every ending reachable". Then run
`python tools/validate_story.py yourbook.json`. It catches what models get wrong: labels
too long, dead ends, flags required but never set, rolls pointing at missing nodes, a
tier that does not match the features used.
