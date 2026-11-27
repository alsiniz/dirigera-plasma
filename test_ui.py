"""Qt slider regression test. Run with QT_QPA_PLATFORM=offscreen on CI."""
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
import os
import unittest
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
try:
    from PySide6.QtCore import Qt, QPoint, QPointF, QCoreApplication, QEvent, QTimer
    from PySide6.QtTest import QTest
    from PySide6.QtGui import QColor, QIcon, QPalette, QWheelEvent
    from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QMenu, QScrollArea
    from shiboken6 import isValid
    from app import panel_is_dark, IconPickerDialog, ClickToJumpSlider, TraySettingsDialog, ConnectionDialog, MainWindow
    from core import EnvironmentInfo, LightInfo
except ImportError:
    ClickToJumpSlider = None


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
