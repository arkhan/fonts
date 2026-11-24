#!/usr/bin/env fontforge
"""
Build one Code New Roman style: UFO -> symbols/braille -> Fira Code ligatures -> OTF+TTF.

usage: fontforge -lang=py -script Scripts/build_font.py lig SRC.ufo OUT.sfd
       fontforge -lang=py -script Scripts/build_font.py gen OUT.sfd OUTDIR
env:   DEJAVU_DIR, CASCADIA_DIR (donor glyphs), FIRA_DIR (FiraCode-*.ttf/otf),
       LIGATURIZER_DIR (checkout providing ligaturize.py + ligatures.py)
Metrics are derived from the font itself (cell width, cap height, centre of the
filled circle), so nothing is tied to one em size.
"""
import os
import subprocess
import sys

import fontforge
import psMat

LIGATURIZER_DIR = os.environ.get('LIGATURIZER_DIR', '/opt/Ligaturizer')
sys.path.insert(0, LIGATURIZER_DIR)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # our curated ligatures.py wins over upstream's
from ligaturize import LigatureCreator  # noqa: E402
from ligatures import ligatures  # noqa: E402

DEJAVU_DIR = os.environ.get('DEJAVU_DIR') or os.path.dirname(subprocess.check_output(
    ['fc-match', '-f', '%{file}', 'DejaVu Sans Mono']).decode())
CASCADIA_DIR = os.environ.get('CASCADIA_DIR', '/opt/donors')
FIRA_DIR = os.environ.get('FIRA_DIR', '/opt/fira')

WANT = ('⎋␣⌃⌘⌥⇥␀␉␊␍↵➡➔➙➞↪₹₿₺☆❤◆◇◈◉○◔◦□‣∥▲▼▶◀△▽▷▸▹▾▿▴▵'
        '➤❯⚠✶✳☑✓✗❝⬆⬇⯆⯈⧉⚹▁▂▃▄▅▆▇┄╭╮╯╰')
BRAILLE = range(0x2800, 0x2900)
SOURCES = {
    'regular': {'dv': 'DejaVuSansMono.ttf', 'cc': 'CascadiaCode-Regular.ttf'},
    'bold': {'dv': 'DejaVuSansMono-Bold.ttf', 'cc': 'CascadiaCode-Bold.ttf'},
}
DIRS = {'dv': DEJAVU_DIR, 'cc': CASCADIA_DIR}


def bbox(g):
    b = g.boundingBox()
    return b[0], b[1], b[2], b[3], b[2] - b[0], b[3] - b[1]


def center(g, cx, cy, width):
    x0, y0, x1, y1, _, _ = bbox(g)
    g.transform(psMat.translate(cx - (x0 + x1) / 2, cy - (y0 + y1) / 2))
    g.width = width


def rescale(g, size, cx, cy, width):
    _, _, _, _, w, h = bbox(g)
    if w and h:
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


