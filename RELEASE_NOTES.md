# DIRIGERA Plasma v1.0.1

This patch fixes memory growth in long-running tray sessions. Each successful refresh in v1.0.0 retained old room and climate controls and an extra tray submenu. The app now releases replaced controls, reuses its tray menu, and frees Tray Settings after Save or Cancel.

## Updating from v1.0.0

1. Choose **Quit DIRIGERA Plasma** from the tray menu to stop the old process.
2. Download `DIRIGERA-Plasma-v1.0.1-x86_64.AppImage` and `SHA256SUMS.txt` from this release. Run `sha256sum -c SHA256SUMS.txt` in the download directory.
3. Run `chmod +x DIRIGERA-Plasma-v1.0.1-x86_64.AppImage` and launch the new file. It uses your existing hub pairing and device approvals. If a launcher points to the old filename, update it to the new one.
