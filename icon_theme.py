"""Discover *installed* KDE icon themes for a theme-aware tray icon picker.

This module has no Qt dependency or bundled icon assets. QIcon.fromTheme()
remains responsible for rendering the selected icon in the active palette.
"""
from __future__ import annotations

import configparser
import os
from pathlib import Path

_ICON_SUFFIXES = {'.svg', '.svgz', '.png', '.xpm'}


def active_theme(qt_theme: str = '', kdeglobals: Path | None = None) -> str:
    """Prefer KDE's configured icon theme, then Qt's current theme.

    PySide6 pip wheels are not guaranteed to load KDE's Qt platform theme,
    especially on containerized or non-distro Python builds. The user's KDE
    setting is a useful read-only fallback; never override QIcon.setThemeName.
    """
    path = kdeglobals or Path(os.environ.get('XDG_CONFIG_HOME', str(Path.home() / '.config'))) / 'kdeglobals'
    config = configparser.ConfigParser(interpolation=None, strict=False)
    config.optionxform = str
    try:
        config.read(path, encoding='utf-8')
        name = config.get('Icons', 'Theme', fallback='').strip()
        if name:
            return name
    except (OSError, configparser.Error):
        pass
    return qt_theme or 'hicolor'


def search_paths(qt_paths=()):
    """User themes, XDG data icon themes, and Qt's existing theme search paths."""
    xdg_home = Path(os.environ.get('XDG_DATA_HOME', str(Path.home() / '.local/share')))
    xdg_dirs = os.environ.get('XDG_DATA_DIRS', '/usr/local/share:/usr/share').split(':')
    paths = [xdg_home / 'icons', Path.home() / '.icons']
    paths += [Path(entry) / 'icons' for entry in xdg_dirs if entry]
    paths += [Path(path) for path in qt_paths]
    result = []
    seen = set()
    for path in paths:
        key = str(path.expanduser())
        if key not in seen:
            seen.add(key)
            result.append(path.expanduser())
    return result


def _inherits(theme_dir: Path) -> list[str]:
    config = configparser.ConfigParser(interpolation=None, strict=False)
    try:
        config.read(theme_dir / 'index.theme', encoding='utf-8')
        line = config.get('Icon Theme', 'Inherits', fallback='')
        return [part.strip() for part in line.split(',') if part.strip()]
    except (OSError, configparser.Error):
        return []


def discover_icon_files(theme: str, roots: list[Path], include_inherited=True) -> dict[str, str]:
    """Map icon names to preview paths, only from current/inherited icon themes.

    Inheritance mirrors the freedesktop icon-theme convention. Individual
    icons are never copied or packaged with this application.
    """
    icons = {}
    seen = set()
    queue = [theme]
    if theme != 'hicolor':
        queue.append('hicolor')  # final freedesktop fallback
    while queue:
        current = queue.pop(0)
        if current in seen:
            continue
        seen.add(current)
        directories = [root / current for root in roots if (root / current).is_dir()]
        # Process all directories for this theme (user-installed takes precedence).
        for directory in directories:
            for file in directory.rglob('*'):
                if file.is_file() and file.suffix.lower() in _ICON_SUFFIXES:
                    name = file.name[:-len(file.suffix)]
                    if name:
                        icons.setdefault(name, str(file))
        if include_inherited:
            inherited = []
            for directory in directories:
                inherited += _inherits(directory)
            for inherited_name in inherited:
                if inherited_name not in seen and inherited_name not in queue:
                    # Before hicolor, which should be the last fallback.
                    queue.insert(max(0, len(queue) - (1 if 'hicolor' in queue else 0)), inherited_name)
    return icons
