#!/usr/bin/env bash
set -euo pipefail
DATA="${XDG_DATA_HOME:-$HOME/.local/share}"
CONFIG="${XDG_CONFIG_HOME:-$HOME/.config}"
BIN="${XDG_BIN_HOME:-$HOME/.local/bin}"
ID=io.github.alsiniz.Lysnav
if [[ -L "$BIN/lysnav" && "$(readlink -- "$BIN/lysnav")" == "$DATA/lysnav/lysnav" ]]; then
  rm -- "$BIN/lysnav"
fi
rm -f -- "$DATA/applications/$ID.desktop" "$DATA/icons/hicolor/scalable/apps/$ID.svg" "$DATA/icons/hicolor/scalable/apps/$ID-symbolic.svg"
rm -rf -- "$DATA/lysnav"
echo 'Lysnav for KDE Plasma application files removed.'
echo "Private configuration remains at $CONFIG/lysnav/config.json"
echo 'Previous installations may also have a copy of your token and device approvals.'
