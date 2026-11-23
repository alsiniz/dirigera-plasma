# Third-party components and acknowledgments

DIRIGERA Plasma does **not** bundle the dependencies below in its source archive.
The user-local installer downloads them into a virtual environment. Their
licenses remain their own and are not replaced by this project's MIT license.

| Component | Purpose | License / upstream |
|---|---|---|
| [dirigera](https://github.com/Leggin/dirigera) | Unofficial local DIRIGERA API and device models | MIT; Leggin and contributors |
| [PySide6 / Qt for Python](https://doc.qt.io/qtforpython-6/) | Qt desktop interface and widgets | LGPLv3/GPLv3/commercial license options; Qt for Python team |
| [dbus-next](https://github.com/altdesktop/python-dbus-next) | D-Bus StatusNotifierItem and D-BusMenu | MIT; dbus-next contributors |
| [KDE Plasma](https://kde.org/plasma-desktop/) | System tray host and OSD | KDE community; various licenses |
| [KDE and freedesktop icon themes](https://develop.kde.org/docs/features/icons/) | System-provided theme icon names (no icon files distributed) | Themes remain the property of their respective authors |

**Protocols:** `org.kde.StatusNotifierItem` and `com.canonical.dbusmenu` via the
session D-Bus. The IKEA DIRIGERA hub's undocumented local HTTPS API is accessed
through the `dirigera` library. No proprietary IKEA SDK or API files are bundled.

**Development acknowledgment:** initial implementation and troubleshooting
were carried out collaboratively with OpenAI's ChatGPT. Credit for the
upstream libraries and protocols belongs to their respective projects.

IKEA and DIRIGERA are marks of their respective owners. This is an independent
community project, unaffiliated with IKEA or KDE.
