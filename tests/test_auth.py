import unittest

from src import auth


class AuthTest(unittest.TestCase):
    def test_valid_login(self):
        self.assertTrue(auth.login("alice@bank.example", "s3cret-Alice"))
