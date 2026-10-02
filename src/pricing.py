"""Price calculation."""


def calc_total(prices, discount_pct=0):
    """Sum prices and apply a percentage discount."""
    total = sum(prices) * (1 - discount_pct / 100.0)
    return round(total, 2)
