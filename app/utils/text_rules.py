import re
from typing import Optional

_THRESHOLD_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(km/h|kmh|mph|km\\h)", re.IGNORECASE)


def extract_threshold(text: str) -> Optional[tuple[float, str]]:
    match = _THRESHOLD_RE.search(text)
    if not match:
        return None
    return float(match.group(1)), match.group(2)
