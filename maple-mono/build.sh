#!/usr/bin/env bash
# Build Maple Mono SL NF CN with generic tags in a container (podman preferred, docker fallback).
# Output: export/fonts/ (rootless podman maps the container root to you, so files stay yours). Extra arguments go to upstream build.py (e.g. --no-hinted).
set -euo pipefail
cd "$(dirname "$0")"

engine=$(command -v podman || command -v docker) || { echo "podman or docker required" >&2; exit 1; }
mkdir -p export
"$engine" build -t maple-mono-build -f Containerfile .
"$engine" run --rm -v "$PWD/export:/out:Z" maple-mono-build "$@"
