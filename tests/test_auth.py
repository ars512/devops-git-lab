import unittest

from src import auth


class AuthTest(unittest.TestCase):
    def test_valid_login(self):
        self.assertTrue(auth.login("alice@bank.example", "s3cret-Alice"))

    def test_login_is_case_insensitive_and_trims_spaces(self):
        self.assertTrue(auth.login(" Alice@Bank.example ", "s3cret-Alice"))

    def test_wrong_password(self):
        self.assertFalse(auth.login("alice@bank.example", "nope"))
