#!/usr/bin/env bash
# Build a local experimental Flatpak bundle. Requires internet access for dependencies.
set -euo pipefail
cd "$(dirname "$0")/../.."
ROOT="$PWD"
FLATPAK_DIR="$ROOT/packaging/flatpak"
ID=io.github.alsiniz.DirigeraPlasma
BRANCH=6.10
command -v flatpak-builder >/dev/null || { echo 'Install flatpak-builder first.' >&2; exit 2; }
flatpak remote-add --user --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
flatpak install --user -y flathub "org.kde.Sdk//$BRANCH" "org.kde.Platform//$BRANCH" "io.qt.PySide.BaseApp//$BRANCH"
TOOLS_DIR="$(mktemp -d)"
trap 'rm -rf "$TOOLS_DIR"' EXIT
git clone --depth 1 https://github.com/flatpak/flatpak-builder-tools "$TOOLS_DIR/tools"
python3 -m venv "$TOOLS_DIR/venv"
"$TOOLS_DIR/venv/bin/pip" -q install requirements-parser packaging
"$TOOLS_DIR/venv/bin/python" "$TOOLS_DIR/tools/pip/flatpak-pip-generator.py" \
  --runtime="org.kde.Sdk//$BRANCH" \
  --requirements-file="$FLATPAK_DIR/requirements-flatpak.txt" \
  --prefer-wheels=pydantic-core \
  --wheel-arches=x86_64 \
  --output="$FLATPAK_DIR/python3-deps"
test -f "$FLATPAK_DIR/python3-deps.json" || { echo 'Missing pip dependencies manifest' >&2; exit 1; }
flatpak-builder --user --install-deps-from=flathub --force-clean --repo="$ROOT/flatpak-repo" \
  "$ROOT/flatpak-build" "$FLATPAK_DIR/$ID.json"
flatpak build-bundle "$ROOT/flatpak-repo" "$ROOT/dirigera-plasma.flatpak" "$ID"
echo 'Flatpak bundle produced (must be tested under KDE Plasma before release).'
