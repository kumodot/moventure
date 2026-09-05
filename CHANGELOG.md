# Changelog

Versioning rule for this project: every release bumps `APP_VERSION` inside the simulator
**and** the file name (`simulator/moventure_sim_vX.Y.Z.html`). The version shows in the
browser tab, the page header, the device bezel, the boot screen and the About screen.
`run_sim.bat` always opens the newest file. Old versions can be kept or deleted, they are
self-contained (they only share `stories.js`).

## Books - 2026-09-05 (Foundation Files no. 2-11)
- Ten new SCP gamebooks, EN + PT-BR, 27-30 nodes and 6-8 endings each, all CC BY-SA 3.0 with
  `based_on` credits: 173: Blink (T2), 096: The Face (T2), 049: The Cure (T3), 106: Pocket (T3),
  914: Very Fine (T2), 682: The Acid (T3), 3008: Closing (T3), 1730: Site-13 (T3),
  2521: Hush (T1), 1471: MalO (T2). The catalog now has 14 books.
- `build_catalog.py` orders series books by their number ("Foundation Files, no. N").

## 0.7.0 / Studio 0.4.0 - 2026-09-05 (your own books)
- **Load a book**: button in player mode (and in the sim header), or drag a `.json` onto the page.
  The book goes to the browser's own library and opens on its cover. Works online and in the
  local sim / single-file player.
- **My books** shelf in the LIBRARY (right after All) lists everything added by the reader:
  loaded files, QR / `?add=` books and books sent from the Studio. It only appears when there
  is something in it.
- **Remove book** in the menu of any My books title, with a yes / no screen.
- Studio: **Open in Player** button. Saves the book straight into the Player's My books (same
  site, same browser) and opens the Player on its cover: no export, no file. Export JSON is
  still there for sharing the file.
- Fixed `build_player.py` (the single-file player was not starting in player mode since 0.6.0).

