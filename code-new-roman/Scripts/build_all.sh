#!/usr/bin/env bash
# Pipeline (container or local with the same env vars): per style build symbols +
# ligatures, then patch with Nerd Fonts (single width) and keep the name "Code New Roman".
set -euo pipefail
cd "$(dirname "$0")/.."

work=.font-build; rm -rf "$work/out"; mkdir -p "$work/out" export/nerd
for u in Sources/*.ufo; do
    fontforge -quiet -lang=py -script Scripts/build_font.py "$u" "$work/out"
done

PATCHER_DIR=${PATCHER_DIR:-$work/patcher}
if [ ! -f "$PATCHER_DIR/font-patcher" ]; then
    mkdir -p "$PATCHER_DIR"
    curl -fsSL -o "$PATCHER_DIR/FontPatcher.zip" \
        "https://github.com/ryanoasis/nerd-fonts/releases/download/${NERD_FONTS_VERSION:-v3.5.1}/FontPatcher.zip"
    unzip -qo "$PATCHER_DIR/FontPatcher.zip" -d "$PATCHER_DIR"
fi

rm -f export/nerd/*
for f in "$work"/out/*.otf "$work"/out/*.ttf; do
    (
        tmp=$(mktemp -d)
        fontforge -lang=py -script "$PATCHER_DIR/font-patcher" --complete --mono \
            --no-progressbars --makegroups 0 -out "$tmp" "$f" >"$tmp/log" 2>&1 || { cat "$tmp/log"; exit 1; }
        mv "$(ls "$tmp"/*.?tf)" "export/nerd/$(basename "$f")"
        rm -rf "$tmp"
    ) &
done
wait
python3 Scripts/rename_family.py "Code New Roman" export/nerd/*
python3 Scripts/terminal_tune.py export/nerd/*
