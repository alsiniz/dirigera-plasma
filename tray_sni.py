"""Native KDE StatusNotifierItem tray integration with actual Scroll support.

Qt's own Linux DBus tray adapter deliberately ignores the Scroll method. A
separate StatusNotifierItem service is required for wheel-to-brightness control.
Runs *inside the GUI process*, with an asyncio event loop in one Python thread.
No listeners, external service, or system-wide daemon.
"""
from __future__ import annotations

import asyncio
import os
import threading

# dbus-next 0.2.3 uses typing.no_type_check_decorator, removed in Python 3.15.
# Restore its type-checking-only behavior inside this process BEFORE importing
# dbus_next.service. No changes to the OS, user's Python, or site-packages.
from tray_compat import ensure_dbus_next_typing_compat
ensure_dbus_next_typing_compat()

from dbus_next import BusType, Message, MessageType, RequestNameReply, Variant
from tray_menu_model import get_node, menu_properties, layout_for
from dbus_next.aio import MessageBus
from dbus_next.constants import PropertyAccess
from dbus_next.service import ServiceInterface, dbus_property, method, signal


class Item(ServiceInterface):
    def __init__(self, signals, icon_name: str, tooltip: str):
        super().__init__("org.kde.StatusNotifierItem")
        self.signals = signals
        self.icon_name = icon_name
        self.tooltip = tooltip
        self.scroll_calls = 0
        self.last_scroll = None

    @dbus_property(access=PropertyAccess.READ)
    def Category(self) -> 's':
        return 'ApplicationStatus'

    @dbus_property(access=PropertyAccess.READ)
    def Id(self) -> 's':
        return 'lysnav'

    @dbus_property(access=PropertyAccess.READ)
    def Title(self) -> 's':
        return 'Lysnav for KDE Plasma'

    @dbus_property(access=PropertyAccess.READ)
    def Status(self) -> 's':
        return 'Active'

    @dbus_property(access=PropertyAccess.READ)
    def WindowId(self) -> 'u':
        return 0

    @dbus_property(access=PropertyAccess.READ)
    def IconName(self) -> 's':
        return self.icon_name

    @dbus_property(access=PropertyAccess.READ)
    def IconPixmap(self) -> 'a(iiay)':
        return []

    @dbus_property(access=PropertyAccess.READ)
    def IconThemePath(self) -> 's':
        return ''

    @dbus_property(access=PropertyAccess.READ)
    def OverlayIconName(self) -> 's':
        return ''

    @dbus_property(access=PropertyAccess.READ)
    def OverlayIconPixmap(self) -> 'a(iiay)':
        return []

    @dbus_property(access=PropertyAccess.READ)
    def AttentionIconName(self) -> 's':
        return ''

    @dbus_property(access=PropertyAccess.READ)
    def AttentionIconPixmap(self) -> 'a(iiay)':
        return []

    @dbus_property(access=PropertyAccess.READ)
    def AttentionMovieName(self) -> 's':
        return ''

    @dbus_property(access=PropertyAccess.READ)
    def ItemIsMenu(self) -> 'b':
        return False

    @dbus_property(access=PropertyAccess.READ)
    def Menu(self) -> 'o':
        # Plasma imports this menu and places its own native context popup.
        # NEVER use /NO_DBUSMENU or QMenu.popup(cursor position) on Wayland.
        return '/MenuBar'

    @dbus_property(access=PropertyAccess.READ)
    def ToolTip(self) -> '(sa(iiay)ss)':
        return ['', [], 'Lysnav for KDE Plasma', self.tooltip]

    @method()
    def Activate(self, x: 'i', y: 'i'):
        self.signals.show_requested.emit()

    @method()
    def SecondaryActivate(self, x: 'i', y: 'i'):
        # KDE Plasma sends middle-click via SecondaryActivate, not Activate.
        self.signals.middle_clicked.emit()

    @method()
    def ContextMenu(self, x: 'i', y: 'i'):
        self.signals.menu_requested.emit(int(x), int(y))

    @method()
    def Scroll(self, delta: 'i', orientation: 's'):
        # The signal crosses safely to the GUI thread. No network commands
        # are performed on this DBus thread.
        self.scroll_calls += 1
        self.last_scroll = (int(delta), str(orientation))
        self.signals.scroll_requested.emit(int(delta), str(orientation))

    @method()
    def ProvideXdgActivationToken(self, token: 's'):
        # Optional KDE extension. The Qt window receives the activation request.
        pass

    @signal()
    def NewIcon(self):
        pass

    @signal()
    def NewToolTip(self):
        pass

    def update(self, icon=None, tooltip=None):
        if icon is not None and icon != self.icon_name:
            self.icon_name = icon
            self.NewIcon()
        if tooltip is not None and tooltip != self.tooltip:
            self.tooltip = tooltip
            self.NewToolTip()


