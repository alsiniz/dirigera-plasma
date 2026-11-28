"""Pure, testable model for a Plasma-native D-BusMenu.

No Qt or D-Bus imports. The menu is rendered by Plasma, not by a Qt popup
whose cursor position can be wrong or unavailable on Wayland.
"""
from __future__ import annotations

from core import ALL_APPROVED


def node(ident, label='', action='', *, enabled=True, children=None, separator=False, checked=None):
    return dict(id=ident, label=label, action=action, enabled=bool(enabled),
                children=list(children or []), separator=separator, checked=checked)


def build_menu(rooms: dict[str, str], selected_room: str | None, *, power_available: bool,
               brightness_available: bool, native_ready: bool) -> dict:
    """Native tray menu with approved-device actions only.

    Scrolling the tray icon already changes brightness. Repeated five-percent
    buttons don't belong in the context menu. Authorization stays in core.py.
    """
    choices = [node(10, 'All approved lights', f'room:{ALL_APPROVED}', checked=selected_room == ALL_APPROVED)]
    for i, (room_id, room_name) in enumerate(sorted(rooms.items(), key=lambda p: p[1].casefold())):
        choices.append(node(100 + i, room_name, f'room:{room_id}', checked=selected_room == room_id))
    return node(0, children=[
        node(1, 'Show controls', 'show'),
        node(2, 'Toggle selected lights', 'toggle', enabled=power_available),
        node(3, 'Refresh', 'refresh'),
        node(4, 'Tray controls for…', children=choices),
        node(5, 'Tray settings / change icon…', 'settings'),
        node(7, 'About Lysnav for KDE Plasma…', 'about'),
        node(8, separator=True),
        node(9, 'Quit Lysnav for KDE Plasma', 'quit'),
    ])


def get_node(tree: dict, ident: int):
    if tree['id'] == ident:
        return tree
    for child in tree['children']:
        result = get_node(child, ident)
        if result is not None:
            return result
    return None


def menu_properties(entry: dict, variant, property_names=()):
    # Root id 0 is a protocol sentinel, not a visible menu entry.
    # KDE's DBusMenu importer expects its property map to be empty.
    if entry['id'] == 0:
        return {}
    if entry['separator']:
        props = {'type': variant('s', 'separator')}
    else:
        props = {'label': variant('s', entry['label']),
                 'enabled': variant('b', entry['enabled'])}
        if entry['children']:
            props['children-display'] = variant('s', 'submenu')
        if entry['checked'] is not None:
            props['toggle-type'] = variant('s', 'radio')
            props['toggle-state'] = variant('i', int(entry['checked']))
    return {k: v for k, v in props.items() if not property_names or k in property_names}


def layout_for(entry: dict, depth: int, property_names, variant):
    """Build the D-Bus (ia{sv}av) layout, with children wrapped in variants."""
    children = []
    if depth != 0:
        for child in entry['children']:
            sub = layout_for(child, depth - 1 if depth > 0 else -1, property_names, variant)
            children.append(variant('(ia{sv}av)', sub))
    # dbus-next requires *lists* for D-Bus STRUCT values, including structs
    # nested inside Variants. Tuples may look equivalent in Python but cause
    # SignatureBodyMismatchError when Plasma requests GetLayout.
    return [entry['id'], menu_properties(entry, variant, property_names), children]
