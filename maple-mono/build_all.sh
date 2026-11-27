#!/usr/bin/env bash
# Runs in the container: patch upstream, add the extra tag glyphs, regenerate the feature
# files, build, check, and copy the fonts to /out.
set -euo pipefail
cd /opt/maple

# Idempotent: a re-run in the same container starts from a clean tree.
git checkout -q -- . && git clean -fdq

git apply /opt/mods/patches/generic-tags.patch
python /opt/mods/tools/add_tag_glyphs.py sources
python task.py fea

# Slim width, one-cell Nerd Font icons, Simplified Chinese; the four main styles, TTF only.
python build.py --width slim --nf-mono --cn --least-styles --format ttf "$@"

mkdir -p /out
rm -rf /out/fonts && cp -r fonts /out/fonts
echo "output: $(find /out/fonts -name '*.ttf' | wc -l) TTF files"

for f in $(find fonts -name '*Regular.ttf' | sort); do
    python /opt/mods/tools/check_tags.py "$f" | sed "s#^#$f: #"
done