class NativeMenu(ServiceInterface):
    """D-BusMenu served in the same process as the tray item.

    Plasma owns the popup window and mouse input, fixing Wayland positioning
    and the repeated-failure problem caused by QMenu.popup(QCursor.pos()).
    """

    def __init__(self, signals, menu_model):
        super().__init__('com.canonical.dbusmenu')
        self.signals = signals
        self.model = menu_model
        self.revision = 1
        self.layout_requests = 0
        self.last_request = 'none'

    @dbus_property(access=PropertyAccess.READ)
    def Version(self) -> 'u':
        return 3

    @dbus_property(access=PropertyAccess.READ)
    def TextDirection(self) -> 's':
        return 'ltr'

    @dbus_property(access=PropertyAccess.READ)
    def Status(self) -> 's':
        return 'normal'

    @dbus_property(access=PropertyAccess.READ)
    def IconThemePath(self) -> 'as':
        return []

    @method()
    def GetLayout(self, parent_id: 'i', recursion_depth: 'i', property_names: 'as') -> 'u(ia{sv}av)':
        self.layout_requests += 1
        self.last_request = f'GetLayout(parent={parent_id}, depth={recursion_depth})'
        item = get_node(self.model, parent_id)
        if item is None:
            # Invalid ids must not silently return the whole root menu.
            raise ValueError(f'No menu item with ID {parent_id}')
        return [self.revision, layout_for(item, recursion_depth, property_names, Variant)]

    @method()
    def GetGroupProperties(self, ids: 'ai', property_names: 'as') -> 'a(ia{sv})':
        if not ids:
            def all_ids(node):
                return [node['id']] + [i for child in node['children'] for i in all_ids(child)]
            ids = all_ids(self.model)
        # D-Bus structs must be lists, not tuples, in dbus-next.
        return [[i, menu_properties(item, Variant, property_names)]
                for i in ids if (item := get_node(self.model, i)) is not None]

    @method()
    def GetProperty(self, id: 'i', name: 's') -> 'v':
        item = get_node(self.model, id)
        props = menu_properties(item, Variant) if item is not None else {}
        return props.get(name, Variant('s', ''))

    @method()
    def Event(self, id: 'i', event_id: 's', data: 'v', timestamp: 'u'):
        if event_id != 'clicked':
            return
        item = get_node(self.model, id)
        if item is not None and item['enabled'] and not item['separator'] and item['action']:
            self.signals.menu_action.emit(item['action'])

    @method()
    def EventGroup(self, events: 'a(isvu)') -> 'ai':
        errors = []
        for ident, event_id, data, timestamp in events:
            if get_node(self.model, ident) is None:
                errors.append(ident)
            else:
                self.Event(ident, event_id, data, timestamp)
        return errors

    @method()
    def AboutToShow(self, id: 'i') -> 'b':
        return False

    @method()
    def AboutToShowGroup(self, ids: 'ai') -> 'aiai':
        return [[], []]

    @signal()
    def LayoutUpdated(self, revision: 'u', parent: 'i') -> 'ui':
        return [revision, parent]

    @signal()
    def ItemsPropertiesUpdated(self, updated: 'a(ia{sv})', removed: 'a(ias)') -> 'a(ia{sv})a(ias)':
        return [updated, removed]

    @signal()
    def ItemActivationRequested(self, ident: 'i', timestamp: 'u') -> 'iu':
        return [ident, timestamp]

    def replace(self, model):
        if model != self.model:
            self.model = model
            self.revision += 1
            self.LayoutUpdated(self.revision, 0)


