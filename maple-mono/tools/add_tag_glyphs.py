#!/usr/bin/env python3
"""
Add tag background ("pill") glyphs for digits, underscore and hyphen to Maple Mono's masters.

Upstream draws a tag character `X.bg` as a full-cell rectangle with the character cut out of
it, and ships A.bg..Z.bg only. Every master uses the same outline for these glyphs: the
ExtraBold (or ExtraBoldItalic) glyph, so tags look identical at every weight and the glyph
stays interpolation-compatible. This adds the missing characters the same way.

usage: add_tag_glyphs.py SOURCES_DIR           add missing glyphs (idempotent)
       add_tag_glyphs.py --check SOURCES_DIR   rebuild existing letters and compare them
"""
import sys
from pathlib import Path

import ufoLib2
from fontTools.pens.recordingPen import DecomposingRecordingPen

EXTRA = [
    (name, name + ".bg")
    for name in "zero one two three four five six seven eight nine underscore hyphen".split()
]
CHECK = [(n, n + ".bg") for n in ("T", "O", "I", "A", "M", "S", "J", "Q")]


def contour_points(glyph):
    return [[(p.x, p.y, p.type) for p in c.points] for c in glyph.contours]


def build(font, heavy, src_name, dst_name, *, replace=False):
    if dst_name in font and not replace:
        return False
    rect = font["T.bg"].contours[0]  # the cell bar, with upstream's point order
    glyph = font[dst_name] if dst_name in font else font.newGlyph(dst_name)
    glyph.clearContours()
    glyph.width = font["T.bg"].width
    pen = glyph.getPen()
    pen.moveTo((rect.points[0].x, rect.points[0].y))
    for p in rect.points[1:]:
        pen.lineTo((p.x, p.y))
    pen.closePath()
    rec = DecomposingRecordingPen(heavy)
    heavy[src_name].draw(rec)  # the character keeps its direction: it cuts a hole in the bar
    rec.replay(pen)
    return True


def main(argv):
    check = "--check" in argv
    root = Path([a for a in argv if not a.startswith("--")][0])
    ok = True
    for path in sorted(root.glob("MapleMono-*.ufo")):
        italic = "Italic" in path.name
        heavy = ufoLib2.Font.open(root / ("MapleMono-ExtraBoldItalic.ufo" if italic else "MapleMono-ExtraBold.ufo"))
        font = ufoLib2.Font.open(path)
        if check:
            for src, dst in CHECK:
                ref = contour_points(font[dst])
                build(font, heavy, src, dst, replace=True)
                same = contour_points(font[dst]) == ref
                ok &= same
                if not same:
                    print(path.name, dst, "DIFFERENT")
            print(path.name, "letters identical" if ok else "MISMATCH")
            continue
        added = [dst for src, dst in EXTRA if build(font, heavy, src, dst)]
        if added:
            order = list(font.glyphOrder)
            if order:
                font.glyphOrder = order + [g for g in added if g not in order]
            font.save(overwrite=True)
        print(path.name, "added", len(added), "glyphs")
    return 0 if ok else 1


sys.exit(main(sys.argv[1:]))
