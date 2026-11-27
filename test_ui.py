"""Qt slider regression test. Run with QT_QPA_PLATFORM=offscreen on CI."""
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
import gc
import tracemalloc
import sys
import os
import unittest
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
try:
    from PySide6.QtCore import QObject, Qt, QPoint, QPointF, QCoreApplication, QEvent, QTimer
    from PySide6.QtTest import QTest
    from PySide6.QtGui import QColor, QIcon, QPalette, QWheelEvent
    from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QMenu, QScrollArea, QDialog, QDialogButtonBox, QSystemTrayIcon
    from shiboken6 import isValid
    from app import panel_is_dark, IconPickerDialog, ClickToJumpSlider, TraySettingsDialog, ConnectionDialog, MainWindow
    from core import EnvironmentInfo, LightInfo
except ImportError:
    if os.environ.get('LYSNAV_REQUIRE_QT_TESTS') == '1':
        raise
    ClickToJumpSlider = None


def process_memory_bytes():
    """Current resident/working-set bytes, diagnostic only (not a leak verdict)."""
    if sys.platform == "win32":
        import ctypes
        from ctypes import wintypes

        class Counters(ctypes.Structure):
            _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD)] + [
                (name, ctypes.c_size_t) for name in (
                    "PeakWorkingSetSize", "WorkingSetSize", "QuotaPeakPagedPoolUsage",
                    "QuotaPagedPoolUsage", "QuotaPeakNonPagedPoolUsage",
                    "QuotaNonPagedPoolUsage", "PagefileUsage", "PeakPagefileUsage")]

        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        psapi = ctypes.WinDLL("psapi", use_last_error=True)
        kernel.GetCurrentProcess.restype = wintypes.HANDLE
        psapi.GetProcessMemoryInfo.argtypes = (
            wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD)
        psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
        stats = Counters()
        stats.cb = ctypes.sizeof(stats)
        if psapi.GetProcessMemoryInfo(kernel.GetCurrentProcess(), ctypes.byref(stats), stats.cb):
            return stats.WorkingSetSize
    elif sys.platform.startswith("linux"):
        try:
            return int(Path("/proc/self/statm").read_text().split()[1]) * os.sysconf("SC_PAGE_SIZE")
        except (OSError, ValueError, IndexError):
            pass
    return None


@unittest.skipUnless(ClickToJumpSlider is not None, 'PySide6 not installed (non-UI test environment)')
class SliderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_wheel_notifies_window_for_debounced_commit(self):
        slider = ClickToJumpSlider(Qt.Orientation.Horizontal)
        slider.setRange(1, 100)
        slider.setValue(50)
        slider.resize(300, 32)
        slider.show()
        seen = []
        slider.wheelAdjusted.connect(seen.append)
        center = QPointF(150, 16)
        event = QWheelEvent(center, center, QPoint(0, 0), QPoint(0, 120),
                            Qt.MouseButton.NoButton, Qt.KeyboardModifier.NoModifier,
                            Qt.ScrollPhase.ScrollUpdate, False)
        QApplication.sendEvent(slider, event)
        self.assertGreater(slider.value(), 50)
        self.assertEqual(seen, [slider.value()])
        slider.close()

    def test_track_click_jumps_and_emits_commit(self):
        slider = ClickToJumpSlider(Qt.Orientation.Horizontal)
        slider.resize(300, 32)
        slider.setRange(1, 100)
        slider.setValue(10)
        slider.show()
        events = []
        slider.trackClicked.connect(events.append)
        QTest.mouseClick(slider, Qt.MouseButton.LeftButton, pos=QPoint(260, 16))
        self.assertEqual(len(events), 1)
        self.assertGreater(slider.value(), 65)
        self.assertEqual(events[0], slider.value())
        slider.close()


