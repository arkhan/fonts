#!/usr/bin/env fontforge
# Build only the "Normal" variant (no LargeLineHeight / NoLoopK permutations).
# usage: fontforge -lang=py -script Scripts/build_normal.py SFDIR OUTDIR
import sys

from fontbuilder import build

build(sys.argv[2], sys.argv[1])
