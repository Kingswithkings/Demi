# app/services/location_suggester.py

from __future__ import annotations
from typing import Optional

DEFAULT_LOCATIONS = [
    "Costa Coffee",
    "Starbucks",
    "Pret A Manger",
    "Library",
    "WeWork",
]

def suggest_location(area: Optional[str], attempt: int = 0) -> str:
    """
    Simple deterministic suggestion.
    attempt: increments to rotate suggestions.
    """
    base = DEFAULT_LOCATIONS[attempt % len(DEFAULT_LOCATIONS)]
    if area:
        return f"{base}, {area}"
    return f"{base} (nearest to you)"
