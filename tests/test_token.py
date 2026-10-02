import unittest

from src import auth


class TokenTest(unittest.TestCase):
    def test_issue_token(self):
        self.assertTrue(auth.issue_token("alice@bank.example").startswith("alice"))
