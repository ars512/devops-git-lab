import unittest

from src import pricing


class PricingTest(unittest.TestCase):
    def test_total(self):
        self.assertEqual(pricing.calc_total([19.99, 10.00]), 29.99)

    def test_discount(self):
        self.assertEqual(pricing.calc_total([19.99, 10.00], 10), 26.99)
