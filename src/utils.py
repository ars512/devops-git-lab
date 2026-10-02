"""Helper functions."""


def normalize_phone(phone):
    """Keep only digits of a phone number."""
    return "".join(ch for ch in phone if ch.isdigit())


def format_money(amount):
    """Format amount with two decimals."""
    return "{:.2f}".format(amount)
