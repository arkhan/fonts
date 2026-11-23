#!/usr/bin/env bash
# Build all fonts in a container (podman preferred, docker fallback).
# Output: export/ (plain) and export/nerd/ (Nerd Font, family "fantasque").
# Optional: ./build.sh --install  copies export/nerd/* to ~/.local/share/fonts/fantasque
# (close Emacs first: replacing fonts in use crashes it).
set -euo pipefail
cd "$(dirname "$0")"

engine=$(command -v podman || command -v docker) || { echo "podman or docker required" >&2; exit 1; }
opts=()
[ "$(basename "$engine")" = podman ] && opts+=(--userns=keep-id)

"$engine" build -t fantasque-build -f Containerfile .
"$engine" run --rm "${opts[@]}" -v "$PWD:/work:Z" fantasque-build

if [ "${1:-}" = --install ]; then
    dest=$HOME/.local/share/fonts/fantasque
    mkdir -p "$dest"
    rm -f "$dest"/*
    cp export/nerd/FantasqueSansMono-*.otf export/nerd/FantasqueSansMono-*.ttf "$dest"/
    fc-cache -f "$dest"
fi