@unittest.skipUnless(ClickToJumpSlider is not None, 'PySide6 not installed (non-UI test environment)')
class TraySettingsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_preview_restore_and_cancel_are_staged(self):
        parent = QWidget()
        self.addCleanup(parent.deleteLater)
        with TemporaryDirectory() as folder:
            path = Path(folder) / "custom.svg"
            path.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48">'
                            '<rect width="48" height="48" fill="#176a95"/></svg>')
            default = QIcon(str(Path(__file__).parent / "assets" / "tray-dark-on.svg"))
            dialog = TraySettingsDialog(parent, str(path), "r1", {"r1": "Room"},
                                        default_icon=lambda: default)
            self.addCleanup(dialog.deleteLater)
            self.assertTrue(dialog.restore_button.isEnabled())
            self.assertEqual(dialog.icon_status.text(), "Dynamic lighting status disabled")
            self.assertEqual(dialog.icon_preview.pixmap().toImage().pixelColor(24, 24).name(),
                             "#176a95")
            self.assertIn("Custom icons do not reflect", dialog.icon_notice.text())
            dialog.restore_button.click()
            self.assertEqual(dialog.icon_name, "")
            self.assertFalse(dialog.restore_button.isEnabled())
            self.assertEqual(dialog.icon_status.text(), "Dynamic lighting status enabled")
            self.assertEqual(dialog.icon_preview.pixmap().toImage().pixelColor(24, 19).name(),
                             "#fe8019")
            self.assertEqual(dialog.room.currentData(), "r1")
            dialog.reject()
            self.assertEqual(dialog.result(), QDialog.DialogCode.Rejected)

    def test_picker_selection_updates_preview_but_cancel_keeps_selection(self):
        parent = QWidget()
        self.addCleanup(parent.deleteLater)
        with TemporaryDirectory() as folder:
            path = Path(folder) / "custom.svg"
            path.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48">'
                            '<rect width="48" height="48" fill="#176a95"/></svg>')
            dialog = TraySettingsDialog(parent, "", "", {})
            self.addCleanup(dialog.deleteLater)
            self.assertFalse(dialog.restore_button.isEnabled())
            with patch("app.IconPickerDialog") as picker:
                picker.return_value.chosen = str(path)
                picker.return_value.exec.return_value = QDialog.DialogCode.Accepted
                dialog.browse_button.click()
                self.assertEqual(dialog.icon_name, str(path))
                self.assertTrue(dialog.restore_button.isEnabled())
                self.assertEqual(dialog.icon_label.text(), "custom.svg")
                self.assertEqual(dialog.icon_status.text(), "Dynamic lighting status disabled")
                picker.return_value.chosen = ""
                picker.return_value.exec.return_value = QDialog.DialogCode.Rejected
                dialog.browse_button.click()
                self.assertEqual(dialog.icon_name, str(path))
            dialog.restore_button.click()
            dialog.findChild(QDialogButtonBox).button(QDialogButtonBox.StandardButton.Save).click()
            self.assertEqual(dialog.result(), QDialog.DialogCode.Accepted)
            self.assertEqual(dialog.icon_name, "")

    def test_icon_action_buttons_have_equal_unclipped_height(self):
        parent = QWidget()
        self.addCleanup(parent.deleteLater)
        # Cover larger fonts as well as the usual desktop font size.
        for larger in (False, True):
            with self.subTest(larger_font=larger):
                font = self.app.font()
                if larger:
                    if font.pointSize() > 0:
                        font.setPointSize(font.pointSize() + 6)
                    else:
                        font.setPixelSize(max(1, font.pixelSize()) + 8)
                parent.setFont(font)
                dialog = TraySettingsDialog(parent, "", "r1", {"r1": "Room"})
                self.addCleanup(dialog.deleteLater)
                dialog.show()
                self.app.processEvents()
                dialog.resize(dialog.minimumSizeHint())
                self.app.processEvents()
                browse, restore = dialog.browse_button, dialog.restore_button
                self.assertFalse(restore.isEnabled())
                for enabled in (False, True):
                    restore.setEnabled(enabled)
                    self.app.processEvents()
                    self.assertEqual(browse.height(), restore.height())
                    for button in (browse, restore):
                        self.assertGreaterEqual(button.height(), 32)
                        self.assertGreaterEqual(button.height(), button.fontMetrics().height() + 12)
                        self.assertGreaterEqual(button.height(), button.sizeHint().height())
                dialog.close()

    def test_diagnostics_accessible_from_tray_settings_without_closing(self):
        class FakeMain(QWidget):
            def __init__(self):
                super().__init__()
                self.requested_from = None

            def show_tray_diagnostics(self, dialog_parent=None):
                self.requested_from = dialog_parent

        parent = FakeMain()
        dialog = TraySettingsDialog(parent, 'weather-clear', 'r1', {'r1': 'Room'})
        matches = [b for b in dialog.findChildren(QPushButton)
                   if b.text() == 'Input diagnostics…']
        self.assertEqual(len(matches), 1)
        matches[0].click()
        self.assertIs(parent.requested_from, dialog)
        self.assertEqual(dialog.result(), 0)
        dialog.close()
        parent.close()


