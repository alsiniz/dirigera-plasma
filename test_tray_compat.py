"""Dependency-free checks for the Python 3.15 dbus-next import workaround."""

import subprocess
import sys
import textwrap
import unittest

from tray_compat import ensure_dbus_next_typing_compat


class DBusCompatTests(unittest.TestCase):
    def test_existing_decorator_is_untouched(self):
        import typing
        # On Python 3.15 the helper is initially absent. Installing it first
        # makes this idempotence test valid on both old and new interpreters.
        ensure_dbus_next_typing_compat()
        previous = typing.no_type_check_decorator
        self.assertFalse(ensure_dbus_next_typing_compat())
        self.assertIs(typing.no_type_check_decorator, previous)

    def test_removed_helper_simulation(self):
        # Separate interpreter keeps global typing changes away from other tests.
        script = textwrap.dedent('''
            import typing
            if hasattr(typing, 'no_type_check_decorator'):
                del typing.no_type_check_decorator
            from tray_compat import ensure_dbus_next_typing_compat
            assert ensure_dbus_next_typing_compat()
            assert not ensure_dbus_next_typing_compat()
            from typing import no_type_check_decorator
            @no_type_check_decorator
            def decorator(fn):
                def call(*args, **kwargs):
                    return fn(*args, **kwargs)
                return call
            @decorator
            def add(x, y):
                return x + y
            assert add(2, 3) == 5
            assert getattr(add, '__no_type_check__', False)
        ''')
        result = subprocess.run([sys.executable, '-c', script], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()
