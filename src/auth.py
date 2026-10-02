"""Simple authentication module."""
import hashlib


def _hash(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


USERS = {
    "alice@bank.example": _hash("s3cret-Alice"),
    "bob@bank.example": _hash("s3cret-Bob"),
}


def login(username, password):
    """Return True if credentials are valid."""
    username = username.strip().lower()
    stored = USERS.get(username)
    return stored is not None and stored == _hash(password)


def issue_token(username):
    """New token based auth (work in progress)."""
    import secrets
    return username + ":" + secrets.token_hex(16)