## 0.6.0 - 2026-09-04 (first online release)
- Online mode: when served over http(s) with no stories.js, the player loads `catalog.json`
  and fetches each book. `?book=<id>` opens a cover directly (the portal's Play buttons);
  `?add=<url>` fetches any Moventure JSON, keeps it in the browser's own library
  (localStorage) and opens it: this is what QR codes will point at.
- `tools/build_catalog.py` (validated books only, gen_* and test books skipped),
  `tools/build_site.py` builds `docs/` for GitHub Pages: portal (`site/index_template.html`,
  pixel covers drawn per category, EN / PT-BR), `player/`, `studio/`, `stories/`, `catalog.json`.
- Repo hygiene: `.gitignore` (generated files, local folders, .bat), MIT LICENSE for the code,
  `publish.bat` (rebuild + commit + push).

## Studio 0.3.0 - 2026-09-04 (manuscript mode)
- Rewritten editor: write the story top to bottom like a manuscript. Put the cursor where the
  text should split and pick **Fork here** from the ⋯ menu: what follows becomes path A, an
  empty path B opens. **Random event here** splits the same way with the dice deciding
  (paths P / F). The End and Go to live in the same menu; nothing else is on screen.
- Paths have codes built from the reader's choices (START, A, B, A-B, A-P, A-B-F…). Each path
  folds to one line (code, first words, blocks / words / endings, problem dot). Opening a path
  folds its siblings (focus mode); "Expand all" shows the whole tree; breadcrumb on top.
- Conditions are now "only if the reader went through A-B" with a dropdown, no dialogs.
- Silent forks (no question text) attach the choices to the previous paragraph on export, and
  pure Go to blocks vanish on export, so imported books round-trip node for node.
- Extra meta (based_on, series, stats) survives import/export; tier 3 books warn that stats
  are not editable yet. License picker under ⋯ in the header.

## 0.5.2 / Studio 0.2.2 - 2026-09-04
- New category SCP (device, validator, Studio). `meta.license` is now expected on every book
  (validator warns), and `meta.based_on` is required for derived works; SCP books must be
  CC BY-SA. All shipped books got a license.
- New book: "087: Descent" / "087: Descida" (Foundation Files no. 1), tier 2, EN + PT-BR,
  adapted from SCP-087 (Zaeyde, SCP wiki, CC BY-SA 3.0). 26 nodes, 8 endings.

## 0.5.1 - 2026-09-04
- Portrait phone layout in player mode: the 128x64 screen stays exactly the same, only the
  arrangement changes (screen on top, big D-pad and A/B for thumbs, safe-area aware, buttons
  react on touch-down). Landscape / desktop layout unchanged.

## 0.5.0 / Studio 0.2.1 - 2026-09-04
- Interface language and book language are now separate. "Idioma / Language" in the menu is
  the device UI (EN, PT-BR, ES; remembered). The book language is chosen per book, only among
  the languages the author provided: Left / Right on the cover (active tag highlighted) or
  "Book: XX" in the menu while reading. Books default to the UI language when they have it.
- Spanish UI strings. Studio gets an ES writing tab. Validator knows es.

## 0.4.0 / Studio 0.2.0 - 2026-09-04
- Bilingual books: any reader-facing string can be `{"en": ..., "pt": ...}`; `meta.langs`.
  Device Language setting in the menu (EN / PT-BR, remembered), whole device UI translated
  (BIBLIOTECA, ESCOLHA, FIM, DADO, ATRIBUTOS, categorias...). Cover shows which languages
  the book has. Books without the chosen language fall back to English.
- The Hollow Lighthouse, The Last Train to Halvard and The Bronze Gate translated to PT-BR
  (`tools/translations/*.pt.json`, merged with `tools/merge_translation.py`). A Casa do Farol
  got an English version.
- Validator checks every language (labels, missing translations, glyphs).
- Studio: EN / PT-BR toggle at the top; every field keeps one version per language, the other
  language shows as the placeholder so translating is filling blanks; "no PT text yet" checks;
  export writes plain strings when only one language is filled.

## 0.3.2 / Studio 0.1.1 - 2026-09-04
- Portuguese (and Spanish) accents on the OLED: á à â ã é ê í ó ô õ ú ü ç, their capitals,
  ñ / Ñ, º ª ¿ ¡ °. Extended 5x7 glyphs in `tools/font_ext.txt`, generated by
  `tools/make_font_ext.py` (lowercase keep their shape with the accent in the top 2 rows;
  accented capitals use a compact 5-row capital). Curly quotes, en/em dashes and the
  ellipsis are normalized to plain characters, same in the validator.
- Validator warns about any character the device cannot draw.
- New test book `stories/teste_acentos.json` (A Casa do Farol, in Portuguese).
- Studio rebuilt with the new engine (0.1.1).

## Studio 0.1.0 - 2026-09-04
- First Moventure Studio (`studio/moventure_studio_vX.Y.Z.html`, `run_studio.bat`): a
  non-technical, top-to-bottom block editor. Text blocks, question blocks with 2-6 outputs,
  each output opens its own indented path; The End (good / neutral / bad), Go to block,
  Roll the dice (pass / fail paths), "only if the reader chose…" conditions. Blocks connect
  themselves; tier is worked out from the features used. Live device preview (same engine as
  the sim, injected at build time), plain-language checks, autosave in the browser, several
  stories per browser, Export / Import JSON (any existing book imports; loops become Go to).

## 0.3.1 - 2026-09-04
- Keyboard: A and B keys map to the A and B buttons (Z / X / Enter / Esc still work).

## 0.3.0 - 2026-09-04
- Player mode: only the device, scaled to fit the window, Fullscreen button. Toggle with the
  "Player mode" button or `?player=1` in the URL.
- Gamepad support (standard mapping: Steam Deck, Xbox, PS): d-pad, left stick with auto-repeat,
  A = A, B = B. Status in the bottom-left corner while in player mode.
- `tools/build_player.py`: single-file `simulator/moventure_player_vX.Y.Z.html` with all books
  inlined, starts in player mode. Send that one file to anyone. `run_sim.bat` builds it too.

## 0.2.1 - 2026-09-04
- UP while reading opens the STATS sheet (tier 3 books; any button returns). UP was
  redundant with LEFT / B before.
- Stat changes flash on the reader status bar for ~2 s (`+3 LUCK`, `-1 GRIT`), queued one
  after another when several change at once.

## 0.2.0 - 2026-09-04
- Story format v2: `meta.tier` (1 choices / 2 + dice / 3 + stats), `meta.category`,
  `choice.roll` and node `roll` (NdS + stat vs dc, pass/fail targets, `hidden`),
  `meta.stats` + `mod`, stat comparisons in `require` (e.g. `grit>0`).
- New screens: COVER (category, tier, blurb before starting), DICE (tumbling wireframe
  cube, then real pip faces; big number for d8+), STATS (bars, from the menu).
- LIBRARY: shelves by category (Left / Right), tier tag on every row, marquee at 16 cols.
- Status bar titles marquee too (cover and reader).
- Live map draws roll edges: green = pass, red = fail.
- Validator: rolls, stats, tier consistency, category check. Generator: `--tier 1|2|3`.
- New hand-written books: "The Last Train to Halvard" (Mystery, T2),
  "The Bronze Gate" (Fantasy, T3). Lighthouse tagged Horror, T1.
- Generated books renamed gen_*_t1/t2/t3.json (old derelict_starship / salt_tomb /
  blackpine removed).

## 0.1.2 - 2026-09-04
- Marquee: a selected list item (library title, choice label, menu) that does not fit the
  19-column row now pauses, then scrolls horizontally and loops. Restarts when the cursor moves.

## 0.1.1 - 2026-09-04
- Version number in file name, tab title, header, device bezel, boot and About screens.
- `run_sim.bat`: rebuilds `stories.js` and opens the newest simulator.
- CHANGELOG added.

## 0.1.0 - 2026-09-04
- First simulator: SSD1306 128x64, D-pad + A/B, keyboard mapping, boot / library / reader /
  choice / ending / menu / about screens, live story map, flags panel, JSON loader.
- Story format v1, reference book "The Hollow Lighthouse".
- Generator (starship / tomb / forest themes), validator, stories.js bundler.
