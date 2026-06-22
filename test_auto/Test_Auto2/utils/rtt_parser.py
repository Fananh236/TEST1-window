import re
from typing import Optional


def detect_receipt(line: str) -> bool:
    if not line:
        return False
    return "im:invokecommandrequest" in line.lower()


def detect_on_start(line: str) -> bool:
    if not line:
        return False
    return bool(re.search(r"turning light\s+on", line, re.IGNORECASE))


def detect_on_done(line: str) -> bool:
    if not line:
        return False
    return bool(re.search(r"\bLight\s+ON\b", line, re.IGNORECASE))


def detect_off_start(line: str) -> bool:
    if not line:
        return False
    return bool(re.search(r"turning light\s+off", line, re.IGNORECASE))


def detect_off_done(line: str) -> bool:
    if not line:
        return False
    return bool(re.search(r"\bLight\s+OFF\b", line, re.IGNORECASE))


def detect_command(line: str) -> Optional[str]:
    """Detect a chip-tool onoff command in a Pi log line.

    Returns: 'on'|'off'|'toggle' or None
    """
    if not line:
        return None
    m = re.search(r"chip-tool\s+onoff\s+(on|off|toggle)\s+\d+\s+\d+", line, re.IGNORECASE)
    if not m:
        return None
    return m.group(1).lower()
