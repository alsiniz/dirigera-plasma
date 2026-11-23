#!/usr/bin/env bash
set -euo pipefail
DATA="${XDG_DATA_HOME:-$HOME/.local/share}"
CONFIG="${XDG_CONFIG_HOME:-$HOME/.config}"
rm -f "$DATA/applications/dirigera-plasma.desktop"
rm -rf "$DATA/dirigera-plasma"
echo 'DIRIGERA Plasma application files removed.'
echo "Private configuration remains at $CONFIG/dirigera-plasma/config.json"
echo 'Remove that directory yourself if you also want to delete the token and device approvals.'
