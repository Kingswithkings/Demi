# app/services/intent_detector.py

import re

MEETING_PATTERNS = [
    r"\bmeet(ing)?\b",
    r"\bschedule\b",
    r"\bset up\b",
    r"\bbook\b",
    r"\bcatch up\b",
    r"\bdiscuss\b",
    r"\bchat\b",
    r"\bcall\b",
    r"\bzoom\b",
    r"\bteams\b",
    r"\bgoogle meet\b",
    r"\bin person\b",
    r"\bsee you\b",
]

TIME_PATTERNS = [
    r"\btoday\b",
    r"\btomorrow\b",
    r"\bnext week\b",
    r"\bthis week\b",
    r"\bmon(day)?\b|\btue(sday)?\b|\bwed(nesday)?\b|\bthu(rsday)?\b|\bfri(day)?\b|\bsat(urday)?\b|\bsun(day)?\b",
    r"\b\d{1,2}(:\d{2})?\s?(am|pm)\b",   # 3pm, 3:30pm
    r"\b\d{1,2}\s?(am|pm)\b",
    r"\b\d{1,2}:\d{2}\b",               # 15:00
]

LOCATION_PATTERNS = [
    r"\bat\b\s+\w+",                    # "at Costa"
    r"\bin\b\s+\w+",                    # "in Stratford"
    r"\bstratford\b|\bcosta\b|\bstarbucks\b|\blibrary\b|\boffice\b|\bcafe\b|\brestaurant\b",
]

YES_PATTERNS = [
    r"^\s*(yes|yeah|yep|ok|okay|sure|go ahead|please do|confirm)\s*\.?\s*$"
]

NO_PATTERNS = [
    r"^\s*(no|nope|not now|later|don't|do not|cancel)\s*\.?\s*$"
]


def detect_meeting_intent(text: str) -> bool:
    """
    Lightweight heuristic classifier.
    True if message contains meeting + (time or location) signals OR strong meeting phrases.
    """
    t = (text or "").lower()

    meeting_hit = any(re.search(p, t) for p in MEETING_PATTERNS)
    time_hit = any(re.search(p, t) for p in TIME_PATTERNS)
    location_hit = any(re.search(p, t) for p in LOCATION_PATTERNS)

    # Strong signal: meeting-like phrase alone is enough
    if meeting_hit and (time_hit or location_hit):
        return True

    # Also treat explicit scheduling words as intent even without time/location
    explicit = re.search(r"\b(schedule|set up|book)\b", t) is not None
    return bool(meeting_hit or explicit)


def is_yes(text: str) -> bool:
    t = (text or "").lower()
    return any(re.search(p, t) for p in YES_PATTERNS)


def is_no(text: str) -> bool:
    t = (text or "").lower()
    return any(re.search(p, t) for p in NO_PATTERNS)

def detect_meeting_intent(text: str) -> bool:
    keywords = ["meet", "meeting", "catch up", "discuss"]
    return any(k in text.lower() for k in keywords)

def is_yes(text: str) -> bool:
    return text.strip().lower() in ["yes", "yeah", "yep"]

def is_no(text: str) -> bool:
    return text.strip().lower() in ["no", "nah"]

