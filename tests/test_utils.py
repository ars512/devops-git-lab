import unittest

from src import utils


class UtilsTest(unittest.TestCase):
    def test_mask_account(self):
        self.assertEqual(utils.mask_account("1234567890"), "******7890")

    def test_normalize_phone(self):
        self.assertEqual(utils.normalize_phone("+7 (777) 123-45-67"), "77771234567")

    def test_normalize_phone_empty(self):
        self.assertEqual(utils.normalize_phone(""), "")

    def test_format_money(self):
        self.assertEqual(utils.format_money(5), "5.00")
