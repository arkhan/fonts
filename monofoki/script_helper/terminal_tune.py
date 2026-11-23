#!/usr/bin/env python3
"""Make fonts safe for terminal grids: terminal_tune.py FILE...

Enforces (idempotent): monospace flags, one advance width, consistent vertical
metrics (hhea == typo, win covers them, USE_TYPO_METRICS), and an underline that
sits below the baseline inside the descent.
"""
import sys

from fontTools.ttLib import TTFont

for path in sys.argv[1:]:
    f = TTFont(path)
    upm = f['head'].unitsPerEm
    os2, hhea, post, hmtx = f['OS/2'], f['hhea'], f['post'], f['hmtx']
    adv = hmtx['a'][0]

    post.isFixedPitch = 1
    os2.panose.bProportion = 9
    os2.xAvgCharWidth = adv

    asc, desc = os2.sTypoAscender, os2.sTypoDescender  # design values are the source of truth
    hhea.ascent, hhea.descent, hhea.lineGap = asc, desc, 0
    os2.sTypoLineGap = 0
    os2.usWinAscent = max(os2.usWinAscent, asc)
    os2.usWinDescent = max(os2.usWinDescent, -desc)
    os2.fsSelection |= 1 << 7  # USE_TYPO_METRICS

    thick = post.underlineThickness or round(0.034 * upm)
    pos = post.underlinePosition
    if pos > -thick:  # at/above baseline: invisible or overlapping glyph bottoms
        pos = -round(0.116 * upm)
    pos = max(pos, -(-desc) + thick // 2 + 1)  # keep inside the descent
    post.underlinePosition, post.underlineThickness = pos, thick

    f.save(path)
    print('%s: adv=%d metrics=%d/%d underline=%d/%d' % (path, adv, asc, desc, pos, thick))
