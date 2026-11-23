import unittest
from tray_menu_model import build_menu, get_node, menu_properties, layout_for


class MenuTests(unittest.TestCase):
    def setUp(self):
        self.menu = build_menu({'room-one': 'My room'}, 'room-one',
                               power_available=True, brightness_available=True,
                               native_ready=True)

    def test_contains_usable_native_menu_entries(self):
        for entry in (1, 2, 3, 4, 5, 7, 8, 9, 10, 100):
            self.assertIsNotNone(get_node(self.menu, entry))
        self.assertEqual(get_node(self.menu, 9)['action'], 'quit')
        self.assertIsNone(get_node(self.menu, 6))  # diagnostics moved into settings

    def test_no_bulk_commands_or_5_percent_buttons(self):
        serialized = repr(self.menu)
        self.assertNotIn('other-resident', serialized)
        self.assertNotIn('all_devices', serialized)
        self.assertNotIn('bright_up', serialized)
        self.assertNotIn('bright_down', serialized)
        self.assertNotIn('5%', serialized)
        self.assertEqual(get_node(self.menu, 100)['action'], 'room:room-one')

    def test_toggle_disabled_if_no_eligible_lights(self):
        menu = build_menu({}, '', power_available=False,
                          brightness_available=False, native_ready=False)
        self.assertFalse(get_node(menu, 2)['enabled'])
        self.assertIsNone(get_node(menu, 100))
        self.assertTrue(get_node(menu, 9)['enabled'])  # quit always available

    def test_native_menu_has_submenus_and_radio(self):
        v = lambda sig, val: (sig, val)
        self.assertEqual(menu_properties(get_node(self.menu, 4), v)['children-display'], ('s', 'submenu'))
        self.assertEqual(menu_properties(get_node(self.menu, 100), v)['toggle-state'], ('i', 1))
        result = layout_for(self.menu, -1, [], v)
        self.assertEqual(result[0], 0)
        self.assertEqual(result[2][0][0], '(ia{sv}av)')

    def test_dbus_structs_are_lists_even_inside_variants(self):
        # Regression: dbus-next rejects tuples for D-Bus STRUCT signatures.
        # This exact bug made Plasma's menu importer fail on GetLayout.
        def strict_variant(signature, value):
            if signature == '(ia{sv}av)' and not isinstance(value, list):
                raise TypeError('D-Bus STRUCT must be a list, not tuple')
            return (signature, value)

        result = layout_for(self.menu, -1, [], strict_variant)
        self.assertIsInstance(result, list)
        def validate(item):
            self.assertIsInstance(item, list)
            self.assertEqual(len(item), 3)
            for variant_sig, child in item[2]:
                self.assertEqual(variant_sig, '(ia{sv}av)')
                validate(child)
        validate(result)

    def test_depth_limits(self):
        v = lambda sig, val: (sig, val)
        self.assertFalse(layout_for(self.menu, 0, [], v)[2])
        self.assertFalse(layout_for(self.menu, 1, [], v)[2][3][1][2])

    def test_properties_filtered(self):
        v = lambda sig, val: (sig, val)
        props = menu_properties(get_node(self.menu, 1), v, ['label'])
        self.assertEqual(list(props), ['label'])

    def test_root_has_no_visual_properties(self):
        self.assertEqual(menu_properties(self.menu, lambda a, b: (a, b)), {})

    def test_separator(self):
        v = lambda sig, val: (sig, val)
        self.assertEqual(menu_properties(get_node(self.menu, 8), v), {'type': ('s', 'separator')})

    def test_actions_are_unique(self):
        def visit(n):
            return [n['id']] + [j for c in n['children'] for j in visit(c)]
        all_ids = visit(self.menu)
        self.assertEqual(len(all_ids), len(set(all_ids)))


if __name__ == '__main__':
    unittest.main()
