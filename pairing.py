"""Small, Qt-independent helpers for user-initiated DIRIGERA token pairing."""
from __future__ import annotations

import ipaddress
import re

_HOST_LABEL = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?$")
_TOKEN = re.compile(r"\bYour\s+token\s*:\s*([A-Za-z0-9._~-]{32,})", re.IGNORECASE)


def valid_hub_address(value: str) -> bool:
    """Accept syntactically valid IP literals or LAN hostnames, not URLs/ports.

    Validation here is intentionally offline: a syntactically valid address might
    still be unreachable, and that failure is reported when pairing is attempted.
    """
    if not isinstance(value, str) or not value or value != value.strip():
        return False
    if len(value) > 253 or any(char.isspace() for char in value):
        return False
    try:
        addr = ipaddress.ip_address(value)
    except ValueError:
        # Reject malformed IPv4-looking text rather than treating it as a DNS name.
        if re.fullmatch(r"[0-9.]+", value):
            return False
        return all(_HOST_LABEL.fullmatch(part) for part in value.split("."))
    else:
        return not (addr.is_multicast or addr.is_unspecified or addr.is_loopback)


def extract_generated_token(output: str) -> str | None:
    """Find the generated token without ever printing it or logging the output."""
    if not isinstance(output, str):
        return None
    match = _TOKEN.search(output)
    return match.group(1) if match else None


def run_token_helper(ip: str) -> None:
    """Run the upstream CLI only when the app is launched as a helper process."""
    if not valid_hub_address(ip):
        raise SystemExit("Invalid DIRIGERA hub address")
    import sys
    from dirigera.hub.auth import main
    sys.argv = ["generate-token", ip]
    main()
