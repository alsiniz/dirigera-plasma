#!/usr/bin/env bash
# Build a PyInstaller AppDir then an AppImage (x86_64 Linux).
set -euo pipefail
cd "$(dirname "$0")/../.."
ROOT="$PWD"
python3 -m venv .appimage-build-venv
. .appimage-build-venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt 'pyinstaller>=6.11,<7'
python -m PyInstaller --clean --noconfirm --onedir --name dirigera-plasma \
  --collect-all dirigera --collect-all dbus_next \
  --hidden-import=dbus_next.aio --hidden-import=dbus_next.service app.py
APPDIR="$ROOT/AppDir"
rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/bin" "$APPDIR/usr/share/icons/hicolor/scalable/apps" "$APPDIR/usr/share/doc/dirigera-plasma"
cp -a dist/dirigera-plasma/. "$APPDIR/usr/bin/"
cp "assets/io.github.alsiniz.DirigeraPlasma.svg" "$APPDIR/usr/share/icons/hicolor/scalable/apps/"
cp "packaging/flatpak/io.github.alsiniz.DirigeraPlasma.desktop" "$APPDIR/"
cp "assets/io.github.alsiniz.DirigeraPlasma.svg" "$APPDIR/io.github.alsiniz.DirigeraPlasma.svg"
cp LICENSE THIRD_PARTY_NOTICES.md "$APPDIR/usr/share/doc/dirigera-plasma/"
cat > "$APPDIR/AppRun" <<'RUN'
#!/bin/sh
HERE="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
exec "$HERE/usr/bin/dirigera-plasma" "$@"
RUN
chmod +x "$APPDIR/AppRun"
if ! command -v appimagetool >/dev/null; then
  echo 'AppDir ready; install appimagetool to produce AppImage.' >&2
  exit 2
fi
ARCH=x86_64 appimagetool "$APPDIR" "$ROOT/DIRIGERA-Plasma-x86_64.AppImage"
echo 'AppImage built (must be tested under KDE Plasma before release).'
