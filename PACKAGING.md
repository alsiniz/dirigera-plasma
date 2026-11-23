# Packaging pre-release checklist

This branch provides experimental x86_64 AppImage and Flatpak builds. Run **Actions → Experimental Linux package builds → Run workflow** after merging. Both builds download dependencies. Do not publish v1.0.0 until the artifacts are installed and tested on a KDE Plasma desktop.

## Downloadable artifacts
- `DIRIGERA-Plasma-x86_64.AppImage` (PyInstaller, appimagetool). Use `chmod +x` then run it.
- `dirigera-plasma.flatpak` (KDE runtime 6.10, PySide6 BaseApp). Install with `flatpak install --user ./dirigera-plasma.flatpak`, launch with `flatpak run io.github.alsiniz.DirigeraPlasma`.

The Flatpak requests LAN networking, KDE StatusNotifierWatcher access, a narrowly scoped tray name, Plasma OSD, and read-only KDE icon-theme settings. It does not request full home-directory access. Credentials and approved devices are stored separately inside the Flatpak sandbox, so reauthorize the hub in the GUI on first Flatpak launch.

## Acceptance checks (both formats)
- [ ] First launch and GUI hub authorization work
- [ ] Approved-device safety rules; other household lights cannot be controlled
- [ ] Room and individual light brightness, power, Kelvin and RGB wheel
- [ ] Tray hover climate tooltip
- [ ] Tray wheel changes brightness with an OSD
- [ ] Tray middle-click toggles approved bulbs
- [ ] Native right-click menu opens consistently and Quit works
- [ ] Icon picker shows installed KDE icon theme
- [ ] Program shuts down cleanly and relaunches
- [ ] Third-party licenses and MIT license are included

These builds are for testing first. A GitHub release and Flathub submission are separate follow-up steps.
