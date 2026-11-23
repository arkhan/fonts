#!/usr/bin/env python3
"""Reset the family name after Nerd Fonts patching: rename_family.py "Family Name" FILE..."""
import sys

from fontTools.ttLib import TTFont

new = sys.argv[1]
for path in sys.argv[2:]:
    f = TTFont(path)
    names = f['name']
    style = names.getDebugName(2)
    if style == 'Book':  # the UFO calls Regular 'Book'; RIBBI requires Regular
        style = 'Regular'
    full = '%s %s' % (new, style)
    ps = '%s-%s' % (new.replace(' ', ''), style.replace(' ', ''))
    for n in list(names.names):
        if n.nameID in (1, 16):
            n.string = new
        elif n.nameID == 4:
            n.string = full
        elif n.nameID == 6:
            n.string = ps
        elif n.nameID == 3:
            n.string = '%s;%s' % (new, ps)
        elif n.nameID in (2, 17):
            n.string = style
        elif n.nameID in (21, 22):
            names.removeNames(nameID=n.nameID)
    sel = f['OS/2'].fsSelection & ~0b1100001  # clear ITALIC, BOLD, REGULAR
    sel |= (0b1 if 'Italic' in style else 0) | (0b100000 if 'Bold' in style else 0)
    f['OS/2'].fsSelection = sel | (0b1000000 if style == 'Regular' else 0)
    f['head'].macStyle = (1 if 'Bold' in style else 0) | (2 if 'Italic' in style else 0)
    if 'CFF ' in f:
        f['CFF '].cff.fontNames = [ps]
    f.save(path)
    print(path, '->', full)
