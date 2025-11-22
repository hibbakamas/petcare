# app/utils/join_code.py
"""Utilities for generating short household join codes."""

import random

ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def gen_join_code(n: int = 6) -> str:
    """Generate a readable join code (no ambiguous characters)."""
    return "".join(random.choice(ALPHABET) for _ in range(n))