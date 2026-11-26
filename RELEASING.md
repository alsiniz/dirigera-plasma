# Publishing Lysnav for KDE Plasma releases

## v1.0.0

The first release distributes the validated **Linux x86_64 AppImage only**. Flatpak bundles are built by CI but intentionally excluded until runtime tests on KDE Plasma pass.

The GitHub Actions workflow `.github/workflows/release-appimage.yml` builds the AppImage from the release commit, runs offline tests, generates its SHA-256 checksum, and publishes both files under the stable version from `version.py`.

**Validation:** The candidate AppImage was tested on Bazzite KDE Plasma with an empty configuration and full GUI hub authorization. The tray context menu, scroll-to-dim, middle-click, climate tooltip, icon selection and light controls were tested. The original AppImage's nonfatal XDG portal identity warning is documented.

## Future releases

1. Update `version.py`, release notes, README and changelog.
2. Pass automated unit, Qt and D-Bus tests, and build both bundles in CI.
3. Test portable packages against KDE Plasma, especially the tray's StatusNotifier interface.
4. Keep untested formats off public releases.
5. Tag the exact source commit and publish binaries and checksum hashes.

This is an independent community project distributed under the [MIT License](LICENSE).
