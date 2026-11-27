# Lysnav for KDE Plasma 1.0.0-dev.7 — GUI pairing acceptance test

**Development build only. Do not publish it yet.** Dev.5's native Plasma menu
and tray scrolling were confirmed working. This update should not change either.

### Hub pairing in the graphical interface

1. Open **Hub settings**. Remove the hub address temporarily. **Generate token**
   must become disabled, and must remain disabled for a URL, malformed IP,
   or whitespace-only input. A normal IPv4 LAN address should enable it.
2. Click **Generate token**. A pairing dialog must open without freezing the
   window. Press the physical action button under DIRIGERA and select
   **Continue**. The resulting token must populate the masked Access token
   field; it must not appear in notifications or logs.
3. Choose **Cancel** in Hub settings and verify that your previously saved
   token stays unchanged. Repeat pairing and choose **Save** to keep the new
   token. Only perform the Save check if you intend to replace an existing
   working token.
4. Cancel pairing midway: the helper must terminate, with no lingering process.
5. Confirm Hub settings opens large enough to show its DHCP advice and buttons
   without clipping. About must credit **alsiniz** as maintainer with a link to
   `https://github.com/alsiniz`.

1. Fully quit the previous app via native tray menu or **Ctrl+Q**, then install
   dev.6 and launch it. Confirm stored hub access, approved lights, sensors,
   selected room, and icon are preserved.
2. In the main window, verify **Choose devices** and **Tray settings** have no
   trailing ellipses and match the other buttons visually.
3. Open **Tray settings**. Confirm **Tray icon** affects only the notification area, the
   selected icon is preserved, and **Plasma panel shortcuts** explicitly
   explains scrolling over the panel icon and middle-clicking it. Confirm
   **Input diagnostics…** still opens from the settings dialog.
4. Open **Hub settings**. Confirm the DHCP reservation advice is readable,
   mentions router manuals, and changing nothing can be cancelled safely.
5. **Regressions:** right-click the native Plasma icon repeatedly, scroll over
   it to adjust only your approved room lights, and middle-click to toggle.
   Hover to check both temperature and humidity in the tooltip.
6. Check main-window brightness track-click, wheel and drag; confirm bulb
   commands are sent. Check live colour wheel preview.
7. Open **About**: version reads `1.0.0-dev.7`; MIT license and hub-wide
   access-token explanation remain. **Support on Ko-fi** opens
   `https://ko-fi.com/alsiniz` through the default browser only when clicked.
8. Scroll over the real Plasma tray icon: the brightness percentage appears
   as short-lived **text-only** OSD feedback, with no placeholder icon.
9. Verify that no other household member's lights were controlled.

## Live tray icon and application branding acceptance test

- Open Tray settings in both desktop colour modes. Check that room, tray
  appearance and mouse controls are visually separated, text wraps cleanly,
  and all buttons remain visible at the minimum window size and larger fonts.
- Choose a system or local custom icon; check its preview, disabled dynamic
  status message and the enabled Restore default dynamic icon button. Cancel
  must leave the running tray and config unchanged. Repeat and Save; then
  restore the default, Save, and check the live shade returns. Input diagnostics
  must remain accessible without dismissing the settings.
- In both desktop colour modes, turn the last approved light off and then
  turn an approved light on in a different room. The transparent tray shade
  should be orange only while at least one approved light is on.
- Change an unapproved light; the default tray icon must not react. Test
  physical switches and external controllers within the normal refresh cycle.
- Switch desktop colours while lights are on and off; check the actual panel,
  including an independently selected Plasma theme. Retest the custom tray
  icon override and its default reset.
- Interrupt hub access with an approved light on: the last known orange shade
  must remain and the tooltip must mark status unverified. Restore access.
- Check the full-colour logo in the launcher, task manager, window and
  AppImage file icon (including upgrades; KDE may cache old launcher icons).

## Automated tests

`python3 -m unittest discover -p 'test_*.py' -v`

Qt widget tests need PySide6. The native menu's D-Bus contract tests need
`dbus-next` and a D-Bus session. Neither integration test substitutes for
checking the actual Plasma desktop.
