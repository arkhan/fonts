#!/usr/bin/env python3
"""Shape sample strings with a built font and fail if generic tags misbehave.

usage: check_tags.py FONT.ttf
"""
import sys

import uharfbuzz as hb

PILL = [  # must become tags
    "[T]", "(T)", "<T>", "[abc_1]", "(TODO)", "a (B) c", "<A_B>", "x = [A-1]", "[INFO]", "[123456789012]",
]
PLAIN = [  # ordinary code must stay untouched
    "arr[i]", "f(x)", "List<T>", "<div>", "(ab)", "[x](url)", "[a b]", "[1234567890123]", "if (done) {",
]

face = hb.Face(hb.Blob.from_file_path(sys.argv[1]))
font = hb.Font(face)


def shape(text, calt):
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(font, buf, {"calt": calt})
    return [i.codepoint for i in buf.glyph_infos]


def is_tag(text):
    # Merged CJK fonts drop glyph names, so compare the glyphs with and without calt instead.
    return shape(text, True) != shape(text, False)


bad = [t for t in PILL if not is_tag(t)] + [t for t in PLAIN if is_tag(t)]
for t in bad:
    print("FAIL:", repr(t), "should be", "a tag" if t in PILL else "plain")
print("generic tags:", "FAILED" if bad else "ok", f"({len(PILL)} tags, {len(PLAIN)} plain)")
sys.exit(1 if bad else 0)
