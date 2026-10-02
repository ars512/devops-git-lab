"""Logging helper."""
import logging

LEVEL = logging.DEBUG


def get_logger(name):
    logging.basicConfig(level=LEVEL)
    return logging.getLogger(name)
