"""Real D-BusMenu contract test, run under dbus-run-session in CI.

This does not require Plasma or a hub. It verifies that the *actual* dbus-next
exported service can be introspected, queried and clicked by a separate client.
"""
import asyncio
import os
import unittest

try:
    from dbus_next import BusType, Message, MessageType, Variant
    from dbus_next.aio import MessageBus
    from tray_sni import Item, NativeMenu
except ImportError:
    Item = None

from tray_menu_model import build_menu


class Capture:
    def __init__(self):
        self.values = []

    def emit(self, *values):
        self.values.append(values)


class Signals:
    def __init__(self):
        self.show_requested = Capture()
        self.middle_clicked = Capture()
        self.menu_requested = Capture()
        self.scroll_requested = Capture()
        self.menu_action = Capture()


@unittest.skipUnless(Item is not None and 'DBUS_SESSION_BUS_ADDRESS' in os.environ,
                     'Requires dbus-next and dbus-run-session')
class NativeDBusTests(unittest.TestCase):
    def test_exported_menu_is_readable_and_clickable(self):
        async def exercise():
            signals = Signals()
            model = build_menu({'r1': 'My room'}, 'r1', power_available=True,
                               brightness_available=True, native_ready=True)
            server = await MessageBus(bus_type=BusType.SESSION).connect()
            client = None
            try:
                item = Item(signals, 'weather-clear', '23 C · 40% RH')
                menu = NativeMenu(signals, model)
                server.export('/StatusNotifierItem', item)
                server.export('/MenuBar', menu)
                from dbus_next.constants import RequestNameReply
                service_name = 'org.kde.StatusNotifierItem-999999-1'
                self.assertEqual(await server.request_name(service_name), RequestNameReply.PRIMARY_OWNER)
                client = await MessageBus(bus_type=BusType.SESSION).connect()
                async def call(path, iface, member, signature='', body=None):
                    reply = await client.call(Message(destination=service_name,
                        path=path, interface=iface, member=member,
                        signature=signature, body=body or []))
                    self.assertEqual(reply.message_type, MessageType.METHOD_RETURN,
                                     f'{member} failed: {reply.error_name} {reply.body}')
                    return reply
                menu_property = await call('/StatusNotifierItem',
                    'org.freedesktop.DBus.Properties', 'Get', 'ss',
                    ['org.kde.StatusNotifierItem', 'Menu'])
                self.assertEqual(menu_property.body[0].value, '/MenuBar')
                # A sandboxed or user-supplied image must arrive as network-order ARGB,
                # even when the panel cannot resolve a theme icon by name.
                pixels = [[1, 1, bytes([255, 16, 32, 48])]]
                item.update(icon='', pixmaps=pixels)
                icon = await call('/StatusNotifierItem', 'org.freedesktop.DBus.Properties',
                                  'Get', 'ss', ['org.kde.StatusNotifierItem', 'IconPixmap'])
                self.assertEqual(icon.body[0].value, pixels)
                item.update(icon='weather-clear')
                self.assertEqual(item.IconName, 'weather-clear')
                self.assertEqual(item.IconPixmap, [])
                layout = await call('/MenuBar', 'com.canonical.dbusmenu',
                                    'GetLayout', 'iias', [0, -1, []])
                self.assertEqual(layout.body[1][0], 0)
                self.assertGreaterEqual(len(layout.body[1][2]), 5)
                self.assertEqual(layout.body[1][2][-1].value[0], 9)  # Quit
                # Exercise the second struct-returning method as well. Both
                # methods must return lists, or Plasma may reject the menu.
                group = await call('/MenuBar', 'com.canonical.dbusmenu',
                                   'GetGroupProperties', 'aias', [[1, 4, 9], []])
                self.assertEqual([item[0] for item in group.body[0]], [1, 4, 9])
                self.assertTrue(all(isinstance(item, list) for item in group.body[0]))
                submenu = await call('/MenuBar', 'com.canonical.dbusmenu',
                                     'GetLayout', 'iias', [4, -1, []])
                self.assertEqual(submenu.body[1][0], 4)
                self.assertGreaterEqual(len(submenu.body[1][2]), 1)
                # Trigger the Quit action through a D-Bus Event to validate
                # that the Qt-thread signal would be dispatched.
                await call('/MenuBar', 'com.canonical.dbusmenu', 'Event',
                           'isvu', [9, 'clicked', Variant('s', ''), 0])
                self.assertEqual(signals.menu_action.values, [('quit',)])
                await call('/StatusNotifierItem', 'org.kde.StatusNotifierItem',
                           'Scroll', 'is', [120, 'Vertical'])
                self.assertEqual(signals.scroll_requested.values, [(120, 'Vertical')])
                self.assertEqual(item.scroll_calls, 1)
                self.assertEqual(item.last_scroll, (120, 'Vertical'))
                await call('/StatusNotifierItem', 'org.kde.StatusNotifierItem',
                           'SecondaryActivate', 'ii', [0, 0])
                self.assertEqual(signals.middle_clicked.values, [()])
            finally:
                if client:
                    client.disconnect()
                server.disconnect()
        asyncio.run(exercise())


if __name__ == '__main__':
    unittest.main()
