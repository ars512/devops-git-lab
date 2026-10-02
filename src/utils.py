"""Helper functions."""


def mask_account(number):
    """Hide all but the last 4 digits of an account number."""
    digits = str(number)
    return "*" * (len(digits) - 4) + digits[-4:]


def normalize_phone(phone):
    """Keep only digits of a phone number."""
    return "".join(ch for ch in phone if ch.isdigit())


def format_money(amount):
    """Format amount with two decimals."""
    return "{:.2f}".format(amount)