@unittest.skipUnless(ClickToJumpSlider is not None, 'PySide6 not installed')
class ConnectionDialogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_generate_button_requires_valid_hub_address(self):
        dialog = ConnectionDialog(None, {})
        self.assertFalse(dialog.generate_button.isEnabled())
        dialog.ip.setText('not a valid hub')
        self.assertFalse(dialog.generate_button.isEnabled())
        dialog.ip.setText('192.168.1.20')
        self.assertTrue(dialog.generate_button.isEnabled())
        dialog.ip.setText('192.168.1.999')
        self.assertFalse(dialog.generate_button.isEnabled())
        dialog.close()

    def test_dialog_has_minimum_size_for_dhcp_note(self):
        dialog = ConnectionDialog(None, {})
        self.assertGreaterEqual(dialog.minimumHeight(), 335)
        self.assertGreaterEqual(dialog.minimumWidth(), 620)
        dialog.close()



@unittest.skipUnless(ClickToJumpSlider is not None, 'PySide6 not installed')
class PanelIconTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_all_four_tray_assets_have_exact_colours_and_transparency(self):
        assets = Path(__file__).resolve().parent / "assets"
        for mode, base in (("light", "#282828"), ("dark", "#ebdbb2")):
            for active in (False, True):
                with self.subTest(mode=mode, active=active):
                    suffix = "-on" if active else ""
                    icon = QIcon(str(assets / f"tray-{mode}{suffix}.svg"))
                    image = icon.pixmap(64, 64).toImage()
                    self.assertFalse(image.isNull())
                    self.assertEqual(image.pixelColor(32, 25).name(),
                                     "#fe8019" if active else base)
                    self.assertEqual(image.pixelColor(32, 50).name(), base)
                    self.assertEqual(image.pixelColor(0, 0).alpha(), 0)
        self.assertEqual((assets / "io.github.alsiniz.Lysnav.svg").read_bytes(),
                         (assets / "lysnav-logo.svg").read_bytes())

    def test_explicit_plasma_theme_precedes_app_palette(self):
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#ffffff"))
        with TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "plasmarc").write_text("[Theme]\nname=test-dark\n")
            colours = root / "plasma" / "desktoptheme" / "test-dark" / "colors"
            colours.parent.mkdir(parents=True)
            colours.write_text("[Colors:Window]\nBackgroundNormal=32,32,32\n")
            with patch.dict(os.environ, XDG_CONFIG_HOME=folder,
                            XDG_DATA_HOME=folder, XDG_DATA_DIRS=folder):
                self.assertTrue(panel_is_dark(palette))
                colours.unlink()
                self.assertFalse(panel_is_dark(palette))

    def test_panel_modes_and_custom_override(self):
        self.enterContext(patch('app.panel_is_dark', side_effect=lambda p: p.window().color().lightness() < 128))
        settings = dict(ip='test', token='test', approved={}, approved_sensors={})
        with patch('app.read_config', return_value=settings), patch.object(MainWindow, 'start_worker'), \
                patch.object(MainWindow, '_create_native_tray'):
            window = MainWindow()
        self.addCleanup(window.deleteLater)

        def set_background(colour):
            palette = QPalette(window.palette())
            palette.setColor(QPalette.ColorRole.Window, QColor(colour))
            window.setPalette(palette)

        def centre():
            return window._selected_qicon().pixmap(32, 32).toImage().pixelColor(16, 16).name()

        set_background('#ffffff')
        self.assertEqual(centre(), '#282828')
        self.assertEqual(window.windowIcon().pixmap(64, 64).toImage().pixelColor(32, 20).name(), '#fe8019')
        set_background('#121212')
        self.assertEqual(centre(), '#ebdbb2')

        with TemporaryDirectory() as folder:
            path = Path(folder) / 'custom.svg'
            path.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16">'
                            '<rect width="16" height="16" fill="#176a95"/></svg>')
            with patch('app.discover_system_icons', return_value=('test', {})):
                picker = IconPickerDialog(window, '')
            with patch('app.QFileDialog.getOpenFileName', return_value=(str(path), '')):
                picker.choose_file()
            window.config['tray_icon'] = picker.chosen
            set_background('#ffffff')
            self.assertEqual(centre(), '#176a95')
            name, pixmaps = window._notifier_icon(window._selected_qicon())
            self.assertEqual(name, '')
            self.assertEqual(pixmaps[0], [16, 16, bytes.fromhex('ff176a95') * 256])

            window.config['tray_icon'] = 'my-installed-icon'
            with patch.object(QIcon, 'fromTheme', return_value=QIcon(str(path))):
                set_background('#121212')
                self.assertEqual(centre(), '#176a95')
                self.assertEqual(window._notifier_icon(window._selected_qicon())[0], 'my-installed-icon')

            picker.choose_default()
            window.config['tray_icon'] = picker.chosen
            window._apply_panel_icon()
            self.assertEqual(centre(), '#ebdbb2')
            with patch.object(QIcon, 'hasThemeIcon', return_value=True):
                self.assertEqual(window._notifier_icon(window._selected_qicon())[0], '')
            with patch.object(QIcon, 'hasThemeIcon', return_value=False), patch.dict(os.environ, FLATPAK_ID=''):
                name, pixmaps = window._notifier_icon(window._selected_qicon())
                self.assertEqual(name, '')
                self.assertTrue(pixmaps)


