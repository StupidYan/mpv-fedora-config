#!/usr/bin/env bash
set -euo pipefail

SRC="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
DEST="${MPV_CONFIG_DIR:-${XDG_CONFIG_HOME:-$HOME/.config}/mpv}"

if ! command -v mpv >/dev/null 2>&1; then
    echo "Error: mpv is not installed or not in PATH." >&2
    exit 1
fi

mkdir -p "$(dirname "$DEST")"

if [ -e "$DEST" ]; then
    backup="$DEST.backup-$(date +%Y%m%d-%H%M%S)"
    echo "Backing up existing configuration:"
    echo "  $DEST -> $backup"
    mv -- "$DEST" "$backup"
fi

echo "Installing configuration:"
echo "  $SRC -> $DEST"
mkdir -p "$DEST"

for item in mpv.conf input.conf fonts shaders scripts script-opts; do
    cp -a -- "$SRC/$item" "$DEST/"
done

# Preserve the user's former default: danmaku enabled.
if [ ! -f "$DEST/danmaku-history.json" ]; then
    printf '%s\n' '{"show_danmaku":true}' > "$DEST/danmaku-history.json"
fi

echo "Installation complete."
echo "Test with:"
echo "  mpv --force-window=yes /tmp/mpv-fedora44-test.mp4"