class StatusNotifierTray:
    """Starts a StatusNotifierItem in a thread and provides GUI-safe updates."""

    def __init__(self, signals, icon_name: str, tooltip: str, menu_model):
        self.signals = signals
        self.icon_name = icon_name
        self.tooltip = tooltip
        self.menu_model = menu_model
        self.menu = None
        self.loop = None
        self.done = None
        self.item = None
        self.bus = None
        # Flatpak permits owning names under its application ID by default.
        # The usual org.kde.StatusNotifierItem-PID-1 name is rejected by Flatpak
        # (invalid as a sandbox --own-name wildcard), although Plasma accepts it.
        self.service_name = (
            f"io.github.alsiniz.Lysnav.Tray{os.getpid()}"
            if os.environ.get("FLATPAK_ID")
            else f"org.kde.StatusNotifierItem-{os.getpid()}-1"
        )
        self.menu_probe = 'not attempted'
        self.thread = threading.Thread(target=self._thread_main, name='lysnav-tray', daemon=True)

    def start(self):
        self.thread.start()

    def _thread_main(self):
        try:
            asyncio.run(self._serve())
        except Exception as exc:
            self.signals.failed.emit(f'{type(exc).__name__}: {exc}')

    async def _serve(self):
        self.loop = asyncio.get_running_loop()
        self.done = asyncio.Event()
        bus = await MessageBus(bus_type=BusType.SESSION).connect()
        self.bus = bus
        try:
            self.item = Item(self.signals, self.icon_name, self.tooltip)
            bus.export('/StatusNotifierItem', self.item)
            # Expose the real menu on the very same bus as the StatusNotifierItem.
            # Register both objects before registering the tray with Plasma:
            # otherwise the watcher could query the menu before it exists.
            self.menu = NativeMenu(self.signals, self.menu_model)
            bus.export('/MenuBar', self.menu)
            name_reply = await bus.request_name(self.service_name)
            if name_reply not in (RequestNameReply.PRIMARY_OWNER, RequestNameReply.ALREADY_OWNER):
                raise RuntimeError(f"Cannot own tray D-Bus name {self.service_name}: {name_reply}")

            # Verify the menu's DBus signature and serialized payload before
            # advertising the SNI to Plasma. Otherwise a "connected" tray can
            # offer scroll/middle-click while right-click silently fails.
            reply = await asyncio.wait_for(bus.call(Message(
                destination=self.service_name,
                path='/MenuBar', interface='com.canonical.dbusmenu',
                member='GetLayout', signature='iias', body=[0, -1, []],
            )), timeout=3)
            if not (reply and reply.message_type == MessageType.METHOD_RETURN
                    and len(reply.body) == 2
                    and reply.body[1][0] == 0 and reply.body[1][2]):
                self.menu_probe = ('FAILED: ' + str(reply.error_name if reply else 'empty response')
                                   + ' ' + str(reply.body if reply else ''))
                # Keep the working SNI Scroll/SecondaryActivate methods alive.
                # If Plasma cannot import the menu, ContextMenu opens the main UI
                # and diagnostics retain the exact serialization failure.
                print('Lysnav for KDE Plasma: ' + self.menu_probe, file=__import__('sys').stderr)
            else:
                self.menu_probe = f'OK, {len(reply.body[1][2])} top-level items'

            # Plasma may start the watcher after the GUI process, or be
            # restarting it during session restore. Try both supported watcher
            # names, with short retries, before falling back to Qt's icon.
            errors = []
            for attempt in range(4):
                for watcher in ('org.kde.StatusNotifierWatcher', 'org.freedesktop.StatusNotifierWatcher'):
                    try:
                        response = await asyncio.wait_for(bus.call(Message(
                            destination=watcher,
                            path='/StatusNotifierWatcher',
                            interface=watcher,
                            member='RegisterStatusNotifierItem',
                            signature='s', body=[self.service_name],
                        )), timeout=1.5)
                        if response and response.message_type == MessageType.METHOD_RETURN:
                            self.signals.ready.emit()
                            await self.done.wait()
                            return
                        error = f"{response.error_name}: {response.body}" if response else 'empty D-Bus response'
                    except Exception as exc:
                        error = f"{type(exc).__name__}: {exc}"
                    errors.append(f'{watcher}: {error}')
                if attempt < 3:
                    await asyncio.sleep(0.35)
            raise RuntimeError('Native tray registration failed: ' + '; '.join(errors[-4:]))
        finally:
            self.bus = None
            bus.disconnect()

    def update(self, *, icon=None, tooltip=None, menu_model=None):
        # Preserve changes racing with the initial D-Bus registration.
        if icon is not None:
            self.icon_name = icon
        if tooltip is not None:
            self.tooltip = tooltip
        if menu_model is not None:
            self.menu_model = menu_model
        if self.loop and self.loop.is_running():
            try:
                if self.item:
                    self.loop.call_soon_threadsafe(self.item.update, icon, tooltip)
                if menu_model is not None and self.menu:
                    self.loop.call_soon_threadsafe(self.menu.replace, menu_model)
            except RuntimeError:
                pass

    def show_feedback(self, text: str):
        """Best-effort KDE OSD; shows live target before the debounced write.

        This uses the existing Plasma session service, not a new daemon. The
        SNI tooltip is updated separately and works if OSD is unavailable.
        """
        if not (self.loop and self.loop.is_running() and self.bus):
            return
        async def send():
            try:
                await self.bus.call(Message(
                    destination='org.kde.plasmashell',
                    path='/org/kde/osdService',
                    interface='org.kde.osdService',
                    member='showText',
                    signature='ss',
                    # Empty icon removes the unrelated missing-icon glyph.
                    # Plasma itself uses an empty icon for text-only OSDs.
                    body=['', str(text)],
                ))
            except Exception:
                pass
        try:
            self.loop.call_soon_threadsafe(lambda: asyncio.create_task(send()))
        except RuntimeError:
            pass

    def stop(self):
        if self.loop and self.done and self.loop.is_running():
            try:
                self.loop.call_soon_threadsafe(self.done.set)
            except RuntimeError:
                pass
        if self.thread.is_alive():
            self.thread.join(timeout=3)
