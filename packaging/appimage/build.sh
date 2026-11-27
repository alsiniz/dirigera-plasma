#!/usr/bin/env bash
# Build a PyInstaller AppDir then an AppImage (x86_64 Linux).
set -euo pipefail
cd "$(dirname "$0")/../.."
ROOT="$PWD"
python3 -m venv .appimage-build-venv
. .appimage-build-venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt 'pyinstaller>=6.11,<7'
python -m PyInstaller --clean --noconfirm --onedir --name lysnav \
  --add-data "assets:assets" --collect-all dirigera --collect-all dbus_next \
  --hidden-import=dbus_next.aio --hidden-import=dbus_next.service app.py
APPDIR="$ROOT/AppDir"
rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/bin" "$APPDIR/usr/share/icons/hicolor/scalable/apps" "$APPDIR/usr/share/doc/lysnav"
cp -a dist/lysnav/. "$APPDIR/usr/bin/"
# Prefer the host Fontconfig implementation. An older bundled libfontconfig
# cannot parse current Fedora/Bazzite font rules (e.g. 48-guessfamily.conf).
# Qt/Freetype remain bundled. Revalidate on each supported distro before release.
rm -f "$APPDIR/usr/bin/_internal/libfontconfig.so.1"
cp assets/io.github.alsiniz.Lysnav{,-symbolic}.svg "$APPDIR/usr/share/icons/hicolor/scalable/apps/"
cp "packaging/flatpak/io.github.alsiniz.Lysnav.desktop" "$APPDIR/"
cp "assets/io.github.alsiniz.Lysnav.svg" "$APPDIR/io.github.alsiniz.Lysnav.svg"
# appimagetool uses a raster copy of the desktop icon to create .DirIcon.
cp packaging/appimage/io.github.alsiniz.Lysnav.png "$APPDIR/"
cp LICENSE THIRD_PARTY_NOTICES.md "$APPDIR/usr/share/doc/lysnav/"
cat > "$APPDIR/AppRun" <<'RUN'
#!/bin/sh
HERE="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
exec "$HERE/usr/bin/lysnav" "$@"
RUN
chmod +x "$APPDIR/AppRun"
if ! command -v appimagetool >/dev/null; then
  echo 'AppDir ready; install appimagetool to produce AppImage.' >&2
  exit 2
fi
ARCH=x86_64 appimagetool "$APPDIR" "$ROOT/Lysnav-Plasma-x86_64.AppImage"
echo 'AppImage built (must be tested under KDE Plasma before release).'
