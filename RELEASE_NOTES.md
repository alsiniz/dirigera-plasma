> **Unreleased:** The token pairing GUI is new and has not been tested on a physical DIRIGERA hub. Public release is on hold.

# DIRIGERA Plasma 1.0.0-dev.7 (internal test build)

**Not a public release.** Dev.5's native right-click menu and tray scrolling
were confirmed working on the tester's KDE Plasma setup. This build limits
changes to UI wording and settings content; native tray code is unchanged.

- Removed trailing ellipses from main-window **Choose devices** and **Tray settings**.
- Renamed **Tray icon** to **App icon** and clarified panel scroll/middle-click behavior.
- Added guidance to reserve DIRIGERA's local IP through router DHCP settings.
- Added a native **Support on Ko-fi** button linking to
  <https://ko-fi.com/alsiniz>; it opens the user's browser only when clicked.
- Removed the unnecessary placeholder icon from the Plasma brightness OSD,
  retaining the short-lived text feedback and existing hub command timing.
- Retained MIT licensing, allowlisted-light controls, and plain-language token warning.

See [TESTING.md](TESTING.md) for the focused validation checklist.