def import_symbols(dst, weight):
    W = dst['a'].width
    cap = bbox(dst['H'])[3]
    gcy = cap / 2
    if 0x25CF in dst:
        _, y0, _, y1, _, _ = bbox(dst[0x25CF])
        gcy = (y0 + y1) / 2
    gcx, k = W / 2, W / 575.0

    fonts = {}
    for tag, name in SOURCES[weight].items():
        f = fontforge.open(os.path.join(DIRS[tag], name))
        f.em = dst.em
        fonts[tag] = f
    have = {g.unicode for g in dst.glyphs() if g.unicode > 0}
    added, missing = 0, []
    for cp in [ord(c) for c in WANT] + list(BRAILLE):
        if cp in have:
            continue
        # braille always from the Regular donor: it must not be emboldened
        src = fonts['cc'] if 0x2800 <= cp <= 0x28FF else next(
            (fonts[t] for t in ('dv', 'cc') if cp in fonts[t] and fonts[t][cp].isWorthOutputting()), None)
        if src is None or cp not in src or not src[cp].isWorthOutputting():
            missing.append(chr(cp))
            continue
        src.selection.select(cp)
        src.copy()
        dst.createChar(cp)
        dst.selection.select(cp)
        dst.paste()
        g = dst[cp]
        if 0x2800 <= cp <= 0x28FF:
            g.transform(psMat.scale(W / g.width, 1))
            g.width = W
        elif cp in (0x25C6, 0x25C7, 0x25C8, 0x25C9):
            rescale(g, 500 * k, gcx, gcy, W)
        elif cp in (0x25E6, 0x2023):
            center(g, gcx, gcy, W)
        else:
            fit(g, cap, W * 0.90, gcx, cap / 2, W)
        added += 1
    for cps, size in (((0x25B2, 0x25BC, 0x25B6, 0x25C0, 0x25B3, 0x25BD, 0x25B7, 0x25C1), 460),
                      ((0x25B4, 0x25BE, 0x25B5, 0x25BF, 0x25B8, 0x25B9), 380)):
        for cp in cps:
            if cp in dst:
                rescale(dst[cp], size * k, gcx, gcy, W)
    for f in fonts.values():
        f.close()
    print('symbols: W=%d cap=%d added=%d missing=%s' % (W, cap, added, ''.join(m for m in missing if not 0x2800 <= ord(m) <= 0x28FF) or '-'))


def add_ligatures(font, weight):
    base = os.path.join(FIRA_DIR, 'FiraCode-' + ('Bold' if weight == 'bold' else 'Regular'))
    fira = fontforge.open(base + '.otf' if os.path.exists(base + '.otf') else base + '.ttf')
    creator = LigatureCreator(font, fira, scale_character_glyphs_threshold=0.1, copy_character_glyphs=False)
    for spec in sorted(ligatures, key=lambda l: len(l['chars'])):
        creator.add_ligature(spec['chars'], spec['firacode_ligature_name'])
    fira.close()


def stage_ligatures(src, sfd):
    """Stage 1: UFO -> SFD with Fira Code ligatures. Runs in its own FontForge process:
    generating in the same process after LigatureCreator corrupts the heap."""
    font = fontforge.open(src)
    weight = 'bold' if font.os2_weight >= 700 else 'regular'
    add_ligatures(font, weight)
    font.save(sfd)


def stage_generate(sfd, outdir):
    """Stage 2: symbols/braille, cleanup, OTF + TTF."""
    font = fontforge.open(sfd)
    font.reencode('unicodefull')  # slots must equal code points for the symbol import
    weight = 'bold' if font.os2_weight >= 700 else 'regular'
    upos, uwidth = font.upos, font.uwidth
    import_symbols(font, weight)
    font.upos, font.uwidth = upos, uwidth

    for glyph in font.glyphs():  # same cleanup as the monofoki/fantasque builds
        glyph.unlinkRef()
        glyph.removeOverlap()
        glyph.round()
        glyph.addExtrema('all')
        if glyph.validate() & 0x8 == 0x8:
            glyph.correctDirection()
        glyph.removeOverlap()
        glyph.round()
        glyph.addExtrema('all')

    os.makedirs(outdir, exist_ok=True)
    base = os.path.join(outdir, font.fontname)
    for ext in ('otf', 'ttf'):
        if ext == 'ttf':
            for layer in font.layers:
                font.layers[layer].is_quadratic = True
        font.generate('%s.%s' % (base, ext), flags=('opentype', 'dummy-dsig'))
        print('wrote %s.%s' % (base, ext))
    font.close()


{'lig': stage_ligatures, 'gen': stage_generate}[sys.argv[1]](sys.argv[2], sys.argv[3])
# FontForge's teardown double-frees after LigatureCreator ("free(): double free"), killing the
# process with SIGABRT although the output is already written. Skip teardown.
sys.stdout.flush()
os._exit(0)
