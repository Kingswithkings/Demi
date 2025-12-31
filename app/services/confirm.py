def is_yes(text: str) -> bool:
    t = (text or "").strip().lower()
    return t in {"yes", "y", "yeah", "yep", "confirm", "ok", "okay", "sure"}

def is_no(text: str) -> bool:
    t = (text or "").strip().lower()
    return t in {"no", "n", "nope", "cancel", "stop", "don’t", "dont"}
