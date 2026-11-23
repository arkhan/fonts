#!/usr/bin/env bash
# Build all fonts in a container (podman preferred, docker fallback).
# Output: export/ (plain) and export/nerd/ (Nerd Font, family "monofoki").
# Optional: ./build.sh --install  copies export/nerd/* to ~/.local/share/fonts/code-new-roman
# (close Emacs first: replacing fonts in use crashes it).
set -euo pipefail
cd "$(dirname "$0")"

engine=$(command -v podman || command -v docker) || { echo "podman or docker required" >&2; exit 1; }
opts=()
[ "$(basename "$engine")" = podman ] && opts+=(--userns=keep-id)

"$engine" build -t code-new-roman-build -f Containerfile .
"$engine" run --rm "${opts[@]}" -v "$PWD:/work:Z" code-new-roman-build

if [ "${1:-}" = --install ]; then
    dest=$HOME/.local/share/fonts/code-new-roman
    mkdir -p "$dest"
    rm -f "$dest"/*
    cp export/nerd/CodeNewRoman-*.otf export/nerd/CodeNewRoman-*.ttf "$dest"/
    fc-cache -f "$dest"
fi
