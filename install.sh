#!/usr/bin/env bash
# Install/update into the user's XDG data directory. No sudo or hub commands.
set -euo pipefail
umask 077
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA="${XDG_DATA_HOME:-$HOME/.local/share}"
CONFIG="${XDG_CONFIG_HOME:-$HOME/.config}"
APP="$DATA/dirigera-plasma"
LAUNCHERS="$DATA/applications"
OLD_CONFIG="$CONFIG/dirigera-desktop/config.json"
NEW_CONFIG="$CONFIG/dirigera-plasma/config.json"
OLD_LAUNCHER="$LAUNCHERS/dirigera-desktop.desktop"

mkdir -p "$APP" "$LAUNCHERS" "$CONFIG/dirigera-plasma"
chmod 700 "$CONFIG/dirigera-plasma"

# Preserve credentials, approvals, icon and selected room. Do not delete or
# overwrite the v0.6 configuration (rollback may still be needed).
if [[ ! -e "$NEW_CONFIG" && -f "$OLD_CONFIG" ]]; then
  install -m 600 "$OLD_CONFIG" "$NEW_CONFIG"
  echo 'Migrated existing v0.6 settings and device approvals (old settings kept for rollback).'
fi

for file in app.py core.py tray_sni.py tray_compat.py tray_menu_model.py icon_theme.py pairing.py version.py; do
  install -m 600 "$SRC/$file" "$APP/$file"
done

# Include licensing and third-party credits alongside the installed app.
for file in LICENSE THIRD_PARTY_NOTICES.md README.md; do
  install -m 644 "$SRC/$file" "$APP/$file"
done

if [[ ! -f "$APP/venv/bin/python" ]]; then
  python3 -m venv "$APP/venv"
fi
if ! "$APP/venv/bin/python" -c 'import dirigera, PySide6, dbus_next' >/dev/null 2>&1; then
  "$APP/venv/bin/python" -m pip install -r "$SRC/requirements.txt"
fi
# Python 3.15 dbus-next compatibility: test the actual module import.
PYTHONPATH="$APP${PYTHONPATH:+:$PYTHONPATH}" "$APP/venv/bin/python" \
  -c 'from tray_sni import StatusNotifierTray, NativeMenu'

cat > "$APP/run.sh" <<'RUN'
#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
exec "$HERE/venv/bin/python" "$HERE/app.py" "$@"
RUN
chmod 755 "$APP/run.sh"

cat > "$LAUNCHERS/dirigera-plasma.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=DIRIGERA Plasma
Comment=KDE Plasma controls for explicitly approved IKEA DIRIGERA lights
Exec=$APP/run.sh
Icon=weather-clear
Terminal=false
Categories=Utility;Settings;
StartupNotify=true
EOF
chmod 644 "$LAUNCHERS/dirigera-plasma.desktop"

# Hide only our own legacy launcher. Leave v0.6 code intact for rollback.
if [[ -f "$OLD_LAUNCHER" ]] && grep -q '^Name=DIRIGERA Desktop$' "$OLD_LAUNCHER"; then
  mv -f "$OLD_LAUNCHER" "$OLD_LAUNCHER.previous"
fi

printf '\nInstalled DIRIGERA Plasma. Launch from KDE, or run:\n  %s/run.sh\n' "$APP"
printf 'Your hub token remains private to your account. Never post it in a GitHub issue.\n'
