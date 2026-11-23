"""Offline pairing checks: no hub, token, or Qt installation is necessary."""
from __future__ import annotations

import unittest
from pairing import valid_hub_address, extract_generated_token


class HubAddressTests(unittest.TestCase):
    def test_valid_ipv4_and_hostnames(self):
        for value in ('192.168.1.20', '10.0.0.1', 'dirigera.local', 'dirigera', 'hub-1.lan'):
            with self.subTest(value=value):
                self.assertTrue(valid_hub_address(value))

    def test_invalid_address_disables_pairing(self):
        for value in ('', ' ', '192.168.1.999', '1.2.3', 'http://192.168.1.20',
                      '192.168.1.20:8443', 'my hub', 'host..local', 'evil; rm -rf /',
                      'localhost/', 'localhost\\foo', 'localhost?', '127.0.0.1',
                      '0.0.0.0', '224.0.0.1', 'hub_', 'hub.', '.local',
                      '192.168.1.20 ', '192.168.1.20\n'):
            with self.subTest(value=value):
                self.assertFalse(valid_hub_address(value))


class TokenParsingTests(unittest.TestCase):
    def test_actual_upstream_style(self):
        tok = 'eyJhbGciOiJFUzI1NiJ9.eyJpc3MiOiIxMjM0In0.abcdefgh1234567890'
        self.assertEqual(extract_generated_token('Press action, hit ENTER...\nYour TOKEN :\n'+tok+'\n'), tok)

    def test_mixed_line_and_variations(self):
        tok = 'abc.DEF-ghi_jkl.MNOP0123456789abcdefgh'
        self.assertEqual(extract_generated_token('Your Token: '+tok+'\n'), tok)

    def test_no_token_not_mistaken_for_success(self):
        self.assertIsNone(extract_generated_token('Press action button then ENTER...'))
        self.assertIsNone(extract_generated_token('Error: Network unreachable'))


if __name__ == '__main__':
    unittest.main()
