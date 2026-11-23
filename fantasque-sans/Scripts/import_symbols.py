#!/usr/bin/env fontforge
"""
Import missing symbols (and braille) into copies of the Fantasque Sans Mono
.sfdir sources and normalise the geometric shapes to the font's cell.

Usage: fontforge -lang=py -script Scripts/import_symbols.py DIR...
  DIR = FantasqueSansMono-{Regular,Bold,Italic,BoldItalic}.sfdir (modified in place;
  run it on a copy, see Scripts/build_all.sh).

Donor fonts (env): DEJAVU_DIR (DejaVuSansMono[-Bold].ttf), CASCADIA_DIR (CascadiaCode-*.ttf).
All metrics derive from the font itself, so nothing is hardcoded for one em size.
Ligatures are NOT added: the font already ships its own (*.liga glyphs).
"""
import os
import subprocess
import sys
import unicodedata

import fontforge
import psMat

DEJAVU_DIR = os.environ.get('DEJAVU_DIR') or os.path.dirname(subprocess.check_output(
    ['fc-match', '-f', '%{file}', 'DejaVu Sans Mono']).decode())
CASCADIA_DIR = os.environ.get('CASCADIA_DIR', '/usr/share/fonts/truetype/cascadia')

# Symbols used by agent-shell / org-modern / terminals. Skipped when already present.
WANT = (
    '⎋␣⌃⌘⌥⇥␀␉␊␍'              # keyboard / control pictures
    '↵➡➔➙➞↪'                  # arrows
    '₹₿₺☆❤'                    # misc / currency
    '◆◇◈◉○◔◦□‣∥'              # shapes / bullets
    '▲▼▶◀△▽▷▸▹▾▿▴▵'            # triangles
    '➤❯⚠✶✳☑✓✗❝⬆⬇⯆⯈⧉⚹'      # agent-shell / org-modern
)
DONORS = ('dv', 'cc')
BRAILLE = range(0x2800, 0x2900)

VARIANTS = {'Regular': 'regular', 'Italic': 'regular', 'Bold': 'bold', 'BoldItalic': 'bold'}
SOURCES = {
    'regular': {'dv': 'DejaVuSansMono.ttf', 'cc': 'CascadiaCode-Regular.ttf', 'br': 'CascadiaCode-Regular.ttf'},
    'bold': {'dv': 'DejaVuSansMono-Bold.ttf', 'cc': 'CascadiaCode-Bold.ttf', 'br': 'CascadiaCode-Regular.ttf'},
}
DIRS = {'dv': DEJAVU_DIR, 'cc': CASCADIA_DIR, 'br': CASCADIA_DIR}


def bbox(g):
    b = g.boundingBox()
    return b[0], b[1], b[2], b[3], b[2] - b[0], b[3] - b[1]


def center(g, cx, cy, width):
    x0, y0, x1, y1, _, _ = bbox(g)
    g.transform(psMat.translate(cx - (x0 + x1) / 2, cy - (y0 + y1) / 2))
    g.width = width


def rescale(g, size, cx, cy, width):
    _, _, _, _, w, h = bbox(g)
    if not w or not h:
        return
    g.transform(psMat.scale(size / max(w, h)))
    center(g, cx, cy, width)


def fit(g, max_h, max_w, cx, cy, width):
    _, _, _, _, w, h = bbox(g)
    if not w or not h:
        g.width = width
        return
    s = min(max_h / h, max_w / w)
    if s < 0.99:
        g.transform(psMat.scale(s))
    center(g, cx, cy, width)


def process(path, style):
    dst = fontforge.open(path)
    W = dst['a'].width
    cap = bbox(dst[ord('H')])[3]
    # optical center of the existing filled circle, else mid cap height
    if ord('●') in dst:
        _, y0, _, y1, _, _ = bbox(dst[ord('●')])
        gcy = (y0 + y1) / 2
    else:
        gcy = cap / 2
    gcx = W / 2
    k = W / 575.0  # sizes below were tuned on a 575-unit cell

    srcs, seen = {}, {}
    for tag, name in SOURCES[VARIANTS[style]].items():
        p = os.path.join(DIRS[tag], name)
        if p not in seen:
            f = fontforge.open(p)
            f.em = dst.em
            seen[p] = f
        srcs[tag] = seen[p]

    have = {g.unicode for g in dst.glyphs() if g.unicode > 0}
    todo = [(ord(c), None) for c in WANT] + [(c, 'br') for c in BRAILLE]
    added, missing = 0, []
    for cp, forced in todo:
        if cp in have:
            continue
        tags = (forced,) if forced else DONORS
        src = next((srcs[t] for t in tags if cp in srcs[t] and srcs[t][cp].isWorthOutputting()), None)
        if src is None:
            missing.append(cp)
            continue
        src.selection.select(cp)
        src.copy()
        dst.createChar(cp)
        dst.selection.select(cp)
        dst.paste()
        g = dst[cp]
        if 0x2800 <= cp <= 0x28FF:
            g.transform(psMat.scale(W / g.width, 1))  # keep dot grid; only fit the advance
            g.width = W
        elif cp in (0x25C6, 0x25C7, 0x25C8, 0x25C9):
            rescale(g, 500 * k, gcx, gcy, W)
        elif cp in (0x25E6, 0x2023):
            center(g, gcx, gcy, W)
        else:
            fit(g, cap, W * 0.90, gcx, cap / 2, W)
        added += 1

    # Unify triangles so ▼/▶ pairs match (expand/collapse indicators).
    for cps, size in (((0x25B2, 0x25BC, 0x25B6, 0x25C0, 0x25B3, 0x25BD, 0x25B7, 0x25C1), 460),
                      ((0x25B4, 0x25BE, 0x25B5, 0x25BF, 0x25B8, 0x25B9), 380)):
        for cp in cps:
            if cp in dst:
                rescale(dst[cp], size * k, gcx, gcy, W)

    print('%s: W=%d cap=%d added=%d missing=%s' % (
        os.path.basename(path), W, cap, added,
        ' '.join('%s' % chr(m) for m in missing if not 0x2800 <= m <= 0x28FF) or '-'))
    for f in seen.values():
        f.close()
    dst.save(path)
    dst.close()


for d in sys.argv[1:]:
    style = os.path.basename(d.rstrip('/'))[len('FantasqueSansMono-'):-len('.sfdir')]
    process(d, style)
