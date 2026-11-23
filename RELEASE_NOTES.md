# DIRIGERA Plasma v1.0.0

First stable release of **DIRIGERA Plasma**, a lightweight KDE Plasma desktop controller for homes using an existing **IKEA DIRIGERA hub**.

## Download

- **Linux x86_64 AppImage:** `DIRIGERA-Plasma-v1.0.0-x86_64.AppImage` (portable, no root or additional hub required).
- **SHA-256 checksum:** `SHA256SUMS.txt` to verify the download.
- **Source code:** Available under the MIT License.

The **Flatpak build is not part of v1.0.0**. It builds successfully in CI but still needs a real KDE Plasma runtime test before distribution.

## Features

- Local-only communication with DIRIGERA: no cloud credentials, ongoing internet access, second hub, or Home Assistant service.
- Native KDE Plasma system-tray integration, including scroll-to-dim (5% steps), middle-click room toggle, hover climate tooltip, right-click actions, and a short brightness OSD.
- Per-room and individual-light power, brightness, colour temperature and live RGB colour selection for supported bulbs.
- Opt-in device-ID allowlist for shared households. Room actions only target explicitly approved bulbs, while climate sensors are read-only.
- In-app GUI authorization: generate a hub access token by pressing DIRIGERA's physical action button. No terminal-based pairing required.
- Qt/PySide6 interface with KDE-native styling and icon selection from the active installed icon theme.

## Validation and limitations

- Tested on **Bazzite / KDE Plasma**, including a fresh AppImage GUI token authorization, light and climate discovery, room/device controls, and tray interactions.
- GitHub Actions AppImage build and automated tests pass. Compatibility with other KDE Plasma distributions is expected but **not yet tested or guaranteed**; this is an x86_64 binary.
- Direct AppImage execution may log a **nonfatal XDG desktop portal warning** saying the app's ID is not registered. It does not prevent local control; optional desktop registration can be added later.
- Uses an **unofficial, undocumented IKEA DIRIGERA local API**, and compatibility may change after future hub firmware updates.
- Device approvals restrict *this application*, not the hub token itself. Keep the token private: other software possessing it may be able to control other devices on the hub.

## Quick start

1. Download the AppImage from the assets below.
2. Run `chmod +x DIRIGERA-Plasma-v1.0.0-x86_64.AppImage`, then execute it.
3. Enter your hub's LAN address, select **Generate token**, press the hub action button, and confirm in the GUI.
4. Select **Choose devices** and approve only your own lights and desired climate sensors.

See [README](https://github.com/alsiniz/dirigera-plasma#readme), [Security](https://github.com/alsiniz/dirigera-plasma/blob/main/SECURITY.md), and [Issues](https://github.com/alsiniz/dirigera-plasma/issues).

Developed and maintained by [alsiniz](https://github.com/alsiniz) with development assistance from ChatGPT. Independent community project; not affiliated with IKEA or KDE.
