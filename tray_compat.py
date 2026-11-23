"""Narrow compatibility support for dbus-next on Python 3.15+.

The released dbus-next 0.2.3 service module imports typing.no_type_check_decorator,
which Python removed in 3.15. This decorator only affects *static* type checking;
its wrapping behavior is preserved here for the lifetime of this application.
Nothing is written to, or patched in, the Python installation on disk.
"""

from __future__ import annotations

import typing
from functools import wraps


def ensure_dbus_next_typing_compat() -> bool:
    """Restore the deprecated helper only when Python does not provide it.

    Returns True if the compatibility helper was installed, False if the
    standard-library version already exists. Safe to invoke more than once.
    """
    if hasattr(typing, 'no_type_check_decorator'):
        return False

    def no_type_check_decorator(decorator):
        @wraps(decorator)
        def wrapped_decorator(*args, **kwargs):
            return typing.no_type_check(decorator(*args, **kwargs))
        return wrapped_decorator

    typing.no_type_check_decorator = no_type_check_decorator
    return True
