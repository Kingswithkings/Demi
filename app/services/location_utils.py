# app/services/location_utils.py

from __future__ import annotations
import re
from typing import Optional

# Very lightweight area extractor (Phase 2 baseline)
# Later in Phase 3 we will replace with Google Places / Maps APIs.
KNOWN_AREAS = [
    "stratford",
    "canary wharf",
    "liverpool street",
    "shoreditch",
    "london bridge",
    "greenwich",
    "doncaster",
]

def extract_area(text: str) -> Optional[str]:
    """
    Try to infer an area from conversation history.
    Returns a best-guess area string or None.
    """
    if not text:
        return None

    t = text.lower()

    # Exact known areas first
    for area in KNOWN_AREAS:
        if area in t:
            return area.title()

    # Fallback: simple "in <word>" pattern
    m = re.search(r"\bin\s+([a-zA-Z\s]{3,30})\b", t)
    if m:
        guess = m.group(1).strip()
        # limit to first 3 words to avoid huge captures
        guess = " ".join(guess.split()[:3])
        return guess.title()

    return None
