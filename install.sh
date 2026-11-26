#!/usr/bin/env bash
# Install/update into the user's XDG data directory. No sudo or hub commands.
set -euo pipefail
umask 077
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA="${XDG_DATA_HOME:-$HOME/.local/share}"
CONFIG="${XDG_CONFIG_HOME:-$HOME/.config}"
BIN="${XDG_BIN_HOME:-$HOME/.local/bin}"
APP="$DATA/lysnav"
LAUNCHERS="$DATA/applications"
ID=io.github.alsiniz.Lysnav
ICON_DIR="$DATA/icons/hicolor/scalable/apps"

mkdir -p "$APP" "$LAUNCHERS" "$CONFIG/lysnav" "$BIN" "$ICON_DIR"
chmod 700 "$CONFIG/lysnav"

# Prefer settings from the most recent installation. Keep the original for rollback.
for previous in dirigera-plasma dirigera-desktop; do
  if [[ ! -e "$CONFIG/lysnav/config.json" && -f "$CONFIG/$previous/config.json" ]]; then
    install -m 600 "$CONFIG/$previous/config.json" "$CONFIG/lysnav/config.json"
    break
  fi
done

for file in app.py core.py tray_sni.py tray_compat.py tray_menu_model.py icon_theme.py pairing.py version.py; do
  install -m 600 "$SRC/$file" "$APP/$file"
done
for file in LICENSE THIRD_PARTY_NOTICES.md README.md; do
  install -m 644 "$SRC/$file" "$APP/$file"
done
install -m 644 "$SRC/assets/$ID.svg" "$ICON_DIR/$ID.svg"

if [[ ! -f "$APP/venv/bin/python" ]]; then
  python3 -m venv "$APP/venv"
fi
if ! "$APP/venv/bin/python" -c 'import dirigera, PySide6, dbus_next' >/dev/null 2>&1; then
  "$APP/venv/bin/python" -m pip install -r "$SRC/requirements.txt"
fi
PYTHONPATH="$APP${PYTHONPATH:+:$PYTHONPATH}" "$APP/venv/bin/python" \
  -c 'from tray_sni import StatusNotifierTray, NativeMenu'

cat > "$APP/lysnav" <<'RUN'
#!/usr/bin/env bash
set -euo pipefail
HERE="$(dirname "$(readlink -f -- "$0")")"
exec "$HERE/venv/bin/python" "$HERE/app.py" "$@"
RUN
chmod 755 "$APP/lysnav"

# Preserve an unrelated command if the user already has one by this name.
if [[ ! -e "$BIN/lysnav" && ! -L "$BIN/lysnav" ]]; then
  ln -s -- "$APP/lysnav" "$BIN/lysnav"
elif [[ "$(readlink -f -- "$BIN/lysnav")" != "$APP/lysnav" ]]; then
  printf 'Existing %s kept. Use the application launcher or %s instead.\n' "$BIN/lysnav" "$APP/lysnav"
fi

# The desktop may have a different PATH from the login shell.
python3 - "$SRC/packaging/flatpak/$ID.desktop" "$APP/lysnav" "$LAUNCHERS/$ID.desktop" <<'PY'
from pathlib import Path
import sys

template, executable, target = sys.argv[1:]
# Quote the executable as a Desktop Entry Exec argument, then escape its field value.
for char in ('\\', '"', '`', '$'):
    executable = executable.replace(char, '\\' + char)
executable = executable.replace('\\', '\\\\').replace('%', '%%')
entry = Path(template).read_text(encoding='utf-8').replace('Exec=lysnav', f'Exec="{executable}"')
Path(target).write_text(entry, encoding='utf-8')
PY
chmod 644 "$LAUNCHERS/$ID.desktop"

for previous in dirigera-plasma dirigera-desktop; do
  launcher="$LAUNCHERS/$previous.desktop"
  if [[ -f "$launcher" ]] && grep -Eq '^Name=DIRIGERA (Desktop|Plasma)$' "$launcher"; then
    mv -n -- "$launcher" "$launcher.previous"
  fi
done

printf '\nInstalled Lysnav for KDE Plasma. Launch from KDE or run:\n  %s/lysnav\n' "$APP"
