#!/usr/bin/env bash
set -euo pipefail

SOURCE_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
MODE="${1:-install}"

BIN_DIR="${XDG_BIN_HOME:-$HOME/.local/bin}"
DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"
APPLICATIONS_DIR="$DATA_HOME/applications"
CONFIG_HOME="${XDG_CONFIG_HOME:-$HOME/.config}"
CONFIG_DIR="$CONFIG_HOME/mpv"
CONFIG_FILE="$CONFIG_DIR/external-player-handler.json"
HANDLER="$BIN_DIR/mpv-fedora-ush-handler"
DESKTOP_FILE="$APPLICATIONS_DIR/mpv-fedora-ush-handler.desktop"

uninstall() {
    install -d "$BIN_DIR" "$APPLICATIONS_DIR"
    python3 - "$APPLICATIONS_DIR" <<'PY'
from pathlib import Path
import sys
path = Path(sys.argv[1]) / "mpv-fedora-ush-handler.desktop"
try:
    path.unlink()
except FileNotFoundError:
    pass
PY
    python3 - "$HANDLER" <<'PY'
from pathlib import Path
import sys
path = Path(sys.argv[1])
try:
    path.unlink()
except FileNotFoundError:
    pass
PY
    if command -v desktop-file-install >/dev/null 2>&1; then
        update-desktop-database "$APPLICATIONS_DIR" 2>/dev/null || true
    fi
    python3 - "$CONFIG_HOME/mimeapps.list" <<'PY'
from pathlib import Path
import sys
path = Path(sys.argv[1])
if path.is_file():
    lines = path.read_text(encoding="utf-8").splitlines()
    lines = [line for line in lines if not line.startswith("x-scheme-handler/ush=")]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
PY
    echo "External Player Fedora handler removed."
    echo "Your ~/.config/mpv configuration was not changed."
}

if [[ "$MODE" == "--uninstall" || "$MODE" == "uninstall" ]]; then
    uninstall
    exit 0
elif [[ "$MODE" != "install" && "$MODE" != "--install" ]]; then
    echo "Usage: $0 [--install|--uninstall]" >&2
    exit 2
fi

if ! command -v mpv >/dev/null 2>&1; then
    echo "Error: mpv is not installed or not in PATH." >&2
    exit 1
fi
if ! command -v xdg-mime >/dev/null 2>&1; then
    echo "Error: xdg-mime is required on Fedora." >&2
    exit 1
fi

install -d -m 0700 "$CONFIG_DIR"
install -d "$BIN_DIR" "$APPLICATIONS_DIR"
install -m 0755 "$SOURCE_DIR/fedora-ush-handler.py" "$HANDLER"

if [[ ! -f "$CONFIG_FILE" ]]; then
    MPV_PATH="$(command -v mpv)"
    umask 077
    python3 - "$CONFIG_FILE" "$MPV_PATH" <<'PY'
import json
import sys
path, mpv = sys.argv[1:]
data = {"apps": [{"name": "MPV", "path": mpv}]}
with open(path, "w", encoding="utf-8") as file:
    json.dump(data, file, ensure_ascii=False, indent=2)
    file.write("\n")
PY
    echo "Created handler configuration: $CONFIG_FILE"
else
    echo "Keeping existing handler configuration: $CONFIG_FILE"
fi

python3 - "$HANDLER" "$DESKTOP_FILE" <<'PY'
from pathlib import Path
import sys
handler, desktop = map(Path, sys.argv[1:])
desktop.write_text(
    "[Desktop Entry]\n"
    "Type=Application\n"
    "Name=mpv Fedora USH Handler\n"
    "GenericName=External Player URL Handler\n"
    f'Exec="{handler}" %u\n'
    "Terminal=false\n"
    "NoDisplay=true\n"
    "Icon=mpv\n"
    "Categories=AudioVideo;Player;\n"
    "MimeType=x-scheme-handler/ush;\n"
    "X-KDE-Protocols=ush\n"
    "StartupNotify=false\n",
    encoding="utf-8",
)
PY

if command -v desktop-file-install >/dev/null 2>&1; then
    desktop-file-install --rebuild-mime-info-cache --dir="$APPLICATIONS_DIR" "$DESKTOP_FILE"
else
    echo "Warning: desktop-file-install not found; using desktop file directly." >&2
fi

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$APPLICATIONS_DIR" 2>/dev/null || true
fi

# gio writes the user association without xdg-mime's optional qtpaths lookup.
# Keep xdg-mime as a portable fallback for minimal installations.
if command -v gio >/dev/null 2>&1; then
    gio mime x-scheme-handler/ush mpv-fedora-ush-handler.desktop >/dev/null
else
    xdg-mime default mpv-fedora-ush-handler.desktop x-scheme-handler/ush
fi

echo "Installed handler: $HANDLER"
echo "Installed desktop entry: $DESKTOP_FILE"
echo "Default ush:// handler:"
xdg-mime query default x-scheme-handler/ush
echo
echo "Install or update the userscript from:"
echo "  $SOURCE_DIR/external-player-fedora.user.js"
