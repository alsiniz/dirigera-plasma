"""No Qt dependency; deterministic active icon-theme discovery tests."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from icon_theme import active_theme, discover_icon_files, search_paths


class IconThemeTests(unittest.TestCase):
    def test_picks_user_kde_theme_over_qt_fallback(self):
        with tempfile.TemporaryDirectory() as temp:
            cfg = Path(temp) / 'kdeglobals'
            cfg.write_text('[Icons]\nTheme=Papirus-Dark\n')
            self.assertEqual(active_theme('breeze', cfg), 'Papirus-Dark')

    def test_falls_back_to_qt_theme(self):
        with tempfile.TemporaryDirectory() as temp:
            self.assertEqual(active_theme('Adwaita', Path(temp) / 'missing'), 'Adwaita')

    def test_active_theme_and_inheritance_not_unrelated_themes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            theme = root / 'MyTheme'
            (theme / 'scalable' / 'status').mkdir(parents=True)
            (theme / 'index.theme').write_text('[Icon Theme]\nInherits=FallbackIcons\n')
            (theme / 'scalable' / 'status' / 'weather-clear.svg').write_text('a')
            fallback = root / 'FallbackIcons' / '48x48' / 'apps'
            fallback.mkdir(parents=True)
            (fallback / 'device.png').write_bytes(b'b')
            unrelated = root / 'Unrelated' / 'apps'
            unrelated.mkdir(parents=True)
            (unrelated / 'spy.png').write_bytes(b'c')
            icons = discover_icon_files('MyTheme', [root])
            self.assertIn('weather-clear', icons)
            self.assertIn('device', icons)
            self.assertNotIn('spy', icons)

    def test_user_theme_precedence(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for base in ['user', 'system']:
                path = root / base / 'MyTheme' / 'apps'
                path.mkdir(parents=True)
                (path / 'device.png').write_bytes(b'a')
            icons = discover_icon_files('MyTheme', [root / 'user', root / 'system'])
            self.assertIn('/user/', icons['device'])

    def test_xdg_search_paths(self):
        with tempfile.TemporaryDirectory() as temp:
            with patch.dict(os.environ, {'XDG_DATA_HOME': temp + '/mine', 'XDG_DATA_DIRS': temp + '/sys:/usr/share'}):
                found = search_paths(['/tmp/custom-icons'])
                self.assertIn(Path(temp) / 'mine' / 'icons', found)
                self.assertIn(Path(temp) / 'sys' / 'icons', found)
                self.assertIn(Path('/tmp/custom-icons'), found)


if __name__ == '__main__':
    unittest.main()