@unittest.skipUnless(ClickToJumpSlider is not None, 'PySide6 not installed')
class RefreshLifetimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        config = dict(ip='test', token='test', approved={'lamp': 'room'}, approved_sensors={'sensor': 'room'})
        self.enterContext(patch('app.read_config', return_value=config))
        self.enterContext(patch.object(MainWindow, 'start_worker'))
        self.enterContext(patch.object(MainWindow, '_create_native_tray'))
        self.window = MainWindow()
        self.addCleanup(self.flush_deletions)
        self.addCleanup(self.window.deleteLater)
        self.light = LightInfo('lamp', 'Desk', 'room', 'Study', True, ('isOn', 'lightLevel'),
                               True, 50, None, None, None, 0, 1)
        self.sensor = EnvironmentInfo('sensor', 'Climate', 'room', 'Study', True, 20, 50, 90)

    def flush_deletions(self):
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)

    def test_tray_status_is_global_approved_and_does_not_replace_app_logo(self):
        window = self.window
        window.config["tray_room"] = "other"
        unapproved = replace(self.light, id="unapproved")
        moved = replace(self.light, room_id="moved")
        off = replace(self.light, on=False)
        with patch('app.panel_is_dark', return_value=True):
            def shade():
                return window._selected_qicon().pixmap(64, 64).toImage().pixelColor(32, 25).name()
            def app_shade():
                return window.windowIcon().pixmap(64, 64).toImage().pixelColor(32, 20).name()

            window.on_loaded(([off, unapproved, moved], [], ""))
            self.assertEqual(shade(), "#ebdbb2")
            self.assertEqual(app_shade(), "#fe8019")
            window.on_loaded(([self.light, unapproved], [], ""))
            self.assertEqual(shade(), "#fe8019")
            window.on_failed("offline")
            self.assertEqual(shade(), "#fe8019")
            self.assertIn("last known", window._tray_tooltip())
            window.on_loaded(([off, unapproved], [], ""))
            self.assertEqual(shade(), "#ebdbb2")
            self.assertNotIn("last known", window._tray_tooltip())
            window.on_loaded(([self.light], [], ""))
            window.config["approved"] = {}
            window.update_tray_tooltip()
            self.assertEqual(shade(), "#ebdbb2")
            self.assertEqual(app_shade(), "#fe8019")

    def test_memory_stress_dynamic_icons_refresh_and_dialogs(self):
        """Exercise thousands of updates; assert bounded live resources after warmup."""
        window = self.window
        mode = [False]
        states = (replace(self.light, on=False), self.light)
        # Exercise the Qt tray fallback and native pixmap creation without a real panel.
        window.tray = QSystemTrayIcon(window)
        from tray_sni import Item

        item = Item(window.tray_signals, "", "")
        class LocalNotifier:
            def update(self, *, icon=None, tooltip=None, pixmaps=None, menu_model=None):
                item.update(icon=icon, tooltip=tooltip, pixmaps=pixmaps)
        window.tray_sni = LocalNotifier()
        self.addCleanup(setattr, window, "tray_sni", None)
        window._apply_panel_icon(force=True)
        with TemporaryDirectory() as folder, patch("app.panel_is_dark", new=lambda palette: mode[0]):
            custom_paths = []
            for i in range(8):
                path = Path(folder) / f"custom-{i}.svg"
                path.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32">'
                                '<rect width="32" height="32" fill="#176a95"/></svg>')
                custom_paths.append(str(path))

            def drain():
                self.app.processEvents()
                self.flush_deletions()
                gc.collect()

            def exercise():
                # All four state combinations. Do not let a recording mock
                # itself accumulate thousands of call objects.
                for n in range(500):
                    mode[0] = bool(n & 2)
                    window.lights = [states[n & 1]]
                    window.update_tray_tooltip()
                for n in range(50):
                    mode[0] = bool(n & 2)
                    old = window.tabs.widget(0)
                    window.on_loaded(([states[n & 1]], [self.sensor], ""))
                    self.flush_deletions()
                    if old is not None:
                        self.assertFalse(isValid(old))
                for n in range(16):
                    path = custom_paths[n % len(custom_paths)]
                    window.config["tray_icon"] = path
                    window._apply_panel_icon()
                    dialog = TraySettingsDialog(window, "", "room", {"room": "Study"},
                            default_icon=window._default_qicon)
                    dialog.icon_name = path
                    dialog.update_icon_preview()
                    dialog.restore_default_icon()
                    dialog.reject()
                    dialog.deleteLater()
                    self.flush_deletions()
                    self.assertFalse(isValid(dialog))
                window.config["tray_icon"] = ""
                mode[0] = False
                window.lights = [states[0]]
                window.update_tray_tooltip()
                drain()

            # First batch fills Qt/font/icon caches and establishes steady state.
            exercise()
            baseline_objects = len(window.findChildren(QObject))
            self.assertEqual(len(window._panel_icon_cache), 4)
            before = process_memory_bytes()
            already_tracing = tracemalloc.is_tracing()
            if not already_tracing:
                tracemalloc.start()
            try:
                drain()
                baseline_python = tracemalloc.get_traced_memory()[0]
                samples = []
                for batch in range(4):
                    exercise()
                    current = tracemalloc.get_traced_memory()[0]
                    rss = process_memory_bytes()
                    objects = len(window.findChildren(QObject))
                    samples.append((batch + 1, current - baseline_python, rss, objects))
                    self.assertLessEqual(objects, baseline_objects + 4)
                    self.assertFalse(window.findChildren(TraySettingsDialog))
                    self.assertEqual(len(window._panel_icon_cache), 4)
                retained = tracemalloc.get_traced_memory()[0] - baseline_python
                print(f"MEMORY_STRESS: warmup=1 batch; measured=2000 icon updates, "
                      f"200 refreshes, 64 custom icon/dialog cycles; "
                      f"baseline_objects={baseline_objects}; baseline_rss_bytes={before}; "
                      f"samples(batch,python_delta_bytes,rss_bytes,qt_objects)={samples}; "
                      f"final_python_delta_bytes={retained}", flush=True)
                # A generous guard against sustained Python allocation growth;
                # RSS is reported, not gated because native allocators retain arenas.
                self.assertLess(retained, 2 * 1024 * 1024)
            finally:
                if not already_tracing:
                    tracemalloc.stop()
            self.assertEqual(len(window._panel_pixmap_cache), 4)
            self.assertTrue(all(len(pixmaps) == 5 for pixmaps in window._panel_pixmap_cache.values()))
            self.assertEqual(len(item.pixmaps), 5)


    def test_repeated_refresh_disposes_old_pages_and_reuses_menu(self):
        window = self.window
        welcome = window.tabs.widget(0)
        window.on_loaded(([self.light], [self.sensor], ''))
        room, climate = (window.tabs.widget(i) for i in range(2))
        window.tabs.setCurrentIndex(1)
        submenu, = window._tray_menu.findChildren(QMenu)
        automatic, study = submenu.actions()
        for _ in range(20):
            window.on_loaded(([self.light], [self.sensor], ''))
            self.flush_deletions()
        self.assertFalse(any(isValid(page) for page in (welcome, room, climate)))
        self.assertEqual(window.tabs.currentIndex(), 1)
        self.assertEqual(len(window.tabs.findChildren(QScrollArea)), 2)
        self.assertEqual(window._tray_menu.findChildren(QMenu), [submenu])
        self.assertEqual(submenu.actions(), [automatic, study])
        with patch('app.write_config'):
            study.trigger()
            self.assertEqual(window.config['tray_room'], 'room')
            self.assertTrue(study.isChecked())
            automatic.trigger()
            self.assertEqual(window.config['tray_room'], '')
            self.assertTrue(automatic.isChecked())
        window.on_loaded(([replace(self.light, room_name='Office')], [], ''))
        self.flush_deletions()
        self.assertEqual([a.text() for a in submenu.actions()], ['Automatic (one approved room)', 'Office'])
        window.on_loaded(([], [], ''))
        self.flush_deletions()
        self.assertEqual(len(submenu.actions()), 1)
        self.assertFalse(window.tabs.findChildren(QScrollArea))
        self.assertEqual(window.tabs.count(), 1)

    def test_tray_settings_is_disposed_after_save_and_cancel(self):
        for dismiss in ('accept', 'reject'):
            QTimer.singleShot(0, lambda: getattr(self.app.activeModalWidget(), dismiss)())
            with patch('app.write_config'):
                self.window.change_tray_settings()
            self.flush_deletions()
            self.assertFalse(self.window.findChildren(TraySettingsDialog))


if __name__ == '__main__':
    unittest.main()
