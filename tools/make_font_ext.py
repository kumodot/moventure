#!/usr/bin/env python3
"""
Builds the extended 5x7 glyphs for Portuguese (and Spanish) accented letters and
writes tools/font_ext.txt as a JS object literal: { charCode: [5 column bytes], ... }.

Rules (LSB = top row):
- lowercase letters in the Adafruit font occupy rows 2-6, so the accent goes in rows 0-1.
- uppercase accented letters use a compressed 5-row capital (rows 2-6) + accent in rows 0-1.
- c-cedilla: the letter is lifted one row and the cedilla sits in row 6.
Run this after editing, then rebuild the simulator (the table is pasted by build scripts).
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent
FONT = [int(x, 16) for x in (ROOT / "font_5x7.txt").read_text().strip().split(",")]


def glyph(ch):
    base = (ord(ch) - 32) * 5
    return FONT[base:base + 5]


# accents in rows 0-1 (column bytes)
ACUTE = [0x00, 0x00, 0x02, 0x01, 0x00]
GRAVE = [0x00, 0x01, 0x02, 0x00, 0x00]
CIRC = [0x00, 0x02, 0x01, 0x02, 0x00]
TILDE = [0x02, 0x01, 0x02, 0x01, 0x00]
UMLAUT = [0x00, 0x01, 0x00, 0x01, 0x00]

# compressed 5-row capitals, bit0 = top of the 5 rows; shifted down 2 rows when used
CAP5 = {
    "A": [0x1E, 0x05, 0x05, 0x05, 0x1E],
    "E": [0x1F, 0x15, 0x15, 0x15, 0x11],
    "I": [0x00, 0x11, 0x1F, 0x11, 0x00],
    "O": [0x0E, 0x11, 0x11, 0x11, 0x0E],
    "U": [0x0F, 0x10, 0x10, 0x10, 0x0F],
    "C": [0x0E, 0x11, 0x11, 0x11, 0x0A],
    "N": [0x1F, 0x02, 0x04, 0x08, 0x1F],
}
DOTLESS_I = [0x00, 0x44, 0x7C, 0x40, 0x00]      # 'i' without its dot (rows 2-6)


def combine(letter_cols, accent):
    return [a | b for a, b in zip(letter_cols, accent)]


def cap(letter, accent):
    return combine([c << 2 for c in CAP5[letter]], accent)


ext = {}
for ch, base, acc in [
    ("á", "a", ACUTE), ("à", "a", GRAVE), ("â", "a", CIRC), ("ã", "a", TILDE), ("ä", "a", UMLAUT),
    ("é", "e", ACUTE), ("è", "e", GRAVE), ("ê", "e", CIRC), ("ë", "e", UMLAUT),
    ("ó", "o", ACUTE), ("ò", "o", GRAVE), ("ô", "o", CIRC), ("õ", "o", TILDE), ("ö", "o", UMLAUT),
    ("ú", "u", ACUTE), ("ù", "u", GRAVE), ("û", "u", CIRC), ("ü", "u", UMLAUT),
    ("ñ", "n", TILDE),
]:
    ext[ch] = combine(glyph(base), acc)
for ch, acc in [("í", ACUTE), ("ì", GRAVE), ("î", CIRC), ("ï", UMLAUT)]:
    ext[ch] = combine(DOTLESS_I, acc)
for ch, letter, acc in [
    ("Á", "A", ACUTE), ("À", "A", GRAVE), ("Â", "A", CIRC), ("Ã", "A", TILDE), ("Ä", "A", UMLAUT),
    ("É", "E", ACUTE), ("È", "E", GRAVE), ("Ê", "E", CIRC), ("Ë", "E", UMLAUT),
    ("Í", "I", ACUTE), ("Ì", "I", GRAVE), ("Î", "I", CIRC), ("Ï", "I", UMLAUT),
    ("Ó", "O", ACUTE), ("Ò", "O", GRAVE), ("Ô", "O", CIRC), ("Õ", "O", TILDE), ("Ö", "O", UMLAUT),
    ("Ú", "U", ACUTE), ("Ù", "U", GRAVE), ("Û", "U", CIRC), ("Ü", "U", UMLAUT),
    ("Ñ", "N", TILDE),
]:
    ext[ch] = cap(letter, acc)
# cedilla: lift the letter one row, hook in row 6 under column 2
c = glyph("c")
ext["ç"] = [(v >> 1) for v in c]; ext["ç"][2] |= 0x40
C = [v << 1 for v in CAP5["C"]]           # rows 1-5
ext["Ç"] = C[:]; ext["Ç"][2] |= 0x40
# a few extras that show up in prose
ext["º"] = [0x00, 0x06, 0x09, 0x09, 0x06]
ext["ª"] = [0x00, 0x0A, 0x0A, 0x0E, 0x00]   # tiny a-ish
ext["¡"] = [0x00, 0x00, 0x7D, 0x00, 0x00]
ext["¿"] = [0x00, 0x30, 0x4A, 0x44, 0x00]
ext["°"] = [0x00, 0x06, 0x09, 0x06, 0x00]

lines = ["{"]
for ch in sorted(ext, key=ord):
    lines.append(f"  {ord(ch)}: [{', '.join('0x%02X' % v for v in ext[ch])}],  // {ch}")
lines.append("}")
(ROOT / "font_ext.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"wrote tools/font_ext.txt with {len(ext)} glyphs")

if __name__ == "__main__" and "--show" in __import__("sys").argv:
    for ch in "ãÉçÇíÔ":
        cols = ext[ch]
        for row in range(7):
            print("".join("#" if (cols[i] >> row) & 1 else "." for i in range(5)), end="   ")
        print(ch)
