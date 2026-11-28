# Lysnav for KDE Plasma

## 1.0.4

- Choose a room or All approved lights in Tray settings. Middle-click, brightness scrolling, and the default lamp indicator follow that selection.
- The lampshade turns orange when any light in the selection is on and stays monochrome when all are off.
- Hub settings now includes token reveal and copy controls, a guided pairing dialog, and DHCP reservation guidance.
- Automatic refresh recovers from a failed first hub check.

Existing room and custom icon choices carry over. If you used Automatic with approved lights in more than one room, choose a tray selection after upgrading.

### Download and run

Download `Lysnav-Plasma-v1.0.4-x86_64.AppImage` and `SHA256SUMS.txt` into the same directory. Quit the old app from its tray menu, then run these commands from the download directory.

```sh
sha256sum -c SHA256SUMS.txt
chmod +x Lysnav-Plasma-v1.0.4-x86_64.AppImage
./Lysnav-Plasma-v1.0.4-x86_64.AppImage
```

### Upgrading from DIRIGERA Plasma

The AppImage uses `~/.config/lysnav/config.json` if it exists. Otherwise it reads `~/.config/dirigera-plasma/config.json`, including the hub address and token, light and sensor approvals, selected tray room, and custom icon choice. You can start using your paired hub immediately. On the first settings save, Lysnav writes its own private file and uses it for subsequent launches. The old file stays in place. Both paths follow `XDG_CONFIG_HOME` if you set it.

The source installer copies the old file during installation if Lysnav has no settings yet. The experimental Flatpak uses the separate `io.github.alsiniz.Lysnav` sandbox. If you used the old Flatpak, pair the hub and approve your devices again in the new sandbox. This release distributes the x86_64 AppImage.
